/* "Invite to live callback" dialog: Tutti.reviewCallbackDialog.open({submission, planned}) resolves {callback_date, callback_location, message} or null.
   planned = the audition's callback {date, location} used to prefill. Needs dialog-parts.js and submit-dialog.css. */
(function () {
  const { esc } = Tutti.util;

  function open({ submission, planned }) {
    return new Promise((resolve) => {
      const { scrim, close } = Tutti.dialogParts.openScrim(() => false);
      const finish = (answer) => { close(); resolve(answer); };
      const existing = submission.callback || {};
      const value = (own, fallback) => esc(own || fallback || '');
      scrim.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="callbackTitle">
        <div class="mhead"><div><div class="eyebrow">Live callback</div><h3 style="margin-top:4px" id="callbackTitle">Invite ${esc(submission.musician.name)}</h3></div>
          <button class="t2" style="font-size:22px" data-cancel aria-label="Close">×</button></div>
        <form id="callbackForm"><div class="mbody">
          <div class="field"><label for="callbackDate">Date</label><input class="input" id="callbackDate" type="date" value="${value(existing.date, planned && planned.date)}"></div>
          <div class="field"><label for="callbackPlace">Place</label><input class="input" id="callbackPlace" maxlength="200" value="${value(existing.location, planned && planned.location)}"></div>
          <div class="field"><label for="callbackMessage">Message to the applicant</label><textarea class="input" id="callbackMessage" maxlength="2000" placeholder="What to bring, who will be in the room…">${value(existing.message)}</textarea></div>
          <div class="form-error" id="callbackError" role="alert" hidden></div></div>
        <div class="mfoot"><button class="btn btn-ghost" type="button" data-cancel>Cancel</button><button class="btn btn-primary" type="submit">Send invitation</button></div></form></div>`;
      scrim.querySelectorAll('[data-cancel]').forEach((el) => { el.onclick = () => finish(null); });
      scrim.onclick = (event) => { if (event.target === scrim) finish(null); };
      scrim.querySelector('#callbackForm').onsubmit = (event) => {
        event.preventDefault();
        const answer = {
          callback_date: scrim.querySelector('#callbackDate').value,
          callback_location: scrim.querySelector('#callbackPlace').value.trim(),
          message: scrim.querySelector('#callbackMessage').value.trim(),
        };
        if (!answer.callback_date && !answer.callback_location && !answer.message) {
          const error = scrim.querySelector('#callbackError');
          error.textContent = 'Add a date, a place or a message so the applicant knows what to expect.';
          error.hidden = false;
          return;
        }
        finish(answer);
      };
    });
  }

  Tutti.reviewCallbackDialog = { open };
})();
