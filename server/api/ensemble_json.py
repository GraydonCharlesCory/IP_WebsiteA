"""JSON shapes for ensembles (public pages) and their open opportunities."""
from ..db import load_list
from .serializers import brief_user, opportunity_card


def ensemble_brief(row) -> dict:
    place = ", ".join(part for part in (row["city"], row["state"]) if part)
    return {
        "id": row["id"], "name": row["name"], "category": row["category"], "city": row["city"], "state": row["state"],
        "location": place, "logo_initials": row["logo_initials"], "logo_color": row["logo_color"],
    }


def open_opportunity_rows(conn, ensemble_id: int):
    return conn.execute(
        "SELECT * FROM auditions WHERE ensemble_id=? AND status='open' ORDER BY deadline, id", (ensemble_id,)
    ).fetchall()


def ensemble_json(conn, row, detail: bool = False, viewer=None) -> dict:
    show_directors = viewer is not None and viewer["role"] in ("director", "school")
    director = conn.execute("SELECT * FROM users WHERE id=?", (row["director_id"],)).fetchone()
    opportunities = open_opportunity_rows(conn, row["id"])
    data = {
        **ensemble_brief(row), "about": row["about"], "founded": row["founded"], "season": row["season"],
        "open_opportunity_count": len(opportunities),
    }
    if show_directors:
        data["director"] = brief_user(director)
    if detail:
        roster = load_list(row["roster"])
        if not show_directors:
            director_names = {r["name"].casefold() for r in conn.execute("SELECT name FROM users WHERE role='director'")}
            roster = [p for p in roster if p["name"].casefold() not in director_names]
        data.update({
            "highlights": load_list(row["highlights"]), "roster": roster,
            "open_opportunities": [opportunity_card(r) for r in opportunities],
        })
    return data
