/* "Share feedback with applicant": preview of what the musician will see, plus share/unshare.
   Tutti.reviewFeedback.mount(container, {submission, getReview, ensureSaved}) returns {refresh}.
   getReview() -> {scores, comments, notes}; ensureSaved() -> Promise<boolean> saves pending edits before sharing. */
(function () {
  const { esc, duration } = Tutti.util;
  const { CRITERIA, average } = Tutti.reviewScores;

  function previewMarkup({ scores, comments, notes }, includeNotes) {
    const avg = average(scores);
    const rows = CRITERIA.filter(([key]) => scores[key]).map(([key, label]) => `<div class="fb-row"><span>${label}</span><b>${scores[key]}/10</b></div>`).join('');
    const noteRows = includeNotes && notes.length ? `<div class="eyebrow">Timestamped notes</div>${notes.map((n) => `<div class="tc"><span class="tc-time">${duration(n.time)}</span><span>${esc(n.text)}</span></div>`).join('')}` : '';
    if (avg === null && !comments && !noteRows) return '<p class="small muted">Nothing to share yet. Add a score or a comment first.</p>';
    return `<div class="fb-avg">${avg === null ? '—' : avg.toFixed(1)}<small>/10 average</small></div>${rows}
      ${comments ? `<div class="eyebrow">Comments</div><p class="fb-comments">${esc(comments)}</p>` : ''}${noteRows}`;
  }

  function mount(container, { submission, getReview, ensureSaved }) {
    const initial = submission.review || {};
    const state = { shared: !!initial.feedback_shared, includeNotes: !!initial.feedback_includes_notes };

    function draw() {
      const first = esc(submission.musician.anonymous ? 'the applicant' : submission.musician.name.split(' ')[0]);
      container.innerHTML = `<div class="fb-head"><div class="eyebrow">Share feedback with applicant</div>
          ${state.shared ? '<span class="tag ok">✓ Shared</span>' : '<span class="tag grey">Not shared</span>'}</div>
        <p class="small muted">${state.shared ? `${first} can see this now. Changes you make here are not shown to them until you share again.` : `Nothing below is visible to ${first} until you share it.`}</p>
        <div class="fb-preview" aria-label="What the musician will see">${previewMarkup(getReview(), state.includeNotes)}</div>
        <label class="check"><input type="checkbox" id="includeNotes" ${state.includeNotes ? 'checked' : ''}><span>Include my timestamped notes</span></label>
        <div class="fb-actions"><button class="btn btn-primary" id="shareButton">${state.shared ? 'Update shared feedback' : 'Share feedback'}</button>
          ${state.shared ? '<button class="btn btn-ghost" id="unshareButton">Stop sharing</button>' : ''}</div>`;
      container.querySelector('#includeNotes').onchange = (event) => { state.includeNotes = event.target.checked; draw(); };
      container.querySelector('#shareButton').onclick = () => change(true);
      const unshare = container.querySelector('#unshareButton');
      if (unshare) unshare.onclick = () => change(false);
    }

    async function change(shared) {
      try {
        if (shared && !(await ensureSaved())) return;
        const { submission: updated } = await api.shareFeedback(submission.id, shared, state.includeNotes);
        state.shared = !!(updated.review && updated.review.feedback_shared);
        Tutti.toast(shared ? 'Feedback shared with the applicant.' : 'Feedback is no longer shared.', 'ok');
        draw();
      } catch (error) { Tutti.reportError(error, shared ? 'share feedback' : 'stop sharing feedback'); }
    }

    draw();
    return { refresh: draw };
  }

  Tutti.reviewFeedback = { mount };
})();
