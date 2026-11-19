"""Rubrics, scoped guest evaluations and creator-only composite scores."""
import json
import re
import secrets

from ..db import load_list, now_iso
from ..errors import bad_request, forbidden, not_found
from . import ROUTER
from .lookups import owned_audition
from .serializers import review_json


def validate_rubric(items):
    if (not isinstance(items, list) or not 1 <= len(items) <= 12 or
            not all(isinstance(s, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,39}", s) for s in items) or
            len(set(items)) != len(items)):
        raise bad_request("Choose 1–12 unique rubric keys using lowercase letters, numbers and underscores.")
    return items


def director_review(row):
    data = review_json(row)
    if row["rubric_scores"] != "{}":
        data["scores"] = json.loads(row["rubric_scores"])
    return data


def composite(conn, sid):
    values = [r[0] for r in conn.execute(
        "SELECT average FROM reviews WHERE submission_id=? AND average IS NOT NULL UNION ALL "
        "SELECT average FROM guest_scores WHERE submission_id=?", (sid, sid))]
    return round(sum(values) / len(values), 2) if values else None


@ROUTER.route("PUT", "/api/auditions/<audition_id:int>/rubric")
def configure_rubric(ctx):
    row = owned_audition(ctx, ctx.params["audition_id"])
    if ctx.db.execute("SELECT 1 FROM submissions WHERE audition_id=?", (row["id"],)).fetchone():
        raise bad_request("Configure the rubric before the first application so every reviewer uses the same criteria.")
    rubric = validate_rubric(ctx.json().get("rubric"))
    ctx.db.execute("UPDATE auditions SET rubric=? WHERE id=?", (json.dumps(rubric), row["id"]))
    ctx.db.commit()
    return {"rubric": rubric}


@ROUTER.route("POST", "/api/auditions/<audition_id:int>/guests")
def invite_guest(ctx):
    row = owned_audition(ctx, ctx.params["audition_id"])
    label = str(ctx.json().get("label", "Guest judge")).strip()[:80]
    if not label:
        raise bad_request("Give this review link a label so you can revoke it later.")
    key = secrets.token_urlsafe(32)
    cur = ctx.db.execute("INSERT INTO guest_links(audition_id,capability,label) VALUES(?,?,?)", (row["id"], key, label))
    ctx.db.commit()
    return {"guest_id": cur.lastrowid, "label": label, "url": "/guest.html#" + key}


@ROUTER.route("GET", "/api/auditions/<audition_id:int>/guests")
def list_guests(ctx):
    row = owned_audition(ctx, ctx.params["audition_id"])
    return {"guests": [dict(r) for r in ctx.db.execute("SELECT id,label,revoked FROM guest_links WHERE audition_id=?", (row["id"],))]}


@ROUTER.route("DELETE", "/api/auditions/<audition_id:int>/guests/<guest_id:int>")
def revoke_guest(ctx):
    row = owned_audition(ctx, ctx.params["audition_id"])
    cur = ctx.db.execute("UPDATE guest_links SET revoked=1 WHERE id=? AND audition_id=?", (ctx.params["guest_id"], row["id"]))
    if not cur.rowcount:
        raise not_found("This guest link does not belong to this audition.")
    ctx.db.commit()
    return {"ok": True}


def guest_scope(ctx, sid=None):
    link = ctx.db.execute("SELECT * FROM guest_links WHERE capability=? AND revoked=0", (ctx.headers.get("X-Review-Key", ""),)).fetchone()
    if not link:
        raise forbidden("This review link is invalid or revoked. Ask the creating director for a new link.")
    audition = ctx.db.execute("SELECT * FROM auditions WHERE id=?", (link["audition_id"],)).fetchone()
    submission = None
    if sid is not None:
        submission = ctx.db.execute("SELECT * FROM submissions WHERE id=? AND audition_id=?", (sid, audition["id"])).fetchone()
        if not submission:
            raise not_found("That recording is outside this review link.")
    return link, audition, submission


@ROUTER.route("GET", "/api/guest")
def guest_board(ctx):
    from .submissions import applicant_json
    link, audition, _ = guest_scope(ctx)
    entries = []
    for sub in ctx.db.execute("SELECT * FROM submissions WHERE audition_id=? ORDER BY id", (audition["id"],)):
        score = ctx.db.execute("SELECT scores FROM guest_scores WHERE guest_id=? AND submission_id=?", (link["id"], sub["id"])).fetchone()
        entries.append({"id": sub["id"], "musician": applicant_json(ctx, sub),
                        "scores": json.loads(score[0]) if score else {}})
    return {"title": audition["title"], "blind_review": bool(audition["blind_review"]),
            "rubric": load_list(audition["rubric"]), "submissions": entries}


@ROUTER.route("PUT", "/api/guest/submissions/<submission_id:int>/score")
def guest_score(ctx):
    from .reviews import _score, average_of
    link, audition, sub = guest_scope(ctx, ctx.params["submission_id"])
    scores = ctx.json().get("scores")
    rubric = load_list(audition["rubric"])
    if not isinstance(scores, dict) or set(scores) != set(rubric):
        raise bad_request("Score every rubric criterion, and no others.")
    scores = {key: _score(value, key) for key, value in scores.items()}
    if None in scores.values():
        raise bad_request("Every guest criterion needs a whole-number score from 1 to 10.")
    ctx.db.execute("INSERT INTO guest_scores VALUES(?,?,?,?,?) ON CONFLICT(guest_id,submission_id) "
                   "DO UPDATE SET scores=excluded.scores,average=excluded.average,updated=excluded.updated",
                   (link["id"], sub["id"], json.dumps(scores), average_of(scores), now_iso()))
    ctx.db.commit()
    return {"saved": True, "scores": scores}


@ROUTER.route("GET", "/api/guest/submissions/<submission_id:int>/audio")
def guest_audio(ctx):
    from ..blind_audio import audio_only
    from ..responses import FileResponse
    from .submissions import submission_media_path
    _, audition, sub = guest_scope(ctx, ctx.params["submission_id"])
    path = submission_media_path(ctx, sub)
    if not path:
        raise not_found("This recording is missing. Ask the creating director to check the upload.")
    if audition["blind_review"]:
        return FileResponse(audio_only(path, ctx.settings), "audio/wav", "private, no-store")
    return FileResponse(path, cache="private, no-store")
