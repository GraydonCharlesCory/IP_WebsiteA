"""Fictional demo people, clips, posts and auditions. Every account's password is 'demo'."""

DEMO_PASSWORD = "demo"

# role, name, handle, category, instrument, ensemble (directors), bio, location, avatar style 1-6
USERS = [
    ("musician", "Leo Marquez", "leo-marquez", "jazz", "Tenor & soprano saxophone", "",
     "Tenor player raised on Dexter Gordon and Joe Henderson. Lead tenor in the Eastbridge Concert Jazz Orchestra; "
     "doubling on soprano and clarinet. Looking for big band chairs and summer festival work.", "Boston, MA", 1),
    ("musician", "Dana Brooks", "dana-brooks", "jazz", "Tenor saxophone", "",
     "Late-night session player and arranger. Happiest on fast changes, tenor in hand, with a rhythm section that listens.",
     "New Orleans, LA", 5),
    ("musician", "Aiko Nakamura", "aiko-nakamura", "orchestral", "Violin", "",
     "Conservatory violinist working through the big concertos. Section player first, soloist when asked.",
     "Chicago, IL", 3),
    ("musician", "Maya Okafor", "maya-okafor", "orchestral", "Cello", "",
     "Cellist with a love for Dvorak and Bach suites. Subbing with regional orchestras and teaching beginners on weekends.",
     "Philadelphia, PA", 4),
    ("musician", "Jordan Wells", "jordan-wells", "students", "Trumpet", "",
     "High school senior and all-state trumpet. Practising lead playing, lip slurs and a lot of Arban.",
     "Austin, TX", 6),
    ("director", "Dr. Rhonda Holloway", "rhonda-holloway", "jazz", "Conductor", "Bayview Jazz Orchestra",
     "Directs the Bayview Jazz Orchestra, a professional 17-piece big band. Always listening for a lead player with a big sound.",
     "San Francisco, CA", 2),
    ("director", "Elena Voss", "elena-voss", "orchestral", "Conductor", "Lakeshore Symphony",
     "Music director of the Lakeshore Symphony. Builds sections that breathe together.", "Chicago, IL", 2),
    ("director", "Priya Raman", "priya-raman", "students", "Educator", "Bay Area Youth Jazz All-Stars",
     "Runs the Bay Area Youth Jazz All-Stars, an honors program for players aged 14 to 18.", "Oakland, CA", 2),
    ("musician", "Adam Reyes", "adam-reyes", "orchestral", "Violin", "",
     "Orchestral violinist and AFM member. Section player in regional orchestras; flies only to auditions that fit the repertoire and the schedule, and asks every panel for specific feedback.",
     "New York, NY", 3),
    ("musician", "Ronald Pierce", "ronald-pierce", "jazz", "Trombone", "",
     "Denver jazz trombonist. Weighs every gig by the three M's: Money, Musicians, Music. Teaches lessons and clinics, and judges regional jazz festivals.",
     "Denver, CO", 5),
    ("musician", "Alex Chen", "alex-chen", "students", "Guitar", "",
     "Third-year college guitarist who plays jazz and funk. Wants to find bands, auditions and deadlines in one place instead of through friends of friends.",
     "Boulder, CO", 1),
    ("musician", "Sofia Lindgren", "sofia-lindgren", "orchestral", "Violin", "",
     "Violinist and chamber player auditioning for her first full-time orchestra seat.", "Minneapolis, MN", 2),
    ("director", "Marcus Bell", "marcus-bell", "jazz", "Bandleader", "Mile High Jazz Collective",
     "Bandleader and booker for the Mile High Jazz Collective, Denver's working jazz company. Keeps a sub list so no gig goes uncovered.",
     "Denver, CO", 4),
    ("director", "Naomi Castellanos", "naomi-castellanos", "orchestral", "Conductor", "Rocky Mountain Chamber Orchestra",
     "Music director of the Rocky Mountain Chamber Orchestra. Programs new music beside the classics and wants players who listen.",
     "Denver, CO", 6),
    ("director", "Prof. Tomás Ibarra", "tomas-ibarra", "students", "Educator", "Front Range University Jazz Ensemble",
     "Directs jazz studies at Front Range University and leads the university's flagship jazz ensemble.",
     "Boulder, CO", 1),
]

