# HatchTool, TL;DR

- **Look at .pat files:** https://zeffii.github.io/HatchTool/ — drop files or a folder on it.
- **Use our patterns:** `patterns/*.pat` (mm, works in AutoCAD and Revit).
- **Make or change patterns:** edit `tools/patgen.py`, run `npm run patterns`.
- **Hatch in Blender:** copy the `sverchok/` files (`utils/hatch_module.py`, `nodes/hatch_pattern.py`) into Sverchok, feed the node vertices + polygons or closed edges, pick a pattern from a text block.
- **Before pushing:** `npm test && npm run test:py`.
