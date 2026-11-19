"""Read-only fictional previews, not auditions, teacher services, registrations or applications."""
# Each preview explicitly declares its own purpose and eligibility. No service/activities inference.
PREVIEWS = (
    ("rock-instructor", "lakefront-school", "teaching", "Rock Ensemble Instructor", "Rock", [], ["Guitar"],
     "Demo teaching position. Review this illustrative school opportunity; no application workflow is connected.", "2026-12-15"),
    ("improvisation", "lakefront-school", "clinic", "Improvisation studio", "Jazz", ["high_school", "college"], ["Saxophone"],
     "Demo in-person clinic for high-school and college musicians. January 16, 2027. No registration or payment.", "2027-01-16"),
    ("strings", "prairie-school", "clinic", "Strings technique workshop", "Classical", ["high_school", "college"], ["Violin"],
     "Demo in-person clinic for high-school and college musicians. February 6, 2027. No registration or payment.", "2027-02-06"),
)


def previews(conn):
    result = []
    for key, handle, kind, title, genre, eligibility, instruments, description, date in PREVIEWS:
        school = conn.execute("SELECT s.* FROM schools s JOIN users u ON s.owner_id=u.id WHERE u.handle=? ORDER BY s.id LIMIT 1", (handle,)).fetchone()
        if school:
            city = school["location"].split(",")[0].strip()
            result.append({"preview_id": key, "school_id": school["id"], "type": kind, "discovery_kind": kind,
                           "title": title, "ensemble": school["name"], "city": city, "location": school["location"],
                           "instruments": instruments, "genre": genre, "eligibility": eligibility,
                           "student_hub": kind == "clinic", "description": description, "deadline": date,
                           "status": "open", "workflow_url": None, "demo_preview": True})
    return result
