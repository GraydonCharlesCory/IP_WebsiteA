/* "Endorse" dialog on someone else's profile: Tutti.endorseDialog.open(musician, onEndorsed). Directors and teachers only. */
(function () {
  const { esc } = Tutti.util;
  const { openScrim } = Tutti.dialogParts;

  function open(musician, onEndorsed) {
    const state = { busy: false, error: '' };
    const { scrim, close } = openScrim(() => state.busy);

    function render() {
      const error = state.error ? `<div class="form-error" role="alert">${esc(state.error)}</div>` : '';
      scrim.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="dialogTitle" style="max-width:480px">
        <div class="mhead"><div><div class="eyebrow">Professional connection</div><h3 style="margin-top:4px" id="dialogTitle">${esc(musician.name)}</h3></div>
          <button id="dialogClose" class="t2" style="font-size:22px" aria-label="Close" ${state.busy ? 'disabled' : ''}>×</button></div>
        <div class="mbody">
          <div class="field"><label for="relationshipInput">How do you know them?</label>
            <input class="input" id="relationshipInput" maxlength="120" placeholder="e.g. Hired her as a sub, taught him for two years"></div>
          <div class="field"><label for="endorseText">Connection description</label>
            <textarea class="input" id="endorseText" maxlength="600" placeholder="Describe your professional or educational relationship. No advertising."></textarea></div>${error}</div>
        <div class="mfoot"><span class="small muted">Shown publicly on their profile.</span>
          <button class="btn btn-primary" id="endorseSubmit" ${state.busy ? 'disabled' : ''}>${state.busy ? 'Posting…' : 'Post connection'}</button></div></div>`;
      scrim.querySelector('#dialogClose').onclick = close;
      scrim.querySelector('#endorseSubmit').onclick = submit;
    }

    async function submit() {
      const text = scrim.querySelector('#endorseText').value.trim();
      const relationship = scrim.querySelector('#relationshipInput').value.trim();
      if (!text) { state.error = 'Write a sentence or two before posting.'; return render(); }
      state.busy = true; state.error = ''; render();
      try {
        await api.endorse(musician.handle, text, relationship);
        close();
        onEndorsed();
      } catch (error) {
        console.error('Tutti endorse failed', error);
        Object.assign(state, { busy: false, error: error.message || 'The endorsement could not be saved. Please try again.' });
        render();
      }
    }

    render();
  }

  Tutti.endorseDialog = { open };
})();
