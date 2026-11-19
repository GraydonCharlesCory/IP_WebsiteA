CREATE TABLE IF NOT EXISTS schools (
 id INTEGER PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES users(id), name TEXT NOT NULL,
 location TEXT NOT NULL DEFAULT '', about TEXT NOT NULL DEFAULT '', programs TEXT NOT NULL DEFAULT '[]',
 activities TEXT NOT NULL DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS alumni (
 school_id INTEGER NOT NULL REFERENCES schools(id), musician_id INTEGER NOT NULL REFERENCES users(id),
 PRIMARY KEY(school_id,musician_id)
);
CREATE TABLE IF NOT EXISTS guest_links (
 id INTEGER PRIMARY KEY, audition_id INTEGER NOT NULL REFERENCES auditions(id),
 capability TEXT NOT NULL UNIQUE, label TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS guest_scores (
 guest_id INTEGER NOT NULL REFERENCES guest_links(id), submission_id INTEGER NOT NULL REFERENCES submissions(id),
 scores TEXT NOT NULL, average REAL NOT NULL, updated TEXT NOT NULL,
 PRIMARY KEY(guest_id,submission_id)
);
CREATE TABLE IF NOT EXISTS notices (
 id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), audition_id INTEGER NOT NULL REFERENCES auditions(id),
 body TEXT NOT NULL, created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS email_outbox (
 id INTEGER PRIMARY KEY, notice_id INTEGER NOT NULL UNIQUE REFERENCES notices(id),
 recipient TEXT NOT NULL, body TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'simulated'
);
