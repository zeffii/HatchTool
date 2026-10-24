// Copies the pattern library (patterns/*.pat) into index.html so the page stays one self-contained file.
//   npm run embed            write it
//   npm run embed -- --check exit 1 if index.html is out of date
import { readFileSync, writeFileSync } from 'node:fs';

export const LIBRARY_ORDER = ['bricks.pat', 'tiles.pat', 'stone.pat', 'foliage.pat', 'materials.pat'];

export function libraryJson() {
  const files = {};
  for (const name of LIBRARY_ORDER) {
    files[name] = readFileSync(new URL(`../patterns/${name}`, import.meta.url), 'utf8').replace(/\r\n/g, '\n');
  }
  return JSON.stringify({ Library: files });
}

export function embedded(html) {
  const line = html.split('\n').find(l => l.startsWith('const SAMPLE_FILES = '));
  if (!line) throw new Error('index.html has no "const SAMPLE_FILES = " line');
  return line;
}

if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split('/').pop())) {
  const page = new URL('../index.html', import.meta.url);
  const html = readFileSync(page, 'utf8');
  const fresh = `const SAMPLE_FILES = ${libraryJson()};`;
  if (process.argv.includes('--check')) {
    if (embedded(html) !== fresh) { console.error('index.html is out of date, run: npm run embed'); process.exit(1); }
    console.log('index.html library is up to date');
  } else {
    writeFileSync(page, html.replace(embedded(html), () => fresh));
    console.log(`embedded ${LIBRARY_ORDER.length} files into index.html`);
  }
}
