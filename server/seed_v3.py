"""One-time additive demo expansion, also safe on existing version-2 data."""
import json

from .auth import hash_password
from .db import now_iso


def seed_v3(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS demo_upgrades(name TEXT PRIMARY KEY)")
    if conn.execute("SELECT 1 FROM demo_upgrades WHERE name='v3'").fetchone():
        return
    for name, handle, location in (("Lakefront Conservatory", "lakefront-school", "Chicago, IL"),
                                   ("Prairie Arts Academy", "prairie-school", "Madison, WI")):
        conn.execute("INSERT OR IGNORE INTO users(role,name,handle,email,password_hash,category,ensemble,location,created) "
                     "VALUES('school',?,?,?,?, 'students',?,?,?)",
                     (name, handle, handle.replace('-', '.') + '@tutti.demo', hash_password('demo'), name, location, now_iso()))
        uid = conn.execute("SELECT id FROM users WHERE handle=?", (handle,)).fetchone()[0]
        cur = conn.execute("INSERT INTO schools(owner_id,name,location,about,programs,activities) VALUES(?,?,?,?,?,?)",
                           (uid, name, location, "Fictional demo school supporting emerging performers.",
                            json.dumps(["Bachelor of Music", "Summer performance institute"]), json.dumps(["Chamber ensembles", "Community concerts"])))
        school_id = cur.lastrowid
        if handle == "lakefront-school":
            for kind, title, level, paid in (
                ("grant", "Emerging Performer Project Grant", "college", 1),
                ("residency", "Community Artist Residency", "pro", 1),
                ("college_audition", "High-school seniors: College entrance auditions", "student", 0),
                ("summer_camp", "High-school Summer Chamber Camp", "student", 0),
            ):
                conn.execute("INSERT INTO auditions(director_id,school_id,type,category,title,ensemble,description,deadline,level,paid,city,state,timeline,created) "
                             "VALUES(?,?,?,'students',?,?,?,'2027-03-01',?,?,'Chicago','IL',?,?)",
                             (uid, school_id, kind, title, name, "Fictional opportunity. Submit one performance recording and review the program requirements.",
                              level, paid, json.dumps([{"label": "Applications close", "date": "2027-03-01"}, {"label": "Results", "date": "2027-04-01"}]), now_iso()))
    conn.execute("INSERT INTO demo_upgrades VALUES('v3')")
    conn.commit()
