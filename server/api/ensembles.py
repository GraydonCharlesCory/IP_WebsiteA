"""Ensembles: public pages (info, director, open opportunities); only the director edits their own."""
import json

from ..auth import require_role
from ..errors import bad_request, forbidden, not_found
from ..validation import optional_text, require_category, string_list
from . import ROUTER
from .ensemble_json import ensemble_json


def get_ensemble(conn, ensemble_id: int):
    row = conn.execute("SELECT * FROM ensembles WHERE id=?", (ensemble_id,)).fetchone()
    if not row:
        raise not_found("That ensemble does not exist.")
    return row


@ROUTER.route("GET", "/api/ensembles")
def list_ensembles(ctx):
    """Public. Filters: ?category=&q=<name, city or text>."""
    sql, args = "SELECT * FROM ensembles WHERE 1=1", []
    if ctx.query.get("category"):
        sql, args = sql + " AND category=?", args + [require_category(ctx.query["category"])]
    if ctx.query.get("q"):
        sql += " AND lower(name || ' ' || city || ' ' || state || ' ' || about) LIKE ?"
        args.append(f"%{ctx.query['q'].lower()}%")
    rows = ctx.db.execute(sql + " ORDER BY name", args).fetchall()
    return {"ensembles": [ensemble_json(ctx.db, r, viewer=ctx.user) for r in rows]}


@ROUTER.route("GET", "/api/ensembles/<ensemble_id:int>")
def ensemble_page(ctx):
    return {"ensemble": ensemble_json(ctx.db, get_ensemble(ctx.db, ctx.params["ensemble_id"]), detail=True, viewer=ctx.user)}


def _roster(data, current) -> str:
    if "roster" not in data:
        return current["roster"]
    items = data["roster"]
    if not isinstance(items, list) or not all(isinstance(i, dict) and i.get("name") for i in items):
        raise bad_request("The roster must be a list of {name, instrument} entries.")
    return json.dumps([{"name": str(i["name"]), "instrument": str(i.get("instrument", ""))} for i in items])


@ROUTER.route("PUT", "/api/ensembles/<ensemble_id:int>")
def edit_ensemble(ctx):
    """Owner (the ensemble's director): about, season, highlights[], roster[{name, instrument}], city, state, founded."""
    director = require_role(ctx, "director", "edit ensemble pages")
    row = get_ensemble(ctx.db, ctx.params["ensemble_id"])
    if row["director_id"] != director["id"]:
        raise forbidden("You can only edit your own ensemble's page.")
    data = ctx.json()
    pick = lambda field: optional_text(data, field, 5000) if field in data else row[field]  # noqa: E731
    highlights = json.dumps(string_list(data, "highlights")) if "highlights" in data else row["highlights"]
    ctx.db.execute(
        "UPDATE ensembles SET about=?, season=?, city=?, state=?, highlights=?, roster=? WHERE id=?",
        (pick("about"), pick("season"), pick("city"), pick("state"), highlights, _roster(data, row), row["id"]),
    )
    ctx.db.commit()
    return {"ensemble": ensemble_json(ctx.db, get_ensemble(ctx.db, row["id"]), detail=True, viewer=ctx.user)}
