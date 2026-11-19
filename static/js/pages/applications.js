/* My applications: applications.html. Musicians only. */
(function () {
  const { esc, date } = Tutti.util;
  const { categoryTag, statusTag } = Tutti.components;
  const { tracker, callbackCard, feedbackCard } = Tutti.applicationParts;
  const { showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');
  let activeTab = 'available';
  const filters = { q: new URLSearchParams(location.search).get('q') || '', instrument: '', genre: '', location: '', region: '', city: '', type: '' };

  const { metadata, matches: matchOpportunity, TYPES, options, href, previewCard } = Tutti.discovery;
  let statusFilter = '';
  let genres = [];
  const matches = opp => matchOpportunity(opp, filters);
  function searchMarkup(opportunities) {
    return `<form id="applicationSearch" class="card pad application-search" role="search">
      <label class="field">Search opportunities & applications<input class="input" type="search" id="applicationQuery" data-search="q" value="${esc(filters.q)}" placeholder="Title, ensemble, instrument or location"></label>
      <div class="application-filters"><label class="field">Type<select class="input" data-search="type">${TYPES.map(([value,label])=>`<option value="${value}">${label}</option>`).join('')}</select></label>
      <label class="field">Instrument<select class="input" data-search="instrument">${options(opportunities.flatMap(o=>o.instruments||[]),'Any instrument')}</select></label>
      <label class="field">Genre<select class="input" data-search="genre">${options(genres,'All genres')}</select></label></div>
      ${Tutti.locationSearch.markup('application')}
      <p class="small muted">Genre is explicitly declared, never inferred from sections or descriptions. College entrance discovery is in <a href="students.html">For Students</a>; submitted college applications remain here.</p>
      <button class="btn btn-ghost" id="clearApplicationSearch" type="button">Clear filters</button></form>`;
  }

  function applicationCard(app) {
    const opp = app.opportunity;
    return `<article class="card pad app">
      <div class="app-head"><div><div class="tags">${categoryTag(opp.category)}${statusTag(app.status)}</div>
        <h3><a href="audition.html?id=${app.audition_id}">${esc(opp.title)}</a></h3>
        <div class="small muted">${app.ensemble.id ? `<a href="ensemble.html?id=${app.ensemble.id}">${esc(app.ensemble.name)}</a>` : esc(app.ensemble.name)} · Submitted ${esc(date(app.created, { month: 'long', day: 'numeric', year: 'numeric' }))}</div></div>
        <a class="btn btn-ghost" href="audition.html?id=${app.audition_id}">View audition</a></div>
      ${metadata(opp)}${tracker(app.status)}${callbackCard(app.callback)}${feedbackCard(app.feedback)}</article>`;
  }

  const emptyState = () => `<div class="card pad empty"><h2>No applications yet</h2>
    <p class="muted" style="margin-top:8px">When you submit a clip to an audition, its status and any feedback appear here.</p>
    <p style="margin-top:16px"><a class="btn btn-primary" href="discover.html">Find auditions</a></p></div>`;

  async function load() {
    const [{ applications }, { opportunities }, { previews, genres: declaredGenres }] = await Promise.all([api.myApplications(), api.opportunities({ status:'open' }), api.request('GET','/api/discovery')]);
    genres = declaredGenres;
    const browseOpportunities = [...opportunities.filter(o => o.type !== 'college_audition' && !o.my_submission), ...previews.filter(o=>o.type==='teaching')];
    root.innerHTML = `<div class="wrap page applications-page"><div class="page-intro"><div class="eyebrow">Your next movement</div><h1>Find your place.<br>Make it heard.</h1><p class="muted">Find your next opportunity and keep track of the ones in motion.</p></div>
      ${searchMarkup([...browseOpportunities, ...applications.map(a => a.opportunity)])}
      <div class="application-tabs" role="tablist" aria-label="Application lists"><button id="availableTab" role="tab" aria-controls="available">Browse opportunities</button><button id="submittedTab" role="tab" aria-controls="submitted">Submitted applications</button></div>
      <label class="field" id="submittedStatusField" hidden>Application status<select class="input" id="submittedStatus"><option value="">All statuses</option>${[...new Set(applications.map(a=>a.status))].map(value=>`<option value="${esc(value)}">${esc(value.replaceAll('_',' '))}</option>`).join('')}</select></label><p id="applicationResultCount" class="muted small" role="status"></p>
      <section id="submitted" role="tabpanel" aria-labelledby="submittedTab"></section><section id="available" role="tabpanel" aria-labelledby="availableTab" hidden></section></div>`;
    function render() {
      const submitted = applications.filter(a => matches(a.opportunity) && (!statusFilter || a.status===statusFilter));
      const available = browseOpportunities.filter(matches);
      const empty = '<div class="card pad empty"><h2>Nothing matches</h2><p>Try another search or clear the filters.</p><button class="btn btn-ghost" data-reset-app>Clear filters</button></div>';
      document.getElementById('submitted').innerHTML = `<div class="app-list">${submitted.length ? submitted.map(applicationCard).join('') : applications.length ? empty : emptyState()}</div>`;
      document.getElementById('available').innerHTML = `<div class="app-list">${available.length ? available.map(o => o.demo_preview ? previewCard(o) : `<article class="card pad app"><div class="tags"><span class="tag brass">${esc(o.type.replaceAll('_', ' '))}</span><span class="muted small">Closes ${esc(date(o.deadline))}</span></div><h3><a href="${href(o)}">${esc(o.title)}</a></h3><p>${esc(o.ensemble)}</p>${metadata(o)}${o.my_availability ? `<p class="small">Your availability: ${esc(o.my_availability[0].toUpperCase()+o.my_availability.slice(1))}</p>` : ''}<div><a class="btn btn-primary" href="${href(o)}">${o.type==='gig'?(o.my_availability?'Update availability':'View gig'):'View & apply'}</a></div></article>`).join('') : empty}</div>`;
      ['submitted', 'available'].forEach(id => {
        document.getElementById(id).hidden = activeTab !== id;
        const button = document.getElementById(`${id}Tab`);
        button.setAttribute('aria-selected', String(activeTab === id));
        button.tabIndex = activeTab === id ? 0 : -1;
      });
      document.getElementById('submittedStatusField').hidden = activeTab !== 'submitted';
      root.querySelectorAll('[data-reset-app]').forEach(button=>{button.onclick=reset;});
      document.getElementById('applicationResultCount').textContent = activeTab === 'submitted' ? `${submitted.length} applications` : `${available.length} opportunities`;
    }
    ['available', 'submitted'].forEach(id => {
      const button = document.getElementById(`${id}Tab`);
      button.onclick = () => { activeTab = id; render(); };
      button.onkeydown = event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        activeTab = event.key === 'Home' ? 'available' : event.key === 'End' ? 'submitted' : activeTab === 'submitted' ? 'available' : 'submitted';
        render(); document.getElementById(`${activeTab}Tab`).focus();
      };
    });
    const form = document.getElementById('applicationSearch');
    form.onsubmit = event => { event.preventDefault(); render(); };
    form.oninput = event => {
      if (event.target.dataset.search) { filters[event.target.dataset.search] = event.target.value.trim(); render(); }
    };
    const geography = Tutti.locationSearch.bind(form, filters, render);
    const reset = () => {
      Object.keys(filters).forEach(key => { filters[key] = ''; });
      form.querySelectorAll('[data-search]').forEach(input => { input.value = ''; });
      geography.sync();statusFilter='';document.getElementById('submittedStatus').value='';render();
    };
    document.getElementById('clearApplicationSearch').onclick=reset;
    document.getElementById('submittedStatus').onchange=e=>{statusFilter=e.target.value;render();};
    render();
  }

  Tutti.boot({ active: 'applications', requireAuth: true, requireRole: 'musician' })
    .then(load)
    .catch((error) => showFailure(error, { title: 'Your applications could not be loaded', backHref: 'home.html', backLabel: 'Back to home' }));
})();
