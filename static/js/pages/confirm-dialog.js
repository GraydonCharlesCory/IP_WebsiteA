/* Small yes/no dialog: Tutti.confirmDialog({title, body, confirmLabel}) resolves true or false. Needs dialog-parts.js and submit-dialog.css. */
(function () {
  const { esc } = Tutti.util;

  function confirmDialog({ title, body, confirmLabel = 'Confirm' }) {
    return new Promise((resolve) => {
      const { scrim, close } = Tutti.dialogParts.openScrim(() => false);
      const finish = (answer) => { close(); resolve(answer); };
      scrim.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="confirmTitle" style="max-width:480px">
        <div class="mhead"><h3 id="confirmTitle">${esc(title)}</h3></div>
        <div class="mbody"><p class="t2">${esc(body)}</p></div>
        <div class="mfoot"><button class="btn btn-ghost" data-answer="no">Cancel</button><button class="btn btn-primary" data-answer="yes">${esc(confirmLabel)}</button></div></div>`;
      scrim.querySelectorAll('[data-answer]').forEach((button) => { button.onclick = () => finish(button.dataset.answer === 'yes'); });
      scrim.onclick = (event) => { if (event.target === scrim) finish(false); };
      scrim.querySelector('[data-answer="yes"]').focus();
    });
  }

  Tutti.confirmDialog = confirmDialog;
})();
