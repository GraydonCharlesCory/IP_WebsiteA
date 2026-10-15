# Tutti: "Hudl for musicians" (investor demo)

Musicians post clips, find auditions and gigs on one board, and apply; directors find players, run blind or open reviews, move people to callback and share feedback. Musicians and directors can message each other.
Local, offline-friendly demo: Python 3.9 standard library only, SQLite, plain HTML/CSS/JS. No pip, no npm, no build step.

## Run it

```
python3 run.py              # http://localhost:8000 ; creates data/tutti.db and seeds it on first run
python3 run.py --port 8765  # another port
python3 run.py --reset      # wipe data/ (database and uploads) and reseed
python3 -m unittest discover -s tests
```

`data/` is git-ignored. Uploaded profile clips go to `data/uploads/clips/`, submission videos to `data/uploads/submissions/`.

## v2 features (backend)

1. **Opportunity board**: auditions and gigs in one searchable list (`/api/opportunities`), plus public ensemble pages (`/api/ensembles`).
2. **Video pre-screen**: an audition can accept video and carry callback date/place; the director moves a submission to `callback` with a message.
3. **Blind review**: per-audition switch; while on, the director's APIs return an anonymous "Applicant A-n" (enforced on the server).
4. **Application status and feedback**: `submitted → shortlisted → callback → not_selected`; the musician sees status and, only when the director shares it, scores and comments (`/api/my/applications`).
5. **Credibility**: verified badges (union, school, ensemble) and endorsements from directors and teachers.
6. **Jazz gigs and sub lists**: gigs with date, venue, pay and the 3 M's (Money, Musicians, Music); musicians mark availability; the posting director sees the sub list.
7. **Direct messaging** with an unread count in `/api/me`.
8. **Teachers**: musicians can list lessons and clinics (`/api/teachers`).

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
| Musician | Adam Reyes (violin, AFM Local 802) | adam.reyes@tutti.demo | Orchestral |
| Musician | Ronald Pierce (Denver jazz trombone, teacher) | ronald.pierce@tutti.demo | Jazz |
| Musician | Alex Chen (college guitarist) | alex.chen@tutti.demo | Students |
| Musician | Sofia Lindgren (violin) | sofia.lindgren@tutti.demo | Orchestral |
| Director | Marcus Bell, Mile High Jazz Collective (Denver) | marcus.bell@tutti.demo | Jazz |
| Director | Naomi Castellanos, Rocky Mountain Chamber Orchestra (Denver) | naomi.castellanos@tutti.demo | Orchestral |
| Director | Prof. Tomás Ibarra, Front Range University Jazz Ensemble (Boulder) | tomas.ibarra@tutti.demo | Students |

The sign-in page has "Sign in as musician" / "Sign in as director" one-click buttons (Leo / Dr. Holloway). The top-bar avatar opens the **account switcher**: one click to any account, grouped Musicians / Directors. "Sign in with Apple" only shows a "not available in the demo" toast.

## Demo flow

1. Sign in as a musician (Jordan Wells, say), open an audition (Honors Jazz Combo), submit a clip (pick an MP4 from `demo-uploads/` in the file picker, or choose a profile clip). Optionally open your own profile and use "Upload a clip" the same way.
2. Open the account switcher and switch to that audition's director (Priya Raman).
3. Open "My auditions", then the new submission: play the video, score the five criteria, add comments and timestamped notes, shortlist or pass.
4. Switch to another director or back to the musician: they cannot see the submission's scores, comments or video (the musician only sees "Submitted").

Dr. Holloway's audition already has two submissions (Leo: new; Dana: scored and shortlisted), so the dashboard is not empty.

### What each v2 account shows

