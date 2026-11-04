/* The "Upload a clip" dialog on a musician's own profile: Tutti.uploadClipDialog.open(onUploaded).
   Pick an MP4, give it a title, upload with progress via api.uploadClip. */
(function () {
  const { esc } = Tutti.util;
  const { fileProblem, openScrim, dropZoneHtml, selectedFileHtml, bindDropZone } = Tutti.dialogParts;

  const titleFromFileName = (name) => name.replace(/\.mp4$/i, '').replace(/[_-]+/g, ' ').trim();

  function open(onUploaded) {
    const state = { file: null, title: '', busy: false, error: '' };
    const { scrim, close } = openScrim(() => state.busy);

    function render() {
      const progress = state.busy ? '<div class="file"><div style="flex:1"><div class="small muted">Uploading…</div><div class="bar"><i id="uploadBar" style="width:0"></i></div></div></div>' : '';
      const error = state.error ? `<div class="form-error" role="alert">${esc(state.error)}</div>` : '';
      scrim.innerHTML = `<div class="modal" role="dialog" aria-modal="true" aria-labelledby="dialogTitle">
        <div class="mhead"><div><div class="eyebrow">Your profile</div><h3 style="margin-top:4px" id="dialogTitle">Upload a clip</h3></div>
          <button id="dialogClose" class="t2" style="font-size:22px" aria-label="Close" ${state.busy ? 'disabled' : ''}>×</button></div>
        <div class="mbody"><div class="dialog-page">${dropZoneHtml()}${selectedFileHtml(state.file)}
          <div class="field"><label for="titleInput">Title</label>
            <input class="input" id="titleInput" maxlength="120" placeholder="e.g. Autumn Leaves, take 2" value="${esc(state.title)}" ${state.busy ? 'disabled' : ''}></div>
          ${progress}${error}</div></div>
        <div class="mfoot"><span></span><button class="btn btn-primary" id="uploadNext" ${state.busy || !state.file ? 'disabled' : ''}>${state.busy ? 'Uploading…' : 'Upload clip'}</button></div></div>`;
      bind();
    }

    function chooseFile(file) {
      if (!file) return;
      readTitle();
      const problem = fileProblem(file);
      if (problem) { state.error = problem; return render(); }
      if (!state.title) state.title = titleFromFileName(file.name);
      Object.assign(state, { file, error: '' });
      render();
    }

    function readTitle() {
      const input = scrim.querySelector('#titleInput');
      if (input) state.title = input.value.trim();
    }

    async function upload() {
      readTitle();
      if (!state.title) { state.error = 'Give the clip a title so people know what they are watching.'; return render(); }
      Object.assign(state, { busy: true, error: '' });
      render();
      try {
        await api.uploadClip(state.file, { title: state.title }, (fraction) => {
          const bar = scrim.querySelector('#uploadBar');
          if (bar) bar.style.width = `${Math.round(fraction * 100)}%`;
        });
      } catch (error) {
        console.error('Tutti clip upload failed', error);
        Object.assign(state, { busy: false, error: `${error.message} Your file and title are kept, so you can try again.` });
        return render();
      }
      close();
      onUploaded();
    }

    function bind() {
      scrim.querySelector('#dialogClose').onclick = close;
      scrim.onclick = (event) => { if (event.target === scrim && !state.busy) close(); };
      scrim.querySelector('#uploadNext').onclick = upload;
      bindDropZone(scrim, chooseFile);
    }

    render();
  }

  Tutti.uploadClipDialog = { open };
})();
