/* Pieces shared by the clip dialogs (submit-dialog.js, upload-clip-dialog.js): the scrim, the MP4 drop zone and its validation. */
(function () {
  const { esc } = Tutti.util;
  const ICON_UPLOAD = '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="var(--brass-2)" stroke-width="2" stroke-linecap="round" style="flex:none"><path d="M12 16V4M6 10l6-6 6 6M4 20h16"/></svg>';

  const megabytes = (bytes) => `${(bytes / (1024 * 1024)).toFixed(bytes < 10 * 1024 * 1024 ? 1 : 0)} MB`;
  const isMp4 = (file) => file.type === 'video/mp4' || /\.mp4$/i.test(file.name);

  /* The message to show when a chosen file cannot be uploaded, or '' when it is fine. */
  function fileProblem(file) {
    if (!isMp4(file)) return 'That file is not an MP4. Export your recording as .mp4 and try again.';
    if (file.size > api.MAX_UPLOAD_BYTES) return 'That file is over the 500 MB limit. Export a shorter or smaller MP4.';
    return '';
  }

  /* Adds a full-screen scrim to the page. Escape closes it unless isBusy() says an upload is running. */
  function openScrim(isBusy) {
    const scrim = document.createElement('div');
    scrim.className = 'scrim open';
    document.body.appendChild(scrim);
    const close = () => { scrim.remove(); document.removeEventListener('keydown', onKey); };
    const onKey = (event) => { if (event.key === 'Escape' && !isBusy()) close(); };
    document.addEventListener('keydown', onKey);
    return { scrim, close };
  }

  const dropZoneHtml = () => `<label class="drop" id="dropZone" style="display:flex;gap:12px;align-items:center;justify-content:center;cursor:pointer">
      ${ICON_UPLOAD}<div style="text-align:left"><b style="color:var(--text)">Drag an MP4 here</b> or <span style="color:var(--brass-2);font-weight:600">browse</span>
      <div class="small muted">MP4 · up to 500 MB</div></div>
      <input type="file" id="fileInput" accept="video/mp4,.mp4" hidden></label>`;

  const selectedFileHtml = (file) => (file ? `<div class="file sel"><div style="flex:1"><div style="display:flex;justify-content:space-between;gap:8px;font-size:14px">
      <b>${esc(file.name)}</b><span class="tag ok">✓ Selected</span></div>
      <div class="small muted" style="margin-top:4px">${megabytes(file.size)}</div></div></div>` : '');

  /* Wires the file input and drag-and-drop of dropZoneHtml() inside root; onFile gets the chosen File. */
  function bindDropZone(root, onFile) {
    const input = root.querySelector('#fileInput');
    input.onchange = () => onFile(input.files[0]);
    const zone = root.querySelector('#dropZone');
    zone.ondragover = (event) => { event.preventDefault(); zone.classList.add('over'); };
    zone.ondragleave = () => zone.classList.remove('over');
    zone.ondrop = (event) => { event.preventDefault(); zone.classList.remove('over'); onFile(event.dataTransfer.files[0]); };
  }

  Tutti.dialogParts = { megabytes, fileProblem, openScrim, dropZoneHtml, selectedFileHtml, bindDropZone };
})();
