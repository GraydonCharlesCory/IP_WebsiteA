"""Public musician profiles (visible to everyone, even signed out) and editing your own."""
from ..auth import require_role
from ..validation import optional_text
from . import ROUTER
from .lookups import get_musician_by_handle
from .queries import clips_list, musicians_list, posts_list
from .serializers import full_user


@ROUTER.route("GET", "/api/musicians")
def list_musicians(ctx):
    return {"musicians": musicians_list(ctx.db, ctx.query.get("category"))}


@ROUTER.route("GET", "/api/musicians/<handle>")
def musician_profile(ctx):
    musician = get_musician_by_handle(ctx.db, ctx.params["handle"])
    clips = clips_list(ctx.settings, ctx.db, owner_id=musician["id"])
    posts = posts_list(ctx.settings, ctx.db, author_id=musician["id"], limit=50)
    return {"musician": full_user(musician), "clips": clips, "posts": posts,
            "stats": {"clips": len(clips), "posts": len(posts)}}


@ROUTER.route("PUT", "/api/me")
def update_profile(ctx):
    """Edit your own bio, instrument or location."""
    user = require_role(ctx, "musician", "edit a musician profile")
    data = ctx.json()
    values = {field: optional_text(data, field, 1000) if field in data else user[field]
              for field in ("bio", "instrument", "location")}
    ctx.db.execute("UPDATE users SET bio=?, instrument=?, location=? WHERE id=?",
                   (values["bio"], values["instrument"], values["location"], user["id"]))
    ctx.db.commit()
    return {"user": full_user(ctx.db.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone())}
