# Changelog

## 001 · 2026-10-24

- Hatch Pattern Bench: single-page viewer and editor for AutoCAD / Revit `.pat` files
- Open files or whole folders, or drag them in; multi-pattern files, Revit `;%` directives and the DOS end-of-file marker are handled; non UTF-8 files are read as Windows-1252
- Pan, zoom, scale and rotate; isolate a line family to see its origin and delta; live source editing with copy
- Example patterns: running bond, basketweave, crosshatch, dash-dot grid
- `npm test` covers the parser, dash phase, rotated delta frame and fit budget; GitHub Pages deploy runs the tests first
