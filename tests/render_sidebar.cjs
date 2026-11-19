/* Sidebar affordances use the existing isolated loopback/browser fixture. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const startServer = require('./render_server.cjs');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE);

async function appearance(link) {
  return link.evaluate(el => {
    const style = getComputedStyle(el);
    const luminance = color => color.match(/[\d.]+/g).slice(0,3).map(Number).map(v => {
      v /= 255;
      return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
    }).reduce((sum,v,i) => sum + v * [0.2126,0.7152,0.0722][i],0);
    const a = luminance(style.color), b = luminance(style.backgroundColor);
    return {background:style.backgroundColor, border:style.borderTopStyle,
      shadow:style.boxShadow, weight:style.fontWeight, outline:style.outlineStyle,
      outlineWidth:parseFloat(style.outlineWidth), focused:el.matches(':focus-visible'),
      contrast:(Math.max(a,b)+0.05)/(Math.min(a,b)+0.05)};
  });
}

async function main() {
  const scratch = fs.mkdtempSync(path.join(os.tmpdir(),'tutti-sidebar-'));
  const evidence = process.env.RENDER_ARTIFACT_DIR || scratch;
  fs.mkdirSync(evidence,{recursive:true});
  const {base,stop} = await startServer(scratch);
  let browser;
  try {
    browser = await chromium.launch({executablePath:process.env.CHROME_EXECUTABLE,headless:true});
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror',error => errors.push(error.message));
    const login = async email => {
      const response = await page.request.post(base+'/api/sign-in',{data:{email:email+'@tutti.demo',password:'demo'}});
      assert.equal(response.status(),200);
    };
    await login('leo.marquez');
    await page.goto(base+'/students.html');
    await page.locator('.sidebar .nav a.on').waitFor();
    const destinations = await page.locator('.sidebar .nav a').evaluateAll(links => links.map(el => el.getAttribute('href')));
    assert.deepEqual(destinations,['discover.html','students.html','applications.html','schools.html','feed.html','teachers.html']);
    for (const width of [1440,900,390,320]) for (const dark of [false,true]) {
      await page.setViewportSize({width,height:1000});
      if (await page.locator('body').evaluate(el => el.classList.contains('dark')) !== dark) await page.locator('#themeButton').click();
      await page.mouse.move(width-1,999);
      const active = page.locator('.sidebar .nav a.on');
      const resting = page.locator('.sidebar .nav a[href="schools.html"]');
      const sidebarBackground = await page.locator('.sidebar').evaluate(el => getComputedStyle(el).backgroundColor);
      assert.notEqual(sidebarBackground,await page.locator('body').evaluate(el => getComputedStyle(el).backgroundColor),'Navigation surface must differ from page');
      const normal = await appearance(resting), selected = await appearance(active);
      assert.equal(normal.border,'solid','Resting tabs need a visible edge');
      assert.notEqual(normal.background,sidebarBackground,'Resting tabs need their own surface');
      assert.notEqual(selected.background,normal.background);
      assert.notEqual(selected.shadow,'none','Active tab needs a non-fill marker');
      assert(Number(selected.weight)>Number(normal.weight));
      for (const link of [resting,active]) assert((await appearance(link)).contrast>=4.5,'Readable tab label');
      await resting.hover();
      const hovered = await appearance(resting);
      assert.notEqual(hovered.background,normal.background);
      assert.notEqual(hovered.background,selected.background,'Hover cannot mimic selection');
      assert(hovered.contrast>=4.5);
      await active.hover();
      assert.equal((await appearance(active)).shadow,selected.shadow,'Hover preserves selection marker');
      await page.locator('.sidebar .nav a[href="applications.html"]').press('Tab');
      const focused = await appearance(resting);
      assert(focused.focused && focused.outline !== 'none' && focused.outlineWidth>=2,'Keyboard focus ring');
      assert(await page.evaluate(() => document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow');
      assert(await resting.evaluate(el => el.getBoundingClientRect().height>=44),'Touch target');
      await page.screenshot({path:path.join(evidence,`sidebar-${width}-${dark?'dark':'light'}.png`)});
      await page.keyboard.press('Enter');
      await page.waitForURL('**/schools.html');
      await page.locator('#schoolQuery').waitFor();
      assert.equal(await page.locator('.sidebar .nav a.on').getAttribute('href'),'schools.html');
      await page.goto(base+'/students.html');
      await page.locator('#studentQuery').waitFor();
    }
    for (const destination of destinations) {
      await page.locator(`.sidebar .nav a[href="${destination}"]`).click();
      await page.waitForURL('**/'+destination);
      await page.locator('.sidebar .nav a.on').waitFor();
      assert.equal(await page.locator('.sidebar .nav a.on').getAttribute('href'),destination);
    }
    for (const [account,destination] of [['elena.voss','director.html'],['lakefront.school','manage.html']]) {
      await login(account);
      await page.goto(base+'/'+destination);
      await page.locator('.sidebar .nav a.on').waitFor();
      assert.equal(await page.locator('.sidebar .nav a[href="manage.html"]').count(),1);
      assert.equal(await page.locator('.sidebar .nav a[href="applications.html"]').count(),0);
    }
    assert.deepEqual(errors,[]);
    console.log('PASS sidebar surfaces, label contrast, active/hover/keyboard states, 1440/900/390/320, both themes, destinations and role links');
  } finally {
    if (browser) await browser.close();
    await stop();
  }
}
main().catch(error => {console.error(error);process.exitCode=1;});
