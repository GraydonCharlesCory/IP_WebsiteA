/* Exercise unknown records after a populated-v3 upgrade in an actual browser. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const startServer=require('./render_server.cjs');
module.exports=async function({context,scratch}) {
  const folder=path.join(scratch,'legacy');fs.mkdirSync(folder);
  const {base,stop}=await startServer(folder,true);
  const page=await context.newPage();
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const api=async(method,url,data,expected=200)=>{
    const response=await context.request.fetch(base+url,{method,data});
    assert.equal(response.status(),expected,`${method} ${url}: ${await response.text()}`);return response.json();
  };
  try {
    await api('POST','/api/sign-in',{email:'leo.marquez@tutti.demo',password:'demo'});
    const college=(await api('GET','/api/opportunities?type=college_audition')).opportunities[0];
    assert(college);assert.equal(college.genre,'');assert.deepEqual(college.eligibility,[]);assert.equal(college.student_hub,false);
    await page.goto(base+'/students.html');await page.locator('#studentQuery').waitFor();
    await page.locator('#studentQuery').fill(college.title);
    assert.equal(await page.locator('#student-auditions article').count(),1);
    assert.match(await page.locator('#student-auditions').innerText(),/Student eligibility not specified/);
    for(const level of ['high_school','college']) {
      await page.locator('#studentLevel').selectOption(level);assert.equal(await page.locator('#student-auditions article').count(),0);
    }
    await page.locator('#studentClear').click();await page.locator('#studentQuery').fill(college.title);
    await page.locator('#student-auditions a').click();await page.locator('h1').waitFor();
    assert(page.url().endsWith(`audition.html?id=${college.id}`));
    const clip=(await api('GET','/api/musicians/leo-marquez')).clips[0];
    await api('POST',`/api/auditions/${college.id}/submissions`,{clip_id:clip.id},201);
    await page.goto(base+'/applications.html');await page.locator('#applicationQuery').waitFor();
    await page.locator('#applicationQuery').fill(college.title);assert.equal(await page.locator('#available article').count(),0);
    await page.locator('#submittedTab').click();assert.equal(await page.locator('#submitted article').count(),1);
    assert.match(await page.locator('#submitted').innerText(),/Submitted/);
    const unchanged=(await api('GET',`/api/opportunities/${college.id}`)).opportunity;
    assert.equal(unchanged.genre,'');assert.deepEqual(unchanged.eligibility,[]);assert.equal(unchanged.student_hub,false);
    assert.deepEqual(errors,[],'Legacy discovery uncaught JavaScript errors');
    console.log('PASS populated-v3 college unknown metadata, discovery/detail/submission/history preserved');
  } finally {await page.close();await stop();}
};
