/* Opportunity board: discover.html — auditions and gigs, searchable and filterable, filters kept in the URL. */
(function () {
  const { esc } = Tutti.util;
  const { opportunityCard } = Tutti.opportunityCards;
  const { fromQueryString, toQueryString, activeCount, optionsFrom, controlsMarkup, TYPE_OPTIONS, CATEGORY_OPTIONS } = Tutti.discoverFilters;
  const root = document.getElementById('pageRoot');
  const SEARCH_DELAY_MS = 250;

  const state = { filters: fromQueryString(location.search), choices: null, requestNumber: 0 };

  function shellMarkup() {
    return `<section class="band"><div class="wrap">
        <div class="eyebrow">Discover</div><h1>Every audition and gig, one board</h1>
        <p class="t2 board-lead">Students, orchestral and jazz. Search by instrument, city or ensemble.</p>
        <div class="board-search"><input class="input" id="boardSearch" type="search" placeholder="Search title, ensemble, instrument or city" value="${esc(state.filters.q)}" aria-label="Search the board"></div>
        <div id="quickChips"></div></div></section>
      <div class="wrap page board"><div class="card pad filters-card" id="filterControls"></div>
        <div class="board-bar"><div id="resultCount" class="muted" aria-live="polite"></div><button class="btn btn-ghost" id="clearFilters" type="button">Clear filters</button></div>
        <div id="results"></div></div>`;
  }

  function chipGroup(key, options) {
    return `<div class="filters">${options.map(([value, label]) =>
      `<button type="button" class="chip ${state.filters[key] === value ? 'on' : ''}" data-chip="${key}" data-value="${esc(value)}">${esc(label)}</button>`).join('')}</div>`;
  }

  function renderControls() {
    document.getElementById('quickChips').innerHTML = chipGroup('type', TYPE_OPTIONS) + chipGroup('category', CATEGORY_OPTIONS);
    document.getElementById('filterControls').innerHTML = controlsMarkup(state.filters, state.choices);
    document.getElementById('clearFilters').hidden = activeCount(state.filters) === 0;
  }

  function renderResults(opportunities) {
    const count = opportunities.length;
    document.getElementById('resultCount').textContent = `${count} ${count === 1 ? 'opportunity' : 'opportunities'}`;
    document.getElementById('results').innerHTML = count
      ? `<div class="opp-grid">${opportunities.map(opportunityCard).join('')}</div>`
      : `<div class="card pad empty"><h2>Nothing matches</h2><p class="muted" style="margin-top:8px">Try a different search or clear some filters.</p></div>`;
  }

  function renderFailure(error) {
    console.error('Tutti board failed', error);
    document.getElementById('resultCount').textContent = '';
    document.getElementById('results').innerHTML = `<div class="card pad empty"><h2>The board could not be loaded</h2>
      <p class="muted" style="margin-top:8px">${esc(error.message)}</p><p style="margin-top:16px"><button class="btn btn-ghost" id="retry" type="button">Try again</button></p></div>`;
    document.getElementById('retry').onclick = refresh;
  }

  async function refresh() {
    const mine = ++state.requestNumber;
    try {
      const { opportunities } = await api.opportunities(state.filters);
      if (mine === state.requestNumber) renderResults(opportunities);
    } catch (error) {
      if (mine === state.requestNumber) renderFailure(error);
    }
  }

  function applyFilters(changes) {
    Object.assign(state.filters, changes);
    history.replaceState(null, '', `${location.pathname}${toQueryString(state.filters)}`);
    renderControls();
    refresh();
  }

  function wireEvents() {
    let searchTimer = null;
    root.addEventListener('input', (event) => {
      if (event.target.id !== 'boardSearch') return;
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => applyFilters({ q: event.target.value.trim() }), SEARCH_DELAY_MS);
    });
    root.addEventListener('change', (event) => {
      const key = event.target.dataset && event.target.dataset.filter;
      if (key) applyFilters({ [key]: event.target.value });
    });
    root.addEventListener('click', (event) => {
      const chip = event.target.closest('[data-chip]');
      if (chip) return applyFilters({ [chip.dataset.chip]: chip.dataset.value });
      if (event.target.id === 'clearFilters') {
        document.getElementById('boardSearch').value = '';
        applyFilters({ q: '', category: '', type: '', instrument: '', location: '', level: '', paid: '', video_round: '', deadline_before: '' });
      }
    });
  }

  async function start(user) {
    if (!user) return;
    const everything = await api.opportunities({});
    state.choices = optionsFrom(everything.opportunities);
    root.innerHTML = shellMarkup();
    renderControls();
    wireEvents();
    renderResults(everything.opportunities);
    if (activeCount(state.filters) || state.filters.sort) await refresh();
  }

  Tutti.boot({ active: 'discover', requireAuth: false })
    .then((user) => {
      if (user) return start(user);
      root.innerHTML = `<div class="wrap page"><div class="card pad empty"><h2>Sign in to see the board</h2>
        <p class="muted" style="margin-top:8px">Auditions and gigs are shown to signed-in musicians and directors.</p>
        <p style="margin-top:16px"><a class="btn btn-primary" href="index.html">Sign in</a></p></div></div>`;
      return undefined;
    })
    .catch((error) => Tutti.pageUtil.showFailure(error, { title: 'The board could not be loaded', backHref: 'home.html', backLabel: 'Back to home' }));
})();
