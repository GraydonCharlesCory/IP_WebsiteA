/* Markup shared by the discovery pages (board, ensemble, gig): window.Tutti.opportunityCards.
   Requires util.js and components.js. Every function returns an escaped HTML string. */
(function () {
  const { esc, date, daysUntil } = Tutti.util;
  const { categoryTag } = Tutti.components;

  const MONEY_MUSICIANS_MUSIC = [['money', 'Money'], ['musicians', 'Musicians'], ['music', 'Music']];
  const AVAILABILITY_LABELS = { available: 'Available', maybe: 'Maybe', unavailable: 'Unavailable' };

  const opportunityHref = (opp) => (opp.type === 'gig' ? `gig.html?id=${opp.id}` : `audition.html?id=${opp.id}`);
  const ensembleHref = (id) => `ensemble.html?id=${id}`;
  const messageHref = (userId) => `messages.html?to=${userId}`;
  const profileHref = (user) => `profile.html?h=${encodeURIComponent(user.handle)}`;

  /* Round logo from the ensemble's initials and colour. */
  function ensembleLogo(ensemble, size = '') {
    return `<span class="ens-logo ${size}" style="background:${esc(ensemble.logo_color)}" aria-hidden="true">${esc(ensemble.logo_initials)}</span>`;
  }

  function ensembleLink(opp) {
    return opp.ensemble_id ? `<a class="ens-link" href="${ensembleHref(opp.ensemble_id)}">${esc(opp.ensemble)}</a>` : esc(opp.ensemble);
  }

  function typeTag(opp) {
    return `<span class="tag ${opp.type === 'gig' ? 'warn' : 'brass'}">${opp.type === 'gig' ? 'Gig' : 'Audition'}</span>`;
  }

  function deadlineTag(opp) {
    if (opp.status !== 'open') return '<span class="tag grey">Closed</span>';
    const days = daysUntil(opp.deadline);
    if (days <= 14) return `<span class="tag warn">${days <= 0 ? 'Closes today' : `Closes in ${days} day${days === 1 ? '' : 's'}`}</span>`;
    return `<span class="tag grey">Closes ${esc(date(opp.deadline))}</span>`;
  }

  /* Five dots, `rating` of them filled. */
  function ratingDots(rating) {
    const filled = Number(rating) || 0;
    return `<span class="dots" aria-label="${filled} out of 5">${[1, 2, 3, 4, 5].map((n) => `<i class="${n <= filled ? 'on' : ''}"></i>`).join('')}</span>`;
  }

  /* Compact 3 M's row for cards: three small rated pills. */
  function threeMsPills(gig) {
    if (!gig || !gig.three_ms) return '';
    return `<div class="m-pills">${MONEY_MUSICIANS_MUSIC.map(([key, label]) =>
      `<span class="m-pill" title="${esc(gig.three_ms[key].note)}"><b>${label}</b>${ratingDots(gig.three_ms[key].rating)}</span>`).join('')}</div>`;
  }

  /* Large 3 M's block for the gig page: a bar and a note per M. */
  function threeMsPanel(gig) {
    const rows = MONEY_MUSICIANS_MUSIC.map(([key, label]) => {
      const m = gig.three_ms[key];
      const rating = Number(m.rating) || 0;
      return `<div class="m-row"><div class="m-head"><b>${label}</b><span class="m-score">${rating ? `${rating}<small>/5</small>` : 'Not rated'}</span></div>
        <div class="m-bar"><i style="width:${rating * 20}%"></i></div><p class="small muted">${esc(m.note || '')}</p></div>`;
    }).join('');
    return `<div class="m-panel">${rows}</div>`;
  }

  function gigWhen(gig) {
    return gig ? `${date(gig.date, { weekday: 'short', month: 'short', day: 'numeric' })} · ${esc(gig.start_time)} · ${esc(gig.venue)}` : '';
  }

  /* Card for one audition or gig. Works for the full board items and the short cards on an ensemble page. */
  function opportunityCard(opp) {
    const gig = opp.gig;
    const detail = gig ? `<div class="opp-when">${gigWhen(gig)}</div>` : '';
    const instruments = (opp.instruments || []).join(', ');
    return `<article class="card opp-card">
      <div class="top">${typeTag(opp)}${categoryTag(opp.category)}${deadlineTag(opp)}</div>
      <h3><a class="opp-title" href="${opportunityHref(opp)}">${esc(opp.title)}</a></h3>
      <div class="opp-ens">${opp.ensemble_info ? ensembleLogo(opp.ensemble_info, 'sm') : ''}<span>${ensembleLink(opp)} · ${esc(opp.location)}</span></div>
      ${detail}${threeMsPills(gig)}
      <div class="foot"><span>${esc(instruments)}</span><span>${opp.paid ? esc(opp.pay) : 'Unpaid'}</span></div>
      <div class="chips-row"><span class="chip">${esc(opp.level)}</span>${opp.video_round_accepted ? '<span class="chip">Video round</span>' : ''}</div></article>`;
  }

  Tutti.opportunityCards = { AVAILABILITY_LABELS, opportunityHref, ensembleHref, messageHref, profileHref, ensembleLogo, ensembleLink, typeTag,
    deadlineTag, ratingDots, threeMsPills, threeMsPanel, gigWhen, opportunityCard };
})();
