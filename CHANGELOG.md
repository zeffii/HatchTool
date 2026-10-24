# Changelog

## 002 · 2026-10-24

- Pattern library: 35 patterns drawn for HatchTool in five files (bricks, tiles and paving, stone, foliage, materials), metric with Revit model-pattern directives
- `tools/patgen.py` generates them: shapes drawn in one repeating tile are compiled into exact line families; tilings resolve shared edges so every joint is drawn once
- The bench opens on the library instead of the four examples; `npm run embed` keeps the copy in `index.html` in sync and a test checks it
- Tests cover every library pattern: parsing, AutoCAD name rules, unique names, fit budget
- Pages workflow moved to current action versions (Node 20 deprecation)

## 001 · 2026-10-24

- Hatch Pattern Bench: single-page viewer and editor for AutoCAD / Revit `.pat` files
- Open files or whole folders, or drag them in; multi-pattern files, Revit `;%` directives and the DOS end-of-file marker are handled; non UTF-8 files are read as Windows-1252
- Pan, zoom, scale and rotate; isolate a line family to see its origin and delta; live source editing with copy
- Example patterns: running bond, basketweave, crosshatch, dash-dot grid
- `npm test` covers the parser, dash phase, rotated delta frame and fit budget; GitHub Pages deploy runs the tests first
