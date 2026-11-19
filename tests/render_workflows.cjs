/* Opt-in local rendered checks. Uses explicitly supplied, already installed tools. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const startServer = require('./render_server.cjs');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE);

async function main() {
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'tutti-render-'));
  const evidence = process.env.RENDER_ARTIFACT_DIR || scratch;
  fs.mkdirSync(evidence, {recursive:true});
  const {base,stop} = await startServer(scratch);
  let context;
  try {
    context = await chromium.launchPersistentContext(path.join(scratch,'browser'), {
      executablePath:process.env.CHROME_EXECUTABLE, headless:true,
      viewport:{width:1440,height:1000}, args:['--no-first-run','--disable-background-networking']
    });
    const page = await context.newPage();
    const pageErrors = [];
    page.on('pageerror', e=>pageErrors.push(e.message));
    page.on('console', message=>{if(message.type()==='error') console.error('Browser:',message.text());});
    const api = async (method,url,data,expected=200) => {
      const r = await context.request.fetch(base+url,{method,data});
      assert.equal(r.status(), expected, `${method} ${url}: ${await r.text()}`);
      return r.json();
    };
    const signIn = email => api('POST','/api/sign-in',{email:email+'@tutti.demo',password:'demo'});
    const open = async (url,selector) => {await page.goto(base+url); await page.locator(selector).first().waitFor({state:'attached'});};
    const body = ()=>page.locator('body').innerText();
    const checkViewport = async name => {
      const overflow = await page.evaluate(()=>[...document.querySelectorAll('body *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).map(el=>`${el.tagName}.${el.className}: ${Math.round(el.getBoundingClientRect().right)}`));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${name} overflows narrow viewport: ${overflow.join(', ')}`);
    };
    await open('/index.html','#signinForm');
    assert.equal(await page.locator('#email').evaluate(el=>getComputedStyle(el).backgroundColor),'rgb(255, 253, 248)');
    await page.locator('#submitButton').click();
    await page.getByRole('heading',{name:'Make room for what comes next.'}).waitFor();
    await signIn('leo.marquez');
    await open('/audition.html?id=3','a[href="ensemble.html?id=3"]');
    await page.locator('a[href="ensemble.html?id=3"]').first().click();
    await page.locator('h1').waitFor();
    assert(!(await body()).includes('Priya Raman'));
    await page.screenshot({path:path.join(evidence,'musician-ensemble.png'),fullPage:true});
    const gig = (await api('GET','/api/opportunities?type=gig')).opportunities[0];
    assert(!('director' in gig));
    await open(`/gig.html?id=${gig.id}`,'h1');
    assert(!/Posted by|Marcus Bell/.test(await body()));
    const uploaded = await context.request.post(base+'/api/clips?title=Public%20rendered%20take', {
      headers:{'Content-Type':'video/mp4'}, data:fs.readFileSync(path.join(process.cwd(),'my-clips/aiko-nakamura-1.mp4'))
    });
    assert.equal(uploaded.status(),201);
    const publicClip = (await uploaded.json()).clip;
    await signIn('elena.voss');
    await open('/profile.html?h=leo-marquez',`video[src^="${publicClip.video_url}"]`);
    await page.waitForFunction(url=>[...document.querySelectorAll('video')].some(v=>v.getAttribute('src').startsWith(url)&&v.readyState>=1),publicClip.video_url);
    await api('POST','/api/sign-out');
    assert.equal((await context.request.get(base+publicClip.video_url)).status(),200);
    await signIn('leo.marquez');
    await require('./render_discovery_regressions.cjs')({page,api,open,signIn});
    await require('./render_discovery.cjs')({page,api,open,body,checkViewport,signIn,evidence,publicClip});
    await require('./render_location_search.cjs')({page,api,open,signIn,checkViewport});
    await open('/schools.html','#schoolQuery');
    const schools = (await api('GET','/api/schools')).schools;
    await page.locator('#schoolQuery').fill(schools[0].name);
    assert.equal(await page.locator('.directory-row:visible').count(),1);
    await page.locator('#schoolQuery').fill(schools[0].location);
    assert.equal(await page.locator('.directory-row:visible').count(),schools.filter(s=>s.location.toLowerCase().includes(schools[0].location.toLowerCase())).length);
    await page.locator('#schoolQuery').fill('no-such-school');
    assert(await page.locator('#schoolEmpty').isVisible());
    await page.locator('#clearSchools').click();
    assert.equal(await page.locator('.directory-row:visible').count(),schools.length);
    await open(`/schools.html?id=${schools[0].id}`,'#schoolTab-overview');
    assert.equal(await page.locator('[data-edit], [data-alumni], [data-remove], #editSchool').count(),0);
    await page.locator('#schoolTab-programs').click();
    assert(await page.locator('#schoolPanel-programs').isVisible());
    await page.locator('#schoolTab-programs').press('ArrowRight');
    assert.equal(await page.locator('#schoolTab-alumni').getAttribute('aria-selected'),'true');
    await page.screenshot({path:path.join(evidence,'school-desktop.png'),fullPage:true});
    // Verify theme persistence and readable placeholder tokens in both appearances.
    const placeholderColors = [];
    for (const dark of [false,true]) {
      if ((await page.locator('body').evaluate(el=>el.classList.contains('dark')))!==dark) await page.locator('#themeButton').click();
      await open('/schools.html','#schoolQuery');
      assert.equal(await page.locator('body').evaluate(el=>el.classList.contains('dark')),dark);
      placeholderColors.push(await page.locator('#schoolQuery').evaluate(el=>getComputedStyle(el,'::placeholder').color));
      const contrast = await page.locator('#schoolQuery').evaluate(el=>{
        const luminance = color => color.match(/[\d.]+/g).slice(0,3).map(Number).map(v=>{v/=255;return v<=0.04045?v/12.92:((v+0.055)/1.055)**2.4;}).reduce((sum,v,i)=>sum+v*[0.2126,0.7152,0.0722][i],0);
        const a=luminance(getComputedStyle(el,'::placeholder').color), b=luminance(getComputedStyle(el).backgroundColor);
        return (Math.max(a,b)+0.05)/(Math.min(a,b)+0.05);
      });
      assert(contrast>=4.5,`Placeholder contrast ${contrast} in ${dark?'dark':'light'} appearance`);
      await page.screenshot({path:path.join(evidence,`directory-${dark?'dark':'light'}.png`),fullPage:true});
    }
    assert.notEqual(...placeholderColors);
    await page.locator('#themeButton').click();
    await page.setViewportSize({width:320,height:844});
    for (const [url,selector,name] of [['/schools.html','#schoolQuery','directory'],[`/schools.html?id=${schools[0].id}`,'#schoolTab-overview','school'],['/applications.html','#applicationQuery','applications'],['/feed.html','.greet','community']]) {
      await open(url,selector);
      await page.screenshot({path:path.join(evidence,`${name}-mobile.png`),fullPage:true});
      await checkViewport(name);
      assert(await page.locator('nav a[href="schools.html"]').isVisible());
      if (name==='community') {
        assert.equal(await page.locator('.cats').count(),0);
        assert.match(await body(),/Open auditions/);
        assert.match(await body(),/Trending clips/);
        assert(await page.locator('.clips a[href^="profile.html"]').count()>0);
        assert.equal(await page.locator('.video .dur').first().evaluate(el=>getComputedStyle(el).color),'rgb(255, 253, 248)');
      }
      await page.screenshot({path:path.join(evidence,`${name}-mobile.png`),fullPage:true});
    }
    await page.setViewportSize({width:1440,height:1000});
    await open('/profile-edit.html','#profileForm');
    await page.locator('[name="instrument"]').fill('Tenor saxophone');
    await page.locator('[name="location"]').fill('Chicago, IL');
    const schoolOptions = await page.locator('[data-school]').first().locator('option').evaluateAll(nodes=>nodes.map(n=>n.value).filter(Boolean));
    await page.locator('[data-school]').nth(0).selectOption(schoolOptions[0]);
    await page.locator('[data-degree]').nth(0).fill('Bachelor of Music');
    await page.locator('[data-school]').nth(1).selectOption(schoolOptions[1]);
    await page.locator('[data-degree]').nth(1).fill('Summer certificate');
    await page.locator('[name="certifications"]').fill('First aid');
    const profileSaved = page.waitForResponse(r=>r.url().endsWith('/api/me') && r.request().method()==='PUT');
    await page.locator('#profileForm button').click(); assert.equal((await profileSaved).status(),200);
    assert.equal((await api('GET','/api/me')).user.education.length,2);
    await open('/profile.html?h=leo-marquez','a[href^="schools.html?id="]');
    assert.match(await body(),/Bachelor of Music/);
    console.log('PASS musician Discovery, application tabs, education/profile links');

    await signIn('elena.voss');
    await open('/manage.html','#createForm');
    await page.locator('summary').first().click();
    await page.locator('[name="title"]').fill('Rendered blind audition');
    await page.locator('[name="genre"]').selectOption('Rock');
    await page.locator('[name="eligibility"][value="high_school"]').check();
    await page.locator('[name="student_hub"]').check();
    await page.locator('[name="deadline"]').fill('2027-05-01');
    await page.locator('[name="rubric"]').fill('sound\ninterpretation');
    const created = page.waitForResponse(r=>r.url().endsWith('/api/opportunities') && r.request().method()==='POST');
    await page.locator('#createForm button').click();
    const creation = await created; assert.equal(creation.status(),201);
    const authoredOpportunity = (await creation.json()).opportunity;
    assert.equal(authoredOpportunity.genre,'Rock');
    assert.deepEqual(authoredOpportunity.eligibility,['high_school']);
    assert.equal(authoredOpportunity.student_hub,true);
    const aid = authoredOpportunity.id;
    await page.locator(`article[data-id="${aid}"]`).waitFor();
    await signIn('aiko.nakamura');
    const clips = (await api('GET','/api/musicians/aiko-nakamura')).clips;
    const sid = (await api('POST',`/api/auditions/${aid}/submissions`,{clip_id:clips[0].id,note:'My name is Aiko Nakamura',timestamps:[{time:0,label:'Aiko plays'}]},201)).submission.id;
    await open(`/audition.html?id=${aid}`,'h1');
    assert(!(await body()).includes('Elena Voss'));
    await signIn('elena.voss');
    // Exercise the honest unsupported-browser path without microphone permission.
    await page.addInitScript(()=>{window.SpeechRecognition=undefined;window.webkitSpeechRecognition=undefined;});
    await open(`/review.html?id=${sid}`,'#comments');
    assert(!/Aiko|Nakamura|My name is/.test(await body()));
    assert.equal(await page.locator('#playerRoot video').count(),0);
    await page.waitForFunction(()=>{const a=document.querySelector('#playerRoot audio');return a && a.readyState>=1 && a.duration>0;});
    await page.setViewportSize({width:390,height:844});
    await checkViewport('director blind review');
    assert.equal(await page.locator('.sidebar').count(),1);
    assert(!/Aiko|Nakamura|My name is/.test(await body()));
    await page.screenshot({path:path.join(evidence,'director-blind-mobile.png')});
    await page.setViewportSize({width:1440,height:1000});
    assert.match(await body(),/Voice-to-text is unavailable/);
    await page.locator('[data-criterion="sound"][data-value="8"]').click();
    await page.locator('[data-criterion="interpretation"][data-value="10"]').click();
    await page.locator('#comments').fill('Well shaped musical phrases.');
    await page.locator('#shareButton').click();
    await page.getByText('✓ Shared',{exact:true}).waitFor();
    assert.equal((await api('GET',`/api/submissions/${sid}`)).submission.review.average,9);
    await open('/manage.html',`article[data-id="${aid}"]`);
    const card = page.locator(`article[data-id="${aid}"]`);
    await card.locator('[data-review]').click();
    await card.locator('[data-invite]').click();
    const guestLink = card.locator('[data-link] a'); await guestLink.waitFor();
    const guestUrl = await guestLink.getAttribute('href');
    await card.locator('[data-bulk] textarea').fill('Please prepare your callback repertoire.');
    const sent = page.waitForResponse(r=>r.url().endsWith('/announcements'));
    await card.locator('[data-bulk] button').click(); assert.equal((await sent).status(),200);
    await card.getByText('Local simulated email outbox (1)',{exact:true}).waitFor();
    console.log('PASS director creation, custom rubric, blind decoded audio, typed feedback/fallback and simulated announcements');
    await require('./render_messaging.cjs')({page,api,open,signIn,checkViewport,aid,sid});

    await api('POST','/api/sign-out');
    await open(guestUrl,`article[data-id="${sid}"]`);
    assert(!page.url().includes('#'));
    assert(!/Aiko|Nakamura|Creator-only composite|Overall score/.test(await body()));
    const guestCard = page.locator(`article[data-id="${sid}"]`);
    await guestCard.locator('[data-play]').click();
    await page.waitForFunction(()=>{const a=document.querySelector('article audio');return a && a.readyState>=1 && a.duration>0;});
    assert.equal(await page.locator('video').count(),0);
    await guestCard.locator('[name="sound"]').fill('6');
    await guestCard.locator('[name="interpretation"]').fill('8');
    await guestCard.locator('form button').click();
    await guestCard.getByText('Scores saved.').waitFor();
    await signIn('elena.voss');
    await open(`/review.html?id=${sid}`,'#comments');
    assert.match(await body(),/Creator-only composite: 8 /);
    await signIn('rhonda.holloway');
    await open(`/review.html?id=${sid}`,'h2');
    assert.match(await body(),/This submission is private/);
    assert(!/Creator-only composite/.test(await body()));
    await signIn('aiko.nakamura');
    await open('/applications.html','#submittedTab');
    await page.locator('#submittedTab').click();
    assert.match(await body(),/Well shaped musical phrases/);
    assert(!/Creator-only composite|Overall score|\/10/.test(await body()));
    await open('/notices.html','h1');
    await page.getByText('Please prepare your callback repertoire.').waitFor();
    console.log('PASS guest scoped audio/scoring, creator composite, other-director denial, musician feedback/notice isolation');

    await signIn('lakefront.school');
    await open('/schools.html','#schoolQuery');
    await page.locator('.directory-row').filter({hasText:'Your school'}).getByRole('link',{name:'View school'}).click();
    await page.locator('form[data-edit]').waitFor({state:'attached'});
    assert.equal(await page.locator('form[data-edit]').count(),1);
    const owned = page.locator('form[data-edit]');
    await owned.locator('xpath=..').locator('summary').click();
    await owned.locator('[name="programs"]').fill('Bachelor of Music\nSummer orchestra');
    const schoolSaved = page.waitForResponse(r=>r.url().includes('/api/schools/') && r.request().method()==='PUT');
    await owned.locator('button').click(); assert.equal((await schoolSaved).status(),200);
    await page.getByRole('listitem').filter({hasText:'Summer orchestra'}).waitFor();
    await page.locator('#editSchool').click();
    await page.locator('[data-alumni] [name="handle"]').fill('leo-marquez');
    const alumniAdded = page.waitForResponse(r=>r.url().includes('/alumni/')&&r.request().method()==='PUT');
    const alumniReloaded = page.waitForResponse(r=>r.url().endsWith('/api/schools')&&r.request().method()==='GET');
    await page.locator('[data-alumni] button').click();
    const addedResponse = await alumniAdded;
    assert.equal(addedResponse.status(),200);
    assert((await addedResponse.json()).school.alumni.some(a=>a.handle==='leo-marquez'));
    assert((await (await alumniReloaded).json()).schools.some(s=>s.alumni.some(a=>a.handle==='leo-marquez')));
    const alumni = page.locator('#schoolPanel-alumni .listline').filter({hasText:'Leo Marquez'});
    await alumni.waitFor({state:'attached'});
    await page.locator('#schoolTab-alumni').click();
    await alumni.getByRole('link').waitFor();
    await page.setViewportSize({width:390,height:844});
    await checkViewport('school owner alumni');
    assert(await alumni.locator('[data-remove]').isVisible());
    await page.screenshot({path:path.join(evidence,'school-owner-mobile.png'),fullPage:true});
    await page.setViewportSize({width:1440,height:1000});
    const alumniRemoved = page.waitForResponse(r=>r.url().includes('/alumni/')&&r.request().method()==='DELETE');
    await alumni.locator('[data-remove]').click();
    const removedResponse = await alumniRemoved;
    assert.equal(removedResponse.status(),200);
    assert.deepEqual((await removedResponse.json()).school.alumni,[]);
    await alumni.waitFor({state:'detached'});
    assert(!(await page.locator('.schools-page').innerText()).includes('Leo Marquez'));
    await open('/manage.html','#createForm');
    assert.equal(await page.locator('[name="school_id"] option').count(),1);
    await page.locator('summary').first().click();
    await page.locator('[name="title"]').fill('School rendered posting');
    await page.locator('[name="deadline"]').fill('2027-05-01');
    const schoolCreated = page.waitForResponse(r=>r.url().endsWith('/api/opportunities') && r.request().method()==='POST');
    await page.locator('#createForm button').click();
    const schoolResponse = await schoolCreated; assert.equal(schoolResponse.status(),201);
    const schoolId = (await schoolResponse.json()).opportunity.id;
    const schoolCard = page.locator(`article[data-id="${schoolId}"]`);
    await schoolCard.getByRole('link',{name:'View page'}).click();
    await page.getByRole('link',{name:'Open submissions'}).click();
    await page.locator(`article[data-id="${schoolId}"] [data-invite]`).waitFor();
    assert(page.url().includes('manage.html?audition='));
    assert.match(await body(),/No submissions yet/);
    await signIn('elena.voss');
    await api('GET',`/api/auditions/${schoolId}/submissions`,undefined,403);
    await signIn('lakefront.school');
    console.log('PASS school create, actual Open submissions button, owned administration and other-owner denial');
    const aliasGuest = await api('POST',`/api/auditions/${schoolId}/guests`,{label:'Alias check'});
    const aliasKey = aliasGuest.url.split('#')[1];
    await signIn('leo.marquez');
    await api('POST',`/api/auditions/${schoolId}/submissions`,{clip_id:publicClip.id},201);
    const protectedUrls = [publicClip.video_url, '/media/clips/leo-marquez-2.mp4'];
    for (const url of protectedUrls) assert.equal((await context.request.get(base+url)).status(),200);
    for (const role of [null,'elena.voss','lakefront.school']) {
      if (role) await signIn(role); else await api('POST','/api/sign-out');
      for (const url of protectedUrls) {
        const split = url.lastIndexOf('/');
        const alias = url.slice(0,split+1)+url.slice(split+1).toUpperCase();
        for (const method of ['GET','HEAD']) {
          const response = await context.request.fetch(base+alias,{method,headers:{Range:'bytes=0-3','X-Review-Key':aliasKey}});
          assert.equal(response.status(),role ? 403 : 401);
        }
      }
    }
    console.log('PASS both raw media case aliases denied for anonymous, director, school and valid guest capability, including HEAD/Range');
    assert.deepEqual(pageErrors,[], 'Uncaught browser JavaScript errors');
    await page.screenshot({path:path.join(evidence,'school-manage.png'),fullPage:true});
    await require('./render_legacy_discovery.cjs')({context,scratch});
    await require('./render_demo_enrichment.cjs')({context,scratch,evidence});
    console.log('Rendered workflows passed. Evidence directory: '+evidence);
  } finally {
    if(context) await context.close();
    await stop();
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
