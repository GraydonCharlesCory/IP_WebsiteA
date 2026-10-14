/* Markup and helpers shared by the public pages (home, section, profile): window.Tutti.parts.
   Requires util.js and components.js. Every function returns an escaped HTML string. */
(function () {
  const { esc, date, timeAgo, daysUntil } = Tutti.util;
  const { avatar, categoryTag, videoTile } = Tutti.components;

  const INSTRUMENT_FAMILIES = ['Saxophone', 'Trumpet', 'Trombone', 'Piano', 'Bass', 'Drums', 'Vocals', 'Violin', 'Viola', 'Cello',
    'Flute', 'Clarinet', 'Oboe', 'Bassoon', 'Horn', 'Tuba', 'Guitar', 'Harp', 'Percussion'];

  /* "Tenor & soprano saxophone" -> "Saxophone"; unknown instruments are kept as they are. */
  function instrumentFamily(instrument) {
    const text = String(instrument || '').toLowerCase();
    const family = INSTRUMENT_FAMILIES.find((name) => text.includes(name.toLowerCase()));
    return family || String(instrument || '');
  }

  const profileHref = (user) => `profile.html?h=${encodeURIComponent(user.handle)}`;
  const auditionHref = (audition) => `audition.html?id=${audition.id}`;

  function message(title, text, extra = '') {
    return `<div class="card pad empty"><h2>${esc(title)}</h2><p class="muted">${esc(text)}</p>${extra}</div>`;
  }

  const errorBox = (error) => message('We could not load this page', error.message || 'Something went wrong. Please try again.',
    '<p style="margin-top:16px"><a class="btn btn-ghost" href="">Try again</a></p>');

  const signInPrompt = (what) => message('Sign in to see this', `${what} are shown to signed-in users.`,
    '<p style="margin-top:16px"><a class="btn btn-primary" href="index.html">Sign in</a></p>');

  /* Run an async page task; a failure is logged and shown inside `container` instead of leaving a blank page. */
  async function guard(container, task) {
    try {
      return await task();
    } catch (error) {
      console.error('Tutti page error', error);
      container.innerHTML = errorBox(error);
      return undefined;
    }
  }

  /* Boot the shell on a public page, then render(user) inside `container` with failures shown there. */
  function bootPublicPage(container, active, render) {
    return Tutti.boot({ active, requireAuth: false })
      .then((user) => guard(container, () => render(user)))
      .catch((error) => {
        console.error('Tutti boot failed', error);
        container.innerHTML = errorBox(error);
      });
  }

  /* "Closes in 9 days" (warn) when close, "Closes Nov 30" otherwise. */
  function deadlineTag(audition) {
    if (audition.status !== 'open') return '<span class="tag grey">Closed</span>';
    const days = daysUntil(audition.deadline);
    return days <= 14
      ? `<span class="tag warn">${days <= 0 ? 'Closes today' : `Closes in ${days} day${days === 1 ? '' : 's'}`}</span>`
      : `<span class="tag grey">Closes ${esc(date(audition.deadline))}</span>`;
  }

  const directorLine = (audition) => esc([audition.director.name, audition.ensemble].filter(Boolean).join(' · '));

  /* Card in the open-auditions row. */
  function auditionCard(audition) {
    return `<a class="card aud" href="${auditionHref(audition)}">
      <div class="top">${categoryTag(audition.category)}${deadlineTag(audition)}</div>
      <h3>${esc(audition.title)}</h3>
      <div class="ens">${avatar(audition.director, 'sm')}${directorLine(audition)}</div>
      <div class="foot"><span>${esc(audition.instruments.join(', '))}</span><span>Closes ${esc(date(audition.deadline))}</span></div></a>`;
  }

  /* Compact row for a side column. */
  function auditionMini(audition) {
    return `<a class="mini-aud" href="${auditionHref(audition)}"><b>${esc(audition.title)}</b>
      <span>${esc(audition.ensemble || audition.director.name)} · closes ${esc(date(audition.deadline))}</span></a>`;
  }

  /* Audition shown as a post in the section feed. */
  function auditionPost(audition) {
    return `<article class="card post aud-post">
      <div class="post-head">${avatar(audition.director)}
        <div class="who"><div class="name">${esc(audition.ensemble || audition.director.name)} <span class="muted posted">posted an audition</span></div>
        <div class="meta">${esc(audition.director.name)}, Director · ${esc(timeAgo(audition.created))}</div></div>
        <span class="tag brass">Audition</span></div>
      <h3>${esc(audition.title)}</h3>
      <div class="row"><span>${esc(audition.instruments.join(', '))}</span><span>${deadlineTag(audition)}</span></div>
      <div><a class="btn btn-primary" href="${auditionHref(audition)}">View &amp; apply</a></div></article>`;
  }

  /* A clip post or text post. Call Tutti.components.wire() on the container afterwards. */
  function postCard(post, { showAuthor = true } = {}) {
    const author = post.author;
    const meta = [author.instrument, timeAgo(post.created)].filter(Boolean).map(esc).join(' · ');
    const head = showAuthor
      ? `${avatar(author)}<div class="who"><a class="name" href="${profileHref(author)}">${esc(author.name)}</a><div class="meta">${meta}</div></div>`
      : `<div class="who"><div class="meta">${esc(date(post.created))}</div></div>`;
    return `<article class="card post"><div class="post-head">${head}${categoryTag(post.category)}</div>
      <p class="post-body">${esc(post.body)}</p>${post.clip ? videoTile(post.clip) : ''}</article>`;
  }

  /* Small avatar + name + instrument row linking to a musician's profile. */
  function personRow(user) {
    return `<a class="person" href="${profileHref(user)}">${avatar(user, 'sm')}
      <div class="t"><b>${esc(user.name)}</b><span>${esc([user.instrument, user.location].filter(Boolean).join(' · '))}</span></div></a>`;
  }

  Tutti.parts = { instrumentFamily, profileHref, auditionHref, message, errorBox, signInPrompt, guard, bootPublicPage, deadlineTag,
    auditionCard, auditionMini, auditionPost, postCard, personRow };
})();
