"""
python3 -m unittest discover sverchok/tests

Tests the hatch core and the node's process() outside Blender: bpy, mathutils and the few
Sverchok helpers the node uses are replaced by small stand-ins.
"""

import math
import os
import sys
import types
import unittest
from types import SimpleNamespace as NS

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))


# --------------------------------------------------------------------------- stand-ins

class _Any(types.ModuleType):
    def __getattr__(self, name):
        if name.startswith("__"):
            raise AttributeError(name)
        return lambda *a, **k: None


def _install_stubs():
    for name in ["bpy", "bpy.props", "mathutils", "sverchok", "sverchok.node_tree",
                 "sverchok.data_structure", "sverchok.utils"]:
        sys.modules.setdefault(name, _Any(name))
    sys.modules["bpy"].types = NS(Node=type("Node", (), {}), Text=None)
    sys.modules["bpy"].props = sys.modules["bpy.props"]
    sys.modules["bpy"].utils = NS(register_class=lambda c: None, unregister_class=lambda c: None)
    sys.modules["sverchok.node_tree"].SverchCustomTreeNode = type("SverchCustomTreeNode", (), {})

    def match_long_repeat(lsts):
        n = max(len(l) for l in lsts)
        return [list(l) + [l[-1]] * (n - len(l)) for l in lsts]
    sys.modules["sverchok.data_structure"].match_long_repeat = match_long_repeat
    sys.modules["sverchok.data_structure"].updateNode = lambda *a: None

    class Matrix(list):
        @staticmethod
        def Identity(n):
            return Matrix([[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)])
    sys.modules["mathutils"].Matrix = Matrix

    sys.path.insert(0, os.path.join(ROOT, "sverchok", "utils"))
    import hatch_pattern
    sys.modules["sverchok.utils.hatch_pattern"] = hatch_pattern
    return hatch_pattern


hp = _install_stubs()

import importlib.util
_spec = importlib.util.spec_from_file_location("hatch_node", os.path.join(ROOT, "sverchok", "nodes", "hatch_pattern.py"))
node_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(node_mod)


def library():
    pats = {}
    for name in ("bricks", "tiles", "stone", "foliage", "materials"):
        with open(os.path.join(ROOT, "patterns", f"{name}.pat"), encoding="utf-8") as f:
            text = f.read()
        for p in hp.parse_pat(text)[0]:
            pats[p.name] = (p, text)
    return pats


LIB = library()
SIMPLE = hp.parse_pat("*H, horizontal lines\n0, 0,0, 0,1\n")[0][0]
DASHED = hp.parse_pat("*D\n0, 0,0, 0.5,1, 1,-1\n")[0][0]


def square_with_hole():
    verts = [(0, 0, 0), (10, 0, 0), (10, 6, 0), (0, 6, 0), (3, 2, 0), (3, 4, 0), (7, 4, 0), (7, 2, 0)]
    return verts, [[0, 1, 2, 3], [4, 5, 6, 7]]


def midpoints_in_hole(seg):
    mid = seg.mean(axis=1)
    return int(((mid[:, 0] > 3 + 1e-9) & (mid[:, 0] < 7 - 1e-9) & (mid[:, 1] > 2 + 1e-9) & (mid[:, 1] < 4 - 1e-9)).sum())


# --------------------------------------------------------------------------- core

