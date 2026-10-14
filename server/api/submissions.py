"""Submitting to auditions (musicians) and reading submissions (only the posting director)."""
import json

from ..auth import require_role
from ..db import load_list, now_iso
from ..errors import ApiError, bad_request, not_found
from ..media import save_upload
from ..responses import FileResponse, JsonResponse
from ..validation import optional_text
from . import ROUTER
from .lookups import get_audition, owned_audition, owned_submission
from .queries import clips_list
from .serializers import brief_user, clip_url, full_user, review_json

STATUS_FILTERS = ("new", "shortlisted", "passed", "reviewed")


def _timestamps(raw) -> list:
    """Accepts a list (JSON body) or a JSON string (query param) of {time, label}."""
    if raw in (None, ""):
        return []
    try:
        items = json.loads(raw) if isinstance(raw, str) else raw
        return [{"time": int(i["time"]), "label": str(i["label"])[:120]} for i in items]
    except (ValueError, TypeError, KeyError):
        raise bad_request("Timestamps must be a list like [{\"time\": 134, \"label\": \"Ballad\"}] with times in seconds.")


def _create_submission(ctx, audition, musician) -> int:
    """Insert the submission from either a raw MP4 upload or an existing profile clip."""
    wants_upload = (ctx.headers.get("Content-Type") or "").lower().startswith("video/")
    if wants_upload:
        note = optional_text(ctx.query, "note", 2000)
        timestamps = _timestamps(ctx.query.get("timestamps"))
        file_name = save_upload(ctx, ctx.settings.submission_uploads_dir)
        source, clip_id = "upload", None
    else:
        data = ctx.json()
        note = optional_text(data, "note", 2000)
        timestamps = _timestamps(data.get("timestamps"))
        clip_id = data.get("clip_id")
        owned = ctx.db.execute("SELECT id FROM clips WHERE id=? AND owner_id=?", (clip_id, musician["id"])).fetchone()
        if not owned:
            raise bad_request("Choose one of your own profile clips, or upload an MP4 video.")
        source, file_name = "clip", None
    cur = ctx.db.execute(
        "INSERT INTO submissions (audition_id, musician_id, source, file, clip_id, note, timestamps, status, created)"
        " VALUES (?,?,?,?,?,?,?,'new',?)",
        (audition["id"], musician["id"], source, file_name, clip_id, note, json.dumps(timestamps), now_iso()),
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
    if ctx.db.execute("SELECT 1 FROM submissions WHERE audition_id=? AND musician_id=?", (audition["id"], musician["id"])).fetchone():
        raise ApiError(409, "You have already submitted to this audition.")
    submission_id = _create_submission(ctx, audition, musician)
    created = ctx.db.execute("SELECT created FROM submissions WHERE id=?", (submission_id,)).fetchone()["created"]
    return JsonResponse({"submission": {"id": submission_id, "audition_id": audition["id"], "status": "Submitted", "created": created}}, 201)


@ROUTER.route("GET", "/api/my/submissions")
def my_submissions(ctx):
    """Musician's own submissions: status is always 'Submitted'; scores and comments never appear."""
    musician = require_role(ctx, "musician", "see your submissions")
    rows = ctx.db.execute(
        "SELECT s.id, s.audition_id, s.created, a.title, a.ensemble FROM submissions s"
        " JOIN auditions a ON a.id = s.audition_id WHERE s.musician_id=? ORDER BY s.created DESC", (musician["id"],)
    ).fetchall()
    return {"submissions": [{"id": r["id"], "audition_id": r["audition_id"], "audition_title": r["title"],
                             "ensemble": r["ensemble"], "status": "Submitted", "created": r["created"]} for r in rows]}


def _review_for(conn, submission_id):
    return conn.execute("SELECT * FROM reviews WHERE submission_id=?", (submission_id,)).fetchone()


def submission_summary(ctx, row) -> dict:
    musician = ctx.db.execute("SELECT * FROM users WHERE id=?", (row["musician_id"],)).fetchone()
    review = _review_for(ctx.db, row["id"])
    return {
        "id": row["id"], "audition_id": row["audition_id"], "musician": {**brief_user(musician), "location": musician["location"]},
        "source": row["source"], "status": row["status"], "created": row["created"],
        "average": review["average"] if review else None, "reviewed": bool(review and review["average"] is not None),
    }


@ROUTER.route("GET", "/api/auditions/<audition_id:int>/submissions")
def list_submissions(ctx):
    audition = owned_audition(ctx, ctx.params["audition_id"])
    wanted = ctx.query.get("status")
    if wanted and wanted not in STATUS_FILTERS:
        raise bad_request(f"Filter by status: {', '.join(STATUS_FILTERS)}.")
    rows = ctx.db.execute("SELECT * FROM submissions WHERE audition_id=? ORDER BY created DESC", (audition["id"],)).fetchall()
    items = [submission_summary(ctx, r) for r in rows]
    if wanted == "reviewed":
        items = [i for i in items if i["reviewed"]]
    elif wanted:
        items = [i for i in items if i["status"] == wanted]
    return {"audition": {"id": audition["id"], "title": audition["title"], "ensemble": audition["ensemble"]},
            "submissions": items}


@ROUTER.route("GET", "/api/submissions/<submission_id:int>")
def submission_detail(ctx):
    submission, audition = owned_submission(ctx, ctx.params["submission_id"])
    musician = ctx.db.execute("SELECT * FROM users WHERE id=?", (submission["musician_id"],)).fetchone()
    review = _review_for(ctx.db, submission["id"])
    siblings = [r["id"] for r in ctx.db.execute("SELECT id FROM submissions WHERE audition_id=? ORDER BY created DESC", (audition["id"],))]
    position = siblings.index(submission["id"])
    return {"submission": {
        **submission_summary(ctx, submission),
        "note": submission["note"], "timestamps": load_list(submission["timestamps"]),
        "video_url": f"/api/submissions/{submission['id']}/video",
        "has_video": submission_video_path(ctx, submission) is not None,
        "musician": full_user(musician),
        "musician_clips": clips_list(ctx.settings, ctx.db, owner_id=musician["id"]),
        "review": review_json(review) if review else None,
        "audition": {"id": audition["id"], "title": audition["title"], "ensemble": audition["ensemble"]},
        "position": position + 1, "total": len(siblings),
        "previous_id": siblings[position - 1] if position > 0 else None,
        "next_id": siblings[position + 1] if position + 1 < len(siblings) else None,
    }}


def submission_video_path(ctx, submission):
    """The file on disk for a submission's video, or None when it is missing."""
    s = ctx.settings
    if submission["source"] == "upload":
        path = s.submission_uploads_dir / submission["file"]
    else:
        clip = ctx.db.execute("SELECT * FROM clips WHERE id=?", (submission["clip_id"],)).fetchone()
        path = (s.clips_dir if clip["source"] == "library" else s.profile_uploads_dir) / clip["file"]
    return path if path.is_file() else None


@ROUTER.route("GET", "/api/submissions/<submission_id:int>/video")
def submission_video(ctx):
    """Authorized video stream with Range support; the only way to reach a submission's video."""
    submission, _ = owned_submission(ctx, ctx.params["submission_id"])
    path = submission_video_path(ctx, submission)
    if not path:
        raise not_found("This submission's video file is not available (a seed clip may still be 'coming soon').")
    return FileResponse(path, cache="private, no-store")
