"""Seed ensembles, opportunities (auditions and gigs), submissions with reviews, and gig availability."""
import json

from . import seed_data_opportunities as demo
from .api.reviews import average_of
from .api.serializers import REVIEW_CRITERIA
from .api.statuses import DECISION_TO_STATUS
from .db import days_ago, now_iso
from .seed_data_ensembles import ENSEMBLES


def seed_opportunities(conn, ids, clip_ids) -> list:
    ensemble_ids = {handle: _insert_ensemble(conn, ids[handle], row) for handle, row in ENSEMBLES.items()}
    opportunity_ids = [_insert_opportunity(conn, ids, ensemble_ids, row) for row in demo.OPPORTUNITIES]
    for row in demo.SUBMISSIONS:
        _insert_submission(conn, ids, clip_ids, opportunity_ids, row)
    for gig_index, marks in demo.GIG_AVAILABILITY.items():
        for handle, status in marks.items():
            conn.execute("INSERT INTO gig_availability (audition_id, musician_id, status, updated) VALUES (?,?,?,?)",
                         (opportunity_ids[gig_index], ids[handle], status, now_iso()))
    return opportunity_ids


def _insert_ensemble(conn, director_id, row) -> int:
    cur = conn.execute(
        "INSERT INTO ensembles (director_id, name, category, city, state, about, founded, season, highlights, roster,"
        " logo_initials, logo_color, created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (director_id, row["name"], row["category"], row["city"], row["state"], row["about"], row["founded"], row["season"],
         json.dumps(row["highlights"]), json.dumps(row["roster"]), row["logo_initials"], row["logo_color"], now_iso()),
    )
    return cur.lastrowid


def _insert_opportunity(conn, ids, ensemble_ids, row) -> int:
    ensemble = conn.execute("SELECT * FROM ensembles WHERE id=?", (ensemble_ids[row["director"]],)).fetchone()
    callback_date, callback_location = row.get("callback", ("", ""))
    cur = conn.execute(
        "INSERT INTO auditions (director_id, ensemble_id, type, category, title, ensemble, instruments, description, requirements,"
        " timeline, deadline, status, city, state, level, paid, pay_text, video_round_accepted, callback_date, callback_location,"
        " blind_review, created) VALUES (?,?,?,?,?,?,?,?,?,?,?,'open',?,?,?,?,?,?,?,?,?,?)",
        (ids[row["director"]], ensemble["id"], row.get("type", "audition"), ensemble["category"], row["title"], ensemble["name"],
         json.dumps(row["instruments"]), row["description"], json.dumps(row.get("requirements", [])),
         json.dumps([{"label": label, "date": date} for label, date in row.get("timeline", [])]), row["deadline"],
         ensemble["city"], ensemble["state"], row["level"], int(row["paid"]), row["pay"], int(row.get("video_round", False)),
         callback_date, callback_location, int(row.get("blind", False)), days_ago(10)),
    )
    if "gig" in row:
        _insert_gig(conn, cur.lastrowid, row["gig"])
    return cur.lastrowid


def _insert_gig(conn, audition_id, gig) -> None:
    (money, money_note), (musicians, musicians_note), (music, music_note) = gig["money"], gig["musicians"], gig["music"]
    conn.execute(
        "INSERT INTO gig_details (audition_id, gig_date, start_time, venue, money_rating, money_note, musicians_rating,"
        " musicians_note, music_rating, music_note) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (audition_id, gig["date"], gig["start_time"], gig["venue"], money, money_note, musicians, musicians_note, music, music_note),
    )


def _insert_submission(conn, ids, clip_ids, opportunity_ids, row) -> None:
    review = row.get("review")
    status = row.get("status") or (DECISION_TO_STATUS[review[3]] if review else "submitted")
    callback_date, callback_place, callback_message = row.get("callback", ("", "", ""))
    cur = conn.execute(
        "INSERT INTO submissions (audition_id, musician_id, source, clip_id, note, timestamps, status, callback_date,"
        " callback_location, callback_message, created) VALUES (?,?,'clip',?,?,?,?,?,?,?,?)",
        (opportunity_ids[row["audition"]], ids[row["musician"]], clip_ids[(row["musician"], row["clip"])], row["note"],
         json.dumps(row["timestamps"]), status, callback_date, callback_place, callback_message, days_ago(row["days"])),
    )
    if review:
        scores, comments, notes, decision = review
        shared = int(row.get("share_feedback", False))
        conn.execute(
            "INSERT INTO reviews (submission_id, tone, rhythm, technique, musicality, preparation, average, comments, notes,"
            " decision, feedback_shared, feedback_shared_at, updated) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (cur.lastrowid, *(scores[n] for n in REVIEW_CRITERIA), average_of(scores), comments, json.dumps(notes), decision,
             shared, now_iso() if shared else None, now_iso()),
        )
