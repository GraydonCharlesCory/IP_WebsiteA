"""Director dashboard: KPIs plus the director's own auditions with counts."""
from datetime import date, timedelta

from ..auth import require_role
from . import ROUTER
from .opportunity_queries import opportunities_list


@ROUTER.route("GET", "/api/director/dashboard")
def dashboard(ctx):
    director = require_role(ctx, "director", "open the director dashboard")
    conn, me = ctx.db, director["id"]
    auditions = [o for o in opportunities_list(ctx, mine=True) if o["type"] != "gig"]
    gigs = opportunities_list(ctx, mine=True, type="gig")
    for item in auditions:
        item.update(_audition_counts(conn, item["id"]))
    open_ones = [a for a in auditions if a["status"] == "open"]
    week = (date.today() + timedelta(days=7)).isoformat()
    reviewed = sum(a["reviewed_count"] for a in auditions)
    average = conn.execute(
        "SELECT AVG(r.average) FROM reviews r JOIN submissions s ON s.id=r.submission_id"
        " JOIN auditions a ON a.id=s.audition_id WHERE a.director_id=? AND r.average IS NOT NULL", (me,)
    ).fetchone()[0]
    return {
        "director": {"id": me, "name": director["name"], "ensemble": director["ensemble"]},
        "kpis": {
            "open_auditions": len(open_ones),
            "closing_this_week": sum(1 for a in open_ones if a["deadline"] <= week),
            "total_submissions": sum(a["submission_count"] for a in auditions),
            "new_submissions": sum(a["new_count"] for a in auditions),
            "awaiting_review": sum(a["submission_count"] - a["reviewed_count"] for a in auditions),
            "reviewed": reviewed,
            "average_score": round(average, 1) if average is not None else None,
        },
        "auditions": auditions,
        "gigs": gigs,
    }


def _audition_counts(conn, audition_id):
    row = conn.execute(
        "SELECT COUNT(*) AS total,"
        " SUM(CASE WHEN s.status='submitted' THEN 1 ELSE 0 END) AS new_count,"
        " SUM(CASE WHEN s.status='shortlisted' THEN 1 ELSE 0 END) AS shortlisted,"
        " SUM(CASE WHEN r.average IS NOT NULL THEN 1 ELSE 0 END) AS reviewed,"
        " AVG(r.average) AS average FROM submissions s LEFT JOIN reviews r ON r.submission_id=s.id WHERE s.audition_id=?",
        (audition_id,),
    ).fetchone()
    return {
        "submission_count": row["total"], "new_count": row["new_count"] or 0, "shortlisted_count": row["shortlisted"] or 0,
        "reviewed_count": row["reviewed"] or 0,
        "average_score": round(row["average"], 1) if row["average"] is not None else None,
    }
