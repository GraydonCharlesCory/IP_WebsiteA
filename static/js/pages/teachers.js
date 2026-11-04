/* Lessons & clinics: teachers.html. Public list of teachers with an instrument filter. */
(function () {
  const { esc } = Tutti.util;
  const { avatar, categoryTag } = Tutti.components;
  const { profileHref, message, guard, bootPublicPage } = Tutti.parts;
  const root = document.getElementById('pageRoot');
  const INSTRUMENTS = ['Violin', 'Cello', 'Trombone', 'Saxophone', 'Trumpet', 'Piano', 'Guitar', 'Drums'];
  let selected = Tutti.util.queryParam('instrument') || '';

  function teacherCard(teacher) {
    const teaching = teacher.teaching || {};
    return `<a class="card pad teacher" href="${profileHref(teacher)}"><div class="who">${avatar(teacher)}
        <div><b>${esc(teacher.name)}</b><div class="small muted">${esc([teacher.instrument, teacher.location].filter(Boolean).join(' · '))}</div></div>${categoryTag(teacher.category)}</div>
      <p class="t2 small">${esc(teaching.blurb || teacher.bio)}</p>
      <div class="foot"><span>${esc((teaching.instruments || []).join(', '))}</span><b>${esc(teaching.rate || '')}</b></div></a>`;
  }

  const chip = (label, value) => `<button class="chip ${value === selected ? 'on' : ''}" type="button" data-instrument="${esc(value)}">${esc(label)}</button>`;

  async function render() {
    const { teachers } = await api.teachers(selected ? { instrument: selected } : {});
    root.innerHTML = `<div class="wrap page"><div class="eyebrow">Lessons &amp; clinics</div><h1 style="margin:6px 0 8px">Learn from working musicians</h1>
      <p class="t2" style="margin-bottom:20px">Teachers listed on Tutti, with what they teach and their rate.</p>
      <div class="filters">${chip('All instruments', '')}${INSTRUMENTS.map((name) => chip(name, name)).join('')}</div>
      <div class="teacher-grid">${teachers.length ? teachers.map(teacherCard).join('')
        : message('No teachers found', selected ? `Nobody lists ${selected} lessons yet. Try another instrument.` : 'No teachers are listed yet.')}</div></div>`;
    root.querySelectorAll('[data-instrument]').forEach((button) => {
      button.onclick = () => { selected = button.dataset.instrument; guard(root, render); };
    });
  }

  bootPublicPage(root, 'teachers', render);
})();
