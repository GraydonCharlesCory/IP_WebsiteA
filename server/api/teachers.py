"""Teachers and tutors: musicians who offer lessons or clinics."""
from . import ROUTER
from .credibility import badges_for
from .serializers import full_user


def teachers_list(conn, instrument=None, text=None):
    rows = conn.execute("SELECT * FROM users WHERE role='musician' AND is_teacher=1 ORDER BY name").fetchall()
    people = []
    for row in rows:
        haystack = f"{row['name']} {row['bio']} {row['teacher_blurb']} {row['location']}".lower()
        taught = row["instruments_taught"].lower() + row["instrument"].lower()
        if (instrument and instrument.lower() not in taught) or (text and text.lower() not in haystack):
            continue
        people.append({**full_user(row), "badges": badges_for(conn, row["id"])})
    return people


@ROUTER.route("GET", "/api/teachers")
def list_teachers(ctx):
    """Public. Filters: ?instrument=<taught instrument>&q=<name, city or text>."""
    return {"teachers": teachers_list(ctx.db, ctx.query.get("instrument"), ctx.query.get("q"))}
