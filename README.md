# Tutti: "Hudl for musicians" (investor demo)

Musicians post clips and apply to auditions; directors find players, then score and comment on every submission.
Local, offline-friendly demo: Python 3.9 standard library only, SQLite, plain HTML/CSS/JS. No pip, no npm, no build step.

## Run it

```
python3 run.py              # http://localhost:8000 ; creates data/tutti.db and seeds it on first run
python3 run.py --port 8765  # another port
python3 run.py --reset      # wipe data/ (database and uploads) and reseed
python3 -m unittest discover -s tests
```

`data/` is git-ignored. Uploaded profile clips go to `data/uploads/clips/`, submission videos to `data/uploads/submissions/`.

## Demo accounts (every password is `demo`)

| Role | Name | Email | Section |
|---|---|---|---|
| Musician | Leo Marquez (tenor sax) | leo.marquez@tutti.demo | Jazz |
| Musician | Dana Brooks (tenor sax) | dana.brooks@tutti.demo | Jazz |
| Musician | Aiko Nakamura (violin) | aiko.nakamura@tutti.demo | Orchestral |
| Musician | Maya Okafor (cello) | maya.okafor@tutti.demo | Orchestral |
| Musician | Jordan Wells (trumpet) | jordan.wells@tutti.demo | Students |
| Director | Dr. Rhonda Holloway, Bayview Jazz Orchestra | rhonda.holloway@tutti.demo | Jazz |
| Director | Elena Voss, Lakeshore Symphony | elena.voss@tutti.demo | Orchestral |
| Director | Priya Raman, Bay Area Youth Jazz All-Stars | priya.raman@tutti.demo | Students |

The sign-in page has "Sign in as musician" / "Sign in as director" one-click buttons (Leo / Dr. Holloway). The top-bar avatar opens the **account switcher**: one click to any account, grouped Musicians / Directors. "Sign in with Apple" only shows a "not available in the demo" toast.

## Demo flow

1. Sign in as a musician (Jordan Wells, say), open an audition (Honors Jazz Combo), submit a clip (pick an MP4 from `demo-uploads/` in the file picker, or choose a profile clip). Optionally open your own profile and use "Upload a clip" the same way.
2. Open the account switcher and switch to that audition's director (Priya Raman).
3. Open "My auditions", then the new submission: play the video, score the five criteria, add comments and timestamped notes, shortlist or pass.
4. Switch to another director or back to the musician: they cannot see the submission's scores, comments or video (the musician only sees "Submitted").

Dr. Holloway's audition already has two submissions (Leo: new; Dana: scored and shortlisted), so the dashboard is not empty.

## Live demo: test folder

`demo-uploads/` holds sample performances for the live demo. In the musician's "Submit a clip" dialog (audition page) or the "Upload a clip" dialog (own profile, `profile.html?h=<your handle>`; hidden for other viewers), choose a file from that folder. Drop your own MP4s there too.

`my-clips/` ships with openly licensed sample clips (credits in `my-clips/CREDITS.md`). Replace any of them with your own by keeping the file name. `python3 run.py --reset` only wipes `data/`; it keeps both `my-clips/` and `demo-uploads/` (covered by `tests/test_reset.py`).

## Seed clips: `my-clips/`

Seed profile clips point at fixed file names in `my-clips/` (full list in `my-clips/README.md`). Drop an MP4 with that name there and refresh; until then the UI shows a "Clip coming soon" tile. MP4s are git-ignored.

## Visibility rules (enforced on the server, covered by tests)

- Anyone, even signed out: musician profiles, profile clips, posts, section feeds.
- Signed in: audition postings. Only musicians submit; only directors post/edit auditions (their own).
- Only the director who posted an audition may list its submissions, play submission videos, read or write scores and comments. Anyone else gets 403 (401 if signed out). Submission videos are only served by `GET /api/submissions/<id>/video`, never from a public path.
- A musician sees that they submitted (status always `"Submitted"`) and never any score, comment or decision.

## Data model (SQLite, `server/schema.sql`)

