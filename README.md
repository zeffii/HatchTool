# HatchTool

iteration 1

## Hatch Pattern Bench

A single-page viewer and editor for AutoCAD / Revit `.pat` hatch patterns. Open `index.html` in a browser, no build step.

- Open `.pat` files or whole folders (or drag them onto the page). Multi-pattern files such as `acad.pat` are supported, as are Revit `;%TYPE` / `;%UNITS` directives and the DOS end-of-file marker found in older files.
- Pan, zoom, scale and rotate the hatch. Hover or click a line family to isolate it and see its origin and delta.
- Edit the source live and copy the result.

`examples.pat` holds the example patterns the page starts with.

### The .pat line family

```
angle, x-origin, y-origin, delta-x, delta-y [, dash-1, dash-2, ...]
```

Line *k* of a family passes through `origin + k * (delta-x * u + delta-y * n)`, where `u` is the line direction and `n` is perpendicular to it, so the delta is measured in the family's rotated frame. The dash sequence starts at that point: positive values draw, negative values are gaps, `0` is a dot. With no dashes the lines are continuous.

## Development

`npm test` runs the parser and dash generation tests (Node 20+). Third-party `.pat` files used for testing are not part of this repository.
