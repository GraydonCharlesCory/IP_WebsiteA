(function () {
  const { esc, queryParam } = Tutti.util;
  Tutti.boot({ requireRole: 'musician' }).then(async user => {
    const { schools } = await api.request('GET', '/api/schools');
    document.getElementById('pageRoot').innerHTML = `<main class="wrap page"><h1>Edit your profile</h1><form class="card pad" id="profileForm"><label class="field">Instrument<input class="input" name="instrument" value="${esc(user.instrument)}"></label><label class="field">Location<input class="input" name="location" value="${esc(user.location)}"></label><label class="field">Bio<textarea class="input" name="bio">${esc(user.bio)}</textarea></label><p>Education: one school and degree per row; leave unused rows empty.</p><div id="education">${Array.from({length: Math.max(3,(user.education || []).length + 1)}, (_,i) => { const e = (user.education || [])[i] || {}; return `<div class="field"><select class="input" data-school><option value="">School</option>${schools.map(s => `<option value="${s.id}" ${e.school_id === s.id ? 'selected' : ''}>${esc(s.name)}</option>`).join('')}</select><input class="input" data-degree placeholder="Degree or program" value="${esc(e.degree || '')}"></div>`; }).join('')}</div><label class="field">Certifications (one per line)<textarea class="input" name="certifications">${esc((user.certifications || []).join('\n'))}</textarea></label><button class="btn btn-primary">Save profile</button><a class="btn btn-ghost" href="profile.html?h=${encodeURIComponent(user.handle)}">View profile</a></form></main>`;
    document.getElementById('profileForm').onsubmit = async event => {
      event.preventDefault();
      try {
        const fields = Object.fromEntries(new FormData(event.target));
        fields.certifications = fields.certifications.split('\n').map(s=>s.trim()).filter(Boolean);
        fields.education = [...document.querySelectorAll('#education .field')].map(row=>({ school_id:Number(row.querySelector('select').value), degree:row.querySelector('input').value.trim() })).filter(e=>e.school_id || e.degree);
        await api.updateMe(fields); Tutti.toast('Profile saved.', 'ok');
      } catch (error) { Tutti.reportError(error, 'save profile'); }
    };
  }).catch(Tutti.pageUtil.showFailure);
})();
