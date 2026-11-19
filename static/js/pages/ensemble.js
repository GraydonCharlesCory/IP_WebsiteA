/* Public ensemble page: ensemble.html?id=<ensemble id> */
(function () {
  const { esc, queryParam } = Tutti.util;
  const { avatar, categoryTag } = Tutti.components;
  const { ensembleLogo, opportunityCard } = Tutti.opportunityCards;
  const { showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');

  function header(ensemble) {
    const founded = ensemble.founded ? `<div class="fact"><span>Founded</span><b>${esc(ensemble.founded)}</b></div>` : '';
    return `<section class="band"><div class="wrap">
      <div class="crumb"><a href="discover.html">Discover</a> / Ensembles</div>
      <div class="ens-head">${ensembleLogo(ensemble, 'lg')}<div>
        <div class="tags">${categoryTag(ensemble.category)}</div><h1>${esc(ensemble.name)}</h1></div></div>
      <div class="facts"><div class="fact"><span>City</span><b>${esc(ensemble.location)}</b></div>${founded}
        <div class="fact"><span>Open now</span><b>${ensemble.open_opportunities.length} opportunit${ensemble.open_opportunities.length === 1 ? 'y' : 'ies'}</b></div></div></div></section>`;
  }

  function aboutSection(ensemble) {
    const highlights = (ensemble.highlights || []).map((text) => `<li>${esc(text)}</li>`).join('');
    const season = ensemble.season ? `<p class="season">${esc(ensemble.season)}</p>` : '';
    return `<div class="sec"><h2>About</h2><p>${esc(ensemble.about)}</p></div>
      <div class="sec"><h2>Season highlights</h2>${season}${highlights ? `<ul class="req highlights">${highlights}</ul>` : ''}</div>`;
  }

  function rosterSection(ensemble) {
    if (!(ensemble.roster || []).length) return '';
    const rows = ensemble.roster.map((p) => `<div class="roster-row"><b>${esc(p.name)}</b><span>${esc(p.instrument)}</span></div>`).join('');
    return `<div class="sec"><h2>Core players</h2><div class="roster">${rows}</div></div>`;
  }

  function opportunitiesSection(ensemble) {
    const cards = ensemble.open_opportunities.map(opportunityCard).join('');
    const body = cards ? `<div class="opp-grid">${cards}</div>` : '<div class="card pad empty"><p class="muted">Nothing is open right now. Check back soon.</p></div>';
    return `<div class="sec"><h2>Open auditions and gigs</h2>${body}</div>`;
  }

  function directorCard(ensemble, user) {
    const director = ensemble.director;
    if (!director) return '';
    return `<aside class="apply"><div class="card pad stack"><div class="eyebrow">Director</div>
      <div class="ens">${avatar(director)}<div><b>${esc(director.name)}</b><div class="small muted">${esc(director.instrument)}</div></div></div>
      <p class="small muted">Apply through the opportunity page. Direct messaging is not available.</p></div></aside>`;
  }

  async function load(user) {
    const id = Number(queryParam('id'));
    if (!id) throw new Error('This link has no ensemble in it. Open an ensemble from the board.');
    const { ensemble } = await api.ensemble(id);
    document.title = `Tutti — ${ensemble.name}`;
    root.innerHTML = `${header(ensemble)}<div class="wrap layout"><div>${aboutSection(ensemble)}${opportunitiesSection(ensemble)}${rosterSection(ensemble)}</div>${directorCard(ensemble, user)}</div>`;
  }

  Tutti.boot({ active: 'discover', requireAuth: false })
    .then(load)
    .catch((error) => showFailure(error, { title: 'This ensemble could not be loaded', backHref: 'discover.html', backLabel: 'Back to the board' }));
})();