| Feature | Sign in as | What to see |
|---|---|---|
| Discovery | Alex Chen | `GET /api/opportunities` lists 6 auditions and 5 gigs; filter by `location=Denver`, `paid=0`, `level=college`, `video_round=1`. Six ensemble pages are public. |
| Video pre-screen + callback | Leo Marquez / Dr. Holloway | Lead Tenor audition accepts video and has callback 2026-12-10 at Bayview Hall. Dr. Holloway can set Leo to `callback`. |
| Blind review | Elena Voss | The Lakeshore violin audition is blind: two submissions appear as "Applicant A-n"; `POST /api/submissions/<id>/reveal` unmasks one. |
| Callback + shared feedback | Adam Reyes | `my/applications`: Lakeshore application at `callback` with a message, plus shared scores (average 8.6) and comments; his private timestamped note is not shared. |
| Not selected, feedback private | Sofia Lindgren | Application `not_selected`, `feedback: null` (Elena has scored but not shared). |
| Shortlisted, unshared | Dana Brooks | v1 scenario: shortlisted with a score the director has not shared. |
| Credibility | Adam, Ronald | Verified "AFM Local 802" / "AFM Local 20-47" badges and endorsements on `GET /api/musicians/<handle>`. |
| Gigs, 3 M's, sub list | Ronald Pierce, Marcus Bell | Three Denver paid gigs. Ronald has marked availability; Marcus sees `GET /api/gigs/<id>/availability`. |
| Messaging | Adam, Alex, Marcus, Leo | Each has a thread with an unread message (`unread_messages` in `/api/me`). |
| Teachers | anyone | `GET /api/teachers` lists Ronald (trombone, clinics) and Maya (cello). |

## Live demo: test folder

`demo-uploads/` holds sample performances for the live demo. In the musician's "Submit a clip" dialog (audition page) or the "Upload a clip" dialog (own profile, `profile.html?h=<your handle>`; hidden for other viewers), choose a file from that folder. Drop your own MP4s there too.

`my-clips/` ships with openly licensed sample clips (credits in `my-clips/CREDITS.md`). Replace any of them with your own by keeping the file name. `python3 run.py --reset` only wipes `data/`; it keeps both `my-clips/` and `demo-uploads/` (covered by `tests/test_reset.py`).

## Seed clips: `my-clips/`

Seed profile clips point at fixed file names in `my-clips/` (full list in `my-clips/README.md`). Drop an MP4 with that name there and refresh; until then the UI shows a "Clip coming soon" tile. MP4s are git-ignored.

## Visibility rules (enforced on the server, covered by tests)