`users` (role musician|director, name, handle, email, password_hash, category students|orchestral|jazz, instrument, ensemble, bio, location, avatar_style 1-6) ·
`sessions` · `clips` (owner, title, file, source library|upload, category, instrument) ·
`posts` (author, category, body, optional clip) ·
`auditions` (director, category, title, ensemble, instruments[], description, requirements[], timeline[{label,date}], deadline YYYY-MM-DD, status open|closed) ·
`submissions` (audition, musician, source upload|clip, file / clip, note, timestamps[{time,label}], status new|shortlisted|passed; one per musician per audition) ·
`reviews` (submission, tone, rhythm, technique, musicality, preparation each 1-10, average, comments, notes[{time,text}], decision shortlist|pass).
Lists are stored as JSON text. Review criteria: Tone, Rhythm, Technique, Musicality, Preparation.

## API

JSON under `/api/`. Errors are always `{"error": "plain-language message"}` with an HTTP status: 400 bad input, 401 not signed in, 403 not allowed, 404 not found, 405 wrong method, 409 duplicate/closed, 413 file too big, 416 bad range. Session is the `tutti_session` cookie (HttpOnly); `fetch` with the default same-origin credentials sends it. `video_url` / `available` on clips: `available` is false when the MP4 is missing, so render a "Clip coming soon" tile.
"Who" below: **public**, **user** (any signed-in), **musician**, **director**, **owner** (the director who posted the audition).

Brief user object: `{id, role, name, handle, category, instrument, ensemble, initials, avatar_style}`. Full adds `bio, location`; `/api/me` adds `email`.
Clip: `{id, title, category, instrument, created, video_url, available, owner?}`. Post: `{id, category, body, created, author, clip|null}`.
Audition: `{id, category, title, ensemble, instruments[], description, requirements[], timeline[], deadline, status, created, director}` plus, for musicians, `my_submission: {id, status:"Submitted", created}|null`, and for the owner `submission_count, owned_by_me:true`.

| Method + path | Who | Request | Response |
|---|---|---|---|
| GET `/api/me` | public | | `{user: {...,email}|null}` |
| GET `/api/accounts` | public (demo) | | `{musicians:[user], directors:[user]}` (with `email`) |
| POST `/api/sign-in` | public | `{email, password}` | `{user}` + cookie; 401 on mismatch |
| POST `/api/sign-in-as` | public (demo) | `{role: "musician"\|"director"}` | `{user}` + cookie |
| POST `/api/switch` | public (demo) | `{user_id}` | `{user}` + new cookie |
| POST `/api/sign-out` | public | | `{ok:true}` |
| GET `/api/sections` | public | | `{sections:[{key,label,blurb,musicians,auditions}]}` |
| GET `/api/sections/<students\|orchestral\|jazz>` | public | `?limit=` | `{section, musicians[], posts[], clips[], auditions[]|null}` (`auditions` is null when signed out) |
| GET `/api/feed` | public | `?category=&limit=` | `{posts[]}` newest first |
| GET `/api/clips` | public | `?category=&limit=` | `{clips[]}` with `owner` |
| GET `/api/musicians` | public | `?category=` | `{musicians[]}` |
| GET `/api/musicians/<handle>` | public | | `{musician, clips[], posts[], stats:{clips,posts}}` |
| PUT `/api/me` | musician | `{bio?, instrument?, location?}` | `{user}` |
| POST `/api/posts` | musician | `{body, category?, clip_id?}` (clip must be yours) | 201 `{post}` |
| POST `/api/clips?title=&instrument=` | musician | raw MP4 body, `Content-Type: video/mp4` | 201 `{clip}` |
| GET `/api/auditions` | user | `?category=&mine=1` | `{auditions[]}` |
| GET `/api/auditions/<id>` | user | | `{audition}` |
| POST `/api/auditions` | director | `{title, deadline, category?, ensemble?, description?, instruments[], requirements[], timeline[{label,date}], status?}` | 201 `{audition}` |
| PUT `/api/auditions/<id>` | owner | same fields, all optional | `{audition}` |
| POST `/api/auditions/<id>/submissions` | musician | JSON `{clip_id, note?, timestamps?[{time,label}]}` **or** raw MP4 body with `?note=&timestamps=<url-encoded JSON>` | 201 `{submission:{id,audition_id,status:"Submitted",created}}`; 409 if closed/already submitted |
| GET `/api/my/submissions` | musician | | `{submissions:[{id,audition_id,audition_title,ensemble,status:"Submitted",created}]}` |
| GET `/api/director/dashboard` | director | | `{director, kpis:{open_auditions,closing_this_week,total_submissions,new_submissions,awaiting_review,reviewed,average_score}, auditions[]}`; each audition adds `submission_count,new_count,shortlisted_count,reviewed_count,average_score` |
| GET `/api/auditions/<id>/submissions` | owner | `?status=new\|shortlisted\|passed\|reviewed` | `{audition, submissions:[{id,musician,source,status,created,average,reviewed}]}` |
| GET `/api/submissions/<id>` | owner | | `{submission:{...summary, note, timestamps[], video_url, has_video, musician, musician_clips[], review|null, audition, position, total, previous_id, next_id}}` |
| GET `/api/submissions/<id>/video` | owner | optional `Range` header | MP4 stream (200/206) |
| PUT `/api/submissions/<id>/review` | owner | `{scores?:{tone,rhythm,technique,musicality,preparation}, comments?, notes?[{time,text}], decision?: "shortlist"\|"pass"\|null}`; only sent fields change (safe for auto-save) | `{review:{scores,average,comments,notes,decision,updated}, status}`; `average` = mean of the scores given, 1 decimal |
| GET `/media/clips/<file>` | public | optional `Range` | seed clip from `my-clips/` (206 supported; 404 "coming soon" if missing) |
| GET `/media/uploads/<file>` | public | optional `Range` | an uploaded profile clip |

