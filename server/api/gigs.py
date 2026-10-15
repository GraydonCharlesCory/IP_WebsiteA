"""Gig details (date, venue, the 3 M's) and musicians' availability; only the posting director sees the sub list."""
from ..auth import require_role
from ..db import now_iso
from ..errors import bad_request, forbidden
from ..validation import optional_rating, optional_text, require_choice, require_date, require_text
from . import ROUTER
from .lookups import get_audition
from .serializers import brief_user

THREE_MS = ("money", "musicians", "music")
AVAILABILITY = ("available", "maybe", "unavailable")


def gig_json(conn, audition_id: int):
    row = conn.execute("SELECT * FROM gig_details WHERE audition_id=?", (audition_id,)).fetchone()
    if not row:
        return None
    return {
        "date": row["gig_date"], "start_time": row["start_time"], "venue": row["venue"],
        "three_ms": {m: {"rating": row[f"{m}_rating"], "note": row[f"{m}_note"]} for m in THREE_MS},
    }


def gig_columns(data: dict, current=None) -> dict:
    """Validated gig_details columns from `data['gig']`; `current` (a row) supplies defaults when editing."""
    gig = data.get("gig")
    if gig is None and current is not None:
        return {}
    if not isinstance(gig, dict):
        raise bad_request("A gig needs a 'gig' object: {date, start_time, venue, money, musicians, music}.")
    base = dict(current) if current else {}
    merged = {"date": base.get("gig_date"), "start_time": base.get("start_time", ""), "venue": base.get("venue"), **gig}
    columns = {
        "gig_date": require_date(merged.get("date"), "the gig date"),
        "start_time": optional_text(merged, "start_time", 20),
        "venue": require_text(merged, "venue", "the venue", 160),
    }
    for m in THREE_MS:
        rating_note = gig.get(m) if m in gig else {"rating": base.get(f"{m}_rating"), "note": base.get(f"{m}_note", "")}
        if not isinstance(rating_note, dict):
            raise bad_request(f"'{m}' must be {{rating (1-5), note}}.")
        columns[f"{m}_rating"] = optional_rating(rating_note.get("rating"), m)
        columns[f"{m}_note"] = optional_text(rating_note, "note", 500)
    return columns


def save_gig(conn, audition_id: int, columns: dict) -> None:
    if not columns:
        return
    names = ["audition_id", *columns]
    conn.execute(
        f"INSERT OR REPLACE INTO gig_details ({', '.join(names)}) VALUES ({', '.join('?' * len(names))})",
        [audition_id, *columns.values()],
    )


def get_gig(conn, audition_id: int):
    row = get_audition(conn, audition_id)
    if row["type"] != "gig":
        raise bad_request("That opportunity is an audition, not a gig. Only gigs take availability.")
    return row


@ROUTER.route("PUT", "/api/gigs/<audition_id:int>/availability")
def mark_availability(ctx):
    """Musician: {status: available|maybe|unavailable}. Replaces any earlier mark."""
    musician = require_role(ctx, "musician", "mark availability")
    gig = get_gig(ctx.db, ctx.params["audition_id"])
    status = require_choice(ctx.json().get("status"), AVAILABILITY, "availability status")
    ctx.db.execute(
        "INSERT INTO gig_availability (audition_id, musician_id, status, updated) VALUES (?,?,?,?)"
        " ON CONFLICT(audition_id, musician_id) DO UPDATE SET status=excluded.status, updated=excluded.updated",
        (gig["id"], musician["id"], status, now_iso()),
    )
    ctx.db.commit()
    return {"availability": {"gig_id": gig["id"], "status": status}}


@ROUTER.route("GET", "/api/gigs/<audition_id:int>/availability")
def sub_list(ctx):
    """Posting director only: musicians grouped by their mark; `available` is the sub list."""
    director = require_role(ctx, "director", "see a gig's sub list")
    gig = get_gig(ctx.db, ctx.params["audition_id"])
    if gig["director_id"] != director["id"]:
        raise forbidden("Only the director who posted this gig can see its sub list.")
    rows = ctx.db.execute(
        "SELECT u.*, g.status AS mark, g.updated AS marked FROM gig_availability g JOIN users u ON u.id=g.musician_id"
        " WHERE g.audition_id=? ORDER BY u.name", (gig["id"],)
    ).fetchall()
    groups = {status: [] for status in AVAILABILITY}
    for r in rows:
        groups[r["mark"]].append({**brief_user(r), "location": r["location"], "marked": r["marked"]})
    return {"gig": {"id": gig["id"], "title": gig["title"]}, **groups}


def my_availability(conn, audition_id: int, musician_id: int):
    row = conn.execute(
        "SELECT status FROM gig_availability WHERE audition_id=? AND musician_id=?", (audition_id, musician_id)
    ).fetchone()
    return row["status"] if row else None


def available_count(conn, audition_id: int) -> int:
    return conn.execute(
        "SELECT COUNT(*) FROM gig_availability WHERE audition_id=? AND status='available'", (audition_id,)
    ).fetchone()[0]
