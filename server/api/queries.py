"""Shared list queries returning JSON-ready dicts."""
from ..auth import require_user
from .serializers import audition_json, brief_user, clip_json, full_user, post_json


def musicians_list(conn, category=None):
    sql, args = "SELECT * FROM users WHERE role='musician'", []
    if category:
        sql, args = sql + " AND category=?", [category]
    return [full_user(r) for r in conn.execute(sql + " ORDER BY name", args)]


def clips_list(settings, conn, category=None, owner_id=None, limit=50):
    sql, args = "SELECT * FROM clips WHERE 1=1", []
    if category:
        sql, args = sql + " AND category=?", args + [category]
    if owner_id:
        sql, args = sql + " AND owner_id=?", args + [owner_id]
    rows = conn.execute(sql + " ORDER BY created DESC, id DESC LIMIT ?", args + [limit]).fetchall()
    owners = {}
    result = []
    for row in rows:
        if row["owner_id"] not in owners:
            owners[row["owner_id"]] = conn.execute("SELECT * FROM users WHERE id=?", (row["owner_id"],)).fetchone()
        result.append(clip_json(settings, row, owners[row["owner_id"]]))
    return result


def posts_list(settings, conn, category=None, author_id=None, limit=20):
    sql, args = "SELECT * FROM posts WHERE 1=1", []
    if category:
        sql, args = sql + " AND category=?", args + [category]
    if author_id:
        sql, args = sql + " AND author_id=?", args + [author_id]
    rows = conn.execute(sql + " ORDER BY created DESC, id DESC LIMIT ?", args + [limit]).fetchall()
    return [post_json(settings, conn, r) for r in rows]


def auditions_for_list(ctx, category=None, mine=False):
    """Audition postings for a signed-in user.

    Musicians see `my_submission` (status shown as "Submitted", never scores). The posting director also
    sees submission counts for their own auditions.
    """
    user = require_user(ctx)
    sql, args = "SELECT * FROM auditions WHERE 1=1", []
    if category:
        sql, args = sql + " AND category=?", args + [category]
    if mine:
        sql, args = sql + " AND director_id=?", args + [user["id"]]
    rows = ctx.db.execute(sql + " ORDER BY status DESC, deadline ASC, id", args).fetchall()
    return [audition_detail_json(ctx, row) for row in rows]


def audition_detail_json(ctx, row):
    user = ctx.user
    director = ctx.db.execute("SELECT * FROM users WHERE id=?", (row["director_id"],)).fetchone()
    data = audition_json(row, director)
    if user["role"] == "musician":
        mine = ctx.db.execute(
            "SELECT id, created FROM submissions WHERE audition_id=? AND musician_id=?", (row["id"], user["id"])
        ).fetchone()
        data["my_submission"] = {"id": mine["id"], "status": "Submitted", "created": mine["created"]} if mine else None
    elif row["director_id"] == user["id"]:
        data["submission_count"] = ctx.db.execute(
            "SELECT COUNT(*) FROM submissions WHERE audition_id=?", (row["id"],)
        ).fetchone()[0]
        data["owned_by_me"] = True
    return data
