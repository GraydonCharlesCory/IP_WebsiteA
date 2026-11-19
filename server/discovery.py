"""Explicit discovery metadata, independent of legacy audience sections and review workflows."""
import json

from .db import load_list
from .validation import parse_flag, require_choice, string_list

GENRES = ("Rock", "Pop", "Hip-hop", "R&B", "Soul", "Funk", "Blues", "Electronic", "Country", "Folk",
          "Gospel", "Latin", "Reggae", "World", "Musical theatre", "Experimental", "Classical", "Jazz",
          "Orchestral", "Cross-genre")
ELIGIBILITY = ("high_school", "college")


def metadata(conn, audition_id):
    row = conn.execute("SELECT * FROM opportunity_discovery WHERE audition_id=?", (audition_id,)).fetchone()
    return {"genre": row["genre"] if row else "", "eligibility": load_list(row["eligibility"]) if row else [],
            "student_hub": bool(row["student_hub"]) if row else False}


def validate_metadata(data, current):
    genre = data.get("genre", current["genre"])
    genre = require_choice(genre, ("", *GENRES), "genre")
    eligibility = string_list(data, "eligibility") if "eligibility" in data else current["eligibility"]
    for item in eligibility:
        require_choice(item, ELIGIBILITY, "student eligibility")
    hub = parse_flag(data["student_hub"], "student_hub") if "student_hub" in data else current["student_hub"]
    return {"genre": genre, "eligibility": eligibility, "student_hub": hub}


def save_metadata(conn, audition_id, data):
    conn.execute("INSERT INTO opportunity_discovery VALUES(?,?,?,?) ON CONFLICT(audition_id) DO UPDATE SET "
                 "genre=excluded.genre, eligibility=excluded.eligibility, student_hub=excluded.student_hub",
                 (audition_id, data["genre"], json.dumps(data["eligibility"]), int(data["student_hub"])))
