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
CREATE TABLE IF NOT EXISTS auditions (
  id INTEGER PRIMARY KEY,
  director_id INTEGER NOT NULL REFERENCES users(id),
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  ensemble TEXT NOT NULL,
  instruments TEXT NOT NULL DEFAULT '[]',
  description TEXT NOT NULL DEFAULT '',
  requirements TEXT NOT NULL DEFAULT '[]',
  timeline TEXT NOT NULL DEFAULT '[]',
  deadline TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS submissions (
  id INTEGER PRIMARY KEY,
  audition_id INTEGER NOT NULL REFERENCES auditions(id),
  musician_id INTEGER NOT NULL REFERENCES users(id),
  source TEXT NOT NULL CHECK (source IN ('upload','clip')),
  file TEXT,
  clip_id INTEGER REFERENCES clips(id),
  note TEXT NOT NULL DEFAULT '',
  timestamps TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new','shortlisted','passed')),
  created TEXT NOT NULL,
  UNIQUE (audition_id, musician_id)
);
CREATE TABLE IF NOT EXISTS reviews (
  id INTEGER PRIMARY KEY,
  submission_id INTEGER NOT NULL UNIQUE REFERENCES submissions(id),
  tone INTEGER, rhythm INTEGER, technique INTEGER, musicality INTEGER, preparation INTEGER,
  average REAL,
  comments TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT '[]',
  decision TEXT CHECK (decision IN ('shortlist','pass')),
  updated TEXT NOT NULL
);
