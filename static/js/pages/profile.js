/* Musician profile: profile.html?h=<handle>. Public. A director's handle shows a short director card. */
(function () {
  const { esc, section, queryParam, date } = Tutti.util;
  const { avatar, categoryTag, videoTile, clipCard } = Tutti.components;
  const { postCard, message } = Tutti.parts;
  const content = document.getElementById('content');
  const handle = queryParam('h');

  const kvRows = (rows) => rows.filter(([, value]) => value).map(([label, value]) => `<div><span>${label}</span>${esc(value)}</div>`).join('');
  const card = (title, body) => `<div class="card pad"><h3>${title}</h3>${body}</div>`;

  function featured(clip) {
    return `<div class="feat">${videoTile(clip, { big: true, badge: '<span class="tag brass">★ Featured</span>' })}
      <div><h3>${esc(clip.title)}</h3><p class="small muted">${esc([clip.instrument, `Posted ${date(clip.created)}`].join(' · '))}</p></div></div>`;
  }

  function clipsSection(clips) {
    if (!clips.length) return message('No clips yet', 'This musician has not posted a clip.');
    const rest = clips.slice(1);
    return featured(clips[0]) + (rest.length ? `<div class="cgrid">${rest.map(clipCard).join('')}</div>` : '');
  }

  function postsSection(posts, musician) {
    if (!posts.length) return '';
    return `<section class="posts"><h2>Recent posts</h2>${posts.slice(0, 5).map((post) => postCard({ ...post, author: musician }, { showAuthor: false })).join('')}</section>`;
  }

  function sidebar(musician) {
    const details = kvRows([['Instrument', musician.instrument], ['Section', section(musician.category).label], ['Location', musician.location], ['Ensemble', musician.ensemble]]);
    return `<aside class="side">${card('About', `<p class="t2 small">${esc(musician.bio || 'This musician has not written a bio yet.')}</p>`)}${card('Details', `<div class="kv">${details}</div>`)}</aside>`;
  }

  function renderMusician({ musician, clips, posts, stats }) {
    const facts = [musician.instrument, musician.location, musician.ensemble].filter(Boolean).map((f) => `<span>${esc(f)}</span>`).join('');
    document.title = `Tutti — ${musician.name}`;
    document.documentElement.style.setProperty('--acc', `var(--${section(musician.category).css})`);
    content.innerHTML = `<div class="cover"></div><main class="wrap">
      <div class="idrow">${avatar(musician, 'lg')}<div class="who"><div class="name-row"><h1>${esc(musician.name)}</h1>${categoryTag(musician.category)}</div><div class="facts">${facts}</div></div></div>
      <div class="stats"><div><b>${stats.clips}</b><span>Clips</span></div><div><b>${stats.posts}</b><span>Posts</span></div></div>
      <div class="layout"><div>${clipsSection(clips)}${postsSection(posts, musician)}</div>${sidebar(musician)}</div></main>`;
    Tutti.components.wire(content);
  }

  /* /api/musicians/<handle> only knows musicians; a director's handle is looked up in the public account list. */
  async function renderDirectorOrMissing() {
    const { directors } = await api.accounts();
    const director = directors.find((d) => d.handle === handle);
    document.documentElement.style.setProperty('--acc', `var(--${section(director ? director.category : '').css})`);
    content.innerHTML = `<main class="wrap page">${director
      ? `<div class="card pad director-card">${avatar(director, 'lg')}<h1>${esc(director.name)}</h1><span class="role-pill">Director</span>
         <p class="t2">${esc([director.instrument, director.ensemble].filter(Boolean).join(' · '))}</p>
         <p class="muted small">Directors post auditions rather than clips. Their open auditions are in the ${esc(section(director.category).label)} section.</p>
         <a class="btn btn-primary" href="section.html?s=${esc(director.category)}#auditions">See ${esc(section(director.category).label)} auditions</a></div>`
      : message('Profile not found', 'No musician has that handle.', '<p style="margin-top:16px"><a class="btn btn-ghost" href="home.html">Back to home</a></p>')}</main>`;
  }

  async function load() {
    if (!handle) return renderDirectorOrMissing();
    try {
      renderMusician(await api.musician(handle));
    } catch (error) {
      if (error.status !== 404) throw error;
      await renderDirectorOrMissing();
    }
    return undefined;
  }

  Tutti.parts.bootPublicPage(content, '', load);
})();
