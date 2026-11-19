# Tutti v3 — local musician opportunity demo

Python 3.9+ standard library, SQLite, plain HTML/CSS/JS. No package installation or build step. This folder changes v3 only; separate v1/v2 and mockups are untouched.

## Run and test

```
python3 run.py --port 8000
```

Open http://localhost:8000 (loopback only).

```
python3 -m unittest discover -s tests
```

Optional rendered role/privacy checks use an already installed Playwright module and Chrome, without installing anything:

```
PLAYWRIGHT_MODULE=/path/to/installed/playwright CHROME_EXECUTABLE="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" node tests/render_workflows.cjs
```

The check creates fresh data and an isolated browser profile in the temporary directory, starts a loopback-only server on an allocated port, and closes both afterward. Set `RENDER_ARTIFACT_DIR` to retain the screenshot outside temporary-job cleanup.

Blind playback uses macOS's installed `/usr/bin/afconvert`. The server validates decoded PCM and writes a fresh metadata-free WAV containing audio samples only. If decoding is unavailable or fails, playback fails closed with an actionable error and server log, never the source MP4. Real-media regression tests use the licensed sample recordings in `my-clips/`; see its credits file.

## Demo roles and walkthrough

All demo account passwords are `demo`; the avatar opens the account switcher.

- Musician: `leo.marquez@tutti.demo`, `adam.reyes@tutti.demo`, or `jordan.wells@tutti.demo`.
- Director: `rhonda.holloway@tutti.demo`, `elena.voss@tutti.demo`, or `priya.raman@tutti.demo`.
- School: `lakefront.school@tutti.demo` or `prairie.school@tutti.demo`.

1. **Discovery is home.** Find auditions, gigs, grants, residencies, high-school college auditions and summer camps. Filter by instrument, location, audience and opportunity type. Separate Jazz/Orchestral/Student navigation tabs are gone; their useful opportunities remain. Community posts/clips, teachers, ensemble pages, gig availability and the three M's remain.
2. **Applications** combines submitted applications and opportunities not yet applied to. Both tabs search title, ensemble, instrument and location, with instrument/location filters. On Applications and Discovery, **Genre keywords** searches existing title, ensemble and description text, not a dedicated genre taxonomy or the Jazz/Orchestral/Students section labels. Audition requirements, timelines, status and callback details remain. Musicians never receive applicant counts, review scores or composites, including in shared feedback.
3. **Manage opportunities** lets directors and schools create auditions and application opportunities. Choose blind/nonblind at creation; it cannot change afterward, including via the API or database update. Configure 1–12 rubric criteria; rubrics freeze with the first application.
4. Open **Submissions & administration**, then a review. Blind reviews hide identity, profile, video, original filenames, applicant free text, chapters and submission timestamps. Nonblind reviews show identity/video. Musician-facing audition pages never list individual directors.
5. Create a scoped guest link in administration. Guests can play and score only submissions in that opportunity, and see only their own scores. Each reviewer's criterion mean has equal weight in the composite; only the creating account sees the composite. Revocation blocks future access but retains prior scores for the audit record. Shared feedback contains written comments and optionally director notes, never scores/composites.
6. Directors can type feedback or explicitly start browser-supported speech recognition. Unsupported browsers retain typed input and explain the fallback. Microphone permission and a working browser recognition service are required; recognition may use the browser vendor's online service. This demo does not promise offline transcription.
7. Two-way musician/director chat UI and APIs are removed. Administration provides one-way messages to one selected applicant, bulk announcements, and one-click confirmation/rejection templates. Select an applicant by their displayed label (anonymous for blind auditions); only that applicant receives the individual notice. The recipient selection clears after sending. **Assumption:** “do it all” means both in-app notices and email capability. Email is a LOCAL simulated outbox only: no SMTP, real delivery, paid services or external email connection. Old conversation records remain stored but inaccessible through the removed APIs.
8. Edit a musician profile for instrument, location, multiple schools/degrees and certifications. Education links to school pages. Professional connections describe working relationships, not advertising or independently verified recommendations; existing relationship records are retained.
9. Search the school directory by name or location, then explore a school's banner, overview, programs/activities and alumni tabs. School accounts manage only their owned school pages, programs, activities and alumni connections, and post opportunities for that school. Other accounts cannot edit those pages. Schools are fictional demo institutions, not real affiliations.

The workspace uses local Fraunces/Inter fonts and ivory/sage/sand colors. The appearance button switches between light and dark and remembers the choice in browser storage. Community retains its greeting, open auditions and trending clips; only the section-definition row is removed.

No new deadline-prioritized dashboard is included; that remains future scope.

Applications, For Students, Schools and Find musicians include U.S. region and curated major-city filters alongside location text. All selected constraints combine with existing search filters; smaller/international places remain reachable using All regions/All cities and location text. See [geographic matching policy, catalog coverage and limitations](docs/location-search.md).

