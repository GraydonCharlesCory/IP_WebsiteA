"""Create the demo data on first run."""
import json
from . import seed_data as data
from .auth import hash_password
from .config import log
from .db import days_ago, now_iso
from .durations import mp4_duration
from .seed_opportunities import seed_opportunities
from .seed_social import seed_social


def seed(conn, clips_dir) -> None:
    ids, categories = _insert_users(conn)
    clip_ids = _insert_clips(conn, ids, categories, clips_dir)
    for handle, body, clip_file, days in data.POSTS:
        conn.execute(
            "INSERT INTO posts (author_id, category, body, clip_id, created) VALUES (?,?,?,?,?)",
            (ids[handle], categories[handle], body, clip_ids.get((handle, clip_file)), days_ago(days)),
        )
    opportunity_ids = seed_opportunities(conn, ids, clip_ids)
    seed_social(conn, ids, opportunity_ids)
    conn.commit()
    log.info("Seeded %d accounts, %d clips, %d opportunities", len(data.USERS), len(data.CLIPS), len(opportunity_ids))


def _insert_users(conn):
    password_hash = hash_password(data.DEMO_PASSWORD)
    ids, categories = {}, {}
    for role, name, handle, category, instrument, ensemble, bio, location, style in data.USERS:
        teaching = data.TEACHERS.get(handle)
        blurb, taught, rate = teaching or ("", [], "")
        cur = conn.execute(
            "INSERT INTO users (role, name, handle, email, password_hash, category, instrument, ensemble, bio, location,"
            " avatar_style, is_teacher, teacher_blurb, instruments_taught, rate_text, created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (role, name, handle, f"{handle.replace('-', '.')}@tutti.demo", password_hash, category, instrument, ensemble, bio,
             location, style, int(bool(teaching)), blurb, json.dumps(taught), rate, now_iso()),
        )
        ids[handle], categories[handle] = cur.lastrowid, category
    return ids, categories


def _insert_clips(conn, ids, categories, clips_dir) -> dict:
    """Clip ids keyed by (owner handle, file name): several owners may point at one media file."""
    clip_ids = {}
    for index, (handle, title, file_name, instrument) in enumerate(data.CLIPS):
        cur = conn.execute(
            "INSERT INTO clips (owner_id, title, file, source, category, instrument, duration_sec, created) VALUES (?,?,?,'library',?,?,?,?)",
            (ids[handle], title, file_name, categories[handle], instrument, mp4_duration(clips_dir / file_name), days_ago(20 - index)),
        )
        clip_ids[(handle, file_name)] = cur.lastrowid
    return clip_ids
