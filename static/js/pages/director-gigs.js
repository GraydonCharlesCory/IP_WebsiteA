/* "My gigs" list on the director dashboard: Tutti.directorGigs.markup(gigs) */
(function () {
  const { esc, date } = Tutti.util;

  const gigItem = (gig) => `<a class="aitem gig" href="gig.html?id=${gig.id}"><b>${esc(gig.title)}</b>
    <div class="m"><span>${gig.gig ? `${esc(date(gig.gig.date))} · ${esc(gig.gig.venue)}` : esc(gig.location)}</span><span>${gig.available_count || 0} available</span></div></a>`;

  const markup = (gigs) => (gigs && gigs.length
    ? `<div class="eyebrow" style="margin-top:20px">My gigs</div>${gigs.map(gigItem).join('')}` : '');

  Tutti.directorGigs = { markup };
})();
