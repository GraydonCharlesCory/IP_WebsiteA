/* Round-four rendered discovery checks; the parent owns the isolated server/browser lifecycle. */
const assert = require('node:assert/strict');
const path = require('node:path');
module.exports = async function ({page,api,open,body,checkViewport,signIn,evidence,publicClip}) {
  await open('/home.html','.discover-hero');
  assert(page.url().endsWith('/discover.html'));
  for (const url of ['applications.html','feed.html','students.html','schools.html']) {
    assert(await page.locator(`#pageRoot a[href="${url}"]`).count()>0);
  }
  assert.equal(await page.locator('nav a').filter({hasText:/^(Jazz|Orchestral|Students)$/}).count(),0);
  const opportunities=(await api('GET','/api/opportunities?status=open')).opportunities;
  const college=opportunities.find(o=>o.type==='college_audition'&&o.eligibility.includes('high_school'));
  assert(college);
  await api('POST',`/api/auditions/${college.id}/submissions`,{clip_id:publicClip.id},201);
  const ownApplications=(await api('GET','/api/my/applications')).applications;
  const previews=(await api('GET','/api/discovery')).previews;
  const available=[...opportunities.filter(o=>o.type!=='college_audition'&&!o.my_submission),...previews.filter(o=>o.type==='teaching')];
  await open('/applications.html','#applicationQuery');
  assert(!await page.locator('#submitted').isVisible());
  assert(!/Creator-only composite|Average score|applicants competing/.test(await body()));
  assert.equal(await page.locator('[data-search="genre"] option').count(),21);
  for (const [tab,panel,items] of [['availableTab','available',available],['submittedTab','submitted',ownApplications.map(a=>a.opportunity)]]) {
    await page.locator('#'+tab).click();
    const check=async expected=>assert.equal(await page.locator(`#${panel} article`).count(),expected,`${panel} results`);
    await check(items.length);
    const target=items.find(o=>o.genre&&o.instruments.length&&o.city);
    assert(target,`${panel} explicit metadata fixture`);
    await page.locator('#applicationQuery').fill(target.title);
    await page.locator('[data-search="instrument"]').selectOption(target.instruments[0]);
    await page.locator('[data-search="genre"]').selectOption(target.genre);
    await page.locator('#applicationLocation').fill(target.city);
    const expected=items.filter(o=>o.title.toLowerCase().includes(target.title.toLowerCase())&&o.genre===target.genre&&o.instruments.includes(target.instruments[0])&&o.city===target.city);
    await check(expected.length);
    await page.locator('#applicationQuery').fill('no-such-round4-keyword');await check(0);
    await page.locator(`#${panel} [data-reset-app]`).click();await check(items.length);
    for (const type of ['audition','gig','grant','residency','teaching','summer_camp']) {
      await page.locator('[data-search="type"]').selectOption(type);
      await check(items.filter(o=>o.type===type).length);
      if(type==='teaching'&&panel==='available') {
        assert.match(await page.locator('#available').innerText(),/Fictional demo preview/);
        assert.equal(await page.locator('#available a[href^="audition.html"]').count(),0);
      }
    }
    await page.locator('#clearApplicationSearch').click();
    if(panel==='submitted') {
      assert.match(await page.locator('#submitted').innerText(),/College entrance auditions/);
      const status=ownApplications[0].status;
      await page.locator('#submittedStatus').selectOption(status);
      await check(ownApplications.filter(a=>a.status===status).length);
      await page.locator('[data-search="type"]').selectOption('grant');
      await check(ownApplications.filter(a=>a.status===status&&a.opportunity.type==='grant').length);
      await page.locator('#clearApplicationSearch').click();
    } else assert(!await page.locator('#available').innerText().then(t=>t.includes(college.title)));
  }
  await page.locator('#submittedTab').press('Home');
  assert.equal(await page.locator('#availableTab').getAttribute('aria-selected'),'true');
  await page.locator('#availableTab').press('ArrowRight');
  assert.equal(await page.locator('#submittedTab').getAttribute('aria-selected'),'true');

  await open('/students.html','#studentQuery');
  const studentAuditions=opportunities.filter(o=>o.type==='college_audition'||o.type==='audition'&&o.student_hub);
  assert.equal(await page.locator('#student-auditions article').count(),studentAuditions.length);
  for(const level of ['high_school','college']) {
    await page.locator('#studentLevel').selectOption(level);
    assert.equal(await page.locator('#student-auditions article').count(),studentAuditions.filter(o=>o.eligibility.includes(level)).length);
  }
  await page.locator('#studentClear').click();
  await page.locator('#studentQuery').fill(college.title);
  await page.locator('#studentLevel').selectOption('high_school');
  await page.locator('#studentLocation').fill(college.city);
  assert.equal(await page.locator('#student-auditions article').count(),1);
  await page.locator('#studentQuery').fill('no-such-student');
  assert(await page.locator('#studentEmpty').isVisible());
  await page.locator('[data-student-reset]').click();
  await page.locator('#tab-student-auditions').press('ArrowRight');
  assert.equal(await page.locator('#tab-clinics').getAttribute('aria-selected'),'true');
  assert.equal(await page.locator('#clinics article').count(),2);
  assert.equal(await page.locator('#clinics a[href^="audition.html"],#clinics button').count(),0);
  assert.match(await page.locator('#clinics').innerText(),/Fictional demo preview/);
  const clinic=previews.find(p=>p.type==='clinic');
  await page.locator('#studentQuery').fill(clinic.title);
  await page.locator('#studentLevel').selectOption('college');
  await page.locator('#studentLocation').fill(clinic.city);
  assert.equal(await page.locator('#clinics article').count(),1);
  await page.locator('#studentQuery').fill('no-such-clinic');
  assert(await page.locator('#studentEmpty').isVisible());
  await page.locator('#studentClear').click();
  await page.locator('#tab-clinics').press('End');
  const schools=(await api('GET','/api/schools')).schools;
  await page.locator('#studentLevel').selectOption('college');
  assert.equal(await page.locator('#colleges article').count(),schools.length);
  await page.locator('#studentQuery').fill(schools[0].name);
  await page.locator('#studentLocation').fill(schools[0].location.split(',')[0]);
  assert.equal(await page.locator('#colleges article').count(),1);
  await page.locator('#studentQuery').fill('no-such-school');assert(await page.locator('#studentEmpty').isVisible());
  await page.locator('#studentClear').click();
  await page.locator('#tab-colleges').press('Home');
  assert.equal(await page.locator('#tab-student-auditions').getAttribute('aria-selected'),'true');

  await open('/feed.html','a[href="musicians.html"]');
  await page.locator('a[href="musicians.html"]').click();await page.locator('#musicianQuery').waitFor();
  const musicians=(await api('GET','/api/musicians')).musicians;
  const target=musicians.find(m=>m.instrument&&m.location);
  for(const query of [target.name,target.instrument,target.location.split(',')[0],`${target.name} ${target.instrument}`]) {
    await page.locator('#musicianQuery').fill(query);
    const terms=query.toLowerCase().split(/\s+/);
    assert.equal(await page.locator('#musicianResults article').count(),musicians.filter(m=>terms.every(w=>[m.name,m.instrument,m.location.split(',')[0]].join(' ').toLowerCase().includes(w))).length);
  }
  await page.locator('#musicianQuery').fill('@tutti.demo');assert(await page.locator('#musicianEmpty').isVisible());
  await page.locator('#musicianReset').click();assert.equal(await page.locator('#musicianResults article').count(),musicians.length);
  assert.equal(await page.locator('#musicianResults button').count(),0);
  await api('POST','/api/sign-out');
  await open('/musicians.html','#musicianQuery');
  assert.equal(await page.locator('#musicianResults article').count(),musicians.length);
  await signIn('leo.marquez');

  for(const dark of [false,true]) {
    await open('/applications.html','#applicationQuery');
    if(await page.locator('body').evaluate(el=>el.classList.contains('dark'))!==dark) await page.locator('#themeButton').click();
    for(const width of [1440,900,320]) {
      await page.setViewportSize({width,height:1000});
      for(const [url,selector,name] of [['discover.html','.discover-hero','discover'],['students.html','#studentQuery','students'],['applications.html','#applicationQuery','applications'],['musicians.html','#musicianQuery','musicians']]) {
        await open('/'+url,selector);await checkViewport(`${name} ${width} ${dark?'dark':'light'}`);
        assert.equal(await page.locator('body').evaluate(el=>el.classList.contains('dark')),dark);
        if(name==='applications') assert.equal(await page.locator('.application-filters').evaluate(el=>getComputedStyle(el).gridTemplateColumns.split(' ').length),width===1440?4:width===900?2:1);
        if(width!==900) await page.screenshot({path:path.join(evidence,`${name}-${width}-${dark?'dark':'light'}.png`),fullPage:true});
      }
    }
  }
  await page.setViewportSize({width:1440,height:1000});
  if(await page.locator('body').evaluate(el=>el.classList.contains('dark'))) await page.locator('#themeButton').click();
  console.log('PASS round4 landing, student tabs/AND/empty/reset, public musician search, explicit application filters/status/history, 4/2/1 columns, 320px and both themes');
};
