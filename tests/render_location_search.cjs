/* Uses the parent workflow's isolated database, public API and browser lifecycle. */
const assert = require('node:assert/strict');
module.exports = async function ({page,api,open,signIn,checkViewport}) {
  await signIn('leo.marquez');
  const [{opportunities},{applications},{previews},{schools},{musicians}] = await Promise.all([
    api('GET','/api/opportunities?status=open'),api('GET','/api/my/applications'),
    api('GET','/api/discovery'),api('GET','/api/schools'),api('GET','/api/musicians')
  ]);
  async function exercise({url,prefix,query,reset,tabs}) {
    await open(url,`#${prefix}Region`);
    const region=page.locator(`#${prefix}Region`),city=page.locator(`#${prefix}City`),text=page.locator(`#${prefix}Location`);
    for (const control of [region,city,text]) {
      assert(await control.isVisible());
      assert(await control.evaluate(el=>el.labels.length>0));
    }
    const allOptions=await city.locator('option').count();
    assert(await city.locator('option[value="Chicago|IL"]').count());
    for (const tab of tabs) {
      if(tab.button) await page.locator(tab.button).click();
      const cards=page.locator(tab.cards);
      const original=await cards.allTextContents();
      assert.equal(original.length,tab.records.length,`${prefix} baseline ${tab.cards}`);
      await region.selectOption('Midwest');
      await city.selectOption('Chicago|IL');
      const expected=await page.evaluate(records=>records.filter(record=>Tutti.locationSearch.matches(record,{region:'Midwest',city:'Chicago|IL'})).length,tab.records);
      assert.equal(await cards.count(),expected,`${prefix} region AND city ${tab.cards}`);
      assert(expected>0,`${prefix}: Chicago fixture exercises positive result`);
      if(tabs.length>1) {
        const other=tabs.find(other=>other!==tab);
        await page.locator(other.button).click();
        assert.equal(await region.inputValue(),'Midwest');assert.equal(await city.inputValue(),'Chicago|IL');
        await page.locator(tab.button).click();assert.equal(await cards.count(),expected);
      }
      if(tab.constraint) {
        const [selector,value,predicate]=tab.constraint;
        await page.locator(selector).selectOption(value);
        const count=await page.evaluate(({records,value,predicate})=>records.filter(record=>Tutti.locationSearch.matches(record,{region:'Midwest',city:'Chicago|IL'})&&(predicate==='level'?record.eligibility.includes(value):record[predicate]===value)).length,{records:tab.records,value,predicate});
        assert.equal(await cards.count(),count,`${prefix}: existing filter AND geography`);
        await page.locator(selector).selectOption('');
      }
      await page.locator(query).fill('zz-no-location-fixture-match-zz');
      assert.equal(await cards.count(),0,`${prefix}: keyword AND geography`);
      await page.locator(query).fill('');
      await text.fill('Boston');assert.equal(await cards.count(),0,`${prefix}: text AND city`);
      await text.fill('');assert.equal(await cards.count(),expected);
      await region.selectOption('Northeast');
      assert.equal(await city.inputValue(),'');assert.equal(await city.locator('option[value="Chicago|IL"]').count(),0);
      await region.selectOption('');assert.equal(await city.locator('option').count(),allOptions);
      await city.selectOption('Chicago|IL');assert.equal(await cards.count(),expected,`${prefix}: city with all regions`);
      await page.locator(reset).click();
      for(const control of [region,city,text,page.locator(query)]) assert.equal(await control.inputValue(),'');
      assert.deepEqual(await cards.allTextContents(),original,`${prefix}: reset retains active tab`);
    }
    await region.focus();await page.keyboard.press('Tab');
    assert(await city.evaluate(el=>document.activeElement===el));
    for(const dark of [false,true]) {
      if(await page.locator('body').evaluate(el=>el.classList.contains('dark'))!==dark) await page.locator('#themeButton').click();
      await page.setViewportSize({width:320,height:844});
      for(const control of [region,city,text]) {
        const bounds=await control.boundingBox();assert(bounds&&bounds.width>0&&bounds.x>=0&&bounds.x+bounds.width<=321);
      }
      await checkViewport(`${prefix} geography ${dark?'dark':'light'}`);
    }
    await page.setViewportSize({width:1440,height:1000});
  }
  await exercise({url:'/applications.html',prefix:'application',query:'#applicationQuery',reset:'#clearApplicationSearch',tabs:[
    {button:'#availableTab',cards:'#available article:visible',records:[...opportunities.filter(o=>o.type!=='college_audition'&&!o.my_submission),...previews.filter(o=>o.type==='teaching')],constraint:['[data-search="type"]','teaching','type']},
    {button:'#submittedTab',cards:'#submitted article:visible',records:applications.map(a=>a.opportunity)}
  ]});
  await exercise({url:'/students.html',prefix:'student',query:'#studentQuery',reset:'#studentClear',tabs:[
    {button:'#tab-student-auditions',cards:'#student-auditions article:visible',records:opportunities.filter(o=>o.type==='college_audition'||o.type==='audition'&&o.student_hub),constraint:['#studentLevel','high_school','level']},
    {button:'#tab-clinics',cards:'#clinics article:visible',records:previews.filter(o=>o.type==='clinic')},
    {button:'#tab-colleges',cards:'#colleges article:visible',records:schools}
  ]});
  await exercise({url:'/schools.html',prefix:'school',query:'#schoolQuery',reset:'#clearSchools',tabs:[{cards:'.directory-row:visible',records:schools}]});
  await exercise({url:'/musicians.html',prefix:'musician',query:'#musicianQuery',reset:'#musicianReset',tabs:[{cards:'#musicianResults article:visible',records:musicians}]});
  // Public keyword boundary is unchanged: geography is separate from name/instrument/city.
  await page.locator('#musicianQuery').fill('MA');assert.equal(await page.locator('#musicianResults article').count(),musicians.filter(m=>[m.name,m.instrument,m.location.split(',')[0]].join(' ').toLowerCase().includes('ma')).length);
  await page.locator('#musicianReset').click();
  await api('POST','/api/sign-out');await open('/musicians.html','#musicianRegion');
  await page.locator('#musicianRegion').selectOption('Midwest');await page.locator('#musicianCity').selectOption('Chicago|IL');
  assert.equal(await page.locator('#musicianResults article').count(),musicians.filter(m=>m.location==='Chicago, IL').length);
  await signIn('leo.marquez');
  console.log('PASS region/city controls across Applications, all Students tabs, Schools and public musicians');
};
