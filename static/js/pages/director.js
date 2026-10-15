/* Director dashboard: director.html (optional ?audition=<id> picks the audition shown) */
(function () {
  const { esc, date, timeAgo, daysUntil, queryParam } = Tutti.util;
  const { categoryTag, statusTag } = Tutti.components;
  const { applicantAvatar, directorRound, directorGigs } = Tutti;
  const { privateNote, showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');
  const FILTERS = [
    { key: 'all', label: 'All', test: () => true },
    { key: 'new', label: 'New', test: (s) => s.status === 'submitted' },
    { key: 'reviewed', label: 'Reviewed', test: (s) => s.reviewed },
    { key: 'shortlisted', label: 'Shortlist', test: (s) => s.status === 'shortlisted' },
    { key: 'callback', label: 'Callback', test: (s) => s.status === 'callback' },
    { key: 'not_selected', label: 'Not selected', test: (s) => s.status === 'not_selected' },
  ];
  const state = { dashboard: null, auditionId: null, submissions: [], filter: 'all' };

  const kpi = (label, value, note, noteColor = '') =>
    `<div class="card kpi"><span>${label}</span><b>${value}</b><em style="${noteColor}">${note}</em></div>`;

  function kpiRow({ kpis }) {
    return `<div class="kpis">
      ${kpi('Open auditions', kpis.open_auditions, `${kpis.closing_this_week} closing this week`)}
      ${kpi('Total submissions', kpis.total_submissions, `${kpis.new_submissions} new`)}
      ${kpi('Awaiting review', kpis.awaiting_review, `${kpis.new_submissions} new`, 'color:var(--warn)')}
      ${kpi('Average score', kpis.average_score ?? '—', `across ${kpis.reviewed} reviewed`, 'color:var(--muted)')}</div>`;
  }

  function auditionItem(audition) {
    const days = daysUntil(audition.deadline);
    const deadlineTag = audition.status !== 'open' ? '<span class="tag grey">Closed</span>'
      : `<span class="tag ${days <= 7 ? 'warn' : 'grey'}">Closes ${date(audition.deadline)}</span>`;
    const percent = audition.submission_count ? Math.round((audition.reviewed_count / audition.submission_count) * 100) : 0;
    return `<button class="aitem ${audition.id === state.auditionId ? 'on' : ''}" data-audition-id="${audition.id}">
      <div style="display:flex;justify-content:space-between">${categoryTag(audition.category)}${deadlineTag}</div>
      <b>${esc(audition.title)}</b><div class="prog"><i style="width:${percent}%"></i></div>
      <div class="m"><span>${audition.submission_count} submission${audition.submission_count === 1 ? '' : 's'} · ${audition.new_count} new</span><span>${audition.reviewed_count} reviewed</span></div></button>`;
  }

  function submissionRow(s) {
    const score = s.average === null ? '<span class="muted">—</span>' : `<span class="score">${s.average.toFixed(1)}<small>/10</small></span>`;
    const label = s.status === 'submitted' ? 'Review' : 'Open';
    return `<tr class="${s.status === 'submitted' ? 'new' : ''}" data-href="review.html?id=${s.id}">
      <td><a class="mus" href="review.html?id=${s.id}">${applicantAvatar(s.musician)}<div><b>${esc(s.musician.name)}</b>
        <span>${s.musician.anonymous ? 'Identity hidden · ' : ''}${esc(s.musician.instrument)}${s.musician.location ? ` · ${esc(s.musician.location)}` : ''} · ${s.source === 'upload' ? 'Uploaded clip' : 'Profile clip'}</span></div></a></td>
      <td class="hide t2">${timeAgo(s.created)}</td><td>${score}</td><td>${statusTag(s.status)}</td>
      <td><a class="btn ${s.status === 'submitted' ? 'btn-primary' : 'btn-ghost'}" style="height:34px" href="review.html?id=${s.id}">${label}</a></td></tr>`;
  }

  function submissionsPanel() {
    const audition = state.dashboard.auditions.find((a) => a.id === state.auditionId);
    if (!audition) return '<div class="card pad empty">You have not posted an audition yet.</div>';
    const chips = FILTERS.map((f) => {
      const count = state.submissions.filter(f.test).length;
      return `<button class="chip ${f.key === state.filter ? 'on' : ''}" data-filter="${f.key}">${f.label} ${count}</button>`;
    }).join('');
    const rows = state.submissions.filter(FILTERS.find((f) => f.key === state.filter).test).map(submissionRow).join('');
    const body = rows ? `<table class="tbl"><thead><tr><th>Musician</th><th class="hide">Submitted</th><th>Score</th><th>Status</th><th></th></tr></thead><tbody>${rows}</tbody></table>`
      : '<div class="empty">No submissions here yet.</div>';
    return `<div class="panel-h"><div><h2 style="font-size:22px">${esc(audition.title)} — submissions</h2>
        <div style="margin-top:6px">${privateNote('Only you can see these submissions, scores and comments.')}</div></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap">${chips}</div></div>
      <div class="round-bar">${directorRound.roundMarkup(audition)}</div>${body}`;
  }

  function render() {
    const { director, auditions } = state.dashboard;
    const newCount = state.dashboard.kpis.new_submissions;
    root.innerHTML = `<div class="wrap page">
      <div class="head"><div><div class="eyebrow">${esc(director.ensemble)}</div>
        <h1 style="font-size:clamp(28px,3.4vw,40px);margin-top:6px">Welcome back, ${esc(director.name)}.</h1>
        <p class="t2" style="margin-top:6px">You have <b style="color:var(--text)">${newCount} new submission${newCount === 1 ? '' : 's'}</b> waiting for review.</p></div></div>
      ${kpiRow(state.dashboard)}
      <div class="layout"><div class="alist"><div class="eyebrow">My auditions</div>${auditions.map(auditionItem).join('') || '<p class="muted small">No auditions yet.</p>'}${directorGigs.markup(state.dashboard.gigs)}</div>
      <div class="card" id="submissionsPanel" style="overflow:hidden">${submissionsPanel()}</div></div></div>`;
    root.querySelectorAll('[data-audition-id]').forEach((el) => { el.onclick = () => selectAudition(Number(el.dataset.auditionId)); });
    wirePanel();
  }

  /* Persists the switch, then reloads the table: turning blind review off reveals every applicant. */
  async function setBlindReview(auditionId, enabled) {
    const { audition } = await api.editAudition(auditionId, { blind_review: enabled });
    Object.assign(state.dashboard.auditions.find((a) => a.id === auditionId), audition);
    state.submissions = (await api.auditionSubmissions(auditionId)).submissions;
    refreshPanel();
    Tutti.toast(enabled ? 'Blind review is on: names and photos are hidden.' : 'Blind review is off: applicants are visible.', 'ok');
  }

  function wirePanel() {
    const audition = state.dashboard.auditions.find((a) => a.id === state.auditionId);
    if (audition) directorRound.wireSwitch(root, audition, setBlindReview);
    root.querySelectorAll('[data-filter]').forEach((chip) => {
      chip.onclick = () => { state.filter = chip.dataset.filter; refreshPanel(); };
    });
    root.querySelectorAll('tr[data-href]').forEach((row) => { row.onclick = (event) => { if (!event.target.closest('a')) location.href = row.dataset.href; }; });
  }

  function refreshPanel() {
    document.getElementById('submissionsPanel').innerHTML = submissionsPanel();
    wirePanel();
  }

  async function selectAudition(id) {
    try {
      state.submissions = (await api.auditionSubmissions(id)).submissions;
      Object.assign(state, { auditionId: id, filter: 'all' });
      history.replaceState(null, '', `director.html?audition=${id}`);
      render();
    } catch (error) { Tutti.reportError(error, 'load submissions'); }
  }

  async function load() {
    state.dashboard = await api.dashboard();
    const { auditions } = state.dashboard;
    const wanted = Number(queryParam('audition'));
    const first = auditions.find((a) => a.id === wanted) || auditions.find((a) => a.new_count > 0) || auditions[0];
    state.auditionId = first ? first.id : null;
    state.submissions = first ? (await api.auditionSubmissions(first.id)).submissions : [];
    render();
  }

  Tutti.boot({ active: 'dashboard', requireRole: 'director' })
    .then(load)
    .catch((error) => showFailure(error, { title: 'The dashboard could not be loaded' }));
})();
