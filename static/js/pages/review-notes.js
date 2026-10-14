/* Timestamped notes: Tutti.reviewNotes.mount(container, notes, {getTime, seek, onChange}) */
(function () {
  const { esc, duration, parseTime } = Tutti.util;

  function mount(container, initial, { getTime, seek, onChange }) {
    let notes = [...initial];
    let timeEdited = false;
    container.innerHTML = `<div class="eyebrow">Timestamped notes</div><div id="noteList" class="note-list"></div>
      <form class="addts" id="noteForm"><input class="input" id="noteTime" style="width:72px" value="0:00" aria-label="Time in the video">
        <input class="input" id="noteText" placeholder="Add a note at this moment…" maxlength="1000" aria-label="Note"><button class="btn btn-ghost" type="submit">Add</button></form>`;
    const list = container.querySelector('#noteList');
    const timeInput = container.querySelector('#noteTime');
    const textInput = container.querySelector('#noteText');

    const draw = () => {
      list.innerHTML = notes.length ? notes.map((n, i) =>
        `<div class="tc"><button type="button" class="tc-time" data-seek="${n.time}" title="Jump to this moment">${duration(n.time)}</button><span>${esc(n.text)}</span>
          <button type="button" class="tc-remove" data-remove="${i}" aria-label="Remove note">×</button></div>`).join('')
        : '<p class="small muted">No notes yet. Pause the video and add one.</p>';
    };
    const commit = (next) => { notes = next.sort((a, b) => a.time - b.time); draw(); onChange([...notes]); };

    list.addEventListener('click', (event) => {
      const jump = event.target.closest('[data-seek]');
      const remove = event.target.closest('[data-remove]');
      if (jump) seek(Number(jump.dataset.seek));
      if (remove) commit(notes.filter((_, i) => i !== Number(remove.dataset.remove)));
    });
    timeInput.addEventListener('input', () => { timeEdited = true; });
    container.querySelector('#noteForm').addEventListener('submit', (event) => {
      event.preventDefault();
      const text = textInput.value.trim();
      const time = parseTime(timeInput.value);
      if (time === null) return Tutti.toast('Enter the time as minutes:seconds, like 2:14.', 'error');
      if (!text) return Tutti.toast('Write the note before adding it.', 'error');
      commit([...notes, { time, text }]);
      textInput.value = '';
      timeEdited = false;
    });
    draw();
    return { followVideo: () => { if (!timeEdited) timeInput.value = duration(getTime()); } };
  }

  Tutti.reviewNotes = { mount };
})();
