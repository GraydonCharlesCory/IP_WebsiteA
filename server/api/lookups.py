"""Fetch-or-404 helpers and the ownership rule for auditions and submissions."""
from ..auth import require_role
from ..errors import forbidden, not_found


def get_audition(conn, audition_id: int):
    row = conn.execute("SELECT * FROM auditions WHERE id = ?", (audition_id,)).fetchone()
    if not row:
        raise not_found("That audition does not exist.")
    return row


def get_user(conn, user_id: int):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_musician_by_handle(conn, handle: str):
    row = conn.execute("SELECT * FROM users WHERE handle = ? AND role = 'musician'", (handle,)).fetchone()
    if not row:
        raise not_found("No musician has that handle.")
    return row


def owned_audition(ctx, audition_id: int):
    """The audition, only if the signed-in director posted it."""
    director = require_role(ctx, "director", "see submissions")
    audition = get_audition(ctx.db, audition_id)
    if audition["director_id"] != director["id"]:
        raise forbidden("Only the director who posted this audition can see its submissions.")
    return audition


def owned_submission(ctx, submission_id: int):
    """(submission, audition), only if the signed-in director posted the audition."""
    require_role(ctx, "director", "see submissions")
    submission = ctx.db.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,)).fetchone()
    if not submission:
        raise not_found("That submission does not exist.")
    return submission, owned_audition(ctx, submission["audition_id"])


def is_scored(conn, submission) -> bool:
    review = conn.execute("SELECT average FROM reviews WHERE submission_id=?", (submission["id"],)).fetchone()
    return bool(review and review["average"] is not None)


def is_anonymous(conn, submission) -> bool:
    """Blind review is always on: a director sees who an applicant is only after scoring the submission and moving it
    to callback (the step that lets them contact the musician). Nothing stored or requested can change this."""
    return not (submission["status"] == "callback" and is_scored(conn, submission))
