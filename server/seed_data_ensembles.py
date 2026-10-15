"""Fictional ensembles, one per demo director, with public page content."""

# director handle -> ensemble fields (name matches the director's `ensemble` in seed_data.USERS)
ENSEMBLES = {
    "rhonda-holloway": dict(
        name="Bayview Jazz Orchestra", category="jazz", city="San Francisco", state="CA", founded=1994,
        about="A professional 17-piece big band performing new commissions and the classic repertoire in Bay Area concert halls.",
        season="2027 season: twelve concerts, a spring tour and a live recording at Bayview Hall.",
        highlights=["Nominated for a regional jazz recording award, 2024", "Annual Ellington tribute with student guests", "Residency at the Bayview Hall series since 2011"],
        roster=[{"name": "Dr. Rhonda Holloway", "instrument": "Conductor"}, {"name": "Tyrell Washington", "instrument": "Lead alto saxophone"},
                {"name": "Camille Ortiz", "instrument": "Lead trumpet"}, {"name": "Ben Adler", "instrument": "Bass"}],
        logo_initials="BJ", logo_color="#c2410c"),
    "elena-voss": dict(
        name="Lakeshore Symphony", category="orchestral", city="Chicago", state="IL", founded=1958,
        about="A full-time professional symphony known for adventurous programming and a long tradition of developing section players into principals.",
        season="2027 season: eight subscription weeks, a holiday pops series and a summer lakefront festival.",
        highlights=["Screened auditions with blind first rounds", "Principal chairs filled from within in 6 of the last 8 openings", "Broadcast partnership with a regional public radio station"],
        roster=[{"name": "Elena Voss", "instrument": "Music director"}, {"name": "Priscilla Hart", "instrument": "Concertmaster"},
                {"name": "Daniel Okoye", "instrument": "Principal cello"}, {"name": "Mei-Lin Zhao", "instrument": "Principal flute"}],
        logo_initials="LS", logo_color="#1d4ed8"),
    "priya-raman": dict(
        name="Bay Area Youth Jazz All-Stars", category="students", city="Oakland", state="CA", founded=2012,
        about="An honors jazz program for players aged 14 to 18, with weekly rehearsals, coaching from working professionals and a winter showcase.",
        season="Winter session: weekly rehearsals January to March, showcase on the first Saturday of April.",
        highlights=["Alumni now in conservatory jazz programs nationwide", "Opened for a touring big band, 2025", "Free tuition for every accepted player"],
        roster=[{"name": "Priya Raman", "instrument": "Director"}, {"name": "Jelani Brooks", "instrument": "Coach, drums"}],
        logo_initials="YA", logo_color="#047857"),
    "marcus-bell": dict(
        name="Mile High Jazz Collective", category="jazz", city="Denver", state="CO", founded=2016,
        about="Denver's working jazz company: a rotating pool of professional players covering club nights, private events, festivals and a New Year's big band.",
        season="Weekly club residency plus 40 private and festival dates a year. Subs are paid per gig, same night where possible.",
        highlights=["Weekly residency at the Capitol Hill Jazz Loft", "Headliner at a Front Range summer jazz festival, 2025", "Pays subs within seven days"],
        roster=[{"name": "Marcus Bell", "instrument": "Bandleader, piano"}, {"name": "Lena Park", "instrument": "Alto saxophone"},
                {"name": "Omar Haddad", "instrument": "Bass"}, {"name": "Ronald Pierce", "instrument": "Trombone (regular sub)"}],
        logo_initials="MH", logo_color="#7c3aed"),
    "naomi-castellanos": dict(
        name="Rocky Mountain Chamber Orchestra", category="orchestral", city="Denver", state="CO", founded=1988,
        about="A 38-player chamber orchestra pairing classical staples with new music, rehearsing in the evenings so working players can join.",
        season="Four programs from October to May, plus an outdoor summer concert.",
        highlights=["Three world premieres in the last two seasons", "Evening rehearsals for working musicians", "Guest soloists from regional conservatories"],
        roster=[{"name": "Naomi Castellanos", "instrument": "Music director"}, {"name": "Grace Whitfield", "instrument": "Concertmaster"},
                {"name": "Pedro Alves", "instrument": "Principal viola"}],
        logo_initials="RM", logo_color="#be123c"),
    "tomas-ibarra": dict(
        name="Front Range University Jazz Ensemble", category="students", city="Boulder", state="CO", founded=1971,
        about="The flagship jazz ensemble of Front Range University's jazz studies program. Open to students from any major by audition.",
        season="Fall and spring semesters with a concert each term and an end-of-year festival trip.",
        highlights=["Open to non-majors", "Invited to a collegiate jazz festival three years running", "Guest clinicians from the Denver scene"],
        roster=[{"name": "Prof. Tomás Ibarra", "instrument": "Director"}, {"name": "Sam Whitaker", "instrument": "Student leader, drums"}],
        logo_initials="FR", logo_color="#0e7490"),
}
