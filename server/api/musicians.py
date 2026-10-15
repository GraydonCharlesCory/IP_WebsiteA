"""Public musician profiles (visible to everyone, even signed out) and editing your own."""
from ..auth import require_role
from ..validation import optional_text, parse_flag, string_list
from . import ROUTER
from .credibility import badges_for, endorsements_for
from .lookups import get_musician_by_handle
from .queries import clips_list, musicians_list, posts_list
from .serializers import dumps, full_user


@ROUTER.route("GET", "/api/musicians")
def list_musicians(ctx):
    """Public. Filters: ?category=&teacher=1&instrument=<text>. Each entry carries its badges."""
    people = musicians_list(ctx.db, ctx.query.get("category"))
    if ctx.query.get("teacher") and parse_flag(ctx.query["teacher"], "teacher"):
        people = [p for p in people if p["is_teacher"]]
    if ctx.query.get("instrument"):
        people = [p for p in people if ctx.query["instrument"].lower() in p["instrument"].lower()]
    return {"musicians": [{**p, "badges": badges_for(ctx.db, p["id"])} for p in people]}


@ROUTER.route("GET", "/api/musicians/<handle>")
def musician_profile(ctx):
    musician = get_musician_by_handle(ctx.db, ctx.params["handle"])
    clips = clips_list(ctx.settings, ctx.db, owner_id=musician["id"])
    posts = posts_list(ctx.settings, ctx.db, author_id=musician["id"], limit=50)
    return {"musician": full_user(musician), "clips": clips, "posts": posts,
            "badges": badges_for(ctx.db, musician["id"]), "endorsements": endorsements_for(ctx.db, musician["id"]),
            "stats": {"clips": len(clips), "posts": len(posts)}}


@ROUTER.route("PUT", "/api/me")
def update_profile(ctx):
    """Edit your own bio, instrument, location and teaching details (is_teacher, teacher_blurb, instruments_taught[], rate_text)."""
    user = require_role(ctx, "musician", "edit a musician profile")
    data = ctx.json()
    values = {field: optional_text(data, field, 1000) if field in data else user[field]
              for field in ("bio", "instrument", "location")}
    values["is_teacher"] = int(parse_flag(data["is_teacher"], "is_teacher")) if "is_teacher" in data else user["is_teacher"]
    values["teacher_blurb"] = optional_text(data, "teacher_blurb", 1000) if "teacher_blurb" in data else user["teacher_blurb"]
    values["rate_text"] = optional_text(data, "rate_text", 200) if "rate_text" in data else user["rate_text"]
    values["instruments_taught"] = dumps(string_list(data, "instruments_taught")) if "instruments_taught" in data else user["instruments_taught"]
    assignments = ", ".join(f"{name}=?" for name in values)
    ctx.db.execute(f"UPDATE users SET {assignments} WHERE id=?", [*values.values(), user["id"]])
    ctx.db.commit()
    return {"user": full_user(ctx.db.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone())}
