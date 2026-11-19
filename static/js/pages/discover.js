/* Discovery landing: routes to real workflows without replacing them. */
(function () {
  const query = new URLSearchParams(location.search).get('q') || '';
  const scoped = path => Tutti.util.esc(path + (query ? '?q=' + encodeURIComponent(query) : ''));
  const root = document.getElementById('pageRoot');
  Tutti.boot({active:'discover',requireAuth:false}).then(user=>{
    root.innerHTML = `<div class="wrap page"><div class="discover-hero"><div><div class="eyebrow">Discover</div><h1>Make room for<br>what comes next.</h1></div><p class="muted">Find your next opportunity, or a new connection through the music.</p></div>
      <div class="discover-columns"><section class="discovery-stack"><div class="card pad"><span class="tag brass">Auditions & opportunities</span><h2 class="spaced">Find your next stage.</h2><p class="muted spaced">Search by instrument, genre, location or school.</p><a class="btn btn-primary spaced" href="${user?.role === 'musician' ? scoped('applications.html') : user ? 'manage.html' : 'index.html'}">Find opportunities →</a></div>
      <div class="card pad"><div class="eyebrow">From the community</div><h2 class="spaced">Different voices.<br>Shared momentum.</h2><a class="textlink spaced" href="feed.html">Explore performances →</a></div></section>
      <aside class="discovery-stack"><div class="discovery-aside"><div class="eyebrow">For Students</div><h2 class="spaced">Your next chapter<br>starts here.</h2><p class="spaced">High-school and college auditions, local clinics, and schools to explore.</p><a class="btn btn-ghost spaced" href="${scoped('students.html')}">Explore For Students →</a></div><div class="card pad"><h3>Explore schools</h3><p class="muted spaced">Programs, activities and the people behind the music.</p><a class="textlink spaced" href="schools.html">Browse schools →</a></div></aside></div></div>`;
  }).catch(Tutti.pageUtil.showFailure);
})();