Uploads are streamed to disk in chunks; limit 500 MB; the body must be `video/mp4` and start with an `ftyp` box.

## Front-end shell (for page authors)

Pages live in `static/` and are served at the site root (`/home.html`) with assets under `/static/`. Placeholders exist for `home`, `section` (`section.html?s=students|orchestral|jazz`), `profile` (`profile.html?h=<handle>`), `audition` (`?id=`), `director`, `review` (`?id=<submission id>`).
Dialogs: "Submit a clip" (`submit-dialog.js`, audition page) and "Upload a clip" (`upload-clip-dialog.js`, own profile); both share `dialog-parts.js` (scrim, MP4 drop zone, file checks) and `submit-dialog.css`.

Include, in this order: `/static/css/fonts.css`, `app.css`, `shell.css`; scripts `api.js`, `util.js`, `components.js`, `shell.js`; add `<div data-shell-header></div>` at the top of `<body>`; then:

```js
Tutti.boot({ active: 'home', requireAuth: true, requireRole: 'musician' }).then((user) => { /* render */ });
```

- `api.*` (api.js): one function per endpoint above (`api.musician(handle)`, `api.submitUpload(id, file, meta, onProgress)`, `api.saveReview(id, review)` ...). Errors reject with `Error{status, message}`.
- `Tutti.util`: `esc, section, duration(secs), parseTime("2:14"), date, timeAgo, daysUntil, queryParam`.
- `Tutti.components`: `avatar(user,size), categoryTag(key), dot(key), statusTag(status), videoTile(clip,{big,badge,src}), clipCard(clip), placeholderTile(title), wire(root)`. After inserting `videoTile` HTML call `Tutti.components.wire(container)`; tiles show the real first frame and play on click, and a "Clip coming soon" tile if the file is missing. For a submission video use `videoTile({title}, {src: api.submissionVideoUrl(id), big: true})`.
- `Tutti.toast(msg, 'error'|'ok')`, `Tutti.reportError(error)` (toast + console), `Tutti.landingFor(user)`.
- Fonts (Fraunces, Inter; SIL OFL) are self-hosted in `static/fonts/`.

## Layout

`run.py` · `server/` (app.py handler, router.py, context.py, auth.py, media.py, db.py, schema.sql, seed*.py, api/ one module per resource) · `static/` · `tests/` · `my-clips/`.
