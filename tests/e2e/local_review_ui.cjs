/* Optional browser checks. See docs/PROTOTIPO_F0.md for setup and environment variables. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.PDF_UI_PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.PDF_UI_URL || 'http://127.0.0.1:8421';
const artifacts = path.resolve('.generated/ui-check');
const sample = path.resolve('benchmarks/corpus/files/synthetic_base_invoice.pdf');
const key = 'pdf-converter:theme';

async function expectTheme(page, theme) {
  await page.waitForFunction(expected => document.documentElement.dataset.theme === expected, theme);
  assert.equal(await page.locator('html').evaluate(el => getComputedStyle(el).colorScheme), theme);
}

async function checkLayout(page) {
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Horizontal overflow');
  const geometry = await page.evaluate(() => {
    const toggle = document.querySelector('#theme-toggle').getBoundingClientRect();
    const badge = document.querySelector('.local-badge').getBoundingClientRect();
    return { width: toggle.width, height: toggle.height, gap: toggle.left - badge.right };
  });
  assert(geometry.width >= 44 && geometry.height >= 44, 'Theme touch target below 44px');
  assert(geometry.gap >= 8, 'Theme control too close to its neighbour');
  return geometry;
}

async function checkContextHelp(page) {
  const actions = page.locator('[data-help-action]:visible');
  for (let i = 0; i < await actions.count(); i++) {
    const action = actions.nth(i);
    const key = await action.getAttribute('data-help-action');
    const sibling = action.locator('..').locator(`[data-help-topic="${key}"]`);
    assert.equal(await sibling.count(), 1, `Missing ? next to ${key}`);
    const actionRect = await action.boundingBox();
    const helpRect = await sibling.boundingBox();
    assert(helpRect.width >= 44 && helpRect.height >= 44, `Small help target for ${key}`);
    assert(helpRect.x - actionRect.x - actionRect.width >= 7.9, `Missing spacing before ? for ${key}`);
  }
  const trigger = page.locator('[data-help-topic="convert"]');
  if (await trigger.count()) {
    const fileBefore = await page.locator('#file').evaluate(input => input.files[0]?.name);
    await trigger.click();
    await page.locator('#context-dialog').waitFor({state:'visible'});
    assert.equal(await page.locator('#context-title').textContent(),'Convertir PDF');
    await page.keyboard.press('Escape');
    assert(await trigger.evaluate(el => document.activeElement === el));
    assert.equal(await page.locator('#file').evaluate(input => input.files[0]?.name), fileBefore);
  }
}

async function checkContrast(page) {
  return page.evaluate(() => {
    const root = getComputedStyle(document.documentElement);
    const luminance = name => {
      let hex = root.getPropertyValue(name).trim().slice(1);
      if (hex.length === 3) hex = [...hex].map(c => c + c).join('');
      const rgb = hex.match(/../g).map(c => parseInt(c, 16) / 255)
        .map(c => c <= .04045 ? c / 12.92 : ((c + .055) / 1.055) ** 2.4);
      return rgb[0] * .2126 + rgb[1] * .7152 + rgb[2] * .0722;
    };
    return [
      ['--text', '--bg'], ['--muted', '--surface'], ['--muted', '--bg'],
      ['--on-primary', '--primary'], ['--primary', '--tint'],
      ['--danger', '--danger-bg'], ['--amber', '--amber-bg'],
    ].map(([foreground, background]) => {
      const a = luminance(foreground), b = luminance(background);
      return { foreground, background, ratio: (Math.max(a, b) + .05) / (Math.min(a, b) + .05) };
    });
  });
}

async function main() {
  fs.mkdirSync(artifacts, { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.PDF_UI_CHROMIUM_EXECUTABLE ? { executablePath: process.env.PDF_UI_CHROMIUM_EXECUTABLE } : {}),
  });
  const errors = [];
  const metrics = [];
  const observe = page => {
    page.setDefaultTimeout(10000);
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
      if (message.type() === 'error' && !message.text().startsWith('Failed to load resource:')) errors.push(message.text());
    });
  };
  try {
    const context = await browser.newContext({ colorScheme: 'light', reducedMotion: 'reduce' });
    const page = await context.newPage();
    observe(page);
    await page.goto(base);
    await expectTheme(page, 'light');
    await page.emulateMedia({ colorScheme: 'dark' });
    await expectTheme(page, 'dark');
    await page.getByRole('button', { name: 'Cambiar a modo claro' }).click();
    await expectTheme(page, 'light');
    await page.reload();
    await expectTheme(page, 'light'); // explicit choice wins over the OS

    const second = await context.newPage();
    observe(second);
    await second.goto(base);
    await page.getByRole('button', { name: 'Cambiar a modo oscuro' }).click();
    await expectTheme(second, 'dark'); // preference follows the other tab
    await second.evaluate(k => localStorage.removeItem(k), key);
    await expectTheme(page, 'dark'); // cleared preference returns this tab to its dark OS
    await page.emulateMedia({ colorScheme: 'light' });
    await expectTheme(page, 'light');
    await second.close();

    // Cover upload, validation, results, downloads and responsive geometry in both themes.
    for (const theme of ['light', 'dark']) {
      await page.goto(base);
      if (await page.locator('html').getAttribute('data-theme') !== theme) await page.locator('#theme-toggle').click();
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.screenshot({ path: path.join(artifacts, `form-${theme}.png`), fullPage: true });
      const ratios = await checkContrast(page);
      for (const item of ratios) assert(item.ratio >= 4.5, `${theme} contrast ${item.foreground}/${item.background}: ${item.ratio}`);
      metrics.push({ theme, contrast: ratios });
      const button = page.locator('#theme-toggle');
      await page.mouse.move(0, 0);
      const normal = await button.evaluate(el => getComputedStyle(el).backgroundColor);
      await button.hover();
      // Reduced motion eliminates the CSS transition, allowing a stable computed-style check.
      assert.notEqual(await button.evaluate(el => getComputedStyle(el).backgroundColor), normal, 'Missing hover feedback');
      await button.focus();
      await page.keyboard.press('Tab');
      await page.keyboard.press('Shift+Tab');
      assert(await button.evaluate(el => el.matches(':focus-visible')), 'Missing keyboard focus');
      const previous = await page.locator('html').getAttribute('data-theme');
      await page.keyboard.press('Enter');
      assert.notEqual(await page.locator('html').getAttribute('data-theme'), previous);
      await page.keyboard.press('Space');
      await expectTheme(page, theme);
      for (const viewport of [{width:375,height:812},{width:768,height:900},{width:812,height:375},{width:1024,height:900},{width:1440,height:1000}]) {
        await page.setViewportSize(viewport);
        const geometry = await checkLayout(page);
        metrics.push({ theme, viewport, geometry });
      }
      await page.getByRole('button', {name:'Convertir PDF',exact:true}).click();
      await page.locator('#file-error').waitFor({state:'visible'});
      await page.locator('#file').setInputFiles({name:'notes.txt',mimeType:'text/plain',buffer:Buffer.from('hello')});
      await page.locator('#file-error').waitFor({state:'visible'});
      await page.locator('#remove-file').click();
      const transfer = await page.evaluateHandle(b64 => {
        const data = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
        const transfer = new DataTransfer();
        transfer.items.add(new File([data], 'arrastrado.pdf', {type:'application/pdf'}));
        return transfer;
      }, fs.readFileSync(sample).toString('base64'));
      await page.locator('#drop-zone').dispatchEvent('drop', {dataTransfer:transfer});
      assert.equal(await page.locator('#file-name').textContent(), 'arrastrado.pdf');
      await checkContextHelp(page);
      await page.locator('#pages').fill('1,1');
      await page.locator('#pages').blur();
      await page.locator('#pages-error').waitFor({state:'visible'});
      await page.locator('#pages').fill('1');
      for (const ext of ['xlsx','docx','txt']) await page.locator(`[value="${ext}"]`).uncheck();
      await page.locator('#formats-error').waitFor({state:'visible'});
      for (const ext of ['xlsx','docx','txt']) await page.locator(`[value="${ext}"]`).check();
      await page.evaluate(() => document.querySelector('form').addEventListener('submit', () => {
        sessionStorage.setItem('feedback', JSON.stringify({
          progress: !document.querySelector('#progress').hidden,
          disabled: document.querySelector('[type="submit"]').disabled,
        }));
      }));
      await page.getByRole('button',{name:'Convertir PDF',exact:true}).click();
      await page.waitForURL('**/convert');
      await expectTheme(page, theme);
      assert.deepEqual(await page.evaluate(() => JSON.parse(sessionStorage.getItem('feedback'))), {progress:true,disabled:true});
      assert.equal(await page.locator('.download-card').count(), 3);
      await checkContextHelp(page);
      assert((await page.locator('.text-preview').textContent()).trim());
      const [download] = await Promise.all([
        page.waitForEvent('download'),
        page.getByRole('link',{name:'Descargar Excel',exact:true}).click(),
      ]);
      const target = path.join(artifacts, `result-${theme}.xlsx`);
      await download.saveAs(target);
      assert(fs.readFileSync(target).subarray(0,2).equals(Buffer.from('PK')));
      await page.screenshot({path:path.join(artifacts,`results-${theme}.png`),fullPage:true});
      await page.setViewportSize({width:375,height:812});
      await checkLayout(page);
      await page.screenshot({path:path.join(artifacts,`results-${theme}-mobile.png`),fullPage:true});
      await page.getByRole('link',{name:'Convertir otro PDF',exact:true}).click();
      await expectTheme(page,theme);
      await page.screenshot({path:path.join(artifacts,`form-${theme}-mobile.png`),fullPage:true});
      await page.locator('#file').setInputFiles(sample);
      await page.locator('#pages').fill('99');
      await page.locator('#ocr').check();
      await page.getByRole('button',{name:'Convertir PDF',exact:true}).click();
      await page.locator('.error-banner').waitFor();
      await expectTheme(page,theme);
      assert.equal(await page.locator('#pages').inputValue(),'99');
      assert(await page.locator('#ocr').isChecked());
      assert(await page.locator('.error-banner').evaluate(el => document.activeElement === el));
      await page.screenshot({path:path.join(artifacts,`error-${theme}.png`),fullPage:true});
      await page.locator('.help-menu > summary').click();
      await page.getByRole('link',{name:'Preguntas frecuentes',exact:true}).click();
      await page.waitForURL('**/ayuda#faq');
      await expectTheme(page,theme);
      await checkContextHelp(page);
      const search = page.locator('#faq-search');
      await search.fill('CONTRASENA');
      assert(await page.locator('#topic-upload').isVisible());
      assert(await page.locator('#topic-upload').evaluate(el=>el.open));
      await search.fill('zzzz-no-match');
      await page.locator('#faq-empty').waitFor({state:'visible'});
      await page.locator('#faq-clear').click();
      assert(await page.locator('#faq-empty').isHidden());
      await page.setViewportSize({width:1440,height:1000});
      await page.screenshot({path:path.join(artifacts,`help-${theme}.png`),fullPage:true});
      await page.setViewportSize({width:375,height:812});
      await checkLayout(page);
      await page.screenshot({path:path.join(artifacts,`help-${theme}-mobile.png`),fullPage:true});
      assert(await page.locator('.help-hero img').evaluate(el=>el.complete && el.naturalWidth>0));
    }
    await context.close();

    // Storage can be unavailable or contain an obsolete value without breaking the app.
    const blocked = await browser.newContext({colorScheme:'dark'});
    const blockedPage = await blocked.newPage();
    observe(blockedPage);
    await blockedPage.addInitScript(() => {
      Storage.prototype.getItem = () => {throw new DOMException('Blocked','SecurityError')};
      Storage.prototype.setItem = () => {throw new DOMException('Blocked','QuotaExceededError')};
    });
    await blockedPage.goto(base);
    await expectTheme(blockedPage,'dark');
    await blockedPage.getByRole('button',{name:'Cambiar a modo claro'}).click();
    await expectTheme(blockedPage,'light');
    await blockedPage.locator('#file').setInputFiles(sample);
    await blockedPage.getByRole('button',{name:'Convertir PDF',exact:true}).click();
    await blockedPage.waitForURL('**/convert');
    assert.equal(await blockedPage.locator('.download-card').count(),2);
    await blocked.close();

    const obsolete = await browser.newContext({colorScheme:'dark'});
    const obsoletePage = await obsolete.newPage();
    observe(obsoletePage);
    await obsoletePage.addInitScript(k => localStorage.setItem(k, 'obsolete-theme'), key);
    await obsoletePage.goto(base);
    await expectTheme(obsoletePage,'dark');
    await obsolete.close();

    const fallback = await browser.newContext({javaScriptEnabled:false,colorScheme:'dark',viewport:{width:375,height:812}});
    const plain = await fallback.newPage();
    observe(plain);
    await plain.goto(base);
    assert.equal(await plain.locator('html').evaluate(el => getComputedStyle(el).colorScheme),'dark');
    assert(await plain.locator('#theme-toggle').isHidden());
    await plain.locator('#file').setInputFiles(sample);
    await plain.getByRole('button',{name:'Convertir PDF',exact:true}).click();
    await plain.waitForURL('**/convert');
    assert.equal(await plain.locator('.download-card').count(),2);
    await plain.getByRole('link',{name:'Ayuda: Descargar Excel',exact:true}).click();
    assert(new URL(plain.url()).pathname === '/ayuda');
    await plain.locator('#faq-search').fill('CONTRASENA');
    await plain.getByRole('button',{name:'Buscar',exact:true}).click();
    assert(await plain.locator('#topic-upload').isVisible());
    await fallback.close();
    assert.deepEqual(errors,[]);
    fs.writeFileSync(path.join(artifacts,'report.json'), JSON.stringify({checkedAt:new Date().toISOString(),passed:true,metrics,consoleErrors:errors},null,2));
    console.log('PASS: themes, persistence, contrast, responsive layouts, conversion/downloads, contextual help/focus, FAQ search, mascot and no-JS fallback.');
    console.log(`Evidence: ${artifacts}`);
  } finally {
    await browser.close();
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
