/* One-way individual notices: anonymous selection, isolated delivery, pool regression. */
const assert = require('node:assert/strict');
module.exports = async function ({page,api,open,signIn,checkViewport,aid,sid}) {
  await signIn('leo.marquez');
  const clip = (await api('GET','/api/musicians/leo-marquez')).clips[0];
  await api('POST',`/api/auditions/${aid}/submissions`,{clip_id:clip.id},201);
  await signIn('elena.voss');
  await open(`/manage.html?audition=${aid}`,'[data-individual]');
  const card = page.locator(`article[data-id="${aid}"]`);
  const form = card.locator('[data-individual]');
  const recipient = form.getByLabel('Recipient');
  assert.equal(await recipient.inputValue(),'');
  assert.deepEqual(await recipient.locator('option').allTextContents(),[
    'Choose one applicant', ...(await api('GET',`/api/auditions/${aid}/submissions`)).submissions.map(s=>s.musician.name)
  ]);
  assert(!/Aiko|Nakamura|Leo|Marquez|@tutti/.test(await card.innerText()));
  for (const dark of [false,true]) {
    if ((await page.locator('body').evaluate(el=>el.classList.contains('dark')))!==dark) await page.locator('#themeButton').click();
    await page.setViewportSize({width:320,height:844});
    await checkViewport('individual notice '+(dark?'dark':'light'));
    assert(await recipient.isVisible());
    assert(await form.getByLabel('Message to selected applicant').isVisible());
  }
  await recipient.focus();
  await recipient.selectOption(String(sid));
  await recipient.press('Tab');
  assert(await form.locator('textarea').evaluate(el=>el===document.activeElement));
  const message = 'Selected applicant only: bring the marked score.';
  await form.locator('textarea').fill(message);
  await form.locator('textarea').press('Tab');
  assert(await form.locator('button').evaluate(el=>el===document.activeElement));
  const sent = page.waitForResponse(r=>r.url().endsWith(`/auditions/${aid}/notices`) && r.request().method()==='POST');
  await form.locator('button').press('Enter');
  assert.equal((await sent).status(),200);
  await page.getByText('Notice recorded for the selected applicant only. Email simulated locally.',{exact:true}).waitFor();
  assert.equal(await recipient.inputValue(),'');
  assert.equal(await form.locator('textarea').inputValue(),'');
  assert(await recipient.evaluate(el=>el===document.activeElement));
  await card.getByText('Local simulated email outbox (2)',{exact:true}).click();
  await card.getByText(message+' — simulated',{exact:true}).waitFor();
  const outbox = (await api('GET',`/api/auditions/${aid}/outbox`)).outbox;
  assert(outbox.every(item=>Object.keys(item).sort().join(',')==='body,state'));
  await card.locator('[data-bulk] textarea').fill('Both applicants: the pool announcement still works.');
  const bulk = page.waitForResponse(r=>r.url().endsWith('/announcements'));
  await card.locator('[data-bulk] button').click();
  assert.equal((await (await bulk).json()).delivered,2);
  await card.getByText('Local simulated email outbox (4)',{exact:true}).waitFor();
  for (const [who,received] of [['aiko.nakamura',true],['leo.marquez',false]]) {
    await signIn(who);
    await open('/notices.html','h1');
    await page.getByText('Both applicants: the pool announcement still works.',{exact:true}).waitFor();
    assert.equal(await page.getByText(message,{exact:true}).count(),received?1:0);
  }
  await page.setViewportSize({width:1440,height:1000});
  await signIn('elena.voss');
  console.log('PASS individual anonymous recipient, keyboard, mobile/themes, simulated outbox, receipt isolation and pool regression');
};
