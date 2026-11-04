CREATE TABLE IF NOT EXISTS badges (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  kind TEXT NOT NULL CHECK (kind IN ('union','school','ensemble')),
  label TEXT NOT NULL,
  verified_by_tutti INTEGER NOT NULL DEFAULT 0,
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS endorsements (
  id INTEGER PRIMARY KEY,
  musician_id INTEGER NOT NULL REFERENCES users(id),
  author_id INTEGER NOT NULL REFERENCES users(id),
  relationship TEXT NOT NULL DEFAULT '',
  text TEXT NOT NULL,
  created TEXT NOT NULL
);