- Anyone, even signed out: musician profiles (with badges and endorsements), profile clips, posts, section feeds, the teacher list, **ensemble list and pages** (including a short card for each of the ensemble's open opportunities; full details need sign-in).
- Signed in: the opportunity board and opportunity details (auditions and gigs). This keeps v1's rule; only ensemble pages are public for credibility. Only musicians submit and mark availability; only directors post/edit opportunities (their own).
- Only the director who posted an audition may list its submissions, play submission videos, read or write scores and comments, change status, reveal a blind applicant and share feedback. Anyone else gets 403 (401 if signed out). Submission videos are only served by `GET /api/submissions/<id>/video`, never from a public path.
- **Musicians see** their own application status and callback details. They see scores and comments **only after the director shares feedback** for that submission, and the director's private timestamped notes only if the director also chose `include_notes`. Everything else about the review stays private.
- **Blind review**: while an audition has `blind_review` on and a submission's identity has not been revealed, every director-facing API (list, detail, video) returns the applicant as `{name: "Applicant A-<submission id>", label, handle: null, id: null, anonymous: true, initials: "?", avatar_style: 0, location: ""}` plus the instrument, and `musician_clips: []`. The label is stable. Identity is revealed **only** when the director calls `POST /api/submissions/<id>/reveal` (that submission only) or turns blind review off (everyone). Shortlisting, callbacks, rejection and scoring do **not** reveal. While anonymous, the director cannot start a conversation linked to that submission (403). Limit: the applicant's free-text note and the video itself are shown as submitted, so applicants should not put their name in them.
- Conversations: only the two participants can read, write or mark read; anyone else gets 403 (401 signed out).
- Sub lists: only the director who posted the gig sees who marked availability; a musician sees only their own mark.
- Endorsements: only directors and teachers (musicians with `is_teacher`) can write them, never for themselves. Self-claimed badges are never "verified by Tutti".

## Data model (SQLite, `server/schema/*.sql`, schema version 2)

`users` (role musician|director, name, handle, email, password_hash, category students|orchestral|jazz, instrument, ensemble, bio, location, avatar_style 1-6, **is_teacher, teacher_blurb, instruments_taught[], rate_text**) ·
`sessions` · `clips` (owner, title, file, source library|upload, category, instrument; several clips may point at one media file) ·
`posts` (author, category, body, optional clip) ·
**`ensembles`** (director, name, category, city, state, about, founded, season, highlights[], roster[{name,instrument}], logo_initials, logo_color) ·
`auditions` (holds auditions **and gigs**: director, ensemble_id, **type audition|gig**, category, title, ensemble name, instruments[], description, requirements[], timeline[{label,date}], deadline YYYY-MM-DD, status open|closed, **city, state, level student|college|semi-pro|pro, paid, pay_text, video_round_accepted, callback_date, callback_location, blind_review**) ·
**`gig_details`** (gig, gig_date, start_time, venue, money/musicians/music rating 1-5 + note) · **`gig_availability`** (gig, musician, available|maybe|unavailable) ·
`submissions` (audition, musician, source upload|clip, file / clip, note, timestamps[{time,label}], **status submitted|shortlisted|callback|not_selected, callback_date, callback_location, callback_message, identity_revealed**; one per musician per audition) ·
`reviews` (submission, tone, rhythm, technique, musicality, preparation each 1-10, average, comments, notes[{time,text}], decision shortlist|pass, **feedback_shared, feedback_includes_notes, feedback_shared_at**) ·
**`badges`** (user, kind union|school|ensemble, label, verified_by_tutti) · **`endorsements`** (musician, author, relationship, text) ·
**`conversations`** (one per pair of users; optional linked audition/gig and submission) · **`messages`** (conversation, sender, body, read_at).
Lists are stored as JSON text. Review criteria: Tone, Rhythm, Technique, Musicality, Preparation.
v1 status names map: `new → submitted`, `passed → not_selected` (v1 names are still accepted in `?status=` filters). A review decision `shortlist`/`pass` sets `shortlisted`/`not_selected` only when the decision changes, so an auto-save never undoes a callback.
A `data/` folder made by v1 is refused with a message to run `python3 run.py --reset`.

## API

JSON under `/api/`. Errors are always `{"error": "plain-language message"}` with an HTTP status: 400 bad input, 401 not signed in, 403 not allowed, 404 not found, 405 wrong method, 409 duplicate/closed, 413 file too big, 416 bad range. Session is the `tutti_session` cookie (HttpOnly); `fetch` with the default same-origin credentials sends it. `video_url` / `available` on clips: `available` is false when the MP4 is missing, so render a "Clip coming soon" tile.
"Who" below: **public**, **user** (any signed-in), **musician**, **director**, **owner** (the director who posted the audition).

Brief user object: `{id, role, name, handle, category, instrument, ensemble, initials, avatar_style, is_teacher}`. Full adds `bio, location, teaching: {blurb, instruments[], rate}|null`; `/api/me` and sign-in add `email` and `unread_messages` (top-bar badge).
Clip: `{id, title, category, instrument, created, video_url, available, owner?}`. Post: `{id, category, body, created, author, clip|null}`.
Opportunity card (lists, ensemble pages): `{id, type: "audition"|"gig", category, title, ensemble, ensemble_id, deadline, status, city, state, location: "Denver, CO", level, paid, pay, video_round_accepted}`.
Opportunity (a card plus): `{instruments[], description, requirements[], timeline[], created, director, blind_review, callback: {date, location}|null, ensemble_info: {id, name, category, city, state, location, logo_initials, logo_color}|null, gig: {date, start_time, venue, three_ms: {money|musicians|music: {rating 1-5|null, note}}}|null}` plus, for musicians, `my_submission: {id, status, status_label, created}|null` (auditions) or `my_availability: "available"|"maybe"|"unavailable"|null` (gigs); for the owner `owned_by_me: true` and `submission_count` (auditions) or `available_count` (gigs).
`GET/POST/PUT /api/auditions…` (v1 addresses) answer `{audition}`/`{auditions}`; the same functions at `/api/opportunities…` answer `{opportunity}`/`{opportunities}`. `/api/auditions` lists auditions only.
Statuses are keys `submitted | shortlisted | callback | not_selected` with a `status_label` ("Submitted", "Shortlisted", "Callback", "Not selected").
Error responses to expect: 400 for bad filters or bodies, with the allowed values in the message.

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
| GET `/api/musicians` | public | `?category=&teacher=1&instrument=<text>` | `{musicians[]}` each with `badges[]` |
| GET `/api/musicians/<handle>` | public | | `{musician, clips[], posts[], badges[], endorsements[], stats:{clips,posts}}` |
| PUT `/api/me` | musician | `{bio?, instrument?, location?, is_teacher?, teacher_blurb?, instruments_taught?[], rate_text?}` | `{user}` |
| POST `/api/posts` | musician | `{body, category?, clip_id?}` (clip must be yours) | 201 `{post}` |
| POST `/api/clips?title=&instrument=` | musician | raw MP4 body, `Content-Type: video/mp4` | 201 `{clip}` |
| GET `/api/opportunities` | user | `?q=` (title, ensemble, description, instruments, city) `&category=&type=audition\|gig&instrument=<text>&location=<city or state text>&level=student\|college\|semi-pro\|pro&paid=1\|0&video_round=1\|0&deadline_before=YYYY-MM-DD&status=open\|closed&mine=1&sort=deadline\|newest` | `{opportunities[]}`; default order: open first, soonest deadline |
| GET `/api/opportunities/<id>` | user | | `{opportunity}` |
| POST `/api/opportunities` | director | as POST `/api/auditions` plus `type: "audition"\|"gig"` and, for gigs, `gig: {date, start_time?, venue, money?, musicians?, music?}` (each M is `{rating 1-5, note}`) | 201 `{opportunity}` |
| PUT `/api/opportunities/<id>` | owner | same fields, all optional | `{opportunity}` |
| GET `/api/ensembles` | public | `?category=&q=` | `{ensembles:[{id,name,category,city,state,location,logo_initials,logo_color,about,founded,season,director,open_opportunity_count}]}` |
| GET `/api/ensembles/<id>` | public | | `{ensemble:{...above, highlights[], roster[{name,instrument}], open_opportunities:[opportunity card]}}` |
| PUT `/api/ensembles/<id>` | owner (its director) | `{about?, season?, city?, state?, highlights?[], roster?[{name,instrument}]}` | `{ensemble}` |
| GET `/api/teachers` | public | `?instrument=<taught>&q=` | `{teachers[]}` (full user with `teaching`, plus `badges[]`) |
| PUT `/api/gigs/<id>/availability` | musician | `{status: "available"\|"maybe"\|"unavailable"}` (replaces earlier mark; 400 for auditions) | `{availability:{gig_id,status}}` |
| GET `/api/gigs/<id>/availability` | owner (gig's director) | | the sub list: `{gig:{id,title}, available[], maybe[], unavailable[]}` of users with `location` and `marked` |
| GET `/api/my/applications` | musician | | `{applications:[{id,audition_id,created,status,status_label,opportunity:card,ensemble:{id,name,...},callback:{date,location,message}\|null,feedback:{average,scores,comments,shared_at,notes:null\|[{time,text}]}\|null}]}` newest first |
| PUT `/api/submissions/<id>/status` | owner | `{status: "submitted"\|"shortlisted"\|"callback"\|"not_selected", callback_date?, callback_location?, message?}`; `callback` needs a date, place or message (the audition's callback date/place fill in gaps); other statuses clear callback details | `{submission}` (same as detail) |
| POST `/api/submissions/<id>/reveal` | owner | | `{submission}` with identity (blind mode only matters; harmless otherwise) |
| PUT `/api/submissions/<id>/feedback` | owner | `{shared: true\|false, include_notes?: true\|false}`; sharing needs a score or a comment (400 otherwise) | `{submission}` |
| POST `/api/musicians/<handle>/endorsements` | director or teacher | `{text, relationship?}` (not for yourself) | 201 `{endorsement:{id,text,relationship,created,author}}` |
| POST `/api/me/badges` | musician | `{kind: "union"\|"school"\|"ensemble", label}` (always unverified) | 201 `{badge:{id,kind,label,verified_by_tutti}}`; 409 duplicate label |
| GET `/api/conversations` | user | | `{conversations:[{id,other:user,context:{opportunity:{id,title}\|null,submission_id},last_message,unread_count,updated}], unread_total}` newest activity first |
| POST `/api/conversations` | user | `{user_id, body?, audition_id?, submission_id?}`: opens (or returns) your single conversation with that user; `submission_id` must be your own submission or one sent to your audition, and is refused for an anonymous blind applicant | 201 (new) or 200 `{conversation}` |
| GET `/api/conversations/<id>` | participants | | `{conversation, messages:[{id,sender_id,body,created,read,mine}]}`; does not mark read |
| POST `/api/conversations/<id>/messages` | participants | `{body}` | 201 `{message}` |
| POST `/api/conversations/<id>/read` | participants | | `{ok:true, unread_total}` (marks the other person's messages read) |
| GET `/api/auditions` | user | same filters as `/api/opportunities`, always `type=audition` | `{auditions[]}` |
| GET `/api/auditions/<id>` | user | | `{audition}` (works for gigs too) |
| POST `/api/auditions` | director | `{title, deadline, category?, ensemble?, description?, instruments[], requirements[], timeline[{label,date}], status?, level?, paid?, pay_text?, city?, state?, video_round_accepted?, callback_date?, callback_location?, blind_review?}`; category, ensemble name, city and state default from the director's ensemble; `level` defaults to `pro`; `deadline`/`callback_date` are YYYY-MM-DD | 201 `{audition}` |
| PUT `/api/auditions/<id>` | owner | same fields, all optional; `blind_review` switches blind mode on/off (off reveals everyone); `type` cannot change | `{audition}` |
| POST `/api/auditions/<id>/submissions` | musician | JSON `{clip_id, note?, timestamps?[{time,label}]}` **or** raw MP4 body with `?note=&timestamps=<url-encoded JSON>` | 201 `{submission:{id,audition_id,status:"submitted",status_label,created}}`; 409 if closed, a gig, or already submitted |
| GET `/api/my/submissions` | musician | | v1 list: `{submissions:[{id,audition_id,audition_title,ensemble,status,status_label,created}]}` (never scores or comments) |
| GET `/api/director/dashboard` | director | | `{director, kpis:{open_auditions,closing_this_week,total_submissions,new_submissions (= submitted),awaiting_review,reviewed,average_score}, auditions[], gigs[]}`; each audition adds `submission_count,new_count,shortlisted_count,reviewed_count,average_score` |
| GET `/api/auditions/<id>/submissions` | owner | `?status=submitted\|shortlisted\|callback\|not_selected\|reviewed` (v1 `new`/`passed` accepted) | `{audition:{id,title,ensemble,blind_review}, submissions:[{id,audition_id,musician,source,status,status_label,created,average,reviewed,feedback_shared,callback,identity_revealed}]}`; `musician` is anonymous while blind |
| GET `/api/submissions/<id>` | owner | | `{submission:{...summary, note, timestamps[], video_url, has_video, musician, musician_clips[], review|null, audition, position, total, previous_id, next_id}}`; `review` also has `feedback_shared, feedback_includes_notes`; anonymous while blind (`musician_clips` empty) |
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

`run.py` · `server/` (app.py handler, router.py, context.py, auth.py, media.py, db.py, schema/ SQL split by area, seed*.py split by area, api/ one module per resource) · `static/` · `tests/` · `my-clips/`.
