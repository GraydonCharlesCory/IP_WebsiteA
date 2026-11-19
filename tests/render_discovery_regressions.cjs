/* Revisit discovery routes rather than manufacturing new submission workflows. */
const assert = require('node:assert/strict');
module.exports = async function ({page,api,open,signIn}) {
  const failures=[];
  await signIn('lakefront.school');
  const school=(await api('GET','/api/schools')).schools.find(s=>s.owned_by_me);
  const {opportunity:college}=await api('POST','/api/opportunities',{
    school_id:school.id,type:'college_audition',title:'Default metadata college entrance',deadline:'2027-06-01'
  },201);
  assert.equal(college.genre,'');assert.deepEqual(college.eligibility,[]);assert.equal(college.student_hub,false);
  await signIn('leo.marquez');
  await open('/students.html','#studentQuery');
  await page.locator('#studentQuery').fill(college.title);
  if(await page.locator('#student-auditions article').count()!==1) failures.push('Unknown-metadata college audition hidden');
  else {
    assert.match(await page.locator('#student-auditions').innerText(),/Student eligibility not specified/);
    await page.locator('#studentLevel').selectOption('high_school');
    assert.equal(await page.locator('#student-auditions article').count(),0);
    await page.locator('#studentClear').click();await page.locator('#studentQuery').fill(college.title);
    await page.locator('#student-auditions a').click();assert(page.url().endsWith(`audition.html?id=${college.id}`));
  }
  const gig=(await api('GET','/api/opportunities?type=gig')).opportunities[0];
  await open(`/gig.html?id=${gig.id}`,'#availabilityCard');
  await page.locator('[data-status="maybe"]').click();
  await page.locator('[data-status="maybe"][aria-pressed="true"]').waitFor();
  await open('/applications.html','#applicationQuery');
  await page.locator('#applicationQuery').fill(gig.title);
  if(await page.locator('#available article').count()!==1) failures.push('Marked gig hidden');
  else {
    assert.match(await page.locator('#available').innerText(),/Your availability: Maybe/);
    await page.getByRole('link',{name:'Update availability'}).click();
    await page.locator('[data-status="unavailable"]').click();
    await page.locator('[data-status="unavailable"][aria-pressed="true"]').waitFor();
    await open('/applications.html','#applicationQuery');await page.locator('#applicationQuery').fill(gig.title);
    assert.match(await page.locator('#available').innerText(),/Your availability: Unavailable/);
    await page.getByRole('link',{name:'Update availability'}).click();
    await page.locator('[data-status="unavailable"][aria-pressed="true"]').waitFor();
  }
  await open(`/schools.html?id=${school.id}`,'#schoolTab-overview');
  await page.getByRole('link',{name:'Explore opportunities ↗'}).click();
  await page.getByRole('link',{name:'Find opportunities →'}).click();await page.locator('#applicationQuery').waitFor();
  if(await page.locator('#applicationQuery').inputValue()!==school.name) failures.push('School query dropped from opportunities');
  await open(`/schools.html?id=${school.id}`,'#schoolTab-overview');
  await page.getByRole('link',{name:'View opportunities →',exact:true}).click();
  await page.getByRole('link',{name:'Explore For Students →'}).click();await page.locator('#studentQuery').waitFor();
  if(await page.locator('#studentQuery').inputValue()!==school.name) failures.push('School query dropped from student discovery');
  else {
    assert(await page.locator('#student-auditions article').count()>0);
    await page.locator('#studentClear').click();assert.equal(await page.locator('#studentQuery').inputValue(),'');
  }
  assert.deepEqual(failures,[]);
  console.log('PASS default unknown college discovery, gig mark/revisit/update, both school CTA query routes');
};
