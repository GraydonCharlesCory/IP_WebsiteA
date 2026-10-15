"""A musician's own applications: status, callback details and the feedback the director chose to share."""
from ..auth import require_role
from . import ROUTER
from .ensemble_json import ensemble_brief
from .serializers import opportunity_card, shared_feedback_json
from .statuses import STATUS_LABELS
from .submissions import callback_json


def _application(conn, row) -> dict:
    audition = conn.execute("SELECT * FROM auditions WHERE id=?", (row["audition_id"],)).fetchone()
    ensemble = conn.execute("SELECT * FROM ensembles WHERE id=?", (audition["ensemble_id"],)).fetchone()
    review = conn.execute("SELECT * FROM reviews WHERE submission_id=?", (row["id"],)).fetchone()
    return {
        "id": row["id"], "audition_id": audition["id"], "created": row["created"],
        "status": row["status"], "status_label": STATUS_LABELS[row["status"]],
        "opportunity": opportunity_card(audition),
        "ensemble": ensemble_brief(ensemble) if ensemble else {"id": None, "name": audition["ensemble"]},
        "callback": callback_json(row),
        "feedback": shared_feedback_json(review) if review and review["feedback_shared"] else None,
    }


@ROUTER.route("GET", "/api/my/applications")
def my_applications(ctx):
    """Musician: every application, newest first. `feedback` is null until the director shares it; private
    notes, the director's unshared scores and other applicants never appear."""
    musician = require_role(ctx, "musician", "see your applications")
    rows = ctx.db.execute("SELECT * FROM submissions WHERE musician_id=? ORDER BY created DESC, id DESC", (musician["id"],)).fetchall()
    return {"applications": [_application(ctx.db, r) for r in rows]}


@ROUTER.route("GET", "/api/my/submissions")
def my_submissions(ctx):
    """v1 list, kept for the existing pages: no feedback, scores or comments, just where each submission stands."""
    musician = require_role(ctx, "musician", "see your submissions")
    rows = ctx.db.execute(
        "SELECT s.id, s.audition_id, s.created, s.status, a.title, a.ensemble FROM submissions s"
        " JOIN auditions a ON a.id = s.audition_id WHERE s.musician_id=? ORDER BY s.created DESC, s.id DESC", (musician["id"],)
    ).fetchall()
    return {"submissions": [{"id": r["id"], "audition_id": r["audition_id"], "audition_title": r["title"],
                             "ensemble": r["ensemble"], "status": r["status"], "status_label": STATUS_LABELS[r["status"]],
                             "created": r["created"]} for r in rows]}
