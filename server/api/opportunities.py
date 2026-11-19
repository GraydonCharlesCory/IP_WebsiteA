"""Opportunities (auditions and gigs): signed-in users search and read, only directors write (and only their own).

`/api/auditions` is the v1 address for auditions only; `/api/opportunities` covers auditions and gigs.
"""
from ..auth import require_role, require_user
from ..demo_enrichment import opportunity_example
from ..db import load_list, now_iso
from ..discovery import metadata, validate_metadata, save_metadata
from ..errors import bad_request, forbidden
from ..responses import JsonResponse
from ..validation import optional_text, parse_flag, require_category, require_choice, require_date, require_text, string_list
from . import ROUTER
from .gigs import gig_columns, save_gig
from .lookups import get_audition
from .opportunity_queries import LEVELS, TYPES, opportunities_list, opportunity_json, parse_filters
from .serializers import dumps

FLAGS = ("paid", "video_round_accepted")
TEXT_FIELDS = ("type", "title", "ensemble", "description", "deadline", "category", "status", "city", "state", "level",
               "pay_text", "callback_date", "callback_location")


@ROUTER.route("GET", "/api/opportunities")
def search_opportunities(ctx):
    """Filters: q, category, type, instrument, location, level, paid, video_round, deadline_before, status, mine, sort."""
    require_user(ctx)
    return {"opportunities": opportunities_list(ctx, **parse_filters(ctx.query))}


@ROUTER.route("GET", "/api/auditions")
def list_auditions(ctx):
    """v1 address: the same search, restricted to auditions."""
    require_user(ctx)
    return {"auditions": opportunities_list(ctx, **{**parse_filters(ctx.query), "type": "audition"})}


def _key(ctx) -> str:
    """v1 addresses answer with {audition}; the new /api/opportunities addresses with {opportunity}."""
    return "opportunity" if ctx.path.startswith("/api/opportunities") else "audition"


@ROUTER.route("GET", "/api/opportunities/<audition_id:int>")
@ROUTER.route("GET", "/api/auditions/<audition_id:int>")
def opportunity_detail(ctx):
    require_user(ctx)
    row = get_audition(ctx.db, ctx.params["audition_id"])
    data = opportunity_json(ctx, row)
    data["demo_enrichment"] = opportunity_example(ctx.db, row)
    return {_key(ctx): data}


def _timeline(data) -> list:
    items = data.get("timeline") or []
    ok = isinstance(items, list) and all(isinstance(i, dict) and i.get("label") and i.get("date") for i in items)
    if not ok:
        raise bad_request("The timeline must be a list of {label, date} steps.")
    return [{"label": str(i["label"]), "date": str(i["date"])} for i in items]


def director_ensemble(conn, director):
    return conn.execute("SELECT * FROM ensembles WHERE director_id=?", (director["id"],)).fetchone()


def _create_defaults(conn, director) -> dict:
    ensemble = director_ensemble(conn, director)
    return {
        "category": director["category"], "ensemble": ensemble["name"] if ensemble else director["ensemble"],
        "city": ensemble["city"] if ensemble else "", "state": ensemble["state"] if ensemble else "",
        "type": "audition", "level": "pro", "status": "open",
    }


