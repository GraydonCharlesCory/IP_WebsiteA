"""Searching opportunities (auditions and gigs) and shaping them for the signed-in viewer."""
from ..auth import require_user
from ..discovery import metadata, GENRES, ELIGIBILITY
from ..validation import parse_flag, require_category, require_choice, require_date
from .ensemble_json import ensemble_brief
from .gigs import available_count, gig_json, my_availability
from .serializers import audition_json, brief_user
from .statuses import STATUS_LABELS

TYPES = ("audition", "gig", "grant", "residency", "college_audition", "summer_camp")
LEVELS = ("student", "college", "semi-pro", "pro")
SORTS = ("deadline", "newest")
_ORDER = {
    "deadline": "status DESC, deadline ASC, id",
    "newest": "created DESC, id DESC",
}


def parse_filters(query: dict) -> dict:
    """Validated search filters from a query string (see the README for each one)."""
    filters = {key: query[key].strip() for key in ("q", "instrument", "location") if query.get(key, "").strip()}
    if query.get("genre"):
        filters["genre"] = require_choice(query["genre"], GENRES, "genre")
    if query.get("eligibility"):
        filters["eligibility"] = require_choice(query["eligibility"], ELIGIBILITY, "eligibility")
    if query.get("student_hub"):
        filters["student_hub"] = parse_flag(query["student_hub"], "student_hub")
    if query.get("category"):
        filters["category"] = require_category(query["category"])
    if query.get("type"):
        filters["type"] = require_choice(query["type"], TYPES, "type")
    if query.get("level"):
        filters["level"] = require_choice(query["level"], LEVELS, "level")
    if query.get("status"):
        filters["status"] = require_choice(query["status"], ("open", "closed"), "status")
    if query.get("deadline_before"):
        filters["deadline_before"] = require_date(query["deadline_before"], "deadline_before")
    for name, key in (("paid", "paid"), ("video_round", "video_round_accepted"), ("mine", "mine")):
        if query.get(name):
            filters[key] = parse_flag(query[name], name)
    filters["sort"] = require_choice(query.get("sort", "deadline"), SORTS, "sort")
    return filters


def _where(filters: dict, user) -> tuple:
    clauses, args = [], []
    simple = {"category": "category", "type": "type", "level": "level", "status": "status"}
    for key, column in simple.items():
        if key in filters:
            clauses.append(f"{column}=?")
            args.append(filters[key])
    if "paid" in filters:
        clauses.append("paid=?")
        args.append(int(filters["paid"]))
    if "video_round_accepted" in filters:
        clauses.append("video_round_accepted=?")
        args.append(int(filters["video_round_accepted"]))
    if "deadline_before" in filters:
        clauses.append("deadline<=?")
        args.append(filters["deadline_before"])
    if filters.get("mine"):
        clauses.append("director_id=?")
        args.append(user["id"])
    if "instrument" in filters:
        clauses.append("lower(instruments) LIKE ?")
        args.append(f"%{filters['instrument'].lower()}%")
    if "location" in filters:
        clauses.append("lower(city || ', ' || state) LIKE ?")
        args.append(f"%{filters['location'].lower()}%")
    if "q" in filters:
        clauses.append("lower(title || ' ' || ensemble || ' ' || description || ' ' || instruments || ' ' || city || ' ' || state) LIKE ?")
        args.append(f"%{filters['q'].lower()}%")
    if "genre" in filters:
        clauses.append("id IN (SELECT audition_id FROM opportunity_discovery WHERE genre=?)")
        args.append(filters["genre"])
    if "eligibility" in filters:
        clauses.append("id IN (SELECT audition_id FROM opportunity_discovery WHERE EXISTS (SELECT 1 FROM json_each(eligibility) WHERE value=?))")
        args.append(filters["eligibility"])
    if "student_hub" in filters:
        clauses.append("id IN (SELECT audition_id FROM opportunity_discovery WHERE student_hub=?)")
        args.append(int(filters["student_hub"]))
    return (" AND ".join(clauses) or "1=1"), args


def opportunities_list(ctx, **filters) -> list:
    """Opportunities matching the filters, for a signed-in viewer; `sort` defaults to deadline (open first)."""
    user = require_user(ctx)
    where, args = _where(filters, user)
    order = _ORDER[filters.get("sort", "deadline")]
    rows = ctx.db.execute(f"SELECT * FROM auditions WHERE {where} ORDER BY {order}", args).fetchall()
    return [opportunity_json(ctx, row) for row in rows]


def opportunity_json(ctx, row) -> dict:
    """Full opportunity for the signed-in viewer: musicians get their own application or availability, the owner gets counts."""
    user, conn = ctx.user, ctx.db
    director = conn.execute("SELECT * FROM users WHERE id=?", (row["director_id"],)).fetchone()
    data = {**audition_json(row, director), **metadata(conn, row["id"])}
    if row["type"] == "gig" and user["role"] != "musician":
        data["director"] = brief_user(director)
    ensemble = conn.execute("SELECT * FROM ensembles WHERE id=?", (row["ensemble_id"],)).fetchone() if row["ensemble_id"] else None
    data["ensemble_info"] = ensemble_brief(ensemble) if ensemble else None
    data["gig"] = gig_json(conn, row["id"])
    if user["role"] == "musician":
        if row["type"] == "gig":
            data["my_availability"] = my_availability(conn, row["id"], user["id"])
        else:
            mine = conn.execute(
                "SELECT id, status, created FROM submissions WHERE audition_id=? AND musician_id=?", (row["id"], user["id"])
            ).fetchone()
            data["my_submission"] = {
                "id": mine["id"], "status": mine["status"], "status_label": STATUS_LABELS[mine["status"]], "created": mine["created"],
            } if mine else None
    elif row["director_id"] == user["id"]:
        data["owned_by_me"] = True
        if row["type"] == "gig":
            data["available_count"] = available_count(conn, row["id"])
        else:
            data["submission_count"] = conn.execute("SELECT COUNT(*) FROM submissions WHERE audition_id=?", (row["id"],)).fetchone()[0]
    return data
