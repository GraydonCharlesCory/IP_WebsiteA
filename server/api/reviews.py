"""Director scoring: five 1-10 criteria (average computed), comments, timestamped notes, decision."""
import json

from ..db import now_iso
from ..errors import bad_request
from . import ROUTER
from .lookups import owned_submission
from .serializers import REVIEW_CRITERIA, review_json
from .statuses import DECISION_TO_STATUS



def _score(value, name):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 10:
        raise bad_request(f"The '{name}' score must be a whole number from 1 to 10.")
    return value


def _notes(items):
    try:
        return [{"time": int(i["time"]), "text": str(i["text"]).strip()[:1000]} for i in items if str(i["text"]).strip()]
    except (ValueError, TypeError, KeyError):
        raise bad_request("Notes must be a list like [{\"time\": 134, \"text\": \"Beautiful release\"}] with times in seconds.")


def average_of(scores: dict):
    given = [v for v in scores.values() if v is not None]
    return round(sum(given) / len(given), 1) if given else None


@ROUTER.route("PUT", "/api/submissions/<submission_id:int>/review")
def save_review(ctx):
    """Create or update the review; only fields present in the body change (safe to auto-save).

    Body: {scores: {tone, rhythm, technique, musicality, preparation}, comments, notes: [{time, text}],
    decision: "shortlist" | "pass" | null}.
    """
    submission, _ = owned_submission(ctx, ctx.params["submission_id"])
    data = ctx.json()
    existing = ctx.db.execute("SELECT * FROM reviews WHERE submission_id=?", (submission["id"],)).fetchone()
    current = review_json(existing) if existing else {"scores": dict.fromkeys(REVIEW_CRITERIA), "comments": "", "notes": [], "decision": None}

    incoming = data.get("scores") or {}
    unknown = set(incoming) - set(REVIEW_CRITERIA)
    if not isinstance(incoming, dict) or unknown:
        raise bad_request(f"Scores must use these criteria: {', '.join(REVIEW_CRITERIA)}.")
    scores = {name: _score(incoming[name], name) if name in incoming else current["scores"][name] for name in REVIEW_CRITERIA}
    comments = str(data["comments"]).strip()[:5000] if "comments" in data else current["comments"]
    notes = _notes(data["notes"]) if "notes" in data else current["notes"]
    decision = data["decision"] if "decision" in data else current["decision"]
    if decision not in (None, "shortlist", "pass"):
        raise bad_request("The decision must be 'shortlist', 'pass' or null.")

    ctx.db.execute(
        "INSERT INTO reviews (submission_id, tone, rhythm, technique, musicality, preparation, average, comments, notes, decision, updated)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(submission_id) DO UPDATE SET tone=excluded.tone, rhythm=excluded.rhythm,"
        " technique=excluded.technique, musicality=excluded.musicality, preparation=excluded.preparation,"
        " average=excluded.average, comments=excluded.comments, notes=excluded.notes, decision=excluded.decision,"
        " updated=excluded.updated",
        (submission["id"], *(scores[n] for n in REVIEW_CRITERIA), average_of(scores), comments, json.dumps(notes), decision, now_iso()),
    )
    if decision and decision != current["decision"]:  # an auto-save repeating a decision must not undo a callback
        ctx.db.execute("UPDATE submissions SET status=? WHERE id=?", (DECISION_TO_STATUS[decision], submission["id"]))
    ctx.db.commit()
    saved = ctx.db.execute("SELECT * FROM reviews WHERE submission_id=?", (submission["id"],)).fetchone()
    status = ctx.db.execute("SELECT status FROM submissions WHERE id=?", (submission["id"],)).fetchone()["status"]
    return {"review": review_json(saved), "status": status}
