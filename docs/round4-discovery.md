# Round four discovery data

## Existing installations

The additive `opportunity_discovery` table references existing auditions without changing their types, rows, foreign keys or blind-review triggers. Missing metadata means genre unknown, eligibility unknown and no student-hub placement. Migration never derives metadata from category, level, descriptive text, teacher services or school activities. Existing installations receive no automatic classifications, even for a reused demo title. Creators can declare metadata through the existing ownership-checked opportunity create/edit API; the posting form also exposes these declarations.

## Fresh demo editorial mappings

Only initialization of an empty demo database applies the exact owner/title mappings in `server/seed_discovery.py`. The big-band, jazz-combo and rhythm-section examples are declared Jazz; string-section and holiday-pops examples Orchestral; college entrance and chamber camp Classical; the cross-discipline project grant Cross-genre. These are editorial definitions of fictional examples, not production inference rules.

Only the honors combo is declared high-school eligible, the university rhythm section college eligible, and college entrance and summer camp high-school eligible. The combo, university rhythm section and college entrance audition explicitly belong in the student audition hub. Other eligibility stays unknown. Summer camp stays in Applications rather than the audition hub.

## Read-only previews

`server/demo_discovery.py` explicitly defines a fictional Rock teaching position and two fictional Jazz/Classical clinics. These school-linked previews have a separate preview identifier, no audition identifier and no application, registration or payment workflow. Teaching appears in Applications; clinics appear in For Students. No teacher profile or service is converted into a job or clinic.

## Search boundaries

Applications combine keyword, instrument, declared genre, location and type; submission status is independent. College entrance is excluded only from available application discovery, never submitted history or the underlying API. For Students combines keyword, declared high-school/college eligibility and location; school exploration deliberately ignores eligibility. Find musicians' keyword combines public name, instrument and city only, not email, biography, state or category. Separate shared region, major-city and location-text controls narrow these searches and the school directory; see [geographic matching policy and limitations](location-search.md).

College entrance routes to For Students by its existing type even when optional metadata is unknown; selecting a student level still requires an explicit declaration. Gigs remain in Browse opportunities after an availability mark, showing the real current availability and linking to the existing update workflow. School-scoped keyword links survive the Discover gateway to both Applications and For Students.

## Limitations

Unclassified existing listings do not match a selected genre or eligibility until their creator explicitly authors that metadata. Clinics and teaching positions are labelled demo previews, not new submission types. No live data, real email or external service is involved.
