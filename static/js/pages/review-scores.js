/* Five 1-10 segmented selectors with a live average: Tutti.reviewScores.mount(container, scores, onChange) */
(function () {
  const CRITERIA = [['tone', 'Tone'], ['rhythm', 'Rhythm'], ['technique', 'Technique'], ['musicality', 'Musicality'], ['preparation', 'Preparation']];

  function average(scores) {
    const given = Object.values(scores).filter((v) => v !== null && v !== undefined);
    return given.length ? Math.round((given.reduce((a, b) => a + b, 0) / given.length) * 10) / 10 : null;
  }

  const averageMarkup = (scores) => {
    const value = average(scores);
    return `${value === null ? '—' : value.toFixed(1)}<small>/10</small>`;
  };

  function rowMarkup([key, label], value) {
    const buttons = Array.from({ length: 10 }, (_, i) => {
      const n = i + 1;
      return `<button type="button" data-criterion="${key}" data-value="${n}" aria-label="${label} ${n}" class="${n === value ? 'sel' : value && n < value ? 'fill' : ''}">${n}</button>`;
    }).join('');
    return `<div class="rrow"><div class="l">${label}<span>${value ?? '—'}</span></div><div class="seg">${buttons}</div></div>`;
  }

  /* Draws the selectors into `container`; calls onChange(scores) after each click. Returns {scores, average}. */
  function mount(container, initial, onChange) {
    const scores = { ...initial };
    const averageTarget = document.getElementById('avg');
    const draw = () => {
      container.innerHTML = CRITERIA.map((c) => rowMarkup(c, scores[c[0]])).join('');
      averageTarget.innerHTML = averageMarkup(scores);
    };
    container.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-criterion]');
      if (!button) return;
      scores[button.dataset.criterion] = Number(button.dataset.value);
      draw();
      onChange({ ...scores });
    });
    draw();
    return { scores: () => ({ ...scores }), average: () => average(scores) };
  }

  Tutti.reviewScores = { mount, averageMarkup, average, CRITERIA };
})();
