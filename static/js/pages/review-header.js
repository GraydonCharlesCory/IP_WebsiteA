/* Review page header and applicant column: Tutti.reviewHeader.markup(submission). Anonymous applicants get no name, location, profile link or public clips. */
(function () {
  const { esc, timeAgo } = Tutti.util;
  const { clipCard } = Tutti.components;

  const pagerLink = (id, label) => id
    ? `<a class="btn btn-ghost" style="height:34px" href="review.html?id=${id}">${label}</a>`
    : `<span class="btn btn-ghost disabled" style="height:34px">${label}</span>`;

  const blindBanner = (sub) => (sub.musician.anonymous
    ? `<div class="blind-banner" role="status"><span>🙈</span><div><b>Blind review.</b> Names and photos are hidden while you score. Shortlisting, callbacks and scoring keep this applicant anonymous.</div>
        <button class="btn btn-ghost" id="revealButton">Reveal identity</button></div>`
    : '');

  function applicantRow(sub) {
    const m = sub.musician;
    const details = m.anonymous ? [m.instrument] : [m.instrument, m.location];
    const links = [];
    if (m.handle) links.push(`<a class="btn btn-ghost" href="profile.html?h=${encodeURIComponent(m.handle)}">View public profile</a>`);
    if (!m.anonymous && m.id) links.push(`<a class="btn btn-ghost" href="messages.html?to=${m.id}&submission=${sub.id}">Message applicant</a>`);
    return `<div class="mrow">${Tutti.applicantAvatar(m)}<div class="t"><b style="font-size:17px">${esc(m.name)}</b>
      <div class="small muted">${esc(details.filter(Boolean).join(' · '))} · submitted ${timeAgo(sub.created)}</div></div>${links.join('')}</div>`;
  }

  function applicantNoteAndClips(sub) {
    const first = esc(sub.musician.anonymous ? 'The applicant' : sub.musician.name.split(' ')[0]);
    const clips = sub.musician_clips.filter((c) => c.available).slice(0, 3);
    const note = sub.note ? `<div class="note"><div class="eyebrow">Note from ${first}</div><p>${esc(sub.note)}</p></div>` : '';
    const clipRow = clips.length ? `<div style="margin-top:26px"><div class="eyebrow" style="margin-bottom:12px">${first}'s public clips</div><div class="clip-row">${clips.map(clipCard).join('')}</div></div>` : '';
    return note + clipRow;
  }

  function topBar(sub) {
    return `<div class="bar-top"><div class="crumb"><a href="director.html">My auditions</a> / <a href="director.html?audition=${sub.audition.id}">${esc(sub.audition.title)}</a> / ${esc(sub.musician.name)}</div>
      <div class="pager">${pagerLink(sub.previous_id, '← Prev')}Submission ${sub.position} of ${sub.total}${pagerLink(sub.next_id, 'Next →')}</div></div>`;
  }

  const markup = (sub) => `${topBar(sub)}${blindBanner(sub)}`;
  Tutti.reviewHeader = { markup, applicantRow, applicantNoteAndClips };
})();
