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
        "initials": initials(row["name"]), "avatar_style": row["avatar_style"],
    }


def full_user(row) -> dict:
    return {**brief_user(row), "bio": row["bio"], "location": row["location"]}


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


def audition_json(row, director_row) -> dict:
    return {
        "id": row["id"], "category": row["category"], "title": row["title"], "ensemble": row["ensemble"],
        "instruments": load_list(row["instruments"]), "description": row["description"],
        "requirements": load_list(row["requirements"]), "timeline": load_list(row["timeline"]),
        "deadline": row["deadline"], "status": row["status"], "created": row["created"],
        "director": brief_user(director_row),
    }


def review_json(row) -> dict:
    return {
        "scores": {name: row[name] for name in REVIEW_CRITERIA},
        "average": row["average"], "comments": row["comments"],
        "notes": load_list(row["notes"]), "decision": row["decision"], "updated": row["updated"],
    }


def dumps(value) -> str:
    return json.dumps(value)
