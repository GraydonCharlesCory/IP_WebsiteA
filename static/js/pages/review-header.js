/* Review page header and applicant column: Tutti.reviewHeader.markup(submission). Applicants are always anonymous: no name, location or profile link; nobody gets a video or public clips here. */
(function () {
  const { esc, timeAgo } = Tutti.util;

  const pagerLink = (id, label) => id
    ? `<a class="btn btn-ghost" style="height:34px" href="review.html?id=${id}">${label}</a>`
    : `<span class="btn btn-ghost disabled" style="height:34px">${label}</span>`;

  const blindBanner = (sub) => `<div class="blind-banner" role="status"><b>${sub.blind_review ? 'Blind review: audio only. Identity and applicant free text are withheld from every reviewer.' : 'Nonblind review: applicant identity and original recording are available.'}</b></div>`;

  function applicantRow(sub) {
    const m = sub.musician;
    const links = [];
    return `<div class="mrow">${Tutti.applicantAvatar(m)}<div class="t"><b style="font-size:17px">${esc(m.name)}</b>
      <div class="small muted">${esc(m.instrument)} · submitted ${timeAgo(sub.created)}</div></div>${links.join('')}</div>`;
  }

  function applicantNote(sub) {
    return sub.note ? `<div class="note"><div class="eyebrow">Note from the applicant</div><p>${esc(sub.note)}</p></div>` : '';
  }

  function topBar(sub) {
    return `<div class="bar-top"><div class="crumb"><a href="director.html">My auditions</a> / <a href="director.html?audition=${sub.audition.id}">${esc(sub.audition.title)}</a> / ${esc(sub.musician.name)}</div>
      <div class="pager">${pagerLink(sub.previous_id, '← Prev')}Submission ${sub.position} of ${sub.total}${pagerLink(sub.next_id, 'Next →')}</div></div>`;
  }

  const markup = (sub) => `${topBar(sub)}${blindBanner(sub)}`;
  Tutti.reviewHeader = { markup, applicantRow, applicantNote };
})();
