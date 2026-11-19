/* College entrance routes by type; other student auditions explicitly opt in. No eligibility guesses. */
(function () {
  const { esc } = Tutti.util;
  const { matches, metadata, eligibility, href, previewCard, tabs } = Tutti.discovery;
  const root = document.getElementById('pageRoot');
  const filters = {q:new URLSearchParams(location.search).get('q') || '',level:'',location:'',region:'',city:''};
  Tutti.boot({active:'students',requireAuth:false}).then(async user=>{
    if (!user) { root.innerHTML='<div class="wrap page"><div class="card pad"><h1>For Students</h1><p>Sign in to explore student auditions and local clinics.</p><a class="btn btn-primary" href="index.html">Sign in</a><a class="btn btn-ghost" href="schools.html">Explore schools</a></div></div>';return; }
    const [{opportunities},{previews},{schools}] = await Promise.all([api.opportunities({status:'open'}),api.request('GET','/api/discovery'),api.request('GET','/api/schools')]);
    const auditions=opportunities.filter(o=>o.type==='college_audition'||o.type==='audition'&&o.student_hub);
    const clinics=previews.filter(o=>o.type==='clinic');
    const schoolItems=schools.map(s=>({...s,title:s.name,description:[s.about,...s.programs,...s.activities].join(' '),city:s.location.split(',')[0],instruments:[]}));
    let active='student-auditions';
    root.innerHTML=`<div class="wrap page students-page"><div class="page-intro"><div class="eyebrow">For Students</div><h1>Your music.<br>Your next chapter.</h1><p class="muted">Student auditions, local clinics and a place to find your future school.</p><span class="tag brass spaced">High school & college</span></div>
      <form class="card pad application-search" id="studentSearch" role="search"><label class="field">Search student opportunities & schools<input class="input" id="studentQuery" type="search" value="${esc(filters.q)}" placeholder="Instrument, genre, school or city" data-student="q"></label><div class="student-filters"><label class="field">Student level<select class="input" id="studentLevel" data-student="level"><option value="">All students</option><option value="high_school">High school</option><option value="college">College</option></select></label></div>${Tutti.locationSearch.markup('student')}<button class="btn btn-primary">Search</button></form>
      <div class="application-tabs" role="tablist" aria-label="Student resources">${[['student-auditions','Auditions'],['clinics','Local clinics'],['colleges','Explore schools']].map(([id,label])=>`<button role="tab" id="tab-${id}" data-student-tab="${id}" aria-controls="${id}">${label}</button>`).join('')}</div><div class="board-bar"><span id="studentCount" role="status"></span><button class="btn btn-ghost" id="studentClear">Clear filters</button></div>
      ${['student-auditions','clinics','colleges'].map(id=>`<section class="student-grid" id="${id}" role="tabpanel" aria-labelledby="tab-${id}"></section>`).join('')}<div class="card pad empty" id="studentEmpty" hidden><h2>No matches this time</h2><p>Try another instrument or city, or clear your filters.</p><button class="btn btn-ghost" data-student-reset>Clear filters</button></div><p class="small muted spaced">Known demo listings are fictional; clinic dates and student eligibility are illustrative. Unknown eligibility is not inferred. School exploration is for all students, not an admissions eligibility claim.</p></div>`;
    function render() {
      const groups={'student-auditions':auditions.filter(o=>matches(o,filters)),clinics:clinics.filter(o=>matches(o,filters)),colleges:schoolItems.filter(o=>matches(o,{...filters,level:''}))};
      document.getElementById('student-auditions').innerHTML=groups['student-auditions'].map(o=>`<article class="card pad app"><div class="tags"><span class="tag brass">Audition</span><span>${esc(eligibility(o))}</span></div><h3>${esc(o.title)}</h3><p>${esc(o.ensemble)}</p>${metadata(o)}<p class="small muted">Review exact requirements in the listing.</p><a class="textlink" href="${href(o)}">View audition →</a></article>`).join('');
      document.getElementById('clinics').innerHTML=groups.clinics.map(previewCard).join('');
      document.getElementById('colleges').innerHTML=groups.colleges.map(s=>`<article class="card pad app"><span class="tag grey">School exploration · not admissions eligibility</span><h3>${esc(s.name)}</h3><p>${esc(s.location)}</p><p class="muted">${esc(s.programs.join(' · '))}</p><a class="textlink" href="schools.html?id=${s.id}">Explore school →</a></article>`).join('');
      const count=groups[active].length;document.getElementById('studentCount').textContent=`${count} ${active==='clinics'?'clinics':active==='colleges'?'schools':'auditions'}`;document.getElementById('studentEmpty').hidden=count>0;
    }
    tabs(root,'data-student-tab',active,id=>{active=id;render();});
    const form=document.getElementById('studentSearch');form.onsubmit=e=>{e.preventDefault();render();};form.oninput=e=>{if(e.target.dataset.student){filters[e.target.dataset.student]=e.target.value;render();}};
    const geography=Tutti.locationSearch.bind(form,filters,render);
    const reset=()=>{Object.keys(filters).forEach(k=>filters[k]='');form.reset();form.querySelectorAll('[data-student]').forEach(input=>input.value='');geography.sync();render();document.getElementById('studentQuery').focus();};document.getElementById('studentClear').onclick=reset;root.querySelector('[data-student-reset]').onclick=reset;
  }).catch(Tutti.pageUtil.showFailure);
})();
