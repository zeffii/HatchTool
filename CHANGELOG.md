# Changelog

## 011 · 2026-10-31

- Sverchok Stairs node (`nodes/stairs.py`, `utils/stairs_module.py`): concrete, precast and timber flights from two boundaries, riser lines and a walking path
- Curved and bent risers (chains of edges), winders fanning out from one point; square, chamfer and round toes
- Rise and going checks (private / public) with a note on how many risers are missing; concrete adds a landing when the boundaries carry on past the top riser
- `tools/stairs_preview.py` renders the test sketches with matplotlib

## 010 · 2026-10-30

- Sverchok node: dropped the old `_enum_items` cache, `@keep_enum_reference` does that job now
- `hatch_pattern.py` back to LF line endings; `.gitattributes` keeps text files LF from now on, `.pat` files keep the CRLF that patgen writes

## 009 · 2026-10-30

- Phone layout: one scrolling column with the sheet first, then the pattern list, line families and source
- Landscape phones: compact header and a near full-screen sheet
- HUD moves to the bottom of the sheet on phones so it clears the zoom buttons; bigger touch targets
- Inputs use 16px text on phones so iOS no longer zooms in on focus
- Selecting a pattern no longer scrolls the whole page on phones
- Python tests stub `keep_enum_reference`, so the deploy runs again after the node's switch to it

## 008 · 2026-10-24

- Sverchok core module renamed to `utils/hatch_module.py` (the node keeps `nodes/hatch_pattern.py`)

## 007 · 2026-10-24

- Sverchok node: status line under the pattern picker with dash, dot and object counts
- Hints when the result looks wrong: millimetre pattern at Scale 1 ("Scale 0.001 for metres"), lines wider apart than the region (suggests a scale), close to Max Segments, and region errors

## 006 · 2026-10-24

- Browser tab shows the build number (HatchTool 006); a test keeps it in step with this changelog

## 005 · 2026-10-24

- Bench header: Code button linking to the GitHub repository

## 004 · 2026-10-24

- README_TLDR.md: the five things you need, one line each

## 003 · 2026-10-24

- Sverchok Hatch Pattern node, geometry mode (`sverchok/`): one stream per object; Vertices with Polygons (holes by even-odd) or closed boundary Edges; plane inferred (polygon winding, or a best fit with a fixed facing for edges); Scale and Offset X / Y per object
- Plotting outputs: dashes chained into strokes (collinear pieces merged, outlines closed) and ordered nearest-first to cut pen travel; Min Length drops slivers left by clipping
- Open boundaries and too-dense hatches stop with an error naming the object
- Python tests for the core and the node's process(), run in CI
- Shorter README

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
