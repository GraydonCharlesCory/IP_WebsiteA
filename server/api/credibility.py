"""Verified badges and endorsements shown on musician profiles."""
from ..auth import require_role, require_user
from ..db import now_iso
from ..errors import ApiError, forbidden
from ..responses import JsonResponse
from ..validation import require_choice, require_text
from . import ROUTER
from .lookups import get_musician_by_handle
from .serializers import brief_user

BADGE_KINDS = ("union", "school", "ensemble")


def badge_json(row) -> dict:
    return {"id": row["id"], "kind": row["kind"], "label": row["label"], "verified_by_tutti": bool(row["verified_by_tutti"])}


def endorsement_json(conn, row) -> dict:
    author = conn.execute("SELECT * FROM users WHERE id=?", (row["author_id"],)).fetchone()
    return {"id": row["id"], "text": row["text"], "relationship": row["relationship"], "created": row["created"],
            "author": brief_user(author)}


def badges_for(conn, user_id: int) -> list:
    rows = conn.execute("SELECT * FROM badges WHERE user_id=? ORDER BY verified_by_tutti DESC, id", (user_id,))
    return [badge_json(r) for r in rows]


def endorsements_for(conn, user_id: int) -> list:
    rows = conn.execute("SELECT * FROM endorsements WHERE musician_id=? ORDER BY created DESC, id DESC", (user_id,))
    return [endorsement_json(conn, r) for r in rows]


@ROUTER.route("POST", "/api/musicians/<handle>/endorsements")
def endorse(ctx):
    """Directors and teachers: {text, relationship?} (for example "Taught him for three years")."""
    author = require_user(ctx)
    if author["role"] != "director" and not author["is_teacher"]:
        raise forbidden("Only directors and teachers can endorse a musician.")
    musician = get_musician_by_handle(ctx.db, ctx.params["handle"])
    if musician["id"] == author["id"]:
        raise forbidden("You cannot endorse yourself.")
    data = ctx.json()
    text = require_text(data, "text", "your endorsement", 1000)
    relationship = (data.get("relationship") or "").strip()[:120]
    cur = ctx.db.execute(
        "INSERT INTO endorsements (musician_id, author_id, relationship, text, created) VALUES (?,?,?,?,?)",
        (musician["id"], author["id"], relationship, text, now_iso()),
    )
    ctx.db.commit()
    row = ctx.db.execute("SELECT * FROM endorsements WHERE id=?", (cur.lastrowid,)).fetchone()
    return JsonResponse({"endorsement": endorsement_json(ctx.db, row)}, 201)


@ROUTER.route("POST", "/api/me/badges")
def claim_badge(ctx):
    """Musician: {kind: union|school|ensemble, label}. Self-claimed badges are never "verified by Tutti"."""
    musician = require_role(ctx, "musician", "add badges")
    data = ctx.json()
    kind = require_choice(data.get("kind"), BADGE_KINDS, "badge kind")
    label = require_text(data, "label", "the badge label", 120)
    if ctx.db.execute("SELECT 1 FROM badges WHERE user_id=? AND lower(label)=lower(?)", (musician["id"], label)).fetchone():
        raise ApiError(409, "You already have a badge with that label.")
    cur = ctx.db.execute(
        "INSERT INTO badges (user_id, kind, label, verified_by_tutti, created) VALUES (?,?,?,0,?)",
        (musician["id"], kind, label, now_iso()),
    )
    ctx.db.commit()
    return JsonResponse({"badge": badge_json(ctx.db.execute("SELECT * FROM badges WHERE id=?", (cur.lastrowid,)).fetchone())}, 201)