# handle -> (lessons/clinics blurb, instruments taught, rate)
TEACHERS = {
    "ronald-pierce": ("Private trombone lessons (jazz and classical), improvisation clinics for school bands, and festival adjudication.",
                      ["Trombone", "Euphonium", "Jazz improvisation"], "$70 per hour; first lesson free"),
    "maya-okafor": ("Beginner and intermediate cello lessons on weekends, in person or online.", ["Cello"], "$45 per half hour"),
}

# owner handle, title, my-clips file name, instrument
CLIPS = [
    ("leo-marquez", "Stella by Starlight: solo chorus", "leo-marquez-1.mp4", "Tenor saxophone"),
    ("leo-marquez", "Body and Soul (ballad)", "leo-marquez-2.mp4", "Tenor saxophone"),
    ("leo-marquez", "Oleo: trio, live at The Lantern", "leo-marquez-3.mp4", "Tenor saxophone"),
    ("dana-brooks", "Giant Steps at 280 bpm", "dana-brooks-1.mp4", "Tenor saxophone"),
    ("dana-brooks", "Cherokee, up-tempo", "dana-brooks-2.mp4", "Tenor saxophone"),
    ("aiko-nakamura", "Sibelius Concerto, mvt. I excerpt", "aiko-nakamura-1.mp4", "Violin"),
    ("aiko-nakamura", "Bach Partita no. 2: Allemande", "aiko-nakamura-2.mp4", "Violin"),
    ("maya-okafor", "Dvorak Cello Concerto, opening", "maya-okafor-1.mp4", "Cello"),
    ("maya-okafor", "Bach Suite no. 1: Prelude", "maya-okafor-2.mp4", "Cello"),
    ("jordan-wells", "All-State etude no. 3", "jordan-wells-1.mp4", "Trumpet"),
    ("jordan-wells", "Arban: Carnival of Venice, first variation", "jordan-wells-2.mp4", "Trumpet"),
    # Adam's and Sofia's violin clips reuse Aiko's files (no extra media); there is no trombone or guitar footage yet.
    ("adam-reyes", "Brahms Violin Concerto, mvt. III excerpt", "aiko-nakamura-1.mp4", "Violin"),
    ("adam-reyes", "Bach Sonata no. 1: Fuga", "aiko-nakamura-2.mp4", "Violin"),
    ("sofia-lindgren", "Bach Partita no. 3: Gavotte en Rondeau", "aiko-nakamura-2.mp4", "Violin"),
]

# author handle, body, attached clip file or None, days ago
POSTS = [
    ("leo-marquez", "Callback week! Grateful to everyone who listened to my rough takes this month. Back to long tones and the metronome on 2 and 4. Anyone got a favourite Joe Henderson solo to transcribe next?", None, 3),
    ("leo-marquez", "New featured clip: Stella by Starlight, one chorus. Recorded at Eastbridge Studio B with the new mouthpiece. Let me know what you think of the sound.", "leo-marquez-1.mp4", 12),
    ("dana-brooks", "Giant Steps at 280. Slow it down, learn it, then speed it back up. Feedback welcome.", "dana-brooks-1.mp4", 5),
    ("aiko-nakamura", "Working the Sibelius opening for the spring audition cycle. Any tips on shifting in the first page?", "aiko-nakamura-1.mp4", 6),
    ("maya-okafor", "Sunday practice log: Bach Prelude, three tempos, one very patient neighbour.", "maya-okafor-2.mp4", 4),
    ("jordan-wells", "All-State prep is on. Etude no. 3 finally sits under my fingers. Next up: endurance.", "jordan-wells-1.mp4", 2),
    ("adam-reyes", "Flying out for a live round only after the video round goes well. Anyone else filtering auditions by repertoire fit before booking travel?", None, 1),
    ("ronald-pierce", "Three M's before I say yes to a gig: Money, Musicians, Music. Two out of three is a maybe. What's your rule?", None, 2),
    ("alex-chen", "New in town and looking for a funk or jazz group that rehearses on campus. Where does everyone find these?", None, 1),
]
