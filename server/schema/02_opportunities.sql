CREATE TABLE IF NOT EXISTS ensembles (
  id INTEGER PRIMARY KEY,
  director_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
  name TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL CHECK (category IN ('students','orchestral','jazz')),
  city TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT '',
  about TEXT NOT NULL DEFAULT '',
  founded INTEGER,
  season TEXT NOT NULL DEFAULT '',
  highlights TEXT NOT NULL DEFAULT '[]',
  roster TEXT NOT NULL DEFAULT '[]',
  logo_initials TEXT NOT NULL DEFAULT '',
  logo_color TEXT NOT NULL DEFAULT '#6b4eff',
  created TEXT NOT NULL
);
-- Holds both auditions and gigs (`type`); the table keeps its v1 name.
CREATE TABLE IF NOT EXISTS auditions (
  id INTEGER PRIMARY KEY,
  director_id INTEGER NOT NULL REFERENCES users(id),
  ensemble_id INTEGER REFERENCES ensembles(id),
  type TEXT NOT NULL DEFAULT 'audition' CHECK (type IN ('audition','gig','grant','residency','college_audition','summer_camp')),
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  ensemble TEXT NOT NULL,
  instruments TEXT NOT NULL DEFAULT '[]',
  description TEXT NOT NULL DEFAULT '',
  requirements TEXT NOT NULL DEFAULT '[]',
  timeline TEXT NOT NULL DEFAULT '[]',
  deadline TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
  city TEXT NOT NULL DEFAULT '',
  state TEXT NOT NULL DEFAULT '',
  level TEXT NOT NULL DEFAULT 'pro' CHECK (level IN ('student','college','semi-pro','pro')),
  paid INTEGER NOT NULL DEFAULT 0,
  pay_text TEXT NOT NULL DEFAULT '',
  video_round_accepted INTEGER NOT NULL DEFAULT 0,
  callback_date TEXT NOT NULL DEFAULT '',
  callback_location TEXT NOT NULL DEFAULT '',
  created TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gig_details (
  audition_id INTEGER PRIMARY KEY REFERENCES auditions(id),
  gig_date TEXT NOT NULL,
  start_time TEXT NOT NULL DEFAULT '',
  venue TEXT NOT NULL,
  money_rating INTEGER, money_note TEXT NOT NULL DEFAULT '',
  musicians_rating INTEGER, musicians_note TEXT NOT NULL DEFAULT '',
  music_rating INTEGER, music_note TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS gig_availability (
  audition_id INTEGER NOT NULL REFERENCES auditions(id),
  musician_id INTEGER NOT NULL REFERENCES users(id),
  status TEXT NOT NULL CHECK (status IN ('available','maybe','unavailable')),
  updated TEXT NOT NULL,
  PRIMARY KEY (audition_id, musician_id)
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
  status TEXT NOT NULL DEFAULT 'submitted' CHECK (status IN ('submitted','shortlisted','callback','not_selected')),
  callback_date TEXT NOT NULL DEFAULT '',
  callback_location TEXT NOT NULL DEFAULT '',
  callback_message TEXT NOT NULL DEFAULT '',
  duration_sec REAL,
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
  feedback_shared INTEGER NOT NULL DEFAULT 0,
  feedback_includes_notes INTEGER NOT NULL DEFAULT 0,
  feedback_shared_at TEXT,
  updated TEXT NOT NULL
);