class CoreTests(unittest.TestCase):

    def test_library_parses(self):
        self.assertGreaterEqual(len(LIB), 30)
        for name, (p, _) in LIB.items():
            self.assertEqual(p.issues, [], name)

    def test_parser_details(self):
        pats, issues = hp.parse_pat(";%UNITS=MM\n*A, first\n;%TYPE=MODEL\n0,0,0,0,1\n*B\n45,0,0,0,2,1,-1\n\x1ajunk")
        self.assertEqual(issues, [])
        self.assertEqual([p.name for p in pats], ["A", "B"])
        self.assertEqual(pats[0].directives, {"UNITS": "MM", "TYPE": "MODEL"})
        self.assertEqual(pats[1].families[0].dashes, (1.0, -1.0))

    def test_hole_from_polygons(self):
        verts, polys = square_with_hole()
        r = hp.hatch_region(verts, SIMPLE, loops=polys, offset=(0, 0.5))
        self.assertEqual(midpoints_in_hole(r.segments), 0)
        # lines at y = 0.5 .. 5.5; rows crossing the hole split in two
        self.assertEqual(len(r.segments), 6 + 2)

    def test_edges_give_the_same_region_as_polygons(self):
        verts, polys = square_with_hole()
        edges = [[a, b] for loop in polys for a, b in zip(loop, loop[1:] + loop[:1])]
        edges = edges[::-1]                       # order does not matter
        a = hp.hatch_region(verts, DASHED, loops=polys)
        b = hp.hatch_region(verts, DASHED, edges=edges)
        key = lambda s: np.round(np.sort(s.reshape(-1, 6), axis=0), 9)
        self.assertTrue(np.allclose(key(a.segments), key(b.segments)))

    def test_open_boundary_is_reported(self):
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        with self.assertRaises(hp.RegionError) as ctx:
            hp.hatch_region(verts, SIMPLE, edges=[[0, 1], [1, 2], [2, 3]])
        self.assertIn("not closed", str(ctx.exception))

    def test_vertices_only_form_one_loop(self):
        verts = [(0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0)]
        r = hp.hatch_region(verts, SIMPLE, offset=(0, 0.5))
        self.assertEqual(len(r.segments), 3)

    def test_tilted_plane_matches_flat(self):
        verts, polys = square_with_hole()
        flat = hp.hatch_region(verts, DASHED, loops=polys)
        ang = math.radians(35)
        X, Y = np.array([1.0, 0, 0]), np.array([0, math.cos(ang), math.sin(ang)])
        tilted_verts = [tuple(v[0] * X + v[1] * Y) for v in verts]
        tilted = hp.hatch_region(tilted_verts, DASHED, loops=polys)
        o, x, y, n = tilted.frame
        self.assertTrue(np.allclose(y, Y, atol=1e-9))          # y runs up the slope
        self.assertLess(float(np.abs((tilted.segments.reshape(-1, 3) - o) @ n).max()), 1e-9)
        back = np.stack([(tilted.segments - o) @ x, (tilted.segments - o) @ y], axis=-1)
        key = lambda s: np.round(np.sort(s.reshape(-1, 4), axis=0), 9)
        self.assertTrue(np.allclose(key(back), key(flat.segments[..., :2])))

    def test_edge_plane_facing_is_fixed(self):
        verts = [(0, 0, 0), (4, 0, 0), (4, 3, 0), (0, 3, 0)]
        cw = [[0, 3], [3, 2], [2, 1], [1, 0]]
        ccw = [[0, 1], [1, 2], [2, 3], [3, 0]]
        self.assertTrue(np.allclose(hp.hatch_region(verts, SIMPLE, edges=cw).frame[3], [0, 0, 1]))
        self.assertTrue(np.allclose(hp.hatch_region(verts, SIMPLE, edges=ccw).frame[3], [0, 0, 1]))

    def test_min_length_drops_slivers(self):
        # the top edge drops to 0.005 at x = 10, so the vertical line at x = 9.999 is a sliver
        verts = [(0, 0, 0), (10, 0, 0), (10, 0.005, 0), (0, 5, 0)]
        pat = hp.parse_pat("*V\n90, 0,0, 0,1\n")[0][0]
        all_ = hp.hatch_region(verts, pat, offset=(9.999, 0))
        trimmed = hp.hatch_region(verts, pat, offset=(9.999, 0), min_length=0.01)
        lengths = np.linalg.norm(all_.segments[:, 1] - all_.segments[:, 0], axis=1)
        self.assertLess(lengths.min(), 0.01)
        self.assertEqual(len(trimmed.segments), len(all_.segments) - 1)

    def test_too_dense_raises(self):
        verts = [(0, 0, 0), (1000, 0, 0), (1000, 1000, 0), (0, 1000, 0)]
        with self.assertRaises(hp.HatchTooDense):
            hp.hatch_region(verts, DASHED, scale=0.01, max_segments=10000)

    def test_library_patterns_clip_inside_region(self):
        verts, polys = square_with_hole()
        verts = [(x * 300, y * 300, 0) for x, y, _ in verts]
        for name, (p, _) in LIB.items():
            r = hp.hatch_region(verts, p, loops=polys, scale=1.0, max_segments=3_000_000)
            seg = r.segments / 300
            self.assertEqual(midpoints_in_hole(seg), 0, name)
            mid = seg.mean(axis=1)
            self.assertTrue(((mid[:, 0] >= -1e-9) & (mid[:, 0] <= 10 + 1e-9) &
                             (mid[:, 1] >= -1e-9) & (mid[:, 1] <= 6 + 1e-9)).all(), name)


