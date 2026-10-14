/* The 3-step "Submit a clip" dialog: Tutti.submitDialog.open(audition, user, onSubmitted).
   Step 1 chooses an MP4 from disk or a profile clip, step 2 adds a note and timestamps, step 3 reviews and submits. */
(function () {
  const { esc, parseTime, duration } = Tutti.util;
  const { videoTile, wire } = Tutti.components;
  const { fileProblem, openScrim, dropZoneHtml, selectedFileHtml, bindDropZone } = Tutti.dialogParts;
  const STEP_TITLES = ['Choose your clip', 'Add details', 'Review & submit', 'Done'];
  const TIMESTAMP_ROWS = 3;
  function open(audition, user, onSubmitted) {
    const state = { step: 1, file: null, clip: null, clips: [], note: '', timestamps: [], confirmed: false, busy: false, error: '' };
    const { scrim, close } = openScrim(() => state.busy);

    const chosenName = () => (state.file ? state.file.name : state.clip ? state.clip.title : '');
    const hasChoice = () => Boolean(state.file || state.clip);

    function stepOne() {
      const picks = state.clips.filter((c) => c.available).map((c) => `
        <div class="opt ${state.clip && state.clip.id === c.id ? 'on' : ''}" data-clip-id="${c.id}">
          ${videoTile(c)}<b>${esc(c.title)}</b><span>${esc(c.instrument || 'Profile clip')}</span></div>`).join('');
      return `${dropZoneHtml()}${selectedFileHtml(state.file)}
        <div class="eyebrow">Or pick from your profile</div>
        ${picks ? `<div class="pick">${picks}</div>` : '<p class="small muted">You have no playable profile clips yet. Upload an MP4 above.</p>'}`;
    }

    function stepTwo() {
      const rows = Array.from({ length: TIMESTAMP_ROWS }, (_, i) => {
        const stamp = state.timestamps[i] || { time: '', label: '' };
        return `<input class="input" data-ts-time="${i}" placeholder="${i ? '' : '0:00'}" value="${esc(stamp.time)}"><input class="input" data-ts-label="${i}" placeholder="${i ? '' : 'Ballad'}" value="${esc(stamp.label)}">`;
      }).join('');
      return `<div class="file"><div><b>${esc(chosenName())}</b><div class="small muted">${state.file ? 'Upload from your computer' : 'From your profile'}</div></div></div>
        <div class="field"><label for="noteInput">Note to the director <span class="muted" style="font-weight:400">(optional)</span></label>
          <textarea class="input" id="noteInput" maxlength="2000">${esc(state.note)}</textarea></div>
        <div class="field"><label>Timestamps <span class="muted" style="font-weight:400">(optional, helps the director jump to each piece)</span></label>
          <div style="display:grid;grid-template-columns:90px 1fr;gap:8px">${rows}</div></div>`;
    }

    function stepThree() {
      const stamps = state.timestamps.length;
      const progress = state.busy && state.file ? '<div class="bar"><i id="uploadBar" style="width:0"></i></div>' : '';
      return `<h3 style="font-size:17px">Review &amp; submit</h3>
        <div class="file"><div style="flex:1"><b>${esc(chosenName())}</b>
          <div class="small muted">${stamps} timestamp${stamps === 1 ? '' : 's'} · ${state.note ? 'note included' : 'no note'}</div>${progress}</div></div>
        <label class="check"><input type="checkbox" id="confirmBox" ${state.confirmed ? 'checked' : ''}>This is my own unedited recording.</label>
        ${Tutti.pageUtil.privateNote(`Your submission is visible only to ${audition.director.name}. It won't appear on your public profile.`)}`;
    }

    function stepDone() {
      return `<div class="done"><div class="ring">✓</div><h2>Submitted</h2>
        <p class="t2" style="margin-top:8px">${esc(audition.director.name)} will review your clip.</p></div>`;
    }

    function render() {
      const body = [stepOne, stepTwo, stepThree, stepDone][state.step - 1]();
      const error = state.error ? `<div class="form-error" role="alert">${esc(state.error)}</div>` : '';
      const nextLabel = state.step === 3 ? (state.busy ? 'Submitting…' : 'Submit to audition') : state.step === 4 ? 'Close' : 'Continue';
      scrim.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="dialogTitle">
        <div class="mhead"><div><div class="eyebrow">Submit to ${esc(audition.ensemble)}</div><h3 style="margin-top:4px" id="dialogTitle">${STEP_TITLES[state.step - 1]}</h3></div>
          <button id="dialogClose" class="t2" style="font-size:22px" aria-label="Close" ${state.busy ? 'disabled' : ''}>×</button></div>
        <div class="steps">${[1, 2, 3].map((n) => `<span class="${n <= state.step ? 'on' : ''}"></span>`).join('')}</div>
        <div class="mbody"><div class="dialog-page">${body}${error}</div></div>
        <div class="mfoot"><button class="btn btn-ghost" id="dialogBack" style="visibility:${state.step > 1 && state.step < 4 ? 'visible' : 'hidden'}" ${state.busy ? 'disabled' : ''}>Back</button>
          <button class="btn btn-primary" id="dialogNext" ${state.busy || (state.step === 1 && !hasChoice()) ? 'disabled' : ''}>${nextLabel}</button></div></div>`;
      wire(scrim);
      bind();
    }

    function chooseFile(file) {
      if (!file) return;
      const problem = fileProblem(file);
      if (problem) { state.error = problem; return render(); }
      Object.assign(state, { file, clip: null, error: '' });
      render();
    }

    function readStepTwo() {
      state.note = scrim.querySelector('#noteInput').value.trim();
      const stamps = [];
      for (let i = 0; i < TIMESTAMP_ROWS; i += 1) {
        const time = scrim.querySelector(`[data-ts-time="${i}"]`).value.trim();
        const label = scrim.querySelector(`[data-ts-label="${i}"]`).value.trim();
        if (time || label) stamps.push({ time, label });
      }
      state.timestamps = stamps;
      const bad = stamps.find((s) => parseTime(s.time) === null || !s.label);
      if (bad) { state.error = 'Each timestamp needs a time like 2:58 and a label. Fill in both or clear the row.'; return false; }
      state.error = '';
      return true;
    }

    async function submit() {
      if (!state.confirmed) { state.error = 'Tick the box to confirm this is your own recording.'; return render(); }
      const meta = { note: state.note, timestamps: state.timestamps.map((s) => ({ time: parseTime(s.time), label: s.label })) };
      Object.assign(state, { busy: true, error: '' });
      render();
      try {
        if (state.file) {
          await api.submitUpload(audition.id, state.file, meta, (fraction) => {
            const bar = scrim.querySelector('#uploadBar');
            if (bar) bar.style.width = `${Math.round(fraction * 100)}%`;
          });
        } else {
          await api.submitClip(audition.id, { clipId: state.clip.id, ...meta });
        }
        Object.assign(state, { busy: false, step: 4 });
        onSubmitted();
      } catch (error) {
        console.error('Tutti submission failed', error);
        Object.assign(state, { busy: false, error: `${error.message} Your choices are kept, so you can try again.` });
      }
      render();
    }

    function bind() {
      const $ = (selector) => scrim.querySelector(selector);
      $('#dialogClose').onclick = close;
      scrim.onclick = (event) => { if (event.target === scrim && !state.busy) close(); };
      $('#dialogBack').onclick = () => { if (state.step === 2) readStepTwo(); state.step -= 1; state.error = ''; render(); };
      $('#dialogNext').onclick = () => {
        if (state.step === 4) return close();
        if (state.step === 2 && !readStepTwo()) return render();
        if (state.step === 3) return submit();
        state.step += 1;
        render();
      };
      if (state.step === 1) {
        bindDropZone(scrim, chooseFile);
        scrim.querySelectorAll('.opt').forEach((option) => {
          option.onclick = (event) => {
            event.preventDefault();
            Object.assign(state, { clip: state.clips.find((c) => c.id === Number(option.dataset.clipId)), file: null, error: '' });
            render();
          };
        });
      }
      if (state.step === 3) $('#confirmBox').onchange = (event) => { state.confirmed = event.target.checked; };
    }

    render();
    api.musician(user.handle)
      .then((profile) => { state.clips = profile.clips; if (state.step === 1) render(); })
      .catch((error) => { console.error('Tutti could not load profile clips', error); state.error = `Your profile clips could not be loaded (${error.message}). You can still upload an MP4.`; render(); });
  }

  Tutti.submitDialog = { open };
})();
