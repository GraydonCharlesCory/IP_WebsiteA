"""Direct messages between any two signed-in users; only the two participants can read a conversation."""
from ..auth import require_user
from ..config import log
from ..db import now_iso
from ..errors import bad_request, forbidden, not_found
from ..responses import JsonResponse
from ..validation import require_text
from . import ROUTER
from .lookups import get_user
from .serializers import anonymous_applicant, brief_user


def unread_total(conn, user_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM messages m JOIN conversations c ON c.id=m.conversation_id"
        " WHERE (c.user_low=? OR c.user_high=?) AND m.sender_id!=? AND m.read_at IS NULL",
        (user_id, user_id, user_id),
    ).fetchone()[0]


def _is_director(ctx) -> bool:
    return ctx.user["role"] == "director"


def _message_json(ctx, row) -> dict:
    """A director never learns the other person's user id, so only their own messages carry a sender id."""
    mine = row["sender_id"] == ctx.user["id"]
    return {"id": row["id"], "conversation_id": row["conversation_id"], "sender_id": row["sender_id"] if mine or not _is_director(ctx) else None,
            "body": row["body"], "created": row["created"], "read": row["read_at"] is not None, "mine": mine}


def _participant_conversation(ctx, conversation_id: int):
    user = require_user(ctx)
    row = ctx.db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    if not row:
        raise not_found("That conversation does not exist.")
    if user["id"] not in (row["user_low"], row["user_high"]):
        raise forbidden("You can only open your own conversations.")
    return row


def _other_party(ctx, row) -> dict:
    """The person on the other side as the viewer may see them: a director only ever sees a musician as an anonymous applicant."""
    other = get_user(ctx.db, row["user_high"] if row["user_low"] == ctx.user["id"] else row["user_low"])
    if not (_is_director(ctx) and other["role"] == "musician"):
        return brief_user(other)
    if row["submission_id"]:
        return anonymous_applicant(row["submission_id"], other["instrument"])
    return anonymous_applicant(row["id"], other["instrument"], prefix="C")


def _conversation_json(ctx, row) -> dict:
    me = ctx.user["id"]
    last = ctx.db.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT 1", (row["id"],)).fetchone()
    unread = ctx.db.execute(
        "SELECT COUNT(*) FROM messages WHERE conversation_id=? AND sender_id!=? AND read_at IS NULL", (row["id"], me)
    ).fetchone()[0]
    audition = ctx.db.execute("SELECT id, title FROM auditions WHERE id=?", (row["audition_id"],)).fetchone() if row["audition_id"] else None
    return {
        "id": row["id"], "other": _other_party(ctx, row),
        "context": {"opportunity": dict(audition) if audition else None, "submission_id": row["submission_id"]},
        "last_message": _message_json(ctx, last) if last else None, "unread_count": unread,
        "updated": last["created"] if last else row["created"],
    }


@ROUTER.route("GET", "/api/conversations")
def list_conversations(ctx):
    """Your conversations, newest activity first, with the last message and your unread count."""
    me = require_user(ctx)["id"]
    rows = ctx.db.execute("SELECT * FROM conversations WHERE user_low=? OR user_high=?", (me, me)).fetchall()
    items = sorted((_conversation_json(ctx, r) for r in rows), key=lambda c: (c["updated"], c["id"]), reverse=True)
    return {"conversations": items, "unread_total": unread_total(ctx.db, me)}


@ROUTER.route("GET", "/api/conversations/<conversation_id:int>")
def get_conversation(ctx):
    """Participants only. Opening does not mark messages read: call POST .../read."""
    row = _participant_conversation(ctx, ctx.params["conversation_id"])
    messages = ctx.db.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY id", (row["id"],)).fetchall()
    return {"conversation": _conversation_json(ctx, row), "messages": [_message_json(ctx, m) for m in messages]}


