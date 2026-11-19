"""One-time explicit demo mappings; unknown/custom legacy records remain unknown."""
from .discovery import save_metadata

# Matched to original title AND owner. These are editorial demo definitions, not inferred categories.
MAPPINGS = (
    ("rhonda-holloway", "Lead Tenor Saxophone: 2027 Season", "Jazz", [], False),
    ("elena-voss", "Violin: Section Seat, Second Violins", "Orchestral", [], False),
    ("priya-raman", "Honors Jazz Combo: Winter Session", "Jazz", ["high_school"], True),
    ("naomi-castellanos", "Violin: Section Seats and Sub List", "Orchestral", [], False),
    ("tomas-ibarra", "Jazz Ensemble Rhythm Section: Spring Semester", "Jazz", ["college"], True),
    ("marcus-bell", "Trombone Chair: Mile High Big Band", "Jazz", [], False),
    ("marcus-bell", "Sub Needed: Friday Night Trombone", "Jazz", [], False),
    ("marcus-bell", "New Year's Eve Big Band Gala", "Jazz", [], False),
    ("marcus-bell", "Sunday Brunch Quartet: Rotating Chairs", "Jazz", [], False),
    ("elena-voss", "Holiday Pops: Extra Players", "Orchestral", [], False),
    ("priya-raman", "Student Showcase Rhythm Section", "Jazz", [], False),
    ("lakefront-school", "Emerging Performer Project Grant", "Cross-genre", [], False),
    ("lakefront-school", "Community Artist Residency", "Jazz", [], False),
    ("lakefront-school", "High-school seniors: College entrance auditions", "Classical", ["high_school"], True),
    ("lakefront-school", "High-school Summer Chamber Camp", "Classical", ["high_school"], False),
)


def seed_discovery(conn, fresh_demo=False):
    if conn.execute("SELECT 1 FROM demo_upgrades WHERE name='round4-discovery'").fetchone():
        return
    # Never classify pre-existing/user-authored records, even if a demo title was reused.
    for handle, title, genre, eligibility, hub in MAPPINGS if fresh_demo else ():
        rows = conn.execute("SELECT a.id FROM auditions a JOIN users u ON u.id=a.director_id WHERE u.handle=? AND a.title=?", (handle, title))
        for row in rows:
            if not conn.execute("SELECT 1 FROM opportunity_discovery WHERE audition_id=?", (row["id"],)).fetchone():
                save_metadata(conn, row["id"], {"genre": genre, "eligibility": eligibility, "student_hub": hub})
    conn.execute("INSERT INTO demo_upgrades VALUES('round4-discovery')")
    conn.commit()
