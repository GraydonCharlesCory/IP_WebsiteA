/* Round format line and blind-review note for one audition on the dashboard: Tutti.directorRound */
(function () {
  const { esc, date } = Tutti.util;

  /* "Video pre-screen → live callback on Dec 10, Bayview Hall" or a plain description when there is no video round */
  function formatText(audition) {
    const callback = audition.callback;
    const live = callback ? `live callback on ${[date(callback.date), callback.location].filter(Boolean).join(', ')}` : 'live round to be announced';
    return audition.video_round_accepted ? `Video pre-screen → ${live}` : `Live audition · ${callback ? live : 'details to be announced'}`;
  }

  const roundMarkup = (audition) => `<div class="round"><div class="eyebrow">Round format</div><p>${esc(formatText(audition))}</p>
    <p class="small muted">Blind review is always on: you hear audio only and applicants stay anonymous until you score and call them back.</p></div>`;

  Tutti.directorRound = { formatText, roundMarkup };
})();
