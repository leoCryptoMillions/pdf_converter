/* Optional Chromium check. Uses the same Playwright environment variables as local_review_ui.cjs. */
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PDF_UI_PLAYWRIGHT_MODULE || 'playwright');

(async () => {
  const browser = await chromium.launch({headless:true,
    ...(process.env.PDF_UI_CHROMIUM_EXECUTABLE ? {executablePath:process.env.PDF_UI_CHROMIUM_EXECUTABLE} : {})});
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(pathToFileURL(path.resolve('prototipos/preparacion-brechas/index.html')).href);
    const coverage = await page.locator('.legend-note').allTextContents();
    assert(coverage.some(text => text.includes('18%') && text.includes('27%')));
    const open = async id => {
      await page.locator(`[data-open="${id}"]`).first().click();
      assert(await page.locator('#detail-dialog').isVisible());
    };
    await open('F0-04');
    assert((await page.locator('#detail-source').textContent()).includes('2026-10-26'));
    await page.locator('#field-F0-04-context').fill('Cancelled draft');
    await page.locator('#detail-cancel').click();
    await open('F0-04');
    assert.equal(await page.locator('#field-F0-04-context').inputValue(), '');
    await page.locator('#field-F0-04-context').fill('Browser check: editable Word with layout');
    await page.locator('#detail-save').click();
    await open('F0-04');
    assert.equal(await page.locator('#field-F0-04-context').inputValue(), 'Browser check: editable Word with layout');
    await page.locator('#detail-cancel').click();
    await open('F0-11');
    assert((await page.locator('#detail-source').textContent()).includes('implementado y verificado el 2026-10-23'));
    await page.locator('#detail-cancel').click();
    const artifacts = path.resolve('.generated/docx-review');
    fs.mkdirSync(artifacts,{recursive:true});
    const [download] = await Promise.all([
      page.waitForEvent('download'), page.locator('#btn-download').click()
    ]);
    const exportPath = path.join(artifacts,'dashboard-draft.json');
    await download.saveAs(exportPath);
    const draft = JSON.parse(fs.readFileSync(exportPath,'utf8'));
    assert.equal(draft.validated,false);
    const word = draft.deliverables.find(d => d.id === 'F0-04');
    assert.equal(word.implementation_status,'partial');
    assert.equal(word.verification_status,'pending');
    assert.equal(word.decision_status,'pending');
    assert.equal(word.fields.find(f => f.key === 'context').draft_value,'Browser check: editable Word with layout');
    assert(word.source_refs.includes('docs/adr/0005-word-layout.md'));
    assert.deepEqual(errors,[]);
    await page.screenshot({path:path.join(artifacts,'dashboard-word.png'),fullPage:true});
    fs.writeFileSync(path.join(artifacts,'dashboard-report.json'),JSON.stringify({passed:true,coverage,consoleErrors:errors},null,2));
    console.log('PASS: Word/gate details, cancel/save, draft export, unchanged statuses and coverage, no browser errors.');
  } finally { await browser.close(); }
})().catch(error => {console.error(error);process.exitCode=1});
