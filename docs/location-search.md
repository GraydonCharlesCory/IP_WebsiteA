# Region and major-city search

Applications (available and submitted), all three For Students tabs, the Schools directory and Find musicians share `static/js/pages/location-search.js`. Discover remains a navigation gateway. No backend data, API visibility, eligibility, submission state or stored location is changed.

## Geographic policy

The four U.S. Census regions use the complete explicit grouping of all 50 states and the District of Columbia, verified against [BLS's Census-region list](https://www.bls.gov/lau/laurdqa.htm) and [Census geographic levels](https://www.census.gov/programs-surveys/economic-census/geographies/levels/2022-levels.html). The helper is the single state/city catalog; its tests independently enumerate all 51 state/DC assignments and require a curated city entry for each. City shortcuts are an editorial selection, not a population ranking or an exhaustive list. Duplicate city names include their state, including Portland and Charleston.

All regions exposes the complete city catalog. Selecting a region narrows the city options and clears an incompatible city, while keeping location text and other filters. All cities matches every explicitly located city in the selected region, including smaller cities absent from the catalog. Reset clears geography and the existing search controls without changing the active tab. Students' school tab continues to ignore student eligibility.

Region, city and free-text location constraints AND together, and AND with the surface's existing keyword, instrument, genre, type, status and level constraints. Location text searches the original location/city/state fields. Use All regions and All cities with location text for international, smaller or unrecognized places. Find musicians' keyword remains public name/instrument/city only; the new geography controls are separate and do not search biography, email or private profiles.

## Explicit formats and limitations

Recognized formats are structured `city` plus a U.S. state code/full name, and free-form `City, ST` or `City, State`, optionally followed by an explicit U.S. country token. They cover opportunity cards' city/state/location, discovery previews' city/location, school location strings and public musician location strings. Whitespace/case, D.C., and St./Saint aliases are normalized only for matching. Conflicting explicit city/state/country fields are rejected, not repaired. A full-name Georgia suffix requires an explicit U.S. country or structured state because Georgia is also a country.

Bare city names never imply a state or country, even for catalog cities. Unknown formats, conflicting records and non-U.S. records remain available with All regions/All cities and text search, but do not match a selected U.S. region/city. There is no geocoding, ZIP-code parsing, metro-area expansion, external request, data rewrite or silent city inference. A city shortcut matches the named city and state, not surrounding suburbs.

## Coverage

`tests/location_search.cjs`, invoked by `tests/test_location_search.py`, covers complete state grouping/catalog coverage, explicit source formats, smaller towns, aliases, duplicate/ambiguous cities, international/unknown/conflicting records, all filter conjunctions and region/city/reset transitions. `tests/render_location_search.cjs`, invoked by the existing workflow suite, exercises every applicable surface/tab, persistent tab constraints, keyword/text conjunctions, empty/reset behavior, anonymous public musicians, labelled selects, keyboard order and both themes at mobile width. Existing workflow coverage retains role/ownership, blind-media, legacy-data and enrichment regressions.

Run the full Python unittest suite and existing `tests/render_workflows.cjs` with the installed Playwright module and Chrome. Both use isolated fixture data; no live service is required. Exact-commit command results are recorded by the task runner rather than embedded here as stale claims.
