CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  role TEXT NOT NULL CHECK (role IN ('musician','director')),
  name TEXT NOT NULL,
  handle TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  category TEXT NOT NULL CHECK (category IN ('students','orchestral','jazz')),
  instrument TEXT NOT NULL DEFAULT '',
  ensemble TEXT NOT NULL DEFAULT '',
  bio TEXT NOT NULL DEFAULT '',
  location TEXT NOT NULL DEFAULT '',
  avatar_style INTEGER NOT NULL DEFAULT 1,
  is_teacher INTEGER NOT NULL DEFAULT 0,
  teacher_blurb TEXT NOT NULL DEFAULT '',
  instruments_taught TEXT NOT NULL DEFAULT '[]',
  rate_text TEXT NOT NULL DEFAULT '',
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
  token TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  expires TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS clips (
  id INTEGER PRIMARY KEY,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  title TEXT NOT NULL,
  file TEXT NOT NULL,
  source TEXT NOT NULL CHECK (source IN ('library','upload')),
  category TEXT NOT NULL,
  instrument TEXT NOT NULL DEFAULT '',
  duration_sec REAL,
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY,
  author_id INTEGER NOT NULL REFERENCES users(id),
  category TEXT NOT NULL,
  body TEXT NOT NULL,
  clip_id INTEGER REFERENCES clips(id),
  created TEXT NOT NULL
);
