"""Submitting to auditions (musicians) and reading submissions (only the posting director)."""
import json

from ..auth import require_role
from ..db import load_list, now_iso
from ..errors import ApiError, bad_request, not_found
from ..durations import mp4_duration, require_within
from ..media import save_upload
from ..responses import FileResponse, JsonResponse
from ..validation import optional_text
from . import ROUTER
from .lookups import get_audition, owned_audition, owned_submission
from .serializers import anonymous_applicant, review_json
from .statuses import STATUS_LABELS, parse_status


def _timestamps(raw, duration=None) -> list:
    """Accepts a list (JSON body) or a JSON string (query param) of {time, label}; every time must lie inside the clip."""
    if raw in (None, ""):
        return []
    try:
        items = json.loads(raw) if isinstance(raw, str) else raw
        return [{"time": require_within(int(i["time"]), duration, f"Chapter '{str(i['label'])[:40]}'"), "label": str(i["label"])[:120]} for i in items]
    except (ValueError, TypeError, KeyError):
        raise bad_request("Timestamps must be a list like [{\"time\": 134, \"label\": \"Ballad\"}] with times in seconds.")


def _upload_submission_media(ctx):
    """Save the raw MP4 body; returns (file name, duration, timestamps) with the file removed if the chapters fall outside it."""
    file_name = save_upload(ctx, ctx.settings.submission_uploads_dir)
    path = ctx.settings.submission_uploads_dir / file_name
    duration = mp4_duration(path)
    try:
        return file_name, duration, _timestamps(ctx.query.get("timestamps"), duration)
    except ApiError:
        path.unlink(missing_ok=True)
        raise


def _create_submission(ctx, audition, musician) -> int:
    """Insert the submission from either a raw MP4 upload or an existing profile clip."""
    wants_upload = (ctx.headers.get("Content-Type") or "").lower().startswith("video/")
    if wants_upload:
        note = optional_text(ctx.query, "note", 2000)
        file_name, duration, timestamps = _upload_submission_media(ctx)
        source, clip_id = "upload", None
    else:
        data = ctx.json()
        note = optional_text(data, "note", 2000)
        clip_id = data.get("clip_id")
        clip = ctx.db.execute("SELECT duration_sec FROM clips WHERE id=? AND owner_id=?", (clip_id, musician["id"])).fetchone()
        if not clip:
            raise bad_request("Choose one of your own profile clips, or upload an MP4 video.")
        duration = clip["duration_sec"]
        timestamps = _timestamps(data.get("timestamps"), duration)
        source, file_name = "clip", None
    cur = ctx.db.execute(
        "INSERT INTO submissions (audition_id, musician_id, source, file, clip_id, note, timestamps, duration_sec, status, created)"
        " VALUES (?,?,?,?,?,?,?,?,'submitted',?)",
        (audition["id"], musician["id"], source, file_name, clip_id, note, json.dumps(timestamps), duration, now_iso()),
    )
    ctx.db.commit()
    return cur.lastrowid


@ROUTER.route("POST", "/api/auditions/<audition_id:int>/submissions")
def submit_to_audition(ctx):
    """JSON {clip_id, note, timestamps} or raw MP4 body with ?note=&timestamps=<json>."""
    musician = require_role(ctx, "musician", "submit to auditions")
    audition = get_audition(ctx.db, ctx.params["audition_id"])
    if audition["status"] != "open":
        raise ApiError(409, "This audition is closed and no longer takes submissions.")
    if audition["type"] != "audition":
        raise ApiError(409, "Gigs take availability, not submissions. Use PUT /api/gigs/<id>/availability.")
    if ctx.db.execute("SELECT 1 FROM submissions WHERE audition_id=? AND musician_id=?", (audition["id"], musician["id"])).fetchone():
        raise ApiError(409, "You have already submitted to this audition.")
    submission_id = _create_submission(ctx, audition, musician)
    created = ctx.db.execute("SELECT created FROM submissions WHERE id=?", (submission_id,)).fetchone()["created"]
    return JsonResponse({"submission": {"id": submission_id, "audition_id": audition["id"], "status": "submitted", "status_label": "Submitted", "created": created}}, 201)


