"""Audition postings: signed-in users read, only directors write (and only their own)."""
from ..auth import require_role, require_user
from ..db import load_list, now_iso
from ..errors import bad_request, forbidden
from ..responses import JsonResponse
from ..validation import optional_text, require_category, require_text, string_list
from . import ROUTER
from .lookups import get_audition
from .queries import audition_detail_json, auditions_for_list
from .serializers import dumps


@ROUTER.route("GET", "/api/auditions")
def list_auditions(ctx):
    category = ctx.query.get("category")
    if category:
        require_category(category)
    require_user(ctx)
    return {"auditions": auditions_for_list(ctx, category, mine=ctx.query.get("mine") == "1")}


@ROUTER.route("GET", "/api/auditions/<audition_id:int>")
def audition_detail(ctx):
    require_user(ctx)
    return {"audition": audition_detail_json(ctx, get_audition(ctx.db, ctx.params["audition_id"]))}


def _timeline(data) -> list:
    items = data.get("timeline") or []
    ok = isinstance(items, list) and all(isinstance(i, dict) and i.get("label") and i.get("date") for i in items)
    if not ok:
        raise bad_request("The timeline must be a list of {label, date} steps.")
    return [{"label": str(i["label"]), "date": str(i["date"])} for i in items]


def _fields(data, current=None) -> dict:
    """Validated audition columns from a request body; `current` supplies defaults when editing."""
    cur = dict(current) if current else {}
    merged = {**{k: cur.get(k) for k in ("title", "ensemble", "description", "deadline", "category", "status")}, **data}
    status = merged.get("status") or "open"
    if status not in ("open", "closed"):
        raise bad_request("Status must be 'open' or 'closed'.")
    return {
        "title": require_text(merged, "title", "a title", 160),
        "ensemble": require_text(merged, "ensemble", "the ensemble name", 160),
        "description": optional_text(merged, "description"),
        "deadline": require_text(merged, "deadline", "a deadline (YYYY-MM-DD)", 20),
        "category": require_category(merged.get("category")),
        "status": status,
        "instruments": dumps(string_list(data, "instruments") if "instruments" in data else _loaded(cur, "instruments")),
        "requirements": dumps(string_list(data, "requirements") if "requirements" in data else _loaded(cur, "requirements")),
        "timeline": dumps(_timeline(data) if "timeline" in data else _loaded(cur, "timeline")),
    }


def _loaded(current, field):
    return load_list(current.get(field) or "")


@ROUTER.route("POST", "/api/auditions")
def create_audition(ctx):
    director = require_role(ctx, "director", "post auditions")
    data = ctx.json()
    data.setdefault("category", director["category"])
    data.setdefault("ensemble", director["ensemble"])
    fields = _fields(data)
    cur = ctx.db.execute(
        "INSERT INTO auditions (director_id, category, title, ensemble, instruments, description, requirements,"
        " timeline, deadline, status, created) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (director["id"], fields["category"], fields["title"], fields["ensemble"], fields["instruments"],
         fields["description"], fields["requirements"], fields["timeline"], fields["deadline"], fields["status"], now_iso()),
    )
    ctx.db.commit()
    row = get_audition(ctx.db, cur.lastrowid)
    return JsonResponse({"audition": audition_detail_json(ctx, row)}, 201)


@ROUTER.route("PUT", "/api/auditions/<audition_id:int>")
def edit_audition(ctx):
    director = require_role(ctx, "director", "edit auditions")
    row = get_audition(ctx.db, ctx.params["audition_id"])
    if row["director_id"] != director["id"]:
        raise forbidden("You can only edit auditions you posted.")
    fields = _fields(ctx.json(), row)
    ctx.db.execute(
        "UPDATE auditions SET category=?, title=?, ensemble=?, instruments=?, description=?, requirements=?,"
        " timeline=?, deadline=?, status=? WHERE id=?",
        (fields["category"], fields["title"], fields["ensemble"], fields["instruments"], fields["description"],
         fields["requirements"], fields["timeline"], fields["deadline"], fields["status"], row["id"]),
    )
    ctx.db.commit()
    return {"audition": audition_detail_json(ctx, get_audition(ctx.db, row["id"]))}
