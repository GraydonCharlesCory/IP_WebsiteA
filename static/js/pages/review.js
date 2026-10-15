/* Submission review: review.html?id=<submission id>. Only the posting director may open it. */
(function () {
  const { esc, queryParam, timeAgo } = Tutti.util;
  const { avatar, statusTag, clipCard, wire } = Tutti.components;
  const { privateNote, showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');
  const AUTOSAVE_DELAY_MS = 800;

  function pageMarkup(sub) {
    const m = sub.musician;
    const pagerLink = (id, label) => id ? `<a class="btn btn-ghost" style="height:34px" href="review.html?id=${id}">${label}</a>` : `<span class="btn btn-ghost disabled" style="height:34px">${label}</span>`;
    const clips = sub.musician_clips.filter((c) => c.available).slice(0, 3);
    return `<div class="wrap page">
      <div class="bar-top"><div class="crumb"><a href="director.html">My auditions</a> / <a href="director.html?audition=${sub.audition.id}">${esc(sub.audition.title)}</a> / ${esc(m.name)}</div>
        <div class="pager">${pagerLink(sub.previous_id, '← Prev')}Submission ${sub.position} of ${sub.total}${pagerLink(sub.next_id, 'Next →')}</div></div>
      <div class="layout"><section id="playerRoot">
        <div class="player-tile"></div><div class="marker-strip" aria-label="Chapters and notes on the video timeline"></div><div class="chapter-list"></div>
        <div class="mrow">${avatar(m)}<div class="t"><b style="font-size:17px">${esc(m.name)}</b>
          <div class="small muted">${esc([m.instrument, m.location].filter(Boolean).join(' · '))} · submitted ${timeAgo(sub.created)}</div></div>
          ${m.handle ? `<a class="btn btn-ghost" href="profile.html?h=${encodeURIComponent(m.handle)}">View public profile</a>` : ''}</div>
        ${sub.note ? `<div class="note"><div class="eyebrow">Note from ${esc(m.name.split(' ')[0])}</div><p>${esc(sub.note)}</p></div>` : ''}
        ${clips.length ? `<div style="margin-top:26px"><div class="eyebrow" style="margin-bottom:12px">${esc(m.name.split(' ')[0])}'s public clips</div><div class="clip-row">${clips.map(clipCard).join('')}</div></div>` : ''}
      </section>
      <aside class="card panel">
        <div class="ph"><div style="display:flex;justify-content:space-between;align-items:center"><h3>Your evaluation</h3>${privateNote('Private to you')}</div></div>
        <div class="overall"><div class="big" id="avg"></div><div><b>Overall score</b><div class="small muted">Average of the criteria you score · auto-saved</div></div></div>
        <div class="rub" id="rub"></div>
        <div class="cm"><div class="field"><label for="comments">Comments</label><textarea class="input" id="comments" style="min-height:150px"></textarea></div>
          <div id="notesRoot"></div></div>
        <div class="pf"><button class="btn btn-ghost" id="passButton">Pass</button><button class="btn btn-primary" id="shortlistButton">★ Shortlist &amp; save</button></div>
        <div class="saved" id="saved" role="status"></div>
      </aside></div></div>`;
  }

  /* Sends partial review fields; shows saving/saved/failed state in the panel. Returns the saved review or null on failure. */
  function createSaver(submissionId) {
    const indicator = () => document.getElementById('saved');
    const show = (text, failed = false) => { const el = indicator(); el.textContent = text; el.className = `saved on${failed ? ' failed' : ''}`; };
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

  function start(sub) {
    document.title = `Tutti — Review ${sub.musician.name}`;
    root.innerHTML = pageMarkup(sub);
    const review = sub.review || { scores: {}, comments: '', notes: [], decision: null };
    const save = createSaver(sub.id);
    const first = sub.musician.name.split(' ')[0];
    let player = null;
    let notesUi = null;
    let timer = null;
    const comments = document.getElementById('comments');
    comments.value = review.comments || '';

    const scoresUi = Tutti.reviewScores.mount(document.getElementById('rub'), review.scores, () => queueAutosave());
    const currentNotes = [];
    function queueAutosave() {
      clearTimeout(timer);
      timer = setTimeout(() => save({ scores: onlyGiven(scoresUi.scores()), comments: comments.value }), AUTOSAVE_DELAY_MS);
    }
    comments.addEventListener('input', queueAutosave);

    notesUi = Tutti.reviewNotes.mount(document.getElementById('notesRoot'), review.notes, {
      getTime: () => (player ? player.currentTime() : 0),
      seek: (seconds) => player && player.seek(seconds),
      onChange: async (notes) => {
        currentNotes.splice(0, currentNotes.length, ...notes);
        player.drawMarkers();
        await save({ notes }, '✓ Note saved');
      },
    });
    currentNotes.push(...review.notes);
    const badge = statusTag(sub.status);
    player = Tutti.reviewPlayer.mount(document.getElementById('playerRoot'), sub, { badge, getNotes: () => currentNotes, onTime: () => notesUi.followVideo() });

    async function decide(decision) {
      clearTimeout(timer);
      const text = decision === 'shortlist' ? `✓ Saved · ${first} moved to your shortlist` : `✓ Saved · ${first} passed`;
      const saved = await save({ scores: onlyGiven(scoresUi.scores()), comments: comments.value, notes: currentNotes, decision }, text);
      if (saved) {
        Tutti.toast(text.replace('✓ ', ''), 'ok');
        document.querySelector('.video .badge').innerHTML = statusTag(saved.status);
      }
    }
    document.getElementById('shortlistButton').onclick = () => decide('shortlist');
    document.getElementById('passButton').onclick = () => decide('pass');
    if (sub.review) document.getElementById('saved').className = 'saved';
  }

  const onlyGiven = (scores) => Object.fromEntries(Object.entries(scores).filter(([, v]) => v !== null && v !== undefined));

  async function load() {
    const id = Number(queryParam('id'));
    if (!id) throw new Error('This link has no submission in it. Open a submission from your dashboard.');
    start((await api.submission(id)).submission);
  }

  Tutti.boot({ active: 'dashboard', requireRole: 'director' })
    .then(load)
    .catch((error) => showFailure(error, error.status === 403
      ? { title: 'This submission is private', backHref: 'director.html', backLabel: 'Back to my auditions' }
      : { title: 'This submission could not be loaded', backHref: 'director.html', backLabel: 'Back to my auditions' }));
})();
