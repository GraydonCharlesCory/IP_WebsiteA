/* Real populated pre-change round-four data, not a reset or live database. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const startServer=require('./render_server.cjs');
module.exports=async function({context,scratch,evidence}) {
  const folder=path.join(scratch,'enrichment');fs.mkdirSync(folder);
  const {base,stop}=await startServer(folder,'enrichment');
  const page=await context.newPage();
  const errors=[];page.on('pageerror',error=>errors.push(error.message));
  const api=async(method,url,data,expected=200)=>{
    const r=await context.request.fetch(base+url,{method,data});
    assert.equal(r.status(),expected,`${method} ${url}: ${await r.text()}`);return r.json();
  };
  const open=async(url,selector)=>{await page.goto(base+url);await page.locator(selector).first().waitFor();};
  const noOverflow=async()=>assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Enrichment page overflow');
  try {
    await api('POST','/api/sign-in',{email:'leo.marquez@tutti.demo',password:'demo'});
    const schools=(await api('GET','/api/schools')).schools;
    const lake=schools.find(s=>s.name==='Lakefront Conservatory');
    const prairie=schools.find(s=>s.name==='Prairie Arts Academy');
    assert.deepEqual(lake.demo_enrichment.alumni,[]);
    assert.equal(prairie.demo_enrichment.alumni.length,2);
    for(const handle of ['leo-marquez','dana-brooks','aiko-nakamura','maya-okafor','jordan-wells','adam-reyes','ronald-pierce','alex-chen','sofia-lindgren']) {
      const profile=await api('GET','/api/musicians/'+handle);
      assert(!('stats' in profile));
      await open('/profile.html?h='+handle,'.credentials');
      assert.equal(await page.locator('.stats').count(),0);
      assert(await page.locator('.idrow').evaluate(el=>el.nextElementSibling.matches('.credentials')));
      const text=await page.locator('.credentials').innerText();
      assert(!/\b\d+\s+(Clips|Posts)\b/i.test(await page.locator('main.wrap').innerText()));
      if(handle==='leo-marquez') {
        assert.match(text,/Authored <degree> & study/);assert.match(text,/Authored <certificate> & practice/);
        assert(!text.includes('Simulated'));assert.equal(await page.locator('.credentials degree, .credentials certificate').count(),0);
        assert.equal(await page.locator('.side').getByRole('heading',{name:'Certifications',exact:true}).count(),0);
        await page.locator('.credentials a').focus();await page.keyboard.press('Enter');
        await page.locator('#schoolGlance').waitFor();assert(page.url().endsWith('schools.html?id='+lake.id));
      } else {
        assert.equal((text.match(/Simulated example/g)||[]).length,2);
        assert.match(text,/not verified/);assert(!text.includes('Verified by Tutti'));
      }
    }
    for(const width of [1440,390]) for(const dark of [false,true]) {
      await page.setViewportSize({width,height:1000});
      await open('/profile.html?h=aiko-nakamura','.credentials');
      if((await page.locator('body').evaluate(el=>el.classList.contains('dark')))!==dark) await page.locator('#themeButton').click();
      assert(await page.locator('.credentials').isVisible());await noOverflow();
      await page.screenshot({path:path.join(evidence,`credentials-${width}-${dark?'dark':'light'}.png`),fullPage:true});
      for(const school of [lake,prairie]) {
        await open('/schools.html?id='+school.id,'#schoolPosts');
        assert(await page.locator('#schoolGlance').evaluate(el=>el.nextElementSibling.id==='schoolPosts'));
        assert.equal(await page.locator('#schoolPosts article').count(),2);
        assert.equal((await page.locator('#schoolPosts').innerText()).match(/Simulated school update/g).length,2);
        if(school.id===lake.id) assert.match(await page.locator('.school-identity').innerText(),/Authored <school> & story/);
        assert.equal(await page.locator('[data-edit], [data-alumni], [data-remove]').count(),0);
        await noOverflow();
        await page.locator('#schoolTab-overview').focus();await page.keyboard.press('End');
        assert.equal(await page.locator('#schoolTab-alumni').getAttribute('aria-selected'),'true');
        assert(!(await page.locator('#schoolPosts').isVisible()));
        if(school.id===lake.id) {assert.equal(await page.locator('.demo-alumni').count(),0);assert.match(await page.locator('#schoolPanel-alumni').innerText(),/Leo Marquez/);}
        else {assert.equal(await page.locator('.demo-alumni .listline').count(),2);assert.equal((await page.locator('.demo-alumni').innerText()).match(/Simulated alumnus/g).length,2);assert.equal(await page.locator('.demo-alumni a').count(),0);assert.match(await page.locator('.demo-alumni').innerText(),/demo only/);}
        await page.keyboard.press('Home');assert(await page.locator('#schoolPosts').isVisible());
        await noOverflow();
        await page.screenshot({path:path.join(evidence,`school-posts-${school.id}-${width}-${dark?'dark':'light'}.png`),fullPage:true});
      }
    }
    const college=(await api('GET','/api/opportunities?type=college_audition')).opportunities[0];
    await open('/audition.html?id='+college.id,'.demo-opportunity');
    assert.match(await page.locator('.demo-opportunity').innerText(),/Simulated opportunity example/);
    assert.match(await page.locator('.demo-opportunity').innerText(),/not organizer requirements/);
    const grant=(await api('GET','/api/opportunities?type=grant')).opportunities[0];
    await open('/audition.html?id='+grant.id,'h1');
    assert.equal(await page.locator('.demo-opportunity').count(),0);
    assert.match(await page.locator('.req').innerText(),/Authored requirement/);
    await api('POST','/api/sign-in',{email:'lakefront.school@tutti.demo',password:'demo'});
    await api('PUT',`/api/schools/${prairie.id}`,{about:'Not mine'},403);
    await open('/schools.html?id='+lake.id,'#editSchool');
    await page.locator('#editSchool').focus();await page.keyboard.press('Enter');
    assert.equal(await page.locator('#schoolEditor details').getAttribute('open'),'');
    assert.equal(await page.locator('[name="about"]').inputValue(),'Authored <school> & story');
    await api('POST','/api/sign-out');
    await open('/profile.html?h=leo-marquez','.credentials');
    assert.match(await page.locator('.credentials').innerText(),/Authored <degree>/);
    assert.deepEqual(errors,[]);
    console.log('PASS populated round-four restart preservation, real/simulated credential separation, zero metrics, school Posts position, alumni, opportunity supplement, escaping, themes, responsive and keyboard');
  } finally {await page.close();await stop();}
};
