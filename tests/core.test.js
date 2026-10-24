// Runs the parser and dash generator from index.html (kept as one self-contained page) under node.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const script = html.slice(html.indexOf('<script>') + 8, html.indexOf('</script>'));
const core = script.slice(script.indexOf('function parsePat'), script.indexOf('/* ------------------------------------------------------------------ state */'));
const lib = new Function(`const BUDGET = 600000;\n${core}\nreturn { parsePat, placeFamily, emitFamily, estimatePattern, fitView };`)();
import { LIBRARY_ORDER, libraryJson, embedded } from '../scripts/embed.js';
const library = LIBRARY_ORDER.map(name => [name, readFileSync(new URL(`../patterns/${name}`, import.meta.url), 'utf8')]);

const segments = (family, rect) => {
  const out = [];
  lib.emitFamily(lib.placeFamily(family, 1, 0), rect, (a, b) => out.push([a, b].map(p => p.map(v => +v.toFixed(9)))), () => {}, 1e9);
  return out;
};

test('library files parse without issues', () => {
  let count = 0;
  for (const [name, text] of library) {
    const { patterns, issues } = lib.parsePat(text, name);
    assert.deepEqual(issues, [], name);
    for (const p of patterns) {
      assert.deepEqual(p.issues, [], `${name} ${p.name}`);
      assert.ok(p.name.length <= 31 && !/\s/.test(p.name), `${p.name}: AutoCAD names are 31 characters, no spaces`);
      assert.equal(p.directives.UNITS, 'MM', p.name);
      assert.equal(p.directives.TYPE, 'MODEL', p.name);
      count++;
    }
  }
  assert.ok(count >= 30, `expected the full library, found ${count} patterns`);
});

test('pattern names are unique across the library', () => {
  const names = library.flatMap(([n, t]) => lib.parsePat(t, n).patterns.map(p => p.name));
  assert.equal(new Set(names).size, names.length);
});

test('index.html carries the current library', () => {
  const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  assert.equal(embedded(html), `const SAMPLE_FILES = ${libraryJson()};`, 'run: npm run embed');
});

test('headers, comments, Revit directives and the DOS end-of-file marker', () => {
  const text = ';%UNITS=MM\n;; comment\n*A, first\n;%TYPE=MODEL\n0, 0,0, 0,1\n*B\n45, 0,0, 0,2, 1,-1\n\x1a\x1agarbage';
  const { patterns } = lib.parsePat(text, 't.pat');
  assert.deepEqual(patterns.map(p => p.name), ['A', 'B']);
  assert.equal(patterns[0].desc, 'first');
  assert.deepEqual(patterns[0].directives, { UNITS: 'MM', TYPE: 'MODEL' });
  assert.deepEqual(patterns[1].families[0].dashes, [1, -1]);
  assert.deepEqual(patterns[1].issues, []);
});

test('bad data lines are reported with their line number', () => {
  const { patterns } = lib.parsePat('*X\n0, 0, 0, a, 1\n0,0,0\n', 'x.pat');
  assert.match(patterns[0].issues[0], /^line 2: "a" is not a number/);
  assert.match(patterns[0].issues[1], /^line 3: needs angle/);
});

test('dash phase carries over between lines via delta-x', () => {
  const segs = segments({ angle: 0, x: 0, y: 0, dx: 0.5, dy: 1, dashes: [1, -1] }, { x0: 0, x1: 4, y0: -0.1, y1: 1.1 });
  assert.deepEqual(segs, [[[0, 0], [1, 0]], [[2, 0], [3, 0]], [[0.5, 1], [1.5, 1]], [[2.5, 1], [3.5, 1]]]);
});

test('delta is measured in the rotated frame', () => {
  // 90 degree lines: the perpendicular points to -x, so delta-y = 1 steps the lines to x = 1, 0, -1
  const xs = segments({ angle: 90, x: 0, y: 0, dx: 0, dy: 1, dashes: [] }, { x0: -1.5, x1: 1.5, y0: 0, y1: 1 }).map(s => s[0][0]);
  assert.deepEqual(xs.map(x => x + 0), [1, 0, -1]);
});

test('negative delta-y and dots', () => {
  const ys = segments({ angle: 0, x: 0, y: 0, dx: 0, dy: -2, dashes: [] }, { x0: 0, x1: 1, y0: -5, y1: 5 }).map(s => s[0][1]);
  assert.deepEqual(ys, [4, 2, 0, -2, -4]);
  let dots = 0;
  lib.emitFamily(lib.placeFamily({ angle: 0, x: 0, y: 0, dx: 0, dy: 1, dashes: [0, -1] }, 1, 0),
    { x0: 0, x1: 3, y0: -0.1, y1: 0.1 }, () => {}, () => dots++, 1e9);
  assert.equal(dots, 4);
});

test('fit keeps every library pattern within the dash budget', () => {
  for (const p of library.flatMap(([n, t]) => lib.parsePat(t, n).patterns)) {
    const v = lib.fitView(p, 1, 0, 900, 600, 60000);
    const rect = { x0: v.cx - 450 / v.zoom, x1: v.cx + 450 / v.zoom, y0: v.cy - 300 / v.zoom, y1: v.cy + 300 / v.zoom };
    assert.ok(lib.estimatePattern(p, 1, 0, rect) <= 60000, p.name);
  }
});