def _fields(data, current: dict, creating: bool) -> dict:
    """Validated audition columns: request values over the current row (or the create defaults)."""
    if "blind_review" in data and not creating:
        raise bad_request("Review mode is immutable after creation. Post a new audition to choose a different mode.")
    merged = {**current, **{k: v for k, v in data.items() if k in TEXT_FIELDS or k in FLAGS}}
    kind = merged["type"]
    if not creating and kind != current["type"]:
        raise bad_request("An opportunity's type cannot change after it is posted. Post a new one instead.")
    flags = {name: int(parse_flag(merged.get(name, False), name)) for name in FLAGS}
    return {
        "blind_review": int(parse_flag(data.get("blind_review", True), "blind_review")) if creating else current["blind_review"],
        "title": require_text(merged, "title", "a title", 160),
        "ensemble": require_text(merged, "ensemble", "the ensemble name", 160),
        "description": optional_text(merged, "description"),
        "deadline": require_date(require_text(merged, "deadline", "a deadline (YYYY-MM-DD)", 20), "the deadline"),
        "category": require_category(merged.get("category")),
        "status": require_choice(merged.get("status"), ("open", "closed"), "status"),
        "city": optional_text(merged, "city", 80), "state": optional_text(merged, "state", 40),
        "level": require_choice(merged.get("level"), LEVELS, "level"),
        "pay_text": optional_text(merged, "pay_text", 200),
        "callback_date": require_date(merged["callback_date"], "the callback date") if merged.get("callback_date") else "",
        "callback_location": optional_text(merged, "callback_location", 200),
        **flags,
        "instruments": dumps(string_list(data, "instruments") if "instruments" in data else load_list(current.get("instruments") or "")),
        "requirements": dumps(string_list(data, "requirements") if "requirements" in data else load_list(current.get("requirements") or "")),
        "timeline": dumps(_timeline(data) if "timeline" in data else load_list(current.get("timeline") or "")),
        "type": kind if kind in TYPES else require_choice(kind, TYPES, "type"),
    }


@ROUTER.route("POST", "/api/opportunities")
@ROUTER.route("POST", "/api/auditions")
def create_opportunity(ctx):
    """Director: {title, deadline, type?: audition|gig, gig?: {...}, level?, paid?, pay_text?, city?, state?,
    video_round_accepted?, callback_date?, callback_location?, category?, ensemble?, description?,
    instruments[], requirements[], timeline[{label,date}], status?}."""
    from .schools import posting_account
    director = posting_account(ctx)
    data = ctx.json()
    fields = _fields(data, _create_defaults(ctx.db, director), creating=True)
    discovery = validate_metadata(data, {"genre": "", "eligibility": [], "student_hub": False})
    gig = gig_columns(data) if fields["type"] == "gig" else {}
    ensemble = director_ensemble(ctx.db, director)
    columns = {"director_id": director["id"], "ensemble_id": ensemble["id"] if ensemble else None, **fields, "created": now_iso()}
    from .judging import validate_rubric
    columns["rubric"] = dumps(validate_rubric(data.get("rubric", ["tone", "rhythm", "technique", "musicality", "preparation"])))
    if director["role"] == "school":
        from .schools import owned_school
        columns["school_id"] = owned_school(ctx, data.get("school_id"))["id"]
    cur = ctx.db.execute(
        f"INSERT INTO auditions ({', '.join(columns)}) VALUES ({', '.join('?' * len(columns))})", list(columns.values())
    )
    save_metadata(ctx.db, cur.lastrowid, discovery)
    save_gig(ctx.db, cur.lastrowid, gig)
    ctx.db.commit()
    return JsonResponse({_key(ctx): opportunity_json(ctx, get_audition(ctx.db, cur.lastrowid))}, 201)


@ROUTER.route("PUT", "/api/opportunities/<audition_id:int>")
@ROUTER.route("PUT", "/api/auditions/<audition_id:int>")
def edit_opportunity(ctx):
    """Owner: any of the create fields (blind review is always on and cannot be set)."""
    from .schools import posting_account
    director = posting_account(ctx)
    row = get_audition(ctx.db, ctx.params["audition_id"])
    if row["director_id"] != director["id"]:
        raise forbidden("You can only edit auditions and gigs you posted.")
    data = ctx.json()
    fields = _fields(data, dict(row), creating=False)
    discovery = validate_metadata(data, metadata(ctx.db, row["id"]))
    gig = gig_columns(data, current=ctx.db.execute("SELECT * FROM gig_details WHERE audition_id=?", (row["id"],)).fetchone()) \
        if row["type"] == "gig" and "gig" in data else {}
    ctx.db.execute(
        f"UPDATE auditions SET {', '.join(f'{name}=?' for name in fields)} WHERE id=?", [*fields.values(), row["id"]]
    )
    save_metadata(ctx.db, row["id"], discovery)
    save_gig(ctx.db, row["id"], gig)
    ctx.db.commit()
    return {_key(ctx): opportunity_json(ctx, get_audition(ctx.db, row["id"]))}
