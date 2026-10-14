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
]

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
]

# author handle, body, attached clip file or None, days ago
POSTS = [
    ("leo-marquez", "Callback week! Grateful to everyone who listened to my rough takes this month. Back to long tones and the metronome on 2 and 4. Anyone got a favourite Joe Henderson solo to transcribe next?", None, 3),
    ("leo-marquez", "New featured clip: Stella by Starlight, one chorus. Recorded at Eastbridge Studio B with the new mouthpiece. Let me know what you think of the sound.", "leo-marquez-1.mp4", 12),
    ("dana-brooks", "Giant Steps at 280. Slow it down, learn it, then speed it back up. Feedback welcome.", "dana-brooks-1.mp4", 5),
    ("aiko-nakamura", "Working the Sibelius opening for the spring audition cycle. Any tips on shifting in the first page?", "aiko-nakamura-1.mp4", 6),
    ("maya-okafor", "Sunday practice log: Bach Prelude, three tempos, one very patient neighbour.", "maya-okafor-2.mp4", 4),
    ("jordan-wells", "All-State prep is on. Etude no. 3 finally sits under my fingers. Next up: endurance.", "jordan-wells-1.mp4", 2),
]

# director handle, title, instruments, description, requirements, timeline, deadline
AUDITIONS = [
    ("rhonda-holloway", "Lead Tenor Saxophone: 2027 Season", ["Tenor saxophone"],
     "The Bayview Jazz Orchestra is seeking a lead tenor for its 2027 season: twelve concerts, a spring tour and a live recording. Paid, one chair.",
     ["One ballad of your choice", "One up-tempo swing tune", "Sight-reading excerpt, recorded in one take", "Video, no edits, 10 minutes maximum"],
     [{"label": "Submissions close", "date": "2026-11-24"}, {"label": "Callbacks", "date": "2026-12-10"}, {"label": "Season announced", "date": "2027-01-05"}],
     "2026-11-24"),
    ("elena-voss", "Violin: Section Seat, Second Violins", ["Violin"],
     "Lakeshore Symphony has an opening in the second violin section for the 2027 season, with a path to principal.",
     ["First movement of a Classical or Romantic concerto (solo or with piano)", "One movement of unaccompanied Bach", "Two orchestral excerpts of your choice"],
     [{"label": "Submissions close", "date": "2026-11-30"}, {"label": "Live round", "date": "2027-01-15"}],
     "2026-11-30"),
    ("priya-raman", "Honors Jazz Combo: Winter Session", ["Trumpet", "Saxophone", "Trombone", "Piano", "Bass", "Drums"],
     "Two spots for ages 14 to 18 in the honors combo: weekly rehearsals, a coach from the Bay Area scene and a winter showcase.",
     ["One tune in a style you love", "Scale and arpeggio in a key of your choice", "A short note about why you want to join"],
     [{"label": "Submissions close", "date": "2026-11-20"}, {"label": "Decisions", "date": "2026-12-05"}, {"label": "First rehearsal", "date": "2027-01-12"}],
     "2026-11-20"),
]

# musician handle, audition index, clip file, note, timestamps, days ago, review or None
# review = (scores, comments, timestamped notes, decision)
SUBMISSIONS = [
    ("leo-marquez", 0, "leo-marquez-2.mp4",
     "Hi Dr. Holloway, the ballad is Body and Soul. Recorded in one take at Eastbridge Studio B. I also double on soprano and clarinet. Thanks for listening!",
     [{"time": 0, "label": "Body and Soul (ballad)"}, {"time": 178, "label": "Cherokee"}], 0, None),
    ("dana-brooks", 0, "dana-brooks-1.mp4",
     "Giant Steps and Cherokee, both straight through. I can read lead sheets and charts at sight.",
     [{"time": 0, "label": "Giant Steps"}, {"time": 140, "label": "Cherokee"}], 2,
     ({"tone": 9, "rhythm": 9, "technique": 9, "musicality": 8, "preparation": 9},
      "Fast, clean and swinging. Sound is a touch bright on the top end, nothing a section could not blend.",
      [{"time": 95, "text": "Great control through the bridge at this tempo."}], "shortlist")),
]
