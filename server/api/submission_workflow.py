"""What the posting director does with a submission besides scoring: set its status, reveal a blind applicant, share feedback."""
from ..db import now_iso
from ..errors import bad_request
from ..validation import optional_text, parse_flag, require_date
from . import ROUTER
from .lookups import owned_submission
from .statuses import parse_status
from .submissions import submission_detail


@ROUTER.route("PUT", "/api/submissions/<submission_id:int>/status")
def set_status(ctx):
    """Owner: {status: submitted|shortlisted|callback|not_selected, callback_date?, callback_location?, message?}.

    `callback` needs a date, a place or a message (the audition's callback date/location fill in what you leave out);
    moving to any other status clears the callback details. A status change never reveals a blind applicant.
    """
    submission, audition = owned_submission(ctx, ctx.params["submission_id"])
    data = ctx.json()
    status = parse_status(data.get("status"))
    date_text = place = message = ""
    if status == "callback":
        date_text = data.get("callback_date") or audition["callback_date"]
        place = optional_text(data, "callback_location") or audition["callback_location"]
        message = optional_text(data, "message", 1000)
        if not (date_text or place or message):
            raise bad_request("A callback needs a date, a place or a message so the musician knows what to do next.")
        if date_text:
            date_text = require_date(date_text, "the callback date")
    ctx.db.execute(
        "UPDATE submissions SET status=?, callback_date=?, callback_location=?, callback_message=? WHERE id=?",
        (status, date_text, place, message, submission["id"]),
    )
    ctx.db.commit()
    return submission_detail(ctx)


@ROUTER.route("POST", "/api/submissions/<submission_id:int>/reveal")
def reveal_identity(ctx):
    """Owner: show who this blind-review applicant is. Only this submission is revealed; turning blind review
    off on the audition reveals everyone."""
    submission, _ = owned_submission(ctx, ctx.params["submission_id"])
    ctx.db.execute("UPDATE submissions SET identity_revealed=1 WHERE id=?", (submission["id"],))
    ctx.db.commit()
    return submission_detail(ctx)


@ROUTER.route("PUT", "/api/submissions/<submission_id:int>/feedback")
def share_feedback(ctx):
    """Owner: {shared: true|false, include_notes?: true|false}. Shares (or withdraws) the scores and comments with
    the musician; the private timestamped notes go along only when include_notes is true."""
    submission, _ = owned_submission(ctx, ctx.params["submission_id"])
    data = ctx.json()
    shared = parse_flag(data.get("shared"), "shared")
    include_notes = parse_flag(data.get("include_notes", False), "include_notes")
    review = ctx.db.execute("SELECT * FROM reviews WHERE submission_id=?", (submission["id"],)).fetchone()
    if shared and not (review and (review["average"] is not None or review["comments"])):
        raise bad_request("Score the submission or write a comment before sharing feedback with the musician.")
    if review:
        ctx.db.execute(
            "UPDATE reviews SET feedback_shared=?, feedback_includes_notes=?, feedback_shared_at=? WHERE submission_id=?",
            (int(shared), int(shared and include_notes), now_iso() if shared else None, submission["id"]),
        )
        ctx.db.commit()
    return submission_detail(ctx)
