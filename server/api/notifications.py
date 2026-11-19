"""One-way in-app notices and LOCAL simulated email. No transport or mail credentials."""
from ..auth import require_role
from ..db import now_iso
from ..errors import bad_request
from ..validation import require_text
from . import ROUTER
from .lookups import owned_audition, owned_submission


def deliver(conn, user_id, audition_id, body):
    email = conn.execute("SELECT email FROM users WHERE id=?", (user_id,)).fetchone()[0]
    cur = conn.execute("INSERT INTO notices(user_id,audition_id,body,created) VALUES(?,?,?,?)", (user_id, audition_id, body, now_iso()))
    conn.execute("INSERT INTO email_outbox(notice_id,recipient,body) VALUES(?,?,?)", (cur.lastrowid, email, body))


@ROUTER.route("GET", "/api/my/notices")
def notices(ctx):
    user = require_role(ctx, "musician", "read your notices")
    return {"notices": [dict(r) for r in ctx.db.execute("SELECT id,audition_id,body,created FROM notices WHERE user_id=? ORDER BY id DESC", (user["id"],))]}


@ROUTER.route("POST", "/api/auditions/<audition_id:int>/announcements")
def announce(ctx):
    row = owned_audition(ctx, ctx.params["audition_id"])
    body = require_text(ctx.json(), "body", "an announcement", 3000)
    recipients = ctx.db.execute("SELECT musician_id FROM submissions WHERE audition_id=?", (row["id"],)).fetchall()
    for recipient in recipients:
        deliver(ctx.db, recipient[0], row["id"], body)
    ctx.db.commit()
    return {"delivered": len(recipients), "email": "simulated locally; no mail sent"}


@ROUTER.route("POST", "/api/auditions/<audition_id:int>/notices")
def send_individual(ctx):
    audition = owned_audition(ctx, ctx.params["audition_id"])
    data = ctx.json()
    submission_id = data.get("submission_id")
    if type(submission_id) is not int or not 0 < submission_id <= 9223372036854775807:
        raise bad_request("Choose one applicant from this audition.")
    submission = ctx.db.execute(
        "SELECT musician_id FROM submissions WHERE id=? AND audition_id=?",
        (submission_id, audition["id"]),
    ).fetchone()
    if not submission:
        raise bad_request("Choose one applicant from this audition.")
    body = require_text(data, "body", "a notice", 3000)
    deliver(ctx.db, submission["musician_id"], audition["id"], body)
    ctx.db.commit()
    return {"delivered": 1, "email": "simulated locally; no mail sent"}


@ROUTER.route("POST", "/api/submissions/<submission_id:int>/notification")
def send_template(ctx):
    sub, audition = owned_submission(ctx, ctx.params["submission_id"])
    template = ctx.json().get("template")
    if template == "confirmation":
        body = f"Your application to {audition['title']} has been received. Thank you for applying."
    elif template == "rejection":
        body = f"Thank you for applying to {audition['title']}. You have not been selected for this opportunity."
        ctx.db.execute("UPDATE submissions SET status='not_selected',callback_date='',callback_location='',callback_message='' WHERE id=?", (sub["id"],))
    else:
        raise bad_request("Choose the confirmation or rejection template.")
    deliver(ctx.db, sub["musician_id"], audition["id"], body)
    ctx.db.commit()
    return {"delivered": True, "email": "simulated locally; no mail sent"}


@ROUTER.route("GET", "/api/auditions/<audition_id:int>/outbox")
def outbox(ctx):
    row = owned_audition(ctx, ctx.params["audition_id"])
    # Never expose addresses, recipient ids or other identity-bearing delivery metadata to reviewers.
    return {"outbox": [dict(r) for r in ctx.db.execute(
        "SELECT e.body,e.state FROM email_outbox e JOIN notices n ON n.id=e.notice_id WHERE n.audition_id=? ORDER BY e.id DESC", (row["id"],))]}
