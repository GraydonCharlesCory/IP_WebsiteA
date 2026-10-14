"""Create the demo data on first run."""
import json
from datetime import datetime, timedelta, timezone

from . import seed_data as data
from .api.reviews import DECISION_TO_STATUS, average_of
from .api.serializers import REVIEW_CRITERIA
from .auth import hash_password
from .config import log
from .db import now_iso


def _days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")


def seed(conn) -> None:
    password_hash = hash_password(data.DEMO_PASSWORD)
    ids, categories = {}, {}
    for role, name, handle, category, instrument, ensemble, bio, location, style in data.USERS:
        cur = conn.execute(
            "INSERT INTO users (role, name, handle, email, password_hash, category, instrument, ensemble, bio, location, avatar_style, created)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (role, name, handle, f"{handle.replace('-', '.')}@tutti.demo", password_hash, category, instrument, ensemble, bio, location, style, now_iso()),
        )
        ids[handle], categories[handle] = cur.lastrowid, category
    clip_ids = {}
    for index, (handle, title, file_name, instrument) in enumerate(data.CLIPS):
        cur = conn.execute(
            "INSERT INTO clips (owner_id, title, file, source, category, instrument, created) VALUES (?,?,?,'library',?,?,?)",
            (ids[handle], title, file_name, categories[handle], instrument, _days_ago(20 - index)),
        )
        clip_ids[file_name] = cur.lastrowid
    for handle, body, clip_file, days in data.POSTS:
        conn.execute(
            "INSERT INTO posts (author_id, category, body, clip_id, created) VALUES (?,?,?,?,?)",
            (ids[handle], categories[handle], body, clip_ids.get(clip_file), _days_ago(days)),
        )
    audition_ids = [_insert_audition(conn, ids, row) for row in data.AUDITIONS]
    for handle, audition_index, clip_file, note, timestamps, days, review in data.SUBMISSIONS:
        status = DECISION_TO_STATUS[review[3]] if review else "new"
        cur = conn.execute(
            "INSERT INTO submissions (audition_id, musician_id, source, clip_id, note, timestamps, status, created) VALUES (?,?,'clip',?,?,?,?,?)",
            (audition_ids[audition_index], ids[handle], clip_ids[clip_file], note, json.dumps(timestamps), status, _days_ago(days)),
        )
        if review:
            _insert_review(conn, cur.lastrowid, *review)
    conn.commit()
    log.info("Seeded %d accounts, %d clips, %d auditions", len(data.USERS), len(data.CLIPS), len(audition_ids))


def _insert_audition(conn, ids, row) -> int:
    handle, title, instruments, description, requirements, timeline, deadline = row
    director = conn.execute("SELECT ensemble, category FROM users WHERE id=?", (ids[handle],)).fetchone()
    cur = conn.execute(
        "INSERT INTO auditions (director_id, category, title, ensemble, instruments, description, requirements, timeline, deadline, status, created)"
        " VALUES (?,?,?,?,?,?,?,?,?,'open',?)",
        (ids[handle], director["category"], title, director["ensemble"], json.dumps(instruments), description,
         json.dumps(requirements), json.dumps(timeline), deadline, _days_ago(10)),
    )
    return cur.lastrowid


def _insert_review(conn, submission_id, scores, comments, notes, decision):
    conn.execute(
        "INSERT INTO reviews (submission_id, tone, rhythm, technique, musicality, preparation, average, comments, notes, decision, updated)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (submission_id, *(scores[n] for n in REVIEW_CRITERIA), average_of(scores), comments, json.dumps(notes), decision, now_iso()),
    )
