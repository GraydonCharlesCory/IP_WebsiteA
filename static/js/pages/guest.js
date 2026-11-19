/* Capability is held in the fragment, never a query string or media URL. */
(function () {
  const { esc } = Tutti.util;
  const key = location.hash.slice(1);
  history.replaceState(null, '', location.pathname);
  const root = document.getElementById('pageRoot');
  async function request(path, body) {
    const response = await fetch(path, { method: body ? 'PUT' : 'GET', headers: { 'X-Review-Key': key, 'Content-Type': 'application/json' }, ...(body ? { body: JSON.stringify(body) } : {}) });
    if (!response.ok) { const data = await response.json(); throw new Error(data.error || 'Guest review failed. Ask the organizer for a current link.'); }
    return response;
  }
  async function load() {
    const data = await (await request('/api/guest')).json();
    root.innerHTML = `<main class="wrap page"><h1>${esc(data.title)}</h1><p>${data.blind_review ? 'Blind guest review: identity and applicant free text are withheld. Audio only.' : 'Nonblind guest review.'} Your scores contribute privately to the creator’s composite. No other reviews or composites are shown.</p>${data.submissions.map(s => `<article class="card pad" data-id="${s.id}"><h2>${esc(s.musician.name)}</h2><p>${esc(s.musician.instrument)}</p><button class="btn btn-ghost" data-play>Load recording</button><div data-media></div><form>${data.rubric.map(k => `<label class="field">${esc(k.replaceAll('_',' '))}<input class="input" name="${esc(k)}" type="number" min="1" max="10" step="1" required value="${s.scores?.[k] || ''}"></label>`).join('')}<button class="btn btn-primary">Save scores</button><span role="status"></span></form></article>`).join('') || '<p>No submissions yet.</p>'}</main>`;
    root.querySelectorAll('article').forEach(card => {
      const id = card.dataset.id;
      card.querySelector('form').onsubmit = async event => {
        event.preventDefault();
        try {
          await request(`/api/guest/submissions/${id}/score`, { scores: Object.fromEntries([...new FormData(event.target)].map(([k,v]) => [k,Number(v)])) });
          card.querySelector('[role="status"]').textContent = ' Scores saved.';
        } catch (error) { Tutti.reportError(error, 'save guest scores'); }
      };
      card.querySelector('[data-play]').onclick = async () => {
        try {
          const response = await request(`/api/guest/submissions/${id}/audio`);
          const url = URL.createObjectURL(await response.blob());
          const media = document.createElement(data.blind_review ? 'audio' : 'video');
          media.controls = true; media.src = url;
          media.onerror = () => Tutti.reportError(new Error('Recording could not be decoded. Ask the organizer to check the upload.'), 'guest media');
          window.addEventListener('pagehide', () => URL.revokeObjectURL(url), { once: true });
          card.querySelector('[data-media]').replaceChildren(media);
        } catch (error) { Tutti.reportError(error, 'load guest recording'); }
      };
    });
  }
  load().catch(Tutti.pageUtil.showFailure);
})();
