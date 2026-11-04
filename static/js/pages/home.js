/* Home: section cards, open auditions, trending clips. */
(function () {
  const { esc, section } = Tutti.util;
  const { avatar } = Tutti.components;
  const { profileHref, auditionCard, signInPrompt, message } = Tutti.parts;
  const content = document.getElementById('content');

  /* A still first frame of the section's newest playable clip, or a coloured gradient when there is none. */
  function sectionMedia(clip) {
    return clip && clip.available ? `<video class="cat-media" preload="metadata" muted playsinline src="${esc(clip.video_url)}#t=0.5"></video>` : '<div class="cat-media"></div>';
  }

  function sectionCard(info, clips) {
    const style = section(info.key);
    const clip = clips.find((c) => c.category === info.key && c.available);
    const plural = (count, word) => `<span><b>${count}</b> ${word}${count === 1 ? '' : 's'}</span>`;
    return `<a class="cat" href="section.html?s=${info.key}" style="--acc:var(--${style.css})">${sectionMedia(clip)}<div class="shade"></div><span class="bar"></span>
      <span class="tag ${style.css}">${esc(info.label)}</span><h2>${esc(info.label)}</h2><p class="t2">${esc(info.blurb)}</p>
      <div class="nums">${plural(info.musicians, 'musician')}${plural(info.auditions, 'open audition')}</div><span class="enter">Enter section →</span></a>`;
  }

  function trendingClip(clip) {
    return `<div class="clip">${Tutti.components.videoTile(clip)}
      <a class="cap" href="${profileHref(clip.owner)}">${avatar(clip.owner, 'sm')}<div><b>${esc(clip.title)}</b><span>${esc(clip.owner.name)}</span></div></a></div>`;
  }

  function rowHead(eyebrow, title) {
    return `<div class="row-head"><div><div class="eyebrow">${eyebrow}</div><h2>${title}</h2></div></div>`;
  }

  function auditionsRow(user, auditions) {
    const body = !user ? signInPrompt('Audition postings')
      : !auditions.length ? message('No open auditions right now', 'New postings from directors will show up here.')
        : `<div class="auds">${auditions.map(auditionCard).join('')}</div>`;
    return rowHead(user ? 'Directors are listening' : 'Members only', 'Open auditions') + body;
  }

  function greeting(user) {
    const today = new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    const hello = user ? `Welcome back, ${esc(user.name.split(' ')[0])}.` : 'Where musicians get heard.';
    return `<div class="greet"><div class="eyebrow">${esc(today)}</div><h1>${hello}</h1>
      <p class="t2" style="margin-top:6px">Browse the sections, watch the latest clips and find your next audition.</p></div>`;
  }

  async function render(user) {
    const [{ sections }, { clips }, auditions] = await Promise.all([
      api.sections(), api.clips({ limit: 12 }),
      user ? api.auditions().then((r) => r.auditions.filter((a) => a.status === 'open')) : Promise.resolve([]),
    ]);
    const trending = clips.filter((c) => c.owner).slice(0, 4);
    content.innerHTML = `<main class="wrap page">${greeting(user)}
      <div class="cats">${sections.map((s) => sectionCard(s, clips)).join('')}</div>
      ${auditionsRow(user, auditions.slice(0, 3))}
      ${rowHead('Across Tutti', 'Trending clips')}
      ${trending.length ? `<div class="clips">${trending.map(trendingClip).join('')}</div>` : message('No clips yet', 'Clips musicians post will appear here.')}
      </main>`;
    Tutti.components.wire(content);
  }

  Tutti.parts.bootPublicPage(content, 'home', render);
})();
