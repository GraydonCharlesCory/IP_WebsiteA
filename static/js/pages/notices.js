(function () {
  const { esc, date } = Tutti.util;
  Tutti.boot({ requireRole: 'musician' }).then(async () => {
    const { notices } = await api.notices();
    document.getElementById('pageRoot').innerHTML = `<main class="wrap page"><h1>Notices</h1><p class="muted">Organizer announcements and application confirmations. A matching email is recorded in the local simulated outbox; no mail is sent.</p>${notices.map(n => `<article class="card pad"><p>${esc(n.body)}</p><span class="small muted">${esc(date(n.created))}</span></article>`).join('') || '<p>No notices yet.</p>'}</main>`;
  }).catch(Tutti.pageUtil.showFailure);
})();
