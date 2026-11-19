-- Additive discovery metadata: absence means unknown, never inferred from section or level.
CREATE TABLE IF NOT EXISTS opportunity_discovery (
 audition_id INTEGER PRIMARY KEY REFERENCES auditions(id),
 genre TEXT NOT NULL DEFAULT '',
 eligibility TEXT NOT NULL DEFAULT '[]',
 student_hub INTEGER NOT NULL DEFAULT 0 CHECK(student_hub IN (0,1))
);