class PlotTests(unittest.TestCase):

    def test_chaining_joins_outlines(self):
        # gravel pebbles are closed outlines: chained strokes are far fewer than segments
        p = LIB["STONE-GRAVEL"][0]
        verts = [(0, 0, 0), (2000, 0, 0), (2000, 2000, 0), (0, 2000, 0)]
        r = hp.hatch_region(verts, p)
        strokes = hp.chain_segments(r.segments, tol=1e-6)
        self.assertLess(len(strokes), len(r.segments) / 4)
        # every segment is covered exactly once
        self.assertEqual(sum(len(s) - 1 for s in hp.chain_segments(r.segments, tol=1e-6, simplify=False)),
                         len(r.segments))
        closed = sum(1 for s in strokes if np.allclose(s[0], s[-1]))
        self.assertGreater(closed, len(strokes) // 2)

    def test_collinear_dashes_merge(self):
        seg = np.array([[(0, 0, 0), (1, 0, 0)], [(1, 0, 0), (2, 0, 0)], [(2, 0, 0), (3, 0, 0)]], float)
        strokes = hp.chain_segments(seg)
        self.assertEqual(len(strokes), 1)
        self.assertEqual(len(strokes[0]), 2)

    def test_ordering_reduces_pen_travel(self):
        p = LIB["BRICK-STRETCHER"][0]
        verts = [(0, 0, 0), (3000, 0, 0), (3000, 2000, 0), (0, 2000, 0)]
        r = hp.hatch_region(verts, p)
        strokes = hp.chain_segments(r.segments, tol=1e-6)
        rng = np.random.default_rng(1)
        shuffled = [strokes[i] for i in rng.permutation(len(strokes))]
        ordered = hp.order_strokes(shuffled)
        self.assertEqual(len(ordered), len(strokes))
        self.assertLess(hp.pen_travel(ordered), hp.pen_travel(shuffled) / 5)


# --------------------------------------------------------------------------- node

class Sock:
    def __init__(self, data=None, linked=True):
        self.data, self.is_linked, self.out = data, linked, None

    def sv_get(self, default=None, deepcopy=True):
        return self.data if self.data is not None else default

    def sv_set(self, data):
        self.out = data


class Sockets(dict):
    """like a Blender socket collection: index by name, iterate over sockets"""
    def __iter__(self):
        return iter(self.values())


def make_node(text, pattern_name, **inputs):
    N = node_mod.SvHatchPatternNode
    node = N.__new__(N)
    node.pattern_text = NS(name="lib.pat", as_string=lambda: text)
    node.pattern_name, node.node_id = pattern_name, "test"
    node.min_length, node.order_strokes, node.max_segments = 0.0, True, 1_000_000
    node.status, node.status_level = "", "INFO"
    defaults = {"Vertices": None, "Edges": None, "Polygons": None,
                "Scale": [[1.0]], "Offset X": [[0.0]], "Offset Y": [[0.0]]}
    defaults.update(inputs)
    node.inputs = Sockets({k: Sock(v, v is not None) for k, v in defaults.items()})
    node.inputs["Scale"].is_linked = node.inputs["Offset X"].is_linked = node.inputs["Offset Y"].is_linked = False
    node.outputs = Sockets({k: Sock() for k in ("Vertices", "Edges", "Dots", "Stroke Vertices", "Stroke Edges", "Plane")})
    return node


class NodeTests(unittest.TestCase):

    def test_polygons_per_object(self):
        verts, polys = square_with_hole()
        verts = [(x * 100, y * 100, z) for x, y, z in verts]
        p, text = LIB["BRICK-STRETCHER"]
        node = make_node(text, "BRICK-STRETCHER", Vertices=[verts, verts], Polygons=[polys, [polys[0]]])
        node.process()
        v, e = node.outputs["Vertices"].out, node.outputs["Edges"].out
        self.assertEqual(len(v), 2)
        self.assertGreater(len(e[1]), len(e[0]))       # second object has no hole
        seg = np.array(v[0]).reshape(-1, 2, 3) / 100
        self.assertEqual(midpoints_in_hole(seg), 0)
        self.assertTrue(all(max(max(pair) for pair in obj) < len(vo) for obj, vo in zip(e, v)))

    def test_edges_input_and_parameters_per_object(self):
        verts = [(0, 0, 0), (900, 0, 0), (900, 600, 0), (0, 600, 0)]
        edges = [[0, 1], [1, 2], [2, 3], [3, 0]]
        _, text = LIB["TILE-SQUARE-300"]
        node = make_node(text, "TILE-SQUARE-300", Vertices=[verts], Edges=[edges], Scale=[[1.0], [0.5]])
        node.inputs["Scale"].is_linked = True
        node.process()
        e = node.outputs["Edges"].out
        self.assertEqual(len(e), 2)                     # objects repeat to match the longest input
        self.assertGreater(len(e[1]), len(e[0]))        # half scale, more lines

    def test_single_object_without_outer_list(self):
        verts = [(0, 0, 0), (900, 0, 0), (900, 600, 0), (0, 600, 0)]
        _, text = LIB["TILE-SQUARE-300"]
        node = make_node(text, "TILE-SQUARE-300", Vertices=verts, Polygons=[[0, 1, 2, 3]])
        node.process()
        self.assertEqual(len(node.outputs["Vertices"].out), 1)

    def test_strokes_and_dots(self):
        verts = [(0, 0, 0), (1000, 0, 0), (1000, 1000, 0), (0, 1000, 0)]
        _, text = LIB["FOLIAGE-PLANTING"]
        node = make_node(text, "FOLIAGE-PLANTING", Vertices=[verts], Polygons=[[[0, 1, 2, 3]]])
        node.process()
        sv, se = node.outputs["Stroke Vertices"].out, node.outputs["Stroke Edges"].out
        self.assertEqual(len(sv), len(se))
        self.assertGreater(len(node.outputs["Dots"].out[0]), 0)
        self.assertTrue(all(len(edges) == len(vs) - 1 for vs, edges in zip(sv, se)))

    def test_pattern_enum(self):
        _, text = LIB["BRICK-STACK"]
        node = make_node(text, "BRICK-STACK")
        names = [i[0] for i in node_mod.pattern_items(node, None)]
        self.assertIn("BRICK-STACK", names)
        node._set_pattern(names.index("BRICK-FLEMISH"))
        self.assertEqual(node.pattern_name, "BRICK-FLEMISH")
        self.assertEqual(node._get_pattern(), names.index("BRICK-FLEMISH"))

    def test_region_errors_name_the_object(self):
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        node = make_node(LIB["BRICK-STACK"][1], "BRICK-STACK", Vertices=[verts, verts],
                         Edges=[[[0, 1], [1, 2], [2, 3], [3, 0]], [[0, 1], [1, 2]]])
        with self.assertRaises(hp.RegionError) as ctx:
            node.process()
        self.assertIn("object 1", str(ctx.exception))


class StatusTests(unittest.TestCase):

    def test_counts_when_it_works(self):
        verts = [(0, 0, 0), (900, 0, 0), (900, 600, 0), (0, 600, 0)]
        node = make_node(LIB["TILE-SQUARE-300"][1], "TILE-SQUARE-300", Vertices=[verts, verts], Polygons=[[[0, 1, 2, 3]]])
        node.process()
        self.assertEqual(node.status_level, "INFO")
        self.assertRegex(node.status, r"^\d[\d,]* dashes · 2 objects$")

    def test_millimetre_pattern_in_metres(self):
        # a 2 m plane with a mm brick pattern at Scale 1: nothing inside, point at the unit
        verts = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)]
        node = make_node(LIB["BRICK-STRETCHER"][1], "BRICK-STRETCHER", Vertices=[verts], Polygons=[[[0, 1, 2, 3]]])
        node.process()
        self.assertEqual(node.status_level, "WARNING")
        self.assertIn("pattern is in mm: Scale 0.001 for metres", node.status)

    def test_scale_suggestion_without_units(self):
        text = "*WIDE\n0, 0,0, 0,50\n"
        verts = [(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)]
        node = make_node(text, "WIDE", Vertices=[verts], Polygons=[[[0, 1, 2, 3]]])
        node.process()
        self.assertIn("lines are wider apart than the region: try Scale ≈ 0.0016", node.status)
        hp_suggested = hp.suggest_scale(hp.parse_pat(text)[0][0], 2.0)
        r = hp.hatch_region(verts, hp.parse_pat(text)[0][0], loops=[[0, 1, 2, 3]], scale=hp_suggested)
        self.assertGreater(len(r.segments), 10)

    def test_errors_show_in_the_status(self):
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        node = make_node(LIB["BRICK-STACK"][1], "BRICK-STACK", Vertices=[verts], Edges=[[[0, 1], [1, 2]]])
        with self.assertRaises(hp.RegionError):
            node.process()
        self.assertEqual(node.status_level, "WARNING")
        self.assertIn("not closed", node.status)


if __name__ == "__main__":
    unittest.main()
