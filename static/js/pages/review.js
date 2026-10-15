/* Submission review: review.html?id=<submission id>. Only the posting director may open it. */
(function () {
  const { queryParam } = Tutti.util;
  const { statusTag } = Tutti.components;
  const { privateNote, showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');
  const AUTOSAVE_DELAY_MS = 800;

  const onlyGiven = (scores) => Object.fromEntries(Object.entries(scores).filter(([, v]) => v !== null && v !== undefined));

  function pageMarkup(sub) {
    const header = Tutti.reviewHeader;
    return `<div class="wrap page">${header.markup(sub)}
      <div class="layout"><section id="playerRoot">
        <div class="player-tile"></div><div class="marker-strip" aria-label="Chapters and notes on the video timeline"></div><div class="chapter-list"></div>
        ${header.applicantRow(sub)}${header.applicantNoteAndClips(sub)}
      </section>
      <aside class="card panel">
        <div class="ph"><div style="display:flex;justify-content:space-between;align-items:center"><h3>Your evaluation</h3>${privateNote('Private to you')}</div></div>
        <div class="overall"><div class="big" id="avg"></div><div><b>Overall score</b><div class="small muted">Average of the criteria you score · auto-saved</div></div></div>
        <div class="rub" id="rub"></div>
        <div class="cm"><div class="field"><label for="comments">Comments</label><textarea class="input" id="comments" style="min-height:150px"></textarea></div>
          <div id="notesRoot"></div></div>
        <div class="dec" id="decisionRoot"></div>
        <div class="saved" id="saved" role="status"></div>
        <div class="fb" id="feedbackRoot"></div>
      </aside></div></div>`;
  }

  async function revealIdentity(sub) {
    const confirmed = await Tutti.confirmDialog({
      title: 'Reveal this applicant?', body: 'You will see their name, photo and public clips. Other applicants stay anonymous, and this cannot be undone.', confirmLabel: 'Reveal identity',
    });
    if (!confirmed) return;
    try {
      start((await api.revealApplicant(sub.id)).submission);
      Tutti.toast('Identity revealed.', 'ok');
    } catch (error) { Tutti.reportError(error, 'reveal identity'); }
  }

  function start(sub) {
    document.title = `Tutti — Review ${sub.musician.name}`;
    root.innerHTML = pageMarkup(sub);
    const review = sub.review || { scores: {}, comments: '', notes: [], decision: null };
    const save = Tutti.reviewSaver.create(sub.id);
    const currentNotes = [...review.notes];
    const comments = document.getElementById('comments');
    comments.value = review.comments || '';
    let player = null;
    let feedbackUi = null;
    let timer = null;

    const getFields = () => ({ scores: onlyGiven(scoresUi.scores()), comments: comments.value, notes: currentNotes });
    const scoresUi = Tutti.reviewScores.mount(document.getElementById('rub'), review.scores, () => { queueAutosave(); feedbackUi.refresh(); });
    function queueAutosave() {
      clearTimeout(timer);
      timer = setTimeout(() => save({ scores: getFields().scores, comments: comments.value }), AUTOSAVE_DELAY_MS);
    }
    comments.addEventListener('input', () => { queueAutosave(); feedbackUi.refresh(); });

    const notesUi = Tutti.reviewNotes.mount(document.getElementById('notesRoot'), review.notes, {
      getTime: () => (player ? player.currentTime() : 0),
      seek: (seconds) => player && player.seek(seconds),
      onChange: async (notes) => {
        currentNotes.splice(0, currentNotes.length, ...notes);
        player.drawMarkers();
        feedbackUi.refresh();
        await save({ notes }, '✓ Note saved');
      },
    });
    player = Tutti.reviewPlayer.mount(document.getElementById('playerRoot'), sub, { badge: statusTag(sub.status), getNotes: () => currentNotes, onTime: () => notesUi.followVideo() });

    const saveBeforeAction = async (fields) => { clearTimeout(timer); return save(fields); };
    Tutti.reviewDecision.mount(document.getElementById('decisionRoot'), {
      submission: sub,
      getFields: () => { clearTimeout(timer); return getFields(); },
      save,
      onStatus: (status) => { document.querySelector('.video .badge').innerHTML = statusTag(status); },
    });
    feedbackUi = Tutti.reviewFeedback.mount(document.getElementById('feedbackRoot'), {
      submission: sub,
      getReview: () => ({ ...getFields(), notes: currentNotes }),
      ensureSaved: async () => Boolean(await saveBeforeAction(getFields())),
    });
    if (sub.review) document.getElementById('saved').className = 'saved';
    const reveal = document.getElementById('revealButton');
    if (reveal) reveal.onclick = () => revealIdentity(sub);
  }

  async function load() {
    const id = Number(queryParam('id'));
    if (!id) throw new Error('This link has no submission in it. Open a submission from your dashboard.');
    start((await api.submission(id)).submission);
  }

  Tutti.boot({ active: 'dashboard', requireRole: 'director' })
    .then(load)
    .catch((error) => showFailure(error, { title: error.status === 403 ? 'This submission is private' : 'This submission could not be loaded', backHref: 'director.html', backLabel: 'Back to my auditions' }));
})();
