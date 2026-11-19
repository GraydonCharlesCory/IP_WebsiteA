/* Public profile directory: only name, instrument and city participate in search. */
(function () {
  const { esc } = Tutti.util;
  const root=document.getElementById('pageRoot');
  Tutti.boot({active:'home',requireAuth:false}).then(async()=>{
    const {musicians}=await api.request('GET','/api/musicians');
    const filters={region:'',city:'',location:''};
    root.innerHTML=`<div class="wrap page"><a class="textlink" href="feed.html">← Community</a><div class="page-intro spaced"><div class="eyebrow">Across Tutti</div><h1>Find your people.<br>Through music.</h1><p>Explore musicians and their public performances.</p></div><form class="card pad application-search" id="musicianSearch" role="search"><label class="field">Find musicians<input class="input" type="search" id="musicianQuery" placeholder="Name, instrument or city"></label>${Tutti.locationSearch.markup('musician')}<button class="btn btn-primary">Search</button></form><div class="board-bar"><span id="musicianCount" role="status"></span><button class="btn btn-ghost" id="musicianReset">Clear search</button></div><section class="discovery-stack" id="musicianResults" aria-label="Musician results"></section><div class="card pad empty" id="musicianEmpty" hidden><h2>No musicians found</h2><p>Try a different name, instrument or city.</p></div></div>`;
    const query=document.getElementById('musicianQuery');
    const render=()=>{const terms=query.value.toLowerCase().trim().split(/\s+/);const found=musicians.filter(m=>terms.every(w=>[m.name,m.instrument,m.location.split(',')[0]].join(' ').toLowerCase().includes(w))&&Tutti.locationSearch.matches(m,filters));document.getElementById('musicianResults').innerHTML=found.map(m=>`<article class="card pad"><h2>${esc(m.name)}</h2><p class="muted">${esc(m.instrument)} · ${esc(m.location)}</p><p class="small spaced">Public musician profile</p><a class="textlink spaced" href="profile.html?h=${encodeURIComponent(m.handle)}">View musician profile →</a></article>`).join('');document.getElementById('musicianCount').textContent=`${found.length} musicians`;document.getElementById('musicianEmpty').hidden=found.length>0;};
    const geography=Tutti.locationSearch.bind(document.getElementById('musicianSearch'),filters,render);
    query.oninput=render;document.getElementById('musicianSearch').onsubmit=e=>{e.preventDefault();render();};document.getElementById('musicianReset').onclick=()=>{query.value='';Object.keys(filters).forEach(key=>{filters[key]='';});geography.sync();render();query.focus();};render();
  }).catch(Tutti.pageUtil.showFailure);
})();
