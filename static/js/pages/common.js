/* Helpers shared by the audition, director and review pages: Tutti.pageUtil */
(function () {
  const { esc } = Tutti.util;
  const LOCK = '<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>';

  /* "🔒 text" line used wherever something is private to the director. */
  const privateNote = (text) => `<div class="private">${LOCK}${esc(text)}</div>`;

  /* Replace the page body with an actionable message (403, 404, network failure...) and log it. */
  function showFailure(error, { title = 'This page could not be loaded', backHref = '', backLabel = '' } = {}) {
    console.error('Tutti page failed', error);
    const back = backHref ? `<p style="margin-top:16px"><a class="btn btn-ghost" href="${esc(backHref)}">${esc(backLabel)}</a></p>` : '';
    document.getElementById('pageRoot').innerHTML =
      `<div class="wrap page"><div class="card pad empty"><h2>${esc(title)}</h2><p class="muted" style="margin-top:8px">${esc(error.message)}</p>${back}</div></div>`;
  }

  Tutti.pageUtil = { privateNote, showFailure };
})();
