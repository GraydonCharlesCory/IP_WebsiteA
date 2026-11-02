/* Audio-only player for blind review, with a marker strip and chapter buttons: Tutti.reviewPlayer.mount(root, submission, opts).
   Directors never get a picture of the applicant, so this renders an <audio> element and a neutral placeholder, never a <video>.
   Every chapter and note time is clamped to the clip: anything outside 0..duration is hidden. */
(function () {
  const { esc, duration } = Tutti.util;

  const placeholderTitle = (submission) => `${esc(submission.musician.label)} — audio only`;

  function tileMarkup(submission, badge) {
    const player = submission.has_audio
      ? `<audio controls preload="metadata" src="${esc(submission.audio_url)}"></audio>`
      : '<p class="small muted">This recording is not available yet.</p>';
    return `<div class="audio-tile"><div class="audio-badge">${badge || ''}</div><div class="audio-icon" aria-hidden="true">🎧</div>
      <b>${placeholderTitle(submission)}</b>${player}</div>`;
  }

  const insideClip = (time, length) => time >= 0 && (!length || time <= length);

  function chapterMarkup(chapters) {
    return chapters.length
      ? `<div class="chapters">${chapters.map((c) => `<button type="button" class="chap" data-seek="${c.time}"><b>${duration(c.time)}</b>${esc(c.label)}</button>`).join('')}</div>` : '';
  }

  /* The element must contain: .player-tile, .marker-strip, .chapter-list */
  function mount(root, submission, { badge, getNotes, onTime }) {
    const tile = root.querySelector('.player-tile');
    tile.innerHTML = tileMarkup(submission, badge);
    const audio = tile.querySelector('audio');
    const strip = root.querySelector('.marker-strip');
    const clipLength = () => (audio && Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : submission.duration || 0);
    const chapters = () => submission.timestamps.filter((c) => insideClip(c.time, clipLength()));
    const notes = () => getNotes().filter((n) => insideClip(n.time, clipLength()));
    const drawChapters = () => { root.querySelector('.chapter-list').innerHTML = chapterMarkup(chapters()); };
    drawChapters();
    if (!audio) return { currentTime: () => 0, seek: () => {}, drawMarkers: () => {}, duration: clipLength };

    const seek = (seconds) => {
      audio.currentTime = Math.min(Math.max(seconds, 0), clipLength() || seconds);
      audio.play().catch((error) => Tutti.reportError(error, 'play from marker'));
    };
    const drawMarkers = () => {
      const length = clipLength();
      if (!length) { strip.innerHTML = ''; return; }
      const marker = (time, kind, title) => `<button type="button" class="marker ${kind}" style="left:${(time / length) * 100}%" data-seek="${time}" title="${esc(title)}" aria-label="${esc(title)}"></button>`;
      strip.innerHTML = chapters().map((c) => marker(c.time, 'chapter', `${duration(c.time)} ${c.label}`)).join('')
        + notes().map((n) => marker(n.time, 'note', `${duration(n.time)} ${n.text}`)).join('');
    };
    audio.addEventListener('loadedmetadata', () => { drawChapters(); drawMarkers(); });
    audio.addEventListener('error', () => {
      console.error('Tutti: audio failed to load', audio.currentSrc);
      Tutti.toast('This recording could not be played. Try again, or open the next submission.', 'error');
    });
    audio.addEventListener('timeupdate', () => {
      const now = audio.currentTime;
      const active = chapters().filter((c) => c.time <= now).length - 1;
      root.querySelectorAll('.chap').forEach((el, i) => el.classList.toggle('on', i === active));
      onTime(now);
    });
    root.addEventListener('click', (event) => {
      const target = event.target.closest('.chap[data-seek], .marker[data-seek]');
      if (target) seek(Number(target.dataset.seek));
    });
    drawMarkers();
    return { currentTime: () => audio.currentTime || 0, seek, drawMarkers, duration: clipLength };
  }

  Tutti.reviewPlayer = { mount };
})();
