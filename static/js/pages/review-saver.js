/* Review auto-save with a saving/saved/failed indicator: Tutti.reviewSaver.create(submissionId) -> save(fields, successText) -> saved review or null */
(function () {
  function create(submissionId) {
    const show = (text, failed = false) => {
      const el = document.getElementById('saved');
      el.textContent = text;
      el.className = `saved on${failed ? ' failed' : ''}`;
    };
    return async function save(fields, successText = '✓ Saved') {
      show('Saving…');
      try {
        const saved = await api.saveReview(submissionId, fields);
        show(successText);
        return saved;
      } catch (error) {
        console.error('Tutti review save failed', error);
        const hint = error.status === 403 ? 'Only the director who posted this audition can score it.' : 'Your changes are still on screen, so try again.';
        show(`Not saved: ${error.message} ${hint}`, true);
        Tutti.toast(`Not saved: ${error.message}`, 'error');
        return null;
      }
    };
  }

  Tutti.reviewSaver = { create };
})();