def _context_ids(ctx, data) -> tuple:
    """Validated (audition_id, submission_id) a new conversation may be linked to."""
    audition_id, submission_id = data.get("audition_id"), data.get("submission_id")
    if audition_id is not None and not ctx.db.execute("SELECT 1 FROM auditions WHERE id=?", (audition_id,)).fetchone():
        raise not_found("That audition or gig does not exist.")
    if submission_id is not None:
        submission = ctx.db.execute("SELECT * FROM submissions WHERE id=?", (submission_id,)).fetchone()
        audition = ctx.db.execute("SELECT * FROM auditions WHERE id=?", (submission["audition_id"],)).fetchone() if submission else None
        me = ctx.user["id"]
        if not submission or me not in (submission["musician_id"], audition["director_id"]):
            raise forbidden("You can only link a conversation to your own submission or one sent to your audition.")
        audition_id = audition_id or audition["id"]
    return audition_id, submission_id


def _recipient_id(ctx, data, submission_id) -> int:
    """Who a new conversation goes to. A director reaches a musician only through a submission sent to their audition,
    so the applicant's id never leaves the server; otherwise the person is named with `user_id` (a director still sees a
    musician as anonymous in every response)."""
    if _is_director(ctx) and submission_id is not None:
        return ctx.db.execute("SELECT musician_id FROM submissions WHERE id=?", (submission_id,)).fetchone()["musician_id"]
    other_id = data.get("user_id")
    other = get_user(ctx.db, other_id) if isinstance(other_id, int) else None
    if not other:
        raise not_found("That person does not exist.")
    if other_id == ctx.user["id"]:
        raise bad_request("You cannot start a conversation with yourself.")
    return other_id


def _insert_message(ctx, conversation_id: int, body: str) -> dict:
    cur = ctx.db.execute(
        "INSERT INTO messages (conversation_id, sender_id, body, created) VALUES (?,?,?,?)",
        (conversation_id, ctx.user["id"], body, now_iso()),
    )
    return _message_json(ctx, ctx.db.execute("SELECT * FROM messages WHERE id=?", (cur.lastrowid,)).fetchone())


@ROUTER.route("POST", "/api/conversations")
def start_conversation(ctx):
    """{user_id, body?, audition_id?, submission_id?}: opens (or returns) your one conversation with that user,
    optionally linked to an audition/gig or one of your submissions for context, and sends `body` if given."""
    me = require_user(ctx)["id"]
    data = ctx.json()
    audition_id, submission_id = _context_ids(ctx, data)
    other_id = _recipient_id(ctx, data, submission_id)
    body = require_text(data, "body", "your message", 4000) if data.get("body") is not None else None
    low, high = sorted((me, other_id))
    row = ctx.db.execute("SELECT * FROM conversations WHERE user_low=? AND user_high=?", (low, high)).fetchone()
    created = row is None
    if created:
        cur = ctx.db.execute(
            "INSERT INTO conversations (user_low, user_high, audition_id, submission_id, created) VALUES (?,?,?,?,?)",
            (low, high, audition_id, submission_id, now_iso()),
        )
        conversation_id = cur.lastrowid
    else:
        conversation_id = row["id"]
        if audition_id or submission_id:
            ctx.db.execute("UPDATE conversations SET audition_id=?, submission_id=? WHERE id=?", (audition_id, submission_id, conversation_id))
    if body:
        _insert_message(ctx, conversation_id, body)
    ctx.db.commit()
    row = ctx.db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    return JsonResponse({"conversation": _conversation_json(ctx, row)}, 201 if created else 200)


@ROUTER.route("POST", "/api/conversations/<conversation_id:int>/messages")
def send_message(ctx):
    """Participants: {body}. The other person's unread count goes up."""
    row = _participant_conversation(ctx, ctx.params["conversation_id"])
    message = _insert_message(ctx, row["id"], require_text(ctx.json(), "body", "your message", 4000))
    ctx.db.commit()
    return JsonResponse({"message": message}, 201)


@ROUTER.route("POST", "/api/conversations/<conversation_id:int>/read")
def mark_read(ctx):
    """Participants: marks the other person's messages as read; returns your new unread total."""
    row = _participant_conversation(ctx, ctx.params["conversation_id"])
    ctx.db.execute(
        "UPDATE messages SET read_at=? WHERE conversation_id=? AND sender_id!=? AND read_at IS NULL",
        (now_iso(), row["id"], ctx.user["id"]),
    )
    ctx.db.commit()
    return {"ok": True, "unread_total": unread_total(ctx.db, ctx.user["id"])}
