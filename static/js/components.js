/* Shared UI components. Each returns an HTML string (escaped); call Tutti.components.wire(root) after inserting
   them so video tiles become playable. Requires util.js. */
(function () {
  const { esc, section } = Tutti.util;
  const ICON_PLAY = '<svg viewBox="0 0 24 24" fill="#fff"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z"/></svg>';

  function avatar(user, size = '') {
    return `<div class="av ${size} g${user.avatar_style || 1}" title="${esc(user.name)}">${esc(user.initials)}</div>`;
  }

  /* <span class="tag jazz">Jazz</span> for a category key */
  function categoryTag(key) {
    const s = section(key);
    return `<span class="tag ${s.css}">${esc(s.label)}</span>`;
  }

  function dot(key) {
    return `<span class="dot ${section(key).css}"></span>`;
  }

  /* Submission status as a tag. Musicians only ever get "Submitted". */
  function statusTag(status) {
    const map = { new: ['brass', 'New'], shortlisted: ['ok', 'Shortlisted'], passed: ['grey', 'Passed'], Submitted: ['ok', 'Submitted'], open: ['ok', 'Open'], closed: ['grey', 'Closed'] };
    const [css, label] = map[status] || ['grey', status];
    return `<span class="tag ${css}">${esc(label)}</span>`;
  }

  function placeholderTile(title) {
    return `<div class="clip-soon"><div class="clip-soon-icon">♪</div><b>Clip coming soon</b><span>${esc(title || '')}</span></div>`;
  }

  /* Video tile. clip = {video_url, available, title}. Shows the real first frame (#t=0.5) as the poster; clicking plays it.
     options: {big, badge (html), duration (text), src (override url, e.g. an authorized submission stream)} */
  function videoTile(clip, options = {}) {
    const url = options.src || clip.video_url;
    const available = options.src ? true : clip.available;
    const badge = options.badge ? `<div class="badge">${options.badge}</div>` : '';
    if (!available) return `<div class="video ${options.big ? 'big' : ''} missing">${placeholderTile(clip.title)}${badge}</div>`;
    return `<div class="video ${options.big ? 'big' : ''}" data-playable>
      <video class="poster" preload="metadata" playsinline src="${esc(url)}#t=0.5"></video>
      <div class="play">${ICON_PLAY}</div>${badge}</div>`;
  }

  /* Clip card: tile plus title and owner line. */
  function clipCard(clip) {
    const owner = clip.owner ? `<span class="muted small">${esc(clip.owner.name)}</span>` : '';
    return `<div class="clip-card">${videoTile(clip)}<div class="clip-card-title">${esc(clip.title)}</div>${owner}</div>`;
  }

  function wire(root = document) {
    root.querySelectorAll('.video[data-playable]:not([data-wired])').forEach((tile) => {
      tile.dataset.wired = '1';
      const video = tile.querySelector('video');
      video.addEventListener('loadedmetadata', () => {
        if (!tile.querySelector('.dur') && Number.isFinite(video.duration)) {
          tile.insertAdjacentHTML('beforeend', `<div class="dur">${Tutti.util.duration(video.duration)}</div>`);
        }
      });
      video.addEventListener('error', () => {
        console.error('Tutti: video failed to load', video.currentSrc);
        tile.classList.add('missing');
        tile.removeAttribute('data-playable');
        tile.innerHTML = placeholderTile('This video could not be played');
      });
      tile.addEventListener('click', () => {
        if (video.controls) return;
        video.controls = true;
        tile.classList.add('playing');
        video.play().catch((error) => Tutti.toast(`Could not play this video: ${error.message}`, 'error'));
      });
    });
  }

  Tutti.components = { avatar, categoryTag, dot, statusTag, placeholderTile, videoTile, clipCard, wire };
})();
