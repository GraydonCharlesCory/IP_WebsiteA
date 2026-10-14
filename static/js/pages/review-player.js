/* Video with a marker strip and chapter buttons: Tutti.reviewPlayer.mount(root, submission, {onTime}) */
(function () {
  const { esc, duration } = Tutti.util;
  const { videoTile, wire } = Tutti.components;

  function tileMarkup(submission, badge) {
    const clip = { title: `${submission.musician.name}'s clip`, available: submission.has_video };
    return videoTile(clip, { big: true, badge, src: submission.has_video ? api.submissionVideoUrl(submission.id) : undefined });
  }

  const chapterMarkup = (chapters) => chapters.length
    ? `<div class="chapters">${chapters.map((c) => `<button type="button" class="chap" data-seek="${c.time}"><b>${duration(c.time)}</b>${esc(c.label)}</button>`).join('')}</div>` : '';

  /* The element must contain: .player-tile, .marker-strip, .chapter-list */
  function mount(root, submission, { badge, getNotes, onTime }) {
    const tile = root.querySelector('.player-tile');
    tile.innerHTML = tileMarkup(submission, badge);
    wire(tile);
    root.querySelector('.chapter-list').innerHTML = chapterMarkup(submission.timestamps);
    const video = tile.querySelector('video');
    const strip = root.querySelector('.marker-strip');
    if (!video) return { currentTime: () => 0, seek: () => {}, drawMarkers: () => {} };

    const seek = (seconds) => {
      if (!video.controls) tile.querySelector('.video').click();
      video.currentTime = seconds;
      video.play().catch((error) => Tutti.reportError(error, 'play from marker'));
    };
    const drawMarkers = () => {
      if (!Number.isFinite(video.duration) || !video.duration) return;
      const marker = (time, kind, title) => `<button type="button" class="marker ${kind}" style="left:${Math.min(100, (time / video.duration) * 100)}%" data-seek="${time}" title="${esc(title)}" aria-label="${esc(title)}"></button>`;
      strip.innerHTML = submission.timestamps.map((c) => marker(c.time, 'chapter', `${duration(c.time)} ${c.label}`)).join('')
        + getNotes().map((n) => marker(n.time, 'note', `${duration(n.time)} ${n.text}`)).join('');
    };
    video.addEventListener('loadedmetadata', drawMarkers);
    video.addEventListener('timeupdate', () => {
      const now = video.currentTime;
      const active = submission.timestamps.filter((c) => c.time <= now).length - 1;
      root.querySelectorAll('.chap').forEach((el, i) => el.classList.toggle('on', i === active));
      onTime(now);
    });
    root.addEventListener('click', (event) => {
      const target = event.target.closest('.chap[data-seek], .marker[data-seek]');
      if (target) seek(Number(target.dataset.seek));
    });
    drawMarkers();
    return { currentTime: () => video.currentTime || 0, seek, drawMarkers };
  }

  Tutti.reviewPlayer = { mount };
})();
