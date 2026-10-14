/* Audition posting: audition.html?id=<audition id> */
(function () {
  const { esc, date, timeAgo, queryParam, section } = Tutti.util;
  const { avatar, categoryTag, statusTag } = Tutti.components;
  const { privateNote, showFailure } = Tutti.pageUtil;
  const root = document.getElementById('pageRoot');
  let countdownTimer = null;

  function countdownParts(deadline) {
    const ms = Math.max(0, new Date(`${deadline}T23:59:59`).getTime() - Date.now());
    return { days: Math.floor(ms / 86400000), hours: Math.floor(ms / 3600000) % 24, minutes: Math.floor(ms / 60000) % 60, over: ms === 0 };
  }

  const countdownMarkup = (deadline) => {
    const { days, hours, minutes } = countdownParts(deadline);
    const cell = (value, label) => `<div><b>${String(value).padStart(2, '0')}</b><span>${label}</span></div>`;
    return `<div class="count" id="countdown">${cell(days, 'days')}${cell(hours, 'hours')}${cell(minutes, 'min')}</div>`;
  };

  function startCountdown(deadline) {
    clearInterval(countdownTimer);
    countdownTimer = setInterval(() => {
      const target = document.getElementById('countdown');
      if (target) target.outerHTML = countdownMarkup(deadline);
    }, 30000);
  }

  function band(audition) {
    const days = Tutti.util.daysUntil(audition.deadline);
    const closing = audition.status === 'open' && days <= 14
      ? `<span class="tag warn">${days <= 0 ? 'Closes today' : `Closes in ${days} day${days === 1 ? '' : 's'}`}</span>` : '';
    const sec = section(audition.category);
    return `<section class="band"><div class="wrap">
      <div class="crumb"><a href="section.html?s=${esc(audition.category)}">${esc(sec.label)}</a> / <a href="section.html?s=${esc(audition.category)}#auditions">Auditions</a> / ${esc(audition.ensemble)}</div>
      <div class="ens">${avatar(audition.director)}<div><b>${esc(audition.ensemble)}</b>
        <div class="small muted">Posted by ${esc(audition.director.name)} · ${date(audition.created)}</div></div></div>
      <h1>${esc(audition.title)}</h1>
      <div class="tags">${categoryTag(audition.category)}${statusTag(audition.status)}${closing}</div>
      <div class="facts">
        <div class="fact"><span>Instrument</span><b>${esc(audition.instruments.join(', ') || 'Open')}</b></div>
        <div class="fact"><span>Ensemble</span><b>${esc(audition.ensemble)}</b></div>
        <div class="fact"><span>Deadline</span><b>${date(audition.deadline, { month: 'long', day: 'numeric', year: 'numeric' })}</b></div>
      </div></div></section>`;
  }

  function details(audition) {
    const requirements = audition.requirements.map((text, i) =>
      `<li><span class="n">${i + 1}</span><div><b>${esc(text)}</b></div></li>`).join('');
    const firstUpcoming = audition.timeline.findIndex((step) => step.date >= new Date().toISOString().slice(0, 10));
    const timeline = audition.timeline.map((step, i) =>
      `<div class="${i === firstUpcoming ? 'now' : ''}"><b>${esc(step.label)}</b><span>${date(step.date, { month: 'long', day: 'numeric', year: 'numeric' })}</span></div>`).join('');
    return `<div>
      <div class="sec"><h2>About the chair</h2><p>${esc(audition.description)}</p></div>
      <div class="sec"><h2>What to submit</h2><p style="margin-bottom:14px">One MP4 clip with everything below.</p><ul class="req">${requirements}</ul></div>
      <div class="sec"><h2>Timeline</h2><div class="timeline">${timeline}</div></div></div>`;
  }

  function directorCard(audition) {
    const d = audition.director;
    return `<div class="card pad"><div class="eyebrow" style="margin-bottom:12px">Director</div>
      <div style="display:flex;gap:12px;align-items:center">${avatar(d)}<div><b>${esc(d.name)}</b><div class="small muted">${esc(d.ensemble)}</div></div></div></div>`;
  }

  function musicianCard(audition) {
    const mine = audition.my_submission;
    if (mine) {
      return `<div class="card pad stack"><div style="display:flex;justify-content:space-between;align-items:center">
          <span class="tag ok">✓ Submitted</span><span class="small muted">${date(mine.created, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</span></div>
        <div><b>Your clip is with ${esc(audition.director.name)}</b><div class="small muted">Under review. Only the director sees scores and comments.</div></div></div>`;
    }
    if (audition.status !== 'open') {
      return `<div class="card pad stack"><div class="eyebrow">Closed</div><p class="t2">This audition is closed and no longer takes submissions.</p></div>`;
    }
    return `<div class="card pad stack"><div class="eyebrow">Submissions close ${date(audition.deadline)}</div>${countdownMarkup(audition.deadline)}
      <button class="btn btn-primary btn-lg" id="openSubmit"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 19V5M5 12l7-7 7 7"/></svg>Submit a clip</button>
      ${privateNote(`Only ${audition.director.name} sees your submission. Scores and comments are private to the director.`)}</div>`;
  }

  function ownerCard(audition, submissions) {
    const rows = submissions.slice(0, 5).map((s) =>
      `<a class="sub-row" href="review.html?id=${s.id}">${avatar(s.musician, 'sm')}<span class="who"><b>${esc(s.musician.name)}</b><span>${timeAgo(s.created)}</span></span>${statusTag(s.status)}</a>`).join('');
    return `<div class="card pad stack"><div style="display:flex;justify-content:space-between;align-items:center">
        <div class="eyebrow">Submissions</div><span class="tag brass">${audition.submission_count} total</span></div>
      ${rows || '<p class="small muted">No submissions yet.</p>'}
      <a class="btn btn-primary" href="director.html?audition=${audition.id}">Open submissions</a>
      ${privateNote('Only you can see these submissions.')}</div>`;
  }

  function viewerCard() {
    return `<div class="card pad stack"><div class="eyebrow">Director view</div><p class="t2">You are viewing this posting as a director. Only musicians can submit, and only the posting director sees submissions.</p></div>`;
  }

  function aside(audition, user, submissions) {
    const primary = user.role === 'musician' ? musicianCard(audition) : audition.owned_by_me ? ownerCard(audition, submissions) : viewerCard();
    return `<aside class="apply">${primary}${directorCard(audition)}</aside>`;
  }

  async function load(user) {
    const id = Number(queryParam('id'));
    if (!id) return showFailure(new Error('This link has no audition in it. Open an audition from your section page.'), { title: 'Audition not found', backHref: Tutti.landingFor(user), backLabel: 'Go back' });
    const { audition } = await api.audition(id);
    let submissions = [];
    if (audition.owned_by_me) submissions = (await api.auditionSubmissions(id)).submissions;
    document.title = `Tutti — ${audition.title}`;
    root.innerHTML = `${band(audition)}<div class="wrap layout">${details(audition)}${aside(audition, user, submissions)}</div>`;
    startCountdown(audition.deadline);
    const button = document.getElementById('openSubmit');
    if (button) button.onclick = () => Tutti.submitDialog.open(audition, user, () => {
      Tutti.toast('Submitted. The director has your clip.', 'ok');
      api.audition(id).then((fresh) => { audition.my_submission = fresh.audition.my_submission; document.querySelector('.apply').outerHTML = aside(audition, user, []); })
        .catch((error) => Tutti.reportError(error, 'refresh after submit'));
    });
  }

  Tutti.boot({ active: 'auditions' })
    .then(load)
    .catch((error) => showFailure(error, { title: 'This audition could not be loaded', backHref: 'home.html', backLabel: 'Back to home' }));
})();
