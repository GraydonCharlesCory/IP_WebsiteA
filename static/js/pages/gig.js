/* Gig page: gig.html?id=<gig id> — details, the 3 M's, availability (musicians) and the sub list (posting director). */
(function () {
  const { esc, date, queryParam } = Tutti.util;
  const { avatar, categoryTag } = Tutti.components;
  const { ensembleLogo, ensembleLink, ensembleHref, deadlineTag, threeMsPanel } = Tutti.opportunityCards;
  const { showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');

  function band(gig) {
    const when = date(gig.gig.date, { weekday: 'long', month: 'long', day: 'numeric' });
    return `<section class="band"><div class="wrap">
      <div class="crumb"><a href="discover.html">Discover</a> / Gigs</div>
      <div class="tags"><span class="tag warn">Gig</span>${categoryTag(gig.category)}${deadlineTag(gig)}</div>
      <h1>${esc(gig.title)}</h1>
      <div class="ens">${gig.ensemble_info ? ensembleLogo(gig.ensemble_info, 'sm') : ''}<span>${ensembleLink(gig)} · ${esc(gig.location)}</span></div>
      <div class="facts">
        <div class="fact"><span>Date</span><b>${esc(when)}</b></div>
        <div class="fact"><span>Start</span><b>${esc(gig.gig.start_time)}</b></div>
        <div class="fact"><span>Venue</span><b>${esc(gig.gig.venue)}</b></div>
        <div class="fact"><span>Pay</span><b>${gig.paid ? esc(gig.pay) : 'Unpaid'}</b></div>
        <div class="fact"><span>Instruments</span><b>${esc(gig.instruments.join(', '))}</b></div></div></div></section>`;
  }

  function details(gig) {
    return `<div><div class="sec"><h2>The 3 M's</h2><p class="small muted m-lead">How the posting director rates this gig, out of 5: what it pays, who you will play with, and the music itself.</p>${threeMsPanel(gig.gig)}</div>
      <div class="sec"><h2>About this gig</h2><p>${esc(gig.description)}</p></div></div>`;
  }

  function hostCard(gig) {
    const director = gig.director;
    const ensemble = gig.ensemble_info ? `<a class="btn btn-ghost" href="${ensembleHref(gig.ensemble_info.id)}">See ${esc(gig.ensemble_info.name)}</a>` : '';
    if (!director) return ensemble ? `<div class="card pad stack">${ensemble}</div>` : '';
    const message = '';
    return `<div class="card pad stack"><div class="eyebrow">Posted by</div>
      <div class="ens">${avatar(director)}<div><b>${esc(director.name)}</b><div class="small muted">${esc(director.instrument)}</div></div></div>${message}${ensemble}</div>`;
  }

  async function renderPage(gig, user) {
    const main = await Tutti.gigAvailability.mainCard(gig, user);
    root.innerHTML = `${band(gig)}<div class="wrap layout">${details(gig)}<aside class="apply"><div id="availabilitySlot">${main}</div>${hostCard(gig)}</aside></div>`;
    wireAvailability(gig);
  }

  /* Re-draw the availability card after each saved choice so the current one stays highlighted. */
  function wireAvailability(gig) {
    Tutti.gigAvailability.wireMusicianCard(gig, () => {
      document.getElementById('availabilitySlot').innerHTML = Tutti.gigAvailability.musicianCard(gig);
      wireAvailability(gig);
    });
  }

  async function load(user) {
    const id = Number(queryParam('id'));
    if (!id) throw new Error('This link has no gig in it. Open a gig from the board.');
    const { opportunity: gig } = await api.opportunity(id);
    if (gig.type !== 'gig') return location.replace(`audition.html?id=${id}`);
    document.title = `Tutti — ${gig.title}`;
    return renderPage(gig, user);
  }

  Tutti.boot({ active: 'discover' })
    .then(load)
    .catch((error) => showFailure(error, { title: 'This gig could not be loaded', backHref: 'discover.html', backLabel: 'Back to the board' }));
})();
