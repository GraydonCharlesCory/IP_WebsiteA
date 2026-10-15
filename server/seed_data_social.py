"""Demo badges, endorsements and message threads."""

# handle, kind, label, verified by Tutti
BADGES = [
    ("adam-reyes", "union", "AFM Local 802", True),
    ("adam-reyes", "school", "Lakeview Conservatory, M.M. Violin", True),
    ("adam-reyes", "ensemble", "Section violin, Harbor City Symphony", False),
    ("ronald-pierce", "union", "AFM Local 20-47", True),
    ("ronald-pierce", "ensemble", "Mile High Jazz Collective", True),
    ("leo-marquez", "school", "Eastbridge Conservatory", True),
    ("leo-marquez", "ensemble", "Eastbridge Concert Jazz Orchestra", False),
    ("aiko-nakamura", "school", "Chicago Conservatory of Music", True),
    ("maya-okafor", "union", "AFM Local 77", False),
    ("alex-chen", "school", "Front Range University (student)", True),
    ("jordan-wells", "school", "Texas All-State Honor Band", False),
]

# musician, author, relationship, text
ENDORSEMENTS = [
    ("adam-reyes", "elena-voss", "Hired him as a sub violinist", "Adam learned a full program in four days and sat in the section like he had played with us for years. Specific, honest feedback to his stand partner too."),
    ("ronald-pierce", "marcus-bell", "Has used him as a regular sub for six years", "Never late, always prepared, and the band sounds bigger with him in the chair. Our first call for trombone."),
    ("aiko-nakamura", "maya-okafor", "Stand partner", "Aiko shifts with the section and listens harder than anyone I have played with."),
    ("jordan-wells", "priya-raman", "Clinician at the All-Stars open day", "Strong, reliable lead sound for his age and a great attitude in rehearsal."),
    ("alex-chen", "ronald-pierce", "Taught him in a masterclass", "Alex reads well, takes direction and is ready for a working jazz ensemble."),
    ("leo-marquez", "rhonda-holloway", "Sat in with the Bayview Jazz Orchestra", "A natural lead voice with a big, warm sound."),
]

# (person, person, optional opportunity index, [(sender, text, hours ago, read)])
CONVERSATIONS = [
    ("naomi-castellanos", "adam-reyes", 3, [
        ("naomi-castellanos", "Hi Adam, I saw your profile and your AFM status. We are building our sub list for violin and would love you to apply.", 30, True),
        ("naomi-castellanos", "Our live auditions are January 10 in Denver. Happy to answer questions about the repertoire.", 3, False),
    ]),
    ("ronald-pierce", "marcus-bell", 6, [
        ("marcus-bell", "Can you cover trombone on Friday the 20th? $180 plus dinner.", 20, True),
        ("ronald-pierce", "Yes, marked myself available. Can you send the charts tonight?", 2, False),
    ]),
    ("alex-chen", "ronald-pierce", None, [
        ("alex-chen", "Hi Ronald, do you take guitar students for jazz theory, or only trombone?", 26, True),
        ("ronald-pierce", "I mostly teach brass, but I run improvisation clinics for any instrument. Come to the next one, and check the Front Range jazz ensemble auditions in January.", 4, False),
    ]),
    ("rhonda-holloway", "leo-marquez", 0, [
        ("rhonda-holloway", "Thanks for submitting, Leo. We are watching videos through the week and will be in touch.", 12, False),
    ]),
]
