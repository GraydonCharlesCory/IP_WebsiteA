"""Turn database rows into the JSON shapes documented in the README."""
import json

from ..db import load_list

SECTION_LABELS = {"students": "Students", "orchestral": "Orchestral", "jazz": "Jazz"}
REVIEW_CRITERIA = ("tone", "rhythm", "technique", "musicality", "preparation")


def initials(name: str) -> str:
    return "".join(word[0] for word in name.split()[:2]).upper()


def brief_user(row) -> dict:
    return {
        "id": row["id"], "role": row["role"], "name": row["name"], "handle": row["handle"],
        "category": row["category"], "instrument": row["instrument"], "ensemble": row["ensemble"],
        "initials": initials(row["name"]), "avatar_style": row["avatar_style"], "is_teacher": bool(row["is_teacher"]),
    }


def full_user(row) -> dict:
    return {
        **brief_user(row), "bio": row["bio"], "location": row["location"],
        "teaching": {
            "blurb": row["teacher_blurb"], "instruments": load_list(row["instruments_taught"]), "rate": row["rate_text"],
        } if row["is_teacher"] else None,
    }


def anonymous_applicant(label_id: int, instrument: str, prefix: str = "A") -> dict:
    """The only description of a musician a director may ever see: no name, handle, id, location or photo.
    `prefix` tells the sources apart: A-<submission id> for applicants, C-<conversation id> for other message partners."""
    label = f"Applicant {prefix}-{label_id}"
    return {
        "id": None, "role": "musician", "name": label, "label": label, "handle": None, "category": None,
        "instrument": instrument, "ensemble": "", "initials": "?", "avatar_style": 0, "is_teacher": False,
        "location": "", "anonymous": True,
    }


def own_user(row) -> dict:
    return {**full_user(row), "email": row["email"]}


def clip_url(row) -> str:
    if row["source"] == "library":
        return f"/media/clips/{row['file']}"
    return f"/media/uploads/{row['file']}"


def clip_file_exists(settings, row) -> bool:
    folder = settings.clips_dir if row["source"] == "library" else settings.profile_uploads_dir
    return (folder / row["file"]).is_file()


def clip_json(settings, row, owner_row=None) -> dict:
    data = {
        "id": row["id"], "title": row["title"], "category": row["category"],
        "instrument": row["instrument"], "created": row["created"],
        "video_url": clip_url(row), "available": clip_file_exists(settings, row),
    }
    if owner_row is not None:
        data["owner"] = brief_user(owner_row)
    return data


def post_json(settings, conn, row) -> dict:
    author = conn.execute("SELECT * FROM users WHERE id = ?", (row["author_id"],)).fetchone()
    clip = None
    if row["clip_id"]:
        clip_row = conn.execute("SELECT * FROM clips WHERE id = ?", (row["clip_id"],)).fetchone()
        clip = clip_json(settings, clip_row)
    return {
        "id": row["id"], "category": row["category"], "body": row["body"], "created": row["created"],
        "author": brief_user(author), "clip": clip,
    }


def opportunity_card(row) -> dict:
    """The short description of an opportunity (audition or gig) used in lists and on ensemble pages."""
    place = ", ".join(part for part in (row["city"], row["state"]) if part)
    return {
        "id": row["id"], "type": row["type"], "category": row["category"], "title": row["title"],
        "ensemble": row["ensemble"], "ensemble_id": row["ensemble_id"], "deadline": row["deadline"],
        "status": row["status"], "city": row["city"], "state": row["state"], "location": place,
        "level": row["level"], "paid": bool(row["paid"]), "pay": row["pay_text"],
        "video_round_accepted": bool(row["video_round_accepted"]),
    }


def audition_json(row, director_row) -> dict:
    return {
        **opportunity_card(row),
        "instruments": load_list(row["instruments"]), "description": row["description"],
        "requirements": load_list(row["requirements"]), "timeline": load_list(row["timeline"]),
        "created": row["created"], "director": brief_user(director_row),
        "callback": {"date": row["callback_date"], "location": row["callback_location"]}
        if row["callback_date"] or row["callback_location"] else None,
    }


def review_json(row) -> dict:
    return {
        "scores": {name: row[name] for name in REVIEW_CRITERIA},
        "average": row["average"], "comments": row["comments"],
        "notes": load_list(row["notes"]), "decision": row["decision"], "updated": row["updated"],
        "feedback_shared": bool(row["feedback_shared"]), "feedback_includes_notes": bool(row["feedback_includes_notes"]),
    }


def shared_feedback_json(row) -> dict:
    """What a musician may see of a review once the director shares it (notes only on explicit request)."""
    data = {
        "average": row["average"], "scores": {name: row[name] for name in REVIEW_CRITERIA},
        "comments": row["comments"], "shared_at": row["feedback_shared_at"], "notes": None,
    }
    if row["feedback_includes_notes"]:
        data["notes"] = load_list(row["notes"])
    return data


def dumps(value) -> str:
    return json.dumps(value)
