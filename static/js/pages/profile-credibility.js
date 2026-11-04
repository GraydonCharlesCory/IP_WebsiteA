/* Credibility pieces of profile.html: badges, endorsements, "Lessons & clinics", viewer actions. Tutti.credibility
   Every function returns an escaped HTML string. */
(function () {
  const { esc, date } = Tutti.util;
  const { avatar } = Tutti.components;

  const BADGE_KINDS = { union: 'Union', school: 'School', ensemble: 'Ensemble' };
  const TICK = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12l5 5 9-10"/></svg>';

  function badge(item) {
    const proof = item.verified_by_tutti
      ? `<span class="proof ok" title="Checked by Tutti">${TICK}Verified by Tutti</span>` : '<span class="proof">Self-claimed</span>';
    return `<span class="badge-pill ${item.verified_by_tutti ? 'verified' : ''}"><span class="kind">${esc(BADGE_KINDS[item.kind] || item.kind)}</span><b>${esc(item.label)}</b>${proof}</span>`;
  }

  const badgeRow = (badges) => (badges.length ? `<div class="badges">${badges.map(badge).join('')}</div>` : '');

  function endorsement(item) {
    const role = item.author.role === 'director' ? [item.author.ensemble, 'Director'].filter(Boolean).join(', ') : `${item.author.instrument || 'Musician'}, Teacher`;
    return `<div class="card pad endorse"><div class="who">${avatar(item.author, 'sm')}
        <div><a href="profile.html?h=${encodeURIComponent(item.author.handle)}"><b>${esc(item.author.name)}</b></a>
        <div class="small muted">${esc(role)}${item.relationship ? ` · ${esc(item.relationship)}` : ''}</div></div>
        <span class="small muted when">${esc(date(item.created, { month: 'short', day: 'numeric', year: 'numeric' }))}</span></div>
      <p class="t2">“${esc(item.text)}”</p></div>`;
  }

  function endorsementsSection(endorsements) {
    const body = endorsements.length ? endorsements.map(endorsement).join('') : '<div class="card pad"><p class="small muted">No endorsements yet.</p></div>';
    return `<section class="endorsements"><h2>Endorsements</h2>${body}</section>`;
  }

  function lessonsCard(musician) {
    const teaching = musician.teaching;
    if (!musician.is_teacher || !teaching) return '';
    const rows = [['Teaches', (teaching.instruments || []).join(', ')], ['Rate', teaching.rate]].filter(([, v]) => v)
      .map(([label, value]) => `<div><span>${label}</span>${esc(value)}</div>`).join('');
    return `<div class="card pad"><h3>Lessons &amp; clinics</h3>${teaching.blurb ? `<p class="t2 small" style="margin-bottom:12px">${esc(teaching.blurb)}</p>` : ''}<div class="kv">${rows}</div></div>`;
  }

  const canEndorse = (user, musician) => Boolean(user && user.id !== musician.id && (user.role === 'director' || user.is_teacher));

  /* Pills next to the name: Message and Endorse, only for signed-in viewers of someone else's profile. */
  function viewerActions(user, musician) {
    if (!user || user.id === musician.id) return '';
    return `<a class="btn btn-ghost" href="messages.html?to=${musician.id}">Message</a>${canEndorse(user, musician)
      ? '<button class="btn btn-ghost" id="endorseButton" type="button">Endorse</button>' : ''}`;
  }

  Tutti.credibility = { badgeRow, endorsementsSection, lessonsCard, viewerActions };
})();
