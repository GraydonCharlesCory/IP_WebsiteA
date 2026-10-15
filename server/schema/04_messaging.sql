-- One conversation per pair of users (user_low < user_high); the optional context is the latest one linked.
CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY,
  user_low INTEGER NOT NULL REFERENCES users(id),
  user_high INTEGER NOT NULL REFERENCES users(id),
  audition_id INTEGER REFERENCES auditions(id),
  submission_id INTEGER REFERENCES submissions(id),
  created TEXT NOT NULL,
  UNIQUE (user_low, user_high),
  CHECK (user_low < user_high)
);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY,
  conversation_id INTEGER NOT NULL REFERENCES conversations(id),
  sender_id INTEGER NOT NULL REFERENCES users(id),
  body TEXT NOT NULL,
  created TEXT NOT NULL,
  read_at TEXT
);
