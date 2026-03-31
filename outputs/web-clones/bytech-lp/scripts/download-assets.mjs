import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const URL = 'https://ah-c.bytech.jp/?uid=01KM8AJKHWVPCE85EYCHP6BRKH';
const PUBLIC_DIR = path.join(process.cwd(), 'public', 'assets');
const RESEARCH_DIR = path.join(process.cwd(), 'docs', 'research');

if (!fs.existsSync(PUBLIC_DIR)) fs.mkdirSync(PUBLIC_DIR, { recursive: true });
if (!fs.existsSync(RESEARCH_DIR)) fs.mkdirSync(RESEARCH_DIR, { recursive: true });

async function autoScroll(page) {
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let totalHeight = 0;
      let distance = 300;
      let timer = setInterval(() => {
        let scrollHeight = document.body.scrollHeight;
        window.scrollBy(0, distance);
        totalHeight += distance;
        if (totalHeight >= scrollHeight - window.innerHeight) {
          clearInterval(timer);
          resolve();
        }
      }, 50);
    });
  });
}

(async () => {
  console.log(`Navigating to ${URL}...`);
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();
  
  await page.goto(URL, { waitUntil: 'networkidle' });
  
  console.log('Scrolling page to trigger lazy loaded elements...');
  await autoScroll(page);
  await page.waitForTimeout(2000); // Wait for potential animations

  console.log('Extracting assets and tokens...');
  
  const extracted = await page.evaluate(() => {
    return {
      images: [...document.querySelectorAll('img')].map(img => img.src || img.getAttribute('data-src')).filter(src => src && !src.startsWith('data:')),
      videos: [...document.querySelectorAll('video')].map(v => v.src || v.querySelector('source')?.src).filter(Boolean),
      backgrounds: [...document.querySelectorAll('*')]
        .map(el => getComputedStyle(el).backgroundImage)
        .filter(bg => (bg && bg !== 'none' && bg.includes('url(')))
        .map(bg => bg.match(/url\(['"]?(.*?)['"]?\)/)?.[1] || '')
        .filter(url => url && !url.startsWith('data:')),
        
      colors: [...new Set([...document.querySelectorAll('*')]
        .flatMap(el => {
          const s = getComputedStyle(el);
          return [s.backgroundColor, s.color, s.borderTopColor, s.borderBottomColor];
        })
        .filter(c => c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent')
      )],
      
      fonts: [...new Set([...document.querySelectorAll('*')]
        .map(el => getComputedStyle(el).fontFamily)
        .filter(f => f && f !== '""' && f !== "''")
      )]
    };
  });
  
  // Also dump all SVG strings
  const svgs = await page.evaluate(() => {
    return [...document.querySelectorAll('svg')]
      .filter(svg => svg.getAttribute('width') || svg.viewBox.baseVal.width) // Ignore tiny def icons if possible
      .map(svg => svg.outerHTML)
      .slice(0, 50); // limit to avoid huge payload
  });

  const uniqueImageUrls = [...new Set([...extracted.images, ...extracted.backgrounds])];
  const absoluteImageUrls = uniqueImageUrls.map(url => {
    if (url.startsWith('http')) return url;
    if (url.startsWith('//')) return 'https:' + url;
    return new URL(url, 'https://ah-c.bytech.jp/').href;
  });

  console.log(`Found ${absoluteImageUrls.length} unique images/backgrounds, ${extracted.videos.length} videos, ${svgs.length} SVGs.`);
  console.log(`Found ${extracted.colors.length} unique colors, ${extracted.fonts.length} unique fonts.`);

  // Save tokens to JSON
  fs.writeFileSync(
    path.join(RESEARCH_DIR, 'DESIGN_TOKENS.json'),
    JSON.stringify({
      colors: extracted.colors,
      fonts: extracted.fonts
    }, null, 2)
  );

  // Save SVGs to a file for later conversion
  fs.writeFileSync(
    path.join(RESEARCH_DIR, 'RAW_SVGS.json'),
    JSON.stringify(svgs, null, 2)
  );

  // Use curl down download assets
  console.log('Downloading assets using curl...');
  let downloadedCount = 0;
  for (const url of absoluteImageUrls) {
    try {
      const parsed = new URL(url);
      const filename = path.basename(parsed.pathname) || `asset_${downloadedCount}.jpg`;
      const p = path.join(PUBLIC_DIR, filename);
      if (!fs.existsSync(p)) {
        await execAsync(`curl -sSL "${url}" -o "${p}"`);
      }
      downloadedCount++;
    } catch (e) {
      console.warn(`Failed to process URL: ${url}`, e.message);
    }
  }

  console.log(`Extraction complete. Downloaded ${downloadedCount} assets to public/assets/.`);
  await browser.close();
})();
