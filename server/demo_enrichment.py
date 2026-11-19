"""Read-only, labelled examples for known fictional seeds; never write authored data.

Kept separate from real credentials, alumni relations, posts and requirements so
neither editors nor application/review logic can mistake examples for real data.
"""
from .db import load_list
from .seed_data import USERS

SCHOOLS = {
    "lakefront-school": "Lakefront Conservatory",
    "prairie-school": "Prairie Arts Academy",
}
IDENTITIES = {row[2]: (row[0], row[1], row[3], row[5]) for row in USERS}
IDENTITIES.update({handle: ("school", name, "students", name) for handle, name in SCHOOLS.items()})

# Degree, fictional issuer, year/status, certificate and its demonstrated scope.
CREDENTIALS = {
    "leo-marquez": ("Bachelor of Music, Jazz Performance", "Lakefront Conservatory", "2024 · completed", "Jazz arranging certificate", "Big-band voicings and score preparation · 2025"),
    "dana-brooks": ("Diploma, Contemporary Performance", "Prairie Arts Academy", "2023 · completed", "Improvisation workshop certificate", "Harmonic analysis and ensemble listening · 2025"),
    "aiko-nakamura": ("Bachelor of Music, Violin Performance", "Lakefront Conservatory", "2027 · in progress", "Chamber music certificate", "Rehearsal leadership and string ensemble practice · 2025"),
    "maya-okafor": ("Bachelor of Music, Cello Performance", "Prairie Arts Academy", "2022 · completed", "Teaching foundations certificate", "Beginner lesson planning and supervised practice · 2024"),
    "jordan-wells": ("Secondary school music program", "Prairie Arts Academy", "2027 · in progress; no degree awarded", "Youth ensemble workshop certificate", "Trumpet section playing and aural skills · 2026"),
    "adam-reyes": ("Master of Music, Orchestral Performance", "Lakefront Conservatory", "2023 · completed", "Orchestral excerpts certificate", "Section preparation and audition repertoire · 2024"),
    "ronald-pierce": ("Bachelor of Music, Jazz Studies", "Prairie Arts Academy", "2019 · completed", "Music pedagogy certificate", "Studio lesson design and ensemble coaching · 2021"),
    "alex-chen": ("Bachelor of Music, Contemporary Guitar", "Lakefront Conservatory", "2028 · in progress", "Rhythm section workshop certificate", "Comping, chart reading and collaborative arranging · 2026"),
    "sofia-lindgren": ("Bachelor of Music, Violin Performance", "Prairie Arts Academy", "2025 · completed", "Chamber performance certificate", "Small-ensemble communication and recital preparation · 2025"),
}
UPDATES = {
    "lakefront-school": (
        ("2026-11-10", "Inside the rehearsal studio", "Our sample chamber lab pairs string and jazz students to explore phrasing and collaborative rehearsal."),
        ("2026-11-03", "A season of new work", "This fictional campus update highlights student arrangements and a community concert program in development."),
    ),
    "prairie-school": (
        ("2026-11-09", "Practice with purpose", "Our sample studio week explores warm-ups, reflective practice journals and peer listening."),
        ("2026-11-02", "Community concert notebook", "This fictional school update celebrates a student-led chamber program and conversations about programming."),
    ),
}
ALUMNI = {
    "lakefront-school": (
        ("Illustrative performance graduate — demo only", "Example pathway: chamber performance and ensemble collaboration · fictional class of 2024"),
        ("Illustrative arranging graduate — demo only", "Example pathway: composition and community programming · fictional class of 2023"),
    ),
    "prairie-school": (
        ("Illustrative teaching graduate — demo only", "Example pathway: beginner instruction and studio practice · fictional class of 2022"),
        ("Illustrative strings graduate — demo only", "Example pathway: string ensemble and recital preparation · fictional class of 2025"),
    ),
}
SCHOOL_OPPORTUNITIES = {
    "Emerging Performer Project Grant": "Sample project outline: describe an artistic goal, a rehearsal plan and an illustrative budget. This is not an additional application requirement.",
    "Community Artist Residency": "Sample residency plan: outline a community workshop and a collaborative performance. No placement or funding is promised.",
    "High-school seniors: College entrance auditions": "Sample preparation plan: choose contrasting repertoire and describe your musical interests. This example does not establish admission criteria.",
    "High-school Summer Chamber Camp": "Sample camp overview: explore coached chamber rehearsals, listening sessions and a final sharing. No registration or payment is available.",
}


def known_identity(row):
    return bool(row and IDENTITIES.get(row["handle"]) == (row["role"], row["name"], row["category"], row["ensemble"])
                and row["email"] == row["handle"].replace("-", ".") + "@tutti.demo")


def musician_examples(row):
    if not known_identity(row) or row["handle"] not in CREDENTIALS:
        return {}
    degree, issuer, status, certificate, scope = CREDENTIALS[row["handle"]]
    return {"education": [] if load_list(row["education"]) else [
                {"degree": degree, "school": issuer, "detail": status}],
            "certifications": [] if load_list(row["certifications"]) else [
                {"title": certificate, "issuer": issuer, "detail": scope}]}


def school_examples(conn, row, has_alumni):
    owner = conn.execute("SELECT * FROM users WHERE id=?", (row["owner_id"],)).fetchone()
    if not known_identity(owner) or SCHOOLS.get(owner["handle"]) != row["name"]:
        return {}
    handle = owner["handle"]
    # Never reuse an account identity: unlinking someone must remove that person.
    alumni = [] if has_alumni else [{"name": name, "detail": detail}
                                    for name, detail in ALUMNI[handle]]
    return {"posts": [{"date": date, "title": title, "body": body} for date, title, body in UPDATES[handle]],
            "alumni": alumni}


def opportunity_example(conn, row):
    # Only empty original school seeds; never infer eligibility or change workflow.
    if row["title"] not in SCHOOL_OPPORTUNITIES or load_list(row["requirements"]):
        return ""
    school = conn.execute("SELECT * FROM schools WHERE id=?", (row["school_id"],)).fetchone()
    if not school or school["owner_id"] != row["director_id"]:
        return ""
    owner = conn.execute("SELECT * FROM users WHERE id=?", (row["director_id"],)).fetchone()
    original = "Fictional opportunity. Submit one performance recording and review the program requirements."
    if (not known_identity(owner) or owner["handle"] != "lakefront-school"
            or school["name"] != SCHOOLS["lakefront-school"] or row["description"] != original):
        return ""
    return SCHOOL_OPPORTUNITIES[row["title"]]
