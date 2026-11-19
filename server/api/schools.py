"""School-owned pages, programs, activities and alumni links."""
import json

from ..auth import require_role, require_user
from ..demo_enrichment import school_examples
from ..errors import forbidden, not_found
from ..validation import optional_text, require_text, string_list
from . import ROUTER


def posting_account(ctx):
    user = require_user(ctx)
    if user["role"] not in ("director", "school"):
        raise forbidden("Only director and school accounts can manage opportunities.")
    return user


def get_school(conn, school_id):
    row = conn.execute("SELECT * FROM schools WHERE id=?", (school_id,)).fetchone()
    if not row:
        raise not_found("School not found. Choose a school page from the directory.")
    return row


def owned_school(ctx, school_id):
    user = require_role(ctx, "school", "manage school pages")
    row = get_school(ctx.db, school_id)
    if row["owner_id"] != user["id"]:
        raise forbidden("You can only manage your school's page and opportunities.")
    return row


def school_json(ctx, row):
    data = dict(row)
    data.pop("owner_id")
    data["owned_by_me"] = bool(ctx.user and ctx.user["role"] == "school" and ctx.user["id"] == row["owner_id"])
    for field in ("programs", "activities"):
        data[field] = json.loads(data[field])
    data["alumni"] = [dict(r) for r in ctx.db.execute(
        "SELECT u.id,u.name,u.handle,u.instrument FROM alumni a JOIN users u ON u.id=a.musician_id WHERE a.school_id=?", (row["id"],))]
    data["demo_enrichment"] = school_examples(ctx.db, row, bool(data["alumni"]))
    return data


@ROUTER.route("GET", "/api/schools")
def school_directory(ctx):
    return {"schools": [school_json(ctx, r) for r in ctx.db.execute("SELECT * FROM schools ORDER BY name")]}


@ROUTER.route("GET", "/api/schools/<school_id:int>")
def school_page(ctx):
    return {"school": school_json(ctx, get_school(ctx.db, ctx.params["school_id"]))}


@ROUTER.route("PUT", "/api/schools/<school_id:int>")
def edit_school(ctx):
    row = owned_school(ctx, ctx.params["school_id"])
    data = ctx.json()
    values = {key: optional_text(data, key, 3000) if key in data else row[key] for key in ("location", "about")}
    values["name"] = require_text(data, "name", "a school name", 160) if "name" in data else row["name"]
    values.update({key: json.dumps(string_list(data, key)) if key in data else row[key] for key in ("programs", "activities")})
    ctx.db.execute(f"UPDATE schools SET {','.join(key+'=?' for key in values)} WHERE id=?", [*values.values(), row["id"]])
    ctx.db.commit()
    return school_page(ctx)


@ROUTER.route("PUT", "/api/schools/<school_id:int>/alumni/<musician_id:int>")
def add_alumnus(ctx):
    row = owned_school(ctx, ctx.params["school_id"])
    musician = ctx.db.execute("SELECT id FROM users WHERE id=? AND role='musician'", (ctx.params["musician_id"],)).fetchone()
    if not musician:
        raise not_found("Choose an existing musician to link as an alumnus.")
    ctx.db.execute("INSERT OR IGNORE INTO alumni VALUES(?,?)", (row["id"], musician["id"]))
    ctx.db.commit()
    return school_page(ctx)


@ROUTER.route("DELETE", "/api/schools/<school_id:int>/alumni/<musician_id:int>")
def remove_alumnus(ctx):
    row = owned_school(ctx, ctx.params["school_id"])
    ctx.db.execute("DELETE FROM alumni WHERE school_id=? AND musician_id=?", (row["id"], ctx.params["musician_id"]))
    ctx.db.commit()
    return school_page(ctx)
