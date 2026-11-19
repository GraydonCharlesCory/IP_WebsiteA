(function () {
  const { esc, queryParam } = Tutti.util;
  const root = document.getElementById('pageRoot');
  let selectedTab = 'overview';
  const crest = s => `<div class="crest" aria-label="${esc(s.name)} monogram">${esc(s.name.split(/\s+/).slice(0,2).map(w=>w[0]).join(''))}</div>`;
  const list = values => values.length ? `<ul>${values.map(v=>`<li>${esc(v)}</li>`).join('')}</ul>` : '<p class="muted">Not listed yet.</p>';

  function samplePosts(s) {
    const posts = (s.demo_enrichment || {}).posts || [];
    return `<section class="card pad spaced" id="schoolPosts" aria-labelledby="schoolPostsHeading"><h2 id="schoolPostsHeading">Posts</h2>${posts.map(post => `<article class="listline"><p class="small muted">Simulated school update · <time datetime="${esc(post.date)}">${esc(post.date)}</time></p><h3>${esc(post.title)}</h3><p>${esc(post.body)}</p></article>`).join('') || '<p class="muted spaced">No school updates yet.</p>'}</section>`;
  }

  function sampleAlumni(s) {
    const alumni = (s.demo_enrichment || {}).alumni || [];
    if (!alumni.length) return '';
    return `<section class="spaced demo-alumni"><h3>Illustrative alumni examples</h3>${alumni.map(a => `<div class="listline"><p class="small muted">Simulated alumnus · fictional affiliation, not verified</p><h4>${esc(a.name)}</h4><p>${esc(a.detail)}</p></div>`).join('')}</section>`;
  }

  function directory(schools) {
    return `<div class="page-intro"><div class="eyebrow">Schools & education</div><h1>A home for<br>your ambition.</h1><p class="muted">Explore programs, activities and alumni connections.</p></div>
      <form class="card pad school-search" id="schoolSearch" role="search"><label class="field">Find a school<input class="input" id="schoolQuery" type="search" placeholder="School name or location"></label>${Tutti.locationSearch.markup('school')}<button class="btn btn-primary">Search schools</button><button class="btn btn-ghost" id="clearSchools" type="button">Clear search</button></form>
      <div class="school-resultbar"><span id="schoolCount" role="status"></span><span>Fictional institutions</span></div><div class="card" id="schoolRows">${schools.map(s=>`<article class="directory-row" data-school="${esc(`${s.name} ${s.location}`.toLowerCase())}">${crest(s)}<div><h2><a href="schools.html?id=${s.id}">${esc(s.name)}</a></h2><p class="muted">${esc(s.location)}</p><p>${esc(s.programs.join(' · '))}</p><p class="muted">${esc(s.activities.join(' · '))}</p>${s.owned_by_me ? '<span class="tag grey">Your school</span>' : ''}</div><a class="btn btn-ghost" href="schools.html?id=${s.id}">View school ↗</a></article>`).join('')}</div>
      <div class="card empty" id="schoolEmpty" hidden><h2>No schools found</h2><p>Try a school name or a different city, or clear the search filters above.</p></div>`;
  }

  function detail(s, schools) {
    const opportunities = `discover.html?q=${encodeURIComponent(s.name)}`;
    return `<p class="school-back"><a href="schools.html">← All schools</a></p><section class="card school-header"><div class="school-cover" role="img" aria-label="Abstract sage and sand school banner"><span>${esc(s.location)}</span></div>
      <div class="school-identity">${crest(s)}<h1>${esc(s.name)}</h1><p class="muted">Music education · ${esc(s.location)}</p><p class="spaced">${esc(s.about)}</p><div class="school-actions"><a class="btn btn-primary" href="${opportunities}">Explore opportunities ↗</a>${s.owned_by_me ? '<a class="btn btn-ghost" href="#schoolEditor" id="editSchool">Edit school page</a><span class="tag grey">Your school</span>' : ''}</div></div>
      <div class="application-tabs schooltabs" role="tablist" aria-label="School sections">${[['overview','Overview'],['programs','Programs & activities'],['alumni','Alumni']].map(([id,label])=>`<button role="tab" id="schoolTab-${id}" aria-controls="schoolPanel-${id}" data-school-tab="${id}">${label}</button>`).join('')}</div></section>
      <div class="school-columns spaced"><div><div id="schoolPanel-overview" role="tabpanel" aria-labelledby="schoolTab-overview"><section class="card pad school-stack" id="schoolGlance"><div class="eyebrow">At a glance</div><h2>Room to grow.<br>Space to perform.</h2><div class="listline"><h3>Programs</h3>${list(s.programs)}</div><div class="listline"><h3>Activities</h3>${list(s.activities)}</div></section>${samplePosts(s)}</div>
      <section class="card pad" id="schoolPanel-programs" role="tabpanel" aria-labelledby="schoolTab-programs" hidden><h2>Programs & activities</h2><div class="listline"><h3>Programs</h3>${list(s.programs)}</div><div class="listline"><h3>Activities</h3>${list(s.activities)}</div></section>
      <section class="card pad" id="schoolPanel-alumni" role="tabpanel" aria-labelledby="schoolTab-alumni" hidden><h2>Alumni connections</h2>${s.alumni.map(a=>`<div class="listline"><a href="profile.html?h=${encodeURIComponent(a.handle)}">${esc(a.name)}</a><p class="muted">${esc(a.instrument)}</p>${s.owned_by_me ? `<button class="btn btn-ghost" data-remove="${s.id}/${a.id}">Remove connection</button>` : ''}</div>`).join('') || '<p class="muted spaced">No alumni linked yet.</p>'}${sampleAlumni(s)}</section>
      ${s.owned_by_me ? `<div class="card pad spaced" id="schoolEditor">${editor(s)}</div>` : ''}</div>
      <aside class="school-stack"><div class="school-aside"><div class="eyebrow">Open doors</div><h2 class="spaced">Your next chapter.</h2><p>Search opportunities for this school's name.</p><a class="textlink" href="${opportunities}">View opportunities →</a></div><div class="card pad"><div class="eyebrow">Also on Tutti</div>${schools.filter(other=>other.id!==s.id).map(other=>`<div class="listline"><h3><a href="schools.html?id=${other.id}">${esc(other.name)}</a></h3><p class="muted">${esc(other.location)}</p></div>`).join('')}<a class="textlink" href="schools.html">Browse schools →</a></div></aside></div>`;
  }

  function wireDirectory(schools) {
    const query = document.getElementById('schoolQuery');
    if (!query) return;
    const filters = { region:'', city:'', location:'' };
    const filter = () => {
      let count = 0;
      root.querySelectorAll('[data-school]').forEach((row,index) => { row.hidden = !row.dataset.school.includes(query.value.trim().toLowerCase()) || !Tutti.locationSearch.matches(schools[index],filters); if (!row.hidden) count++; });
      document.getElementById('schoolCount').textContent = `${count} schools`;
      document.getElementById('schoolEmpty').hidden = count > 0;
      document.getElementById('schoolRows').hidden = count === 0;
    };
    query.oninput = filter;
    document.getElementById('schoolSearch').onsubmit = event => { event.preventDefault(); filter(); };
    const geography = Tutti.locationSearch.bind(document.getElementById('schoolSearch'),filters,filter);
    document.getElementById('clearSchools').onclick = () => { query.value = ''; Object.keys(filters).forEach(key=>{filters[key]='';}); geography.sync(); filter(); query.focus(); };
    filter();
  }

  function wireTabs() {
    const tabs = [...root.querySelectorAll('[data-school-tab]')];
    const select = id => {
      selectedTab = id;
      tabs.forEach(button => { const current = button.dataset.schoolTab === id; button.setAttribute('aria-selected', String(current)); button.tabIndex = current ? 0 : -1; document.getElementById(`schoolPanel-${button.dataset.schoolTab}`).hidden = !current; });
    };
    tabs.forEach((button,index) => {
      button.onclick = () => select(button.dataset.schoolTab);
      button.onkeydown = event => {
        if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
        event.preventDefault();
        const next = tabs[event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length-1 : (index + (event.key === 'ArrowRight' ? 1 : tabs.length-1)) % tabs.length];
        next.click(); next.focus();
      };
    });
    if (tabs.length) select(selectedTab);
    const edit = document.getElementById('editSchool');
    if (edit) edit.onclick = () => { document.querySelector('#schoolEditor details').open = true; };
  }
  async function load() {
    const { schools } = await api.request('GET','/api/schools');
    const selected = queryParam('id');
    const school = schools.find(s=>String(s.id)===selected);
    if (selected && !school) throw new Error('School not found. Choose a school from the school directory.');
    root.innerHTML = `<div class="wrap page schools-page">${selected ? detail(school, schools) : directory(schools)}</div>`;
    wireDirectory(schools); wireTabs();
    root.querySelectorAll('[data-edit]').forEach(form=>{ form.onsubmit=async event=>{event.preventDefault();try { const data=Object.fromEntries(new FormData(form));for(const k of ['programs','activities']) data[k]=data[k].split('\n').map(v=>v.trim()).filter(Boolean);await api.request('PUT',`/api/schools/${form.dataset.edit}`,data);await load();Tutti.toast('School page saved.','ok');}catch(error){Tutti.reportError(error,'save school page');}}; });
    root.querySelectorAll('[data-alumni]').forEach(form=>{form.onsubmit=async event=>{event.preventDefault();try {const {musician}=await api.musician(new FormData(form).get('handle'));await api.request('PUT',`/api/schools/${form.dataset.alumni}/alumni/${musician.id}`);await load();}catch(error){Tutti.reportError(error,'link alumnus');}};});
    root.querySelectorAll('[data-remove]').forEach(button=>{button.onclick=async()=>{try {const [sid,uid]=button.dataset.remove.split('/');await api.request('DELETE',`/api/schools/${sid}/alumni/${uid}`);await load();}catch(error){Tutti.reportError(error,'remove alumni connection');}};});
  }
  function editor(s) {
    return `<details><summary>Manage your school page</summary><form data-edit="${s.id}">${['name','location','about','programs','activities'].map(k=>`<label class="field">${esc(k)}${['programs','activities'].includes(k) ? ' (one per line)' : ''}<textarea class="input" name="${k}">${esc(Array.isArray(s[k]) ? s[k].join('\n') : s[k])}</textarea></label>`).join('')}<button class="btn btn-primary">Save school page</button></form><form data-alumni="${s.id}"><label class="field">Link alumnus by musician handle<input class="input" name="handle" required placeholder="leo-marquez"></label><button class="btn btn-ghost">Add alumni connection</button></form><a class="btn btn-primary" href="manage.html">Post auditions & other opportunities</a></details>`;
  }
  Tutti.boot({ active:'schools', requireAuth:false }).then(load).catch(Tutti.pageUtil.showFailure);
})();
