"""Creating posts and profile clips (musicians only); reading clips (public)."""
from ..auth import require_role
from ..db import now_iso
from ..durations import mp4_duration
from ..errors import bad_request
from ..media import save_upload
from ..responses import JsonResponse
from ..validation import require_category, require_text
from . import ROUTER
from .queries import clips_list
from .serializers import clip_json, post_json


@ROUTER.route("GET", "/api/clips")
def list_clips(ctx):
    category = ctx.query.get("category")
    if category:
        require_category(category)
    return {"clips": clips_list(ctx.settings, ctx.db, category, limit=ctx.query_int("limit", 24))}


@ROUTER.route("POST", "/api/clips")
def upload_profile_clip(ctx):
    """Raw MP4 body (Content-Type video/mp4); query: title, instrument (optional)."""
    user = require_role(ctx, "musician", "add profile clips")
    title = require_text(ctx.query, "title", "a clip title", 120)
    name = save_upload(ctx, ctx.settings.profile_uploads_dir)
    cur = ctx.db.execute(
        "INSERT INTO clips (owner_id, title, file, source, category, instrument, duration_sec, created) VALUES (?,?,?,?,?,?,?,?)",
        (user["id"], title, name, "upload", user["category"], ctx.query.get("instrument") or user["instrument"],
         mp4_duration(ctx.settings.profile_uploads_dir / name), now_iso()),
    )
    ctx.db.commit()
    row = ctx.db.execute("SELECT * FROM clips WHERE id=?", (cur.lastrowid,)).fetchone()
    return JsonResponse({"clip": clip_json(ctx.settings, row, user)}, 201)


@ROUTER.route("POST", "/api/posts")
def create_post(ctx):
    user = require_role(ctx, "musician", "post to the feed")
    data = ctx.json()
    body = require_text(data, "body", "your post", 2000)
    category = require_category(data.get("category") or user["category"])
    clip_id = data.get("clip_id")
    if clip_id is not None:
        owned = ctx.db.execute("SELECT id FROM clips WHERE id=? AND owner_id=?", (clip_id, user["id"])).fetchone()
        if not owned:
            raise bad_request("You can only attach one of your own clips to a post.")
    cur = ctx.db.execute(
        "INSERT INTO posts (author_id, category, body, clip_id, created) VALUES (?,?,?,?,?)",
        (user["id"], category, body, clip_id, now_iso()),
    )
    ctx.db.commit()
    row = ctx.db.execute("SELECT * FROM posts WHERE id=?", (cur.lastrowid,)).fetchone()
    return JsonResponse({"post": post_json(ctx.settings, ctx.db, row)}, 201)
