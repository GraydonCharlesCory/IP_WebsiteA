/* My applications: applications.html. Musicians only. */
(function () {
  const { esc, date } = Tutti.util;
  const { categoryTag, statusTag } = Tutti.components;
  const { tracker, callbackCard, feedbackCard } = Tutti.applicationParts;
  const { showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');

  function applicationCard(app) {
    const opp = app.opportunity;
    return `<article class="card pad app">
      <div class="app-head"><div><div class="tags">${categoryTag(opp.category)}${statusTag(app.status)}</div>
        <h3><a href="audition.html?id=${app.audition_id}">${esc(opp.title)}</a></h3>
        <div class="small muted"><a href="ensemble.html?id=${app.ensemble.id}">${esc(app.ensemble.name)}</a> · Submitted ${esc(date(app.created, { month: 'long', day: 'numeric', year: 'numeric' }))}</div></div>
        <a class="btn btn-ghost" href="audition.html?id=${app.audition_id}">View audition</a></div>
      ${tracker(app.status)}${callbackCard(app.callback)}${feedbackCard(app.feedback)}</article>`;
  }

  const emptyState = () => `<div class="card pad empty"><h2>No applications yet</h2>
    <p class="muted" style="margin-top:8px">When you submit a clip to an audition, its status and any feedback appear here.</p>
    <p style="margin-top:16px"><a class="btn btn-primary" href="discover.html">Find auditions</a></p></div>`;

  async function load() {
    const { applications } = await api.myApplications();
    root.innerHTML = `<div class="wrap page"><div class="eyebrow">Your auditions</div><h1 style="margin:6px 0 24px">My applications</h1>
      <div class="app-list">${applications.length ? applications.map(applicationCard).join('') : emptyState()}</div></div>`;
  }

  Tutti.boot({ active: 'applications', requireAuth: true, requireRole: 'musician' })
    .then(load)
    .catch((error) => showFailure(error, { title: 'Your applications could not be loaded', backHref: 'home.html', backLabel: 'Back to home' }));
})();