def _review_for(conn, submission_id):
    return conn.execute("SELECT * FROM reviews WHERE submission_id=?", (submission_id,)).fetchone()


def applicant_json(ctx, submission) -> dict:
    """The musician as the director sees them: always anonymous, in every status, with no way to change that."""
    musician = ctx.db.execute("SELECT instrument FROM users WHERE id=?", (submission["musician_id"],)).fetchone()
    return anonymous_applicant(submission["id"], musician["instrument"])


def submission_summary(ctx, row, audition) -> dict:
    review = _review_for(ctx.db, row["id"])
    return {
        "id": row["id"], "audition_id": row["audition_id"], "musician": applicant_json(ctx, row),
        "source": row["source"], "status": row["status"], "status_label": STATUS_LABELS[row["status"]],
        "created": row["created"], "average": review["average"] if review else None,
        "reviewed": bool(review and review["average"] is not None),
        "feedback_shared": bool(review and review["feedback_shared"]),
        "callback": callback_json(row),
    }


def callback_json(row):
    if row["status"] != "callback":
        return None
    return {"date": row["callback_date"], "location": row["callback_location"], "message": row["callback_message"]}


@ROUTER.route("GET", "/api/auditions/<audition_id:int>/submissions")
def list_submissions(ctx):
    audition = owned_audition(ctx, ctx.params["audition_id"])
    wanted = parse_status(ctx.query["status"], extra=("reviewed",)) if ctx.query.get("status") else None
    rows = ctx.db.execute("SELECT * FROM submissions WHERE audition_id=? ORDER BY created DESC", (audition["id"],)).fetchall()
    items = [submission_summary(ctx, r, audition) for r in rows]
    if wanted == "reviewed":
        items = [i for i in items if i["reviewed"]]
    elif wanted:
        items = [i for i in items if i["status"] == wanted]
    return {"audition": {"id": audition["id"], "title": audition["title"], "ensemble": audition["ensemble"]},
            "submissions": items}


@ROUTER.route("GET", "/api/submissions/<submission_id:int>")
def submission_detail(ctx):
    submission, audition = owned_submission(ctx, ctx.params["submission_id"])
    review = _review_for(ctx.db, submission["id"])
    siblings = [r["id"] for r in ctx.db.execute("SELECT id FROM submissions WHERE audition_id=? ORDER BY created DESC", (audition["id"],))]
    position = siblings.index(submission["id"])
    return {"submission": {
        **submission_summary(ctx, submission, audition),
        "note": submission["note"], "timestamps": load_list(submission["timestamps"]),
        "audio_url": f"/api/submissions/{submission['id']}/audio",
        "has_audio": submission_media_path(ctx, submission) is not None,
        "duration": submission["duration_sec"],
        "review": review_json(review) if review else None,
        "audition": {"id": audition["id"], "title": audition["title"], "ensemble": audition["ensemble"]},
        "position": position + 1, "total": len(siblings),
        "previous_id": siblings[position - 1] if position > 0 else None,
        "next_id": siblings[position + 1] if position + 1 < len(siblings) else None,
    }}


def submission_media_path(ctx, submission):
    """The recording on disk for a submission, or None when it is missing."""
    s = ctx.settings
    if submission["source"] == "upload":
        path = s.submission_uploads_dir / submission["file"]
    else:
        clip = ctx.db.execute("SELECT * FROM clips WHERE id=?", (submission["clip_id"],)).fetchone()
        path = (s.clips_dir if clip["source"] == "library" else s.profile_uploads_dir) / clip["file"]
    return path if path.is_file() else None


@ROUTER.route("GET", "/api/submissions/<submission_id:int>/audio")
def submission_audio(ctx):
    """Authorized recording stream with Range support, for an <audio> element. This is the only route to a submission's
    media: there are no thumbnails or posters, so a director has no still image of a blind applicant."""
    submission, _ = owned_submission(ctx, ctx.params["submission_id"])
    path = submission_media_path(ctx, submission)
    if not path:
        raise not_found("This submission's recording is not available (a seed clip may still be 'coming soon').")
    return FileResponse(path, cache="private, no-store")