### Simulated profile and school detail

Musician headers show education/degrees and certifications instead of clip/post counts; public profile responses no longer include the unused `stats` totals. Authored education links still open the corresponding school, and credentials are not repeated in the sidebar.

Normal profile/school/opportunity reads automatically supply a **read-only simulated overlay** for known fictional seeds, including already-populated databases. No reset, migration, posting or new workflow is needed. Stored authored credentials, school details, alumni, requirements, timelines, applications and files are never replaced. Example credentials are separate from editable/verified credentials; a nonempty education or certification list suppresses that category's examples. School Posts appear immediately below At a glance on Overview, with two labelled sample updates per seed school. Alumni examples have their own illustrative section and disappear when real alumni links exist; they are not stored links and cannot be removed as if they were. Examples never reuse an account name or handle, so removing a real connection never resurrects that person as an example.

The exact inventory is in `server/demo_enrichment.py`: nine musician education/program examples and nine certificate examples (including issuer, study area, year and completion/in-progress status); two school updates each for Lakefront and Prairie; four anonymous illustrative graduate pathways (two per school), with no account identity, profile link or endorsement; and four school-opportunity preparation/overview examples for the project grant, residency, college entrance audition and summer chamber camp. Each displayed example is labelled simulated, fictional and/or illustrative, never verified. These are invented credentials/affiliations, not claims about real people or institutions. Preparation examples never alter actual requirements, eligibility, filters, deadlines, review mode or submission logic; an authored requirement list or edited original description suppresses them.

Qualification requires the original demo handle, name, email, role, category and ensemble; school examples also require the original school name and owner relationship. Other/custom identities receive no examples. This is conservative content matching, not a historical provenance ledger: an exact recreation of an original seed identity is indistinguishable from that seed, and an intentionally cleared list can show a separate simulated fallback again. Renaming a seed identity/school disables its overlay. Existing verified/self-claimed badges remain distinct and unchanged. These examples are local demo displays only: no real posts, email, registration, messaging, follows, payments or external publishing.

## Privacy and demo boundaries

Recordings referenced by blind applications are restricted to their owning musician on raw clip/upload routes; reviewers and guests must use scoped sanitized audio. Unrelated public/community recordings remain playable without signing in. Previously downloaded public media cannot be recalled. Scoped nonblind reviews retain video. Musician-facing ensemble pages omit director cards and director roster entries; gig pages likewise omit individual director cards.

Audio can itself contain spoken names or recognizable performances: software cannot guarantee anonymity against that content or outside knowledge. Directors remain responsible for identifiers they type into shared written feedback. The public demo account switcher and known passwords are authentication simulations, **not production anti-collusion controls**. Do not expose this demo to untrusted users or enter private recordings/credentials.

## Existing data: migrate, never reset to upgrade

Starting with an existing supported v2 database creates `data/tutti.pre-v3.sqlite`, migrates additively to schema 3, preserves existing IDs, rows, reviews, messages and uploaded files, and adds the new fictional school/opportunity seeds once. Restarts are idempotent. Unsupported/future schemas fail with instructions instead of deleting data. The migration backup contains the database only: back up the entire `data/` directory separately to include uploads.

`data/` is git-ignored; profile uploads live under `data/uploads/clips/`, submissions under `data/uploads/submissions/`, sanitized audio under `data/blind-audio/`. Seed recordings live in `my-clips/`; live-demo upload examples live in `demo-uploads/`. Missing sample recordings show an honest unavailable state.

`python3 run.py --reset` is an explicit destructive option for disposable demo data only; **do not use it for an upgrade**. It preserves `my-clips/` and `demo-uploads/`, not database/uploads.

## API areas and implementation

- `/api/opportunities`, `/api/auditions`, `/api/my/applications`: discovery, creation, ownership, submissions and status.
- `/api/submissions/<id>` and its `/audio`, `/review`, `/feedback`, `/status` routes: creator-only review; `/notification` records a template notice.
- `/api/auditions/<id>/rubric`, `/guests`, `/announcements`, `/notices`, `/outbox`: creator-only rubric, scoped guest administration and local delivery records.
- `/api/guest/...`: scoped capability access via `X-Review-Key`; guest page links carry the key in the fragment, remove it from browser history and do not put it in media URLs.
- `/api/schools`, `/api/musicians/<handle>`, `/api/me`, `/api/my/notices`: owned school data, profiles, education, connections and musician notices.
- Existing community, teachers, ensembles, gigs and upload APIs remain. `/api/conversations` and descendants return 404.

Failures are logged server-side or displayed with browser error records and actionable messages. `server/` splits migration, PCM sanitization and each API responsibility; `static/js/pages/` splits page behavior; `tests/` covers existing features plus privacy, immutable modes, roles, guest/composite isolation, notification simulation and populated-v2 migration.
