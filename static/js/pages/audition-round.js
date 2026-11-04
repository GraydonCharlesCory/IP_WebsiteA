/* Round format and application status for audition.html. Tutti.auditionRound */
(function () {
  const { esc, date } = Tutti.util;
  const { statusTag } = Tutti.components;

  const longDate = (iso) => date(iso, { month: 'long', day: 'numeric', year: 'numeric' });

  /* "Video pre-screen first; live callback only if invited, Dec 10, Bayview Hall" or '' when the audition has no video round. */
  function roundText(audition) {
    if (!audition.video_round_accepted) return '';
    const callback = audition.callback || {};
    const where = [callback.date && longDate(callback.date), callback.location].filter(Boolean).join(', ');
    return `Video pre-screen first; live callback only if invited${where ? `, ${where}` : ''}`;
  }

  function roundSection(audition) {
    const text = roundText(audition);
    if (!text) return '';
    return `<div class="sec"><h2>Round format</h2><div class="round"><span class="tag ok">✓ Video round accepted</span><p class="t2">${esc(text)}</p></div></div>`;
  }

  const ensembleFact = (audition) => (audition.ensemble_id
    ? `<a href="ensemble.html?id=${audition.ensemble_id}">${esc(audition.ensemble)}</a>` : esc(audition.ensemble));

  /* Card for a musician who already applied: real status tag plus a link to the tracker. */
  function appliedCard(audition) {
    const mine = audition.my_submission;
    return `<div class="card pad stack"><div style="display:flex;justify-content:space-between;align-items:center">
        ${statusTag(mine.status)}<span class="small muted">${date(mine.created, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</span></div>
      <div><b>Your clip is with ${esc(audition.director.name)}</b><div class="small muted">Only the director sees scores and comments unless they share feedback.</div></div>
      <a class="btn btn-ghost" href="applications.html">See your application</a></div>`;
  }

  Tutti.auditionRound = { roundSection, ensembleFact, appliedCard };
})();
