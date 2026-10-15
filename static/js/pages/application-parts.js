/* Markup for one application on applications.html: status tracker, callback card, shared-feedback card. Tutti.applicationParts */
(function () {
  const { esc, date } = Tutti.util;

  const CRITERIA = [['tone', 'Tone'], ['rhythm', 'Rhythm'], ['technique', 'Technique'], ['musicality', 'Musicality'], ['preparation', 'Preparation']];
  const STEP_INDEX = { submitted: 0, shortlisted: 1, callback: 2, not_selected: 2 };

  /* Submitted → Shortlisted → Callback (or Not selected); the current step is highlighted, earlier steps are done. */
  function tracker(status) {
    const current = STEP_INDEX[status] ?? 0;
    const steps = ['Submitted', 'Shortlisted', status === 'not_selected' ? 'Not selected' : 'Callback'];
    return `<ol class="track">${steps.map((label, i) => {
      const state = i < current ? 'done' : i === current ? `now ${status === 'not_selected' ? 'no' : ''}` : '';
      return `<li class="${state}"><i>${i < current ? '✓' : i + 1}</i><span>${esc(label)}</span></li>`;
    }).join('')}</ol>`;
  }

  function callbackCard(callback) {
    if (!callback) return '';
    const when = callback.date ? date(callback.date, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }) : 'Date to be confirmed';
    return `<div class="note-card callback"><div class="eyebrow">Live callback</div>
      <div class="cb-facts"><div><span>Date</span><b>${esc(when)}</b></div><div><span>Place</span><b>${esc(callback.location || 'To be confirmed')}</b></div></div>
      ${callback.message ? `<blockquote>${esc(callback.message)}</blockquote>` : ''}</div>`;
  }

  const scoreBars = (scores) => CRITERIA.filter(([key]) => scores[key] != null).map(([key, label]) =>
    `<div class="score"><span>${label}</span><div class="meter"><i style="width:${Number(scores[key]) * 10}%"></i></div><b>${Number(scores[key])}</b></div>`).join('');

  const notesList = (notes) => (notes && notes.length
    ? `<div class="fb-notes"><div class="eyebrow">Notes on your clip</div>${notes.map((n) => `<div><span class="tag grey">${esc(n.time)}</span>${esc(n.text)}</div>`).join('')}</div>` : '');

  function feedbackCard(feedback) {
    if (!feedback) {
      return '<div class="note-card muted-card"><div class="eyebrow">Feedback</div><p class="t2 small">Feedback not shared. The director has not shared scores or comments for this application.</p></div>';
    }
    return `<div class="note-card feedback"><div class="fb-head"><div class="eyebrow">Shared feedback</div>
        <div class="avg"><b>${Number(feedback.average).toFixed(1)}</b><span>average</span></div></div>
      <div class="scores">${scoreBars(feedback.scores)}</div>
      ${feedback.comments ? `<blockquote>${esc(feedback.comments)}</blockquote>` : ''}${notesList(feedback.notes)}
      <div class="small muted">Shared ${esc(date(feedback.shared_at, { month: 'short', day: 'numeric', year: 'numeric' }))}</div></div>`;
  }

  Tutti.applicationParts = { tracker, callbackCard, feedbackCard };
})();
