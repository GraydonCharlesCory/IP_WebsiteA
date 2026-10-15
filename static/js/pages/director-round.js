/* Round format line and Blind review switch for one audition on the dashboard: Tutti.directorRound */
(function () {
  const { esc, date } = Tutti.util;

  /* "Video pre-screen → live callback on Dec 10, Bayview Hall" or a plain description when there is no video round */
  function formatText(audition) {
    const callback = audition.callback;
    const live = callback ? `live callback on ${[date(callback.date), callback.location].filter(Boolean).join(', ')}` : 'live round to be announced';
    return audition.video_round_accepted ? `Video pre-screen → ${live}` : `Live audition · ${callback ? live : 'details to be announced'}`;
  }

  const roundMarkup = (audition) => `<div class="round"><div class="eyebrow">Round format</div><p>${esc(formatText(audition))}</p></div>
    <label class="switch"><input type="checkbox" id="blindSwitch" ${audition.blind_review ? 'checked' : ''}><span class="track"></span>
      <span><b>Blind review</b>Names and photos are hidden while you score. Turning it off reveals every applicant.</span></label>`;

  /* Wires the switch inside root. onChange(auditionId, enabled) must persist and return a promise; the switch is restored on failure. */
  function wireSwitch(root, audition, onChange) {
    const input = root.querySelector('#blindSwitch');
    input.onchange = async () => {
      const wanted = input.checked;
      input.disabled = true;
      try {
        const confirmed = wanted || await Tutti.confirmDialog({
          title: 'Turn blind review off?', body: 'Every applicant for this audition will be shown with their name and photo from now on. This cannot be undone.', confirmLabel: 'Turn off and reveal all',
        });
        if (!confirmed) { input.checked = true; return; }
        await onChange(audition.id, wanted);
      } catch (error) {
        input.checked = !wanted;
        Tutti.reportError(error, 'change blind review');
      } finally { input.disabled = false; }
    };
  }

  Tutti.directorRound = { formatText, roundMarkup, wireSwitch };
})();
