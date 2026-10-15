"""Direct messages between any two signed-in users; only the two participants can read a conversation."""
from ..auth import require_user
from ..db import now_iso
from ..errors import bad_request, forbidden, not_found
from ..responses import JsonResponse
from ..validation import require_text
from . import ROUTER
from .lookups import get_user, is_anonymous
from .serializers import brief_user


def unread_total(conn, user_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM messages m JOIN conversations c ON c.id=m.conversation_id"
        " WHERE (c.user_low=? OR c.user_high=?) AND m.sender_id!=? AND m.read_at IS NULL",
        (user_id, user_id, user_id),
    ).fetchone()[0]


def _message_json(row, viewer_id: int) -> dict:
    return {"id": row["id"], "conversation_id": row["conversation_id"], "sender_id": row["sender_id"], "body": row["body"],
            "created": row["created"], "read": row["read_at"] is not None, "mine": row["sender_id"] == viewer_id}


def _participant_conversation(ctx, conversation_id: int):
    user = require_user(ctx)
    row = ctx.db.execute("SELECT * FROM conversations WHERE id=?", (conversation_id,)).fetchone()
    if not row:
        raise not_found("That conversation does not exist.")
    if user["id"] not in (row["user_low"], row["user_high"]):
        raise forbidden("You can only open your own conversations.")
    return row


def _conversation_json(ctx, row) -> dict:
    me = ctx.user["id"]
    other = get_user(ctx.db, row["user_high"] if row["user_low"] == me else row["user_low"])
    last = ctx.db.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY id DESC LIMIT 1", (row["id"],)).fetchone()
    unread = ctx.db.execute(
        "SELECT COUNT(*) FROM messages WHERE conversation_id=? AND sender_id!=? AND read_at IS NULL", (row["id"], me)
    ).fetchone()[0]
    audition = ctx.db.execute("SELECT id, title FROM auditions WHERE id=?", (row["audition_id"],)).fetchone() if row["audition_id"] else None
    return {
        "id": row["id"], "other": brief_user(other),
        "context": {"opportunity": dict(audition) if audition else None, "submission_id": row["submission_id"]},
        "last_message": _message_json(last, me) if last else None, "unread_count": unread,
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
    return {"conversation": _conversation_json(ctx, row), "messages": [_message_json(m, ctx.user["id"]) for m in messages]}


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
        if me == audition["director_id"] and is_anonymous(audition, submission):
            raise forbidden("This applicant is anonymous under blind review. Reveal their identity before messaging them.")
        audition_id = audition_id or audition["id"]
    return audition_id, submission_id


def _insert_message(ctx, conversation_id: int, body: str) -> dict:
    cur = ctx.db.execute(
        "INSERT INTO messages (conversation_id, sender_id, body, created) VALUES (?,?,?,?)",
        (conversation_id, ctx.user["id"], body, now_iso()),
    )
    return _message_json(ctx.db.execute("SELECT * FROM messages WHERE id=?", (cur.lastrowid,)).fetchone(), ctx.user["id"])


@ROUTER.route("POST", "/api/conversations")
def start_conversation(ctx):
    """{user_id, body?, audition_id?, submission_id?}: opens (or returns) your one conversation with that user,
    optionally linked to an audition/gig or one of your submissions for context, and sends `body` if given."""
    me = require_user(ctx)["id"]
    data = ctx.json()
    other_id = data.get("user_id")
    if not isinstance(other_id, int) or not get_user(ctx.db, other_id):
        raise not_found("That person does not exist.")
    if other_id == me:
        raise bad_request("You cannot start a conversation with yourself.")
    audition_id, submission_id = _context_ids(ctx, data)
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
