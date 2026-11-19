/* Opportunity creation and creator-only review administration. */
(function () {
  const { esc, queryParam } = Tutti.util;
  const root = document.getElementById('pageRoot');
  const split = value => value.split('\n').map(s=>s.trim()).filter(Boolean);
  async function load(user) {
    if (!['director','school'].includes(user.role)) throw new Error('Sign in as a director or school to manage opportunities.');
    const { opportunities } = await api.opportunities({ mine: 1 });
    const { schools } = await api.request('GET','/api/schools');
    const { genres } = await api.request('GET','/api/discovery');
    const owned = schools.filter(s=>s.owned_by_me);
    root.innerHTML = `<main class="wrap page"><h1>Manage opportunities</h1><p class="muted">Review mode is fixed when you post. Rubrics freeze when the first application arrives. Email delivery below is simulated locally only.</p><details class="card pad"><summary>Post an opportunity</summary><form id="createForm"><label class="field">Type<select class="input" name="type">${['audition','grant','residency','college_audition','summer_camp'].map(t=>`<option value="${t}">${t.replaceAll('_',' ')}</option>`).join('')}</select></label>${user.role === 'school' ? `<label class="field">Owned school<select class="input" name="school_id">${owned.map(s=>`<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select></label>` : ''}<label class="field">Title<input class="input" name="title" maxlength="160" required></label><label class="field">Organization<input class="input" name="ensemble" required value="${esc(user.ensemble || owned[0]?.name || '')}"></label><label class="field">Description<textarea class="input" name="description"></textarea></label><label class="field">Declared genre<select class="input" name="genre">${Tutti.discovery.options(genres,'Not specified')}</select></label><fieldset><legend>Explicit student eligibility (leave blank if unknown)</legend><label><input type="checkbox" name="eligibility" value="high_school"> High school</label><label><input type="checkbox" name="eligibility" value="college"> College</label></fieldset><label><input type="checkbox" name="student_hub" value="true"> Include this audition in For Students</label><p class="small muted">Eligibility and genre are declarations, not inferred from audience. Only auditions and college entrance auditions appear in the student audition tab.</p><label class="field">Deadline<input class="input" type="date" name="deadline" required></label><label class="field">Audience<select class="input" name="level"><option value="student">High school / student</option><option value="college">College</option><option value="semi-pro">Semi-pro</option><option value="pro">Professional</option></select></label><label class="field">Review mode (cannot change later)<select class="input" name="blind_review"><option value="true">Blind — audio only, anonymous</option><option value="false">Nonblind — identity and video</option></select></label><label class="field">Rubric keys (one per line, lowercase letters and underscores)<textarea class="input" name="rubric">tone\nrhythm\ntechnique\nmusicality\npreparation</textarea></label><label class="field">Instruments (one per line)<textarea class="input" name="instruments"></textarea></label><button class="btn btn-primary">Post opportunity</button></form></details><div id="ownedList">${opportunities.map(o=>`<article class="card pad" data-id="${o.id}"><h2>${esc(o.title)}</h2><p>${o.blind_review ? 'Blind' : 'Nonblind'} · ${esc(o.type)} · ${esc(o.deadline)}</p><a class="btn btn-ghost" href="${o.type === 'gig' ? 'gig' : 'audition'}.html?id=${o.id}">View page</a>${o.type !== 'gig' ? '<button class="btn btn-ghost" data-review>Submissions & administration</button><div data-admin></div>' : ''}</article>`).join('')}</div></main>`;
    root.querySelector('#createForm').onsubmit = async event => {
      event.preventDefault();
      try {
        const data = new FormData(event.target);
        const fields = Object.fromEntries(data);
        fields.eligibility = data.getAll('eligibility'); fields.student_hub = data.has('student_hub');
        fields.blind_review = fields.blind_review === 'true'; fields.rubric = split(fields.rubric); fields.instruments = split(fields.instruments);
        if (fields.school_id) fields.school_id = Number(fields.school_id);
        await api.createOpportunity(fields); await load(user); Tutti.toast('Opportunity posted. Review mode is now immutable.', 'ok');
      } catch (error) { Tutti.reportError(error, 'post opportunity'); }
    };
    root.querySelectorAll('[data-review]').forEach(button => { button.onclick = () => admin(button.closest('article')).catch(error=>Tutti.reportError(error,'load administration')); });
    const selected = queryParam('audition');
    const card = [...root.querySelectorAll('article[data-id]')].find(item=>item.dataset.id === selected);
    if (card) { await admin(card); card.scrollIntoView(); }
  }
  async function admin(card) {
    const id = card.dataset.id;
    const [{ submissions }, { guests }, { outbox }] = await Promise.all([api.auditionSubmissions(id), api.request('GET',`/api/auditions/${id}/guests`),api.request('GET',`/api/auditions/${id}/outbox`)]);
    const target = card.querySelector('[data-admin]');
    const individualForm = `<form data-individual><h3>Message one applicant</h3><p class="small muted">Only the selected applicant receives this one-way in-app notice. Email is simulated locally; no real email or chat is sent.</p><label class="field">Recipient<select class="input" name="submission_id" required><option value="">Choose one applicant</option>${submissions.map(s=>`<option value="${s.id}">${esc(s.musician.name)}</option>`).join('')}</select></label><label class="field">Message to selected applicant<textarea class="input" name="body" required maxlength="3000"></textarea></label><button class="btn btn-primary" ${submissions.length ? '' : 'disabled'}>Send to selected applicant + simulated email</button></form>`;
    target.innerHTML = `<h3>Submissions</h3>${submissions.map(s=>`<p><a href="review.html?id=${s.id}">${esc(s.musician.name)} · ${esc(s.status_label)}</a> <button class="btn btn-ghost" data-template="confirmation" data-sub="${s.id}">Send confirmation</button><button class="btn btn-ghost" data-template="rejection" data-sub="${s.id}">Send rejection</button></p>`).join('') || '<p>No submissions yet.</p>'}<h3>Guest judges</h3><p class="small muted">Links grant access only to this opportunity. Each guest sees only their own scores. Share privately; revoke when finished.</p><button class="btn btn-ghost" data-invite>Create scoped guest link</button><div data-link></div>${guests.map(g=>`<p>${esc(g.label)} ${g.revoked ? '(revoked)' : `<button class="btn btn-ghost" data-revoke="${g.id}">Revoke</button>`}</p>`).join('')}${individualForm}<form data-bulk><label class="field">Announcement to all applicants<textarea class="input" name="body" required maxlength="3000"></textarea></label><button class="btn btn-primary">Send announcement + simulated email</button></form><details><summary>Local simulated email outbox (${outbox.length})</summary>${outbox.map(e=>`<p>${esc(e.body)} — ${esc(e.state)}</p>`).join('') || '<p>Empty. No real email is sent.</p>'}</details>`;
    if (!submissions.length) {
      const { opportunity } = await api.opportunity(id);
      const form = document.createElement('form');
      form.innerHTML = `<label class="field">Configure rubric before applications arrive<textarea class="input" name="rubric">${esc(opportunity.rubric.join('\n'))}</textarea></label><button class="btn btn-ghost">Save rubric</button>`;
      form.onsubmit = async event => { event.preventDefault(); try { await api.request('PUT', `/api/auditions/${id}/rubric`, {rubric:split(form.elements.rubric.value)}); Tutti.toast('Rubric saved.', 'ok'); } catch(error) { Tutti.reportError(error, 'configure rubric'); } };
      target.prepend(form);
    }
    target.querySelector('[data-invite]').onclick = async () => {
      try { const result = await api.request('POST',`/api/auditions/${id}/guests`,{label:'Guest judge'}); const a = document.createElement('a'); a.href = result.url; a.textContent = location.origin + result.url; target.querySelector('[data-link]').replaceChildren(a); }
      catch (error) { Tutti.reportError(error,'create guest link'); }
    };
    target.querySelectorAll('[data-revoke]').forEach(b=>{ b.onclick=async()=>{try {await api.request('DELETE',`/api/auditions/${id}/guests/${b.dataset.revoke}`);await admin(card);}catch(error){Tutti.reportError(error,'revoke guest link');}}; });
    target.querySelectorAll('[data-template]').forEach(b=>{ b.onclick=async()=>{try {await api.request('POST',`/api/submissions/${b.dataset.sub}/notification`,{template:b.dataset.template});await admin(card);Tutti.toast('Notice recorded with simulated email.','ok');}catch(error){Tutti.reportError(error,'send application template');}}; });
    target.querySelector('[data-individual]').onsubmit = async event => {
      event.preventDefault();
      const form = event.target;
      const button = form.querySelector('button');
      button.disabled = true;
      try {
        await api.request('POST', `/api/auditions/${id}/notices`, {submission_id:Number(form.elements.submission_id.value), body:form.elements.body.value});
        await admin(card);
        target.querySelector('[data-individual] select').focus();
        Tutti.toast('Notice recorded for the selected applicant only. Email simulated locally.', 'ok');
      } catch (error) { Tutti.reportError(error, 'message selected applicant'); }
      finally { button.disabled = false; }
    };
    target.querySelector('[data-bulk]').onsubmit=async event=>{event.preventDefault();try {await api.request('POST',`/api/auditions/${id}/announcements`,Object.fromEntries(new FormData(event.target)));await admin(card);Tutti.toast('Announcement recorded with simulated email.','ok');}catch(error){Tutti.reportError(error,'send announcement');}};
  }
  Tutti.boot({ requireAuth:true, active:'manage' }).then(load).catch(Tutti.pageUtil.showFailure);
})();
