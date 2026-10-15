"""Shared list queries returning JSON-ready dicts."""
from .serializers import clip_json, full_user, post_json


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
