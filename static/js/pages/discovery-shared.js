/* Explicit metadata and accessible tabs shared by discovery surfaces. */
(function () {
  const { esc } = Tutti.util;
  const TYPES = [['','All types'],['audition','Auditions'],['gig','Gigs'],['grant','Grants'],['residency','Residencies'],['teaching','Teaching positions'],['summer_camp','Summer camps']];
  const eligibility = o => (o.eligibility || []).map(v => ({high_school:'High school',college:'College'})[v]).join(' · ') || 'Student eligibility not specified';
  const options = (values, label) => `<option value="">${esc(label)}</option>${[...new Set(values.filter(Boolean))].sort().map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('')}`;
  const href = o => o.demo_preview ? '' : `${o.type === 'gig' ? 'gig' : 'audition'}.html?id=${o.id}`;
  const metadata = o => `<p class="application-meta muted">${esc((o.instruments || []).join(', ') || 'Instrument not specified')} · ${esc(o.genre || 'Genre not specified')} · ${esc(o.location || 'Location not specified')}</p>`;
  const matches = (o, f) => {
    const text = [o.title,o.ensemble,o.description,o.genre,...(o.instruments||[]),o.location,o.city].join(' ').toLowerCase();
    return (f.q || '').toLowerCase().split(/\s+/).every(w=>text.includes(w)) &&
      (!f.instrument || (o.instruments||[]).some(i=>i.toLowerCase().includes(f.instrument.toLowerCase()))) &&
      (!f.genre || o.genre === f.genre) && (!f.type || o.type === f.type) &&
      Tutti.locationSearch.matches(o, f) &&
      (!f.level || (o.eligibility||[]).includes(f.level));
  };
  function previewCard(o) {
    return `<article class="card pad app"><span class="tag grey">Fictional demo preview · ${esc(o.type)}</span><h3>${esc(o.title)}</h3><a href="schools.html?id=${o.school_id}">${esc(o.ensemble)}</a>${metadata(o)}<p>${esc(eligibility(o))}</p><p>${esc(o.description)}</p><p class="small muted">Illustrative date: ${esc(o.deadline)}. Preview only — no apply or registration workflow.</p></article>`;
  }
  function tabs(root, attribute, selected, onSelect) {
    const buttons = [...root.querySelectorAll(`[${attribute}]`)];
    const select = id => {
      buttons.forEach(b=>{const active=b.getAttribute(attribute)===id;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;document.getElementById(b.getAttribute('aria-controls')).hidden=!active;});
      onSelect(id);
    };
    buttons.forEach((b,index)=>{
      b.onclick=()=>select(b.getAttribute(attribute));
      b.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=buttons[e.key==='Home'?0:e.key==='End'?buttons.length-1:(index+(e.key==='ArrowRight'?1:buttons.length-1))%buttons.length];next.click();next.focus();};
    });
    select(selected);
  }
  Tutti.discovery = { TYPES, eligibility, options, href, metadata, matches, previewCard, tabs };
})();
