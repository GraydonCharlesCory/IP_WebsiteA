/* Section feed: section.html?s=students|orchestral|jazz (Jazz by default). */
(function () {
  const { esc, section, queryParam } = Tutti.util;
  const { instrumentFamily, auditionMini, auditionPost, postCard, personRow, signInPrompt, message, bootPublicPage } = Tutti.parts;
  const content = document.getElementById('content');
  const key = ['students', 'orchestral', 'jazz'].includes(queryParam('s')) ? queryParam('s') : 'jazz';
  const style = section(key);
  const TABS = [['feed', 'Feed'], ['clips', 'Clips'], ['auditions', 'Auditions'], ['musicians', 'Musicians']];

  const state = { tab: location.hash === '#auditions' ? 'auditions' : 'feed', family: '', user: null, data: null };

  const byNewest = (a, b) => b.created.localeCompare(a.created);
  const matchesFamily = (instruments) => !state.family || instruments.some((i) => instrumentFamily(i) === state.family);

  function familyChips() {
    const { posts, clips, musicians, auditions } = state.data;
    const names = new Set([...posts.map((p) => p.author.instrument), ...clips.map((c) => c.instrument), ...musicians.map((m) => m.instrument),
      ...(auditions || []).flatMap((a) => a.instruments)].filter(Boolean).map(instrumentFamily));
    const chip = (name, label) => `<button class="chip ${state.family === name ? 'on' : ''}" data-family="${esc(name)}">${esc(label)}</button>`;
    return `<div class="filters">${chip('', 'All instruments')}${[...names].sort().map((n) => chip(n, n)).join('')}</div>`;
  }

  function feedView() {
    const { posts, auditions } = state.data;
    const items = [...posts.filter((p) => matchesFamily([p.author.instrument])).map((p) => ({ created: p.created, html: postCard(p) })),
      ...(auditions || []).filter((a) => matchesFamily(a.instruments)).map((a) => ({ created: a.created, html: auditionPost(a) }))].sort(byNewest);
    return items.length ? `<div class="feed">${items.map((i) => i.html).join('')}</div>` : message('Nothing here yet', 'No posts match this instrument. Try another filter.');
  }

  function clipsView() {
    const clips = state.data.clips.filter((c) => matchesFamily([c.instrument]));
    return clips.length ? `<div class="clip-grid">${clips.map(Tutti.components.clipCard).join('')}</div>` : message('No clips yet', 'No clips match this instrument.');
  }

  function auditionsView() {
    if (!state.user) return signInPrompt('Audition postings');
    const auditions = state.data.auditions.filter((a) => matchesFamily(a.instruments));
    return auditions.length ? `<div class="feed">${auditions.map(auditionPost).join('')}</div>` : message('No open auditions', `Nothing is open in ${style.label} right now.`);
  }

  function musiciansView() {
    const musicians = state.data.musicians.filter((m) => matchesFamily([m.instrument]));
    return musicians.length ? `<div class="card people-grid">${musicians.map(personRow).join('')}</div>` : message('No musicians yet', 'No musicians match this instrument.');
  }

  const VIEWS = { feed: feedView, clips: clipsView, auditions: auditionsView, musicians: musiciansView };

  function sidebar() {
    const { auditions, musicians } = state.data;
    const open = !state.user ? '<p class="muted small">Sign in to see open auditions.</p>'
      : auditions.map(auditionMini).join('') || '<p class="muted small">Nothing is open right now.</p>';
    return `<aside class="side"><div class="card pad"><h3>Open auditions in ${esc(style.label)}</h3>${open}</div>
      <div class="card pad"><h3>Musicians to watch</h3>${musicians.slice(0, 4).map(personRow).join('') || '<p class="muted small">No musicians yet.</p>'}</div></aside>`;
  }

  function band() {
    const { section: info } = state.data;
    const auditionCount = state.user ? ` <span class="muted">· ${state.data.auditions.length}</span>` : '';
    return `<section class="band"><div class="wrap"><span class="tag ${style.css}">${esc(style.label)}</span><h1>${esc(style.label)}</h1>
      <p class="t2">${info.musicians} musician${info.musicians === 1 ? '' : 's'} · ${info.auditions} open audition${info.auditions === 1 ? '' : 's'} · ${esc(info.blurb)}</p>
      <nav class="tabs">${TABS.map(([id, label]) => `<button data-tab="${id}" class="${state.tab === id ? 'on' : ''}">${label}${id === 'auditions' ? auditionCount : ''}</button>`).join('')}</nav></div></section>`;
  }

  function render() {
    content.innerHTML = `${band()}<main class="wrap layout"><div>${familyChips()}<div id="view">${VIEWS[state.tab]()}</div></div>${sidebar()}</main>`;
    Tutti.components.wire(content);
  }

  content.addEventListener('click', (event) => {
    const tab = event.target.closest('[data-tab]');
    const chip = event.target.closest('[data-family]');
    if (!tab && !chip) return;
    if (tab) state.tab = tab.dataset.tab;
    if (chip) state.family = chip.dataset.family;
    render();
  });

  document.title = `Tutti — ${style.label}`;
  document.documentElement.style.setProperty('--acc', `var(--${style.css})`);
  bootPublicPage(content, key, async (user) => {
    state.user = user;
    state.data = await api.section(key);
    render();
  });
})();
