/* Decision buttons (Shortlist, Invite to live callback, Not selected) and the current status line.
   Tutti.reviewDecision.mount(container, {submission, getFields, save, onStatus}) */
(function () {
  const { esc, date } = Tutti.util;
  const { statusTag } = Tutti.components;

  function statusLine(status, callback) {
    const where = callback ? [callback.date && date(callback.date), callback.location].filter(Boolean).join(', ') : '';
    return `<div class="dec-state">Status ${statusTag(status)}${status === 'callback' && where ? `<span>Live callback: ${esc(where)}</span>` : ''}</div>`;
  }

  function mount(container, { submission, getFields, save, onStatus }) {
    const first = submission.musician.anonymous ? 'The applicant' : submission.musician.name.split(' ')[0];
    let current = { status: submission.status, callback: submission.callback };

    function draw() {
      container.innerHTML = `${statusLine(current.status, current.callback)}
        <div class="row3"><button class="btn btn-ghost" id="notSelectedButton">Not selected</button><button class="btn btn-primary" id="shortlistButton">★ Shortlist &amp; save</button>
          <button class="btn btn-ghost btn-block" id="callbackButton">${current.status === 'callback' ? 'Edit live callback invitation' : 'Invite to live callback'}</button></div>`;
      container.querySelector('#shortlistButton').onclick = () => decide('shortlist', `${first} moved to your shortlist`);
      container.querySelector('#notSelectedButton').onclick = () => decide('pass', `${first} marked not selected`);
      container.querySelector('#callbackButton').onclick = inviteToCallback;
    }

    function applyStatus(status, callback) {
      current = { status, callback };
      onStatus(status);
      draw();
    }

    async function decide(decision, message) {
      const saved = await save({ ...getFields(), decision }, `✓ Saved · ${message}`);
      if (saved) { Tutti.toast(message, 'ok'); applyStatus(saved.status, null); }
    }

    async function inviteToCallback() {
      try {
        const { audition } = await api.audition(submission.audition.id);
        const answer = await Tutti.reviewCallbackDialog.open({ submission: { ...submission, ...current }, planned: audition.callback });
        if (!answer) return;
        if (!(await save(getFields(), '✓ Saved'))) return;
        const { submission: updated } = await api.setSubmissionStatus(submission.id, { status: 'callback', ...answer });
        applyStatus(updated.status, updated.callback);
        Tutti.toast(`${first} invited to the live callback`, 'ok');
      } catch (error) { Tutti.reportError(error, 'invite to live callback'); }
    }

    draw();
  }

  Tutti.reviewDecision = { mount };
})();
