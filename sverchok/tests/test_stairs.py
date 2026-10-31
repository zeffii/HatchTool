"""
python3 -m unittest discover sverchok/tests

Tests the stairs core outside Blender.
"""

import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "utils")))

import stairs_module as sm  # noqa: E402


# --------------------------------------------------------------------------- sketches

def straight(n=13, going=0.25, rise=0.18, width=1.0, landing=True, sketch_short=False):
    length = 0.5 + (n - 1) * going + (0.5 if landing else 0.0)
    a = [[0, 0, 0], [0, length, 0]]
    b = [[width, 0, 0], [width, length, 0]]
    verts, edges = [], []
    for k in range(n):
        y = 0.5 + k * going
        x0, x1 = (0.2, 0.7) if sketch_short else (-0.3, width + 0.3)
        verts += [[x0, y, 0], [x1, y, 0]]
        edges.append([2 * k, 2 * k + 1])
    path = [[width / 2, 0, 0], [width / 2, length, 0]]
    return [a, b], verts, edges, path, 0.0, n * rise


def quarter_turn():
    """up the y axis, three winders round the inner corner (1, 2), then along x"""
    outer = [[0, 0, 0], [0, 3, 0], [4, 3, 0]]
    inner = [[1, 0, 0], [1, 2, 0], [4, 2, 0]]
    verts, edges = [], []

    def line(p, q):
        verts.extend([p, q])
        edges.append([len(verts) - 2, len(verts) - 1])

    for k in range(7):
        y = 0.25 + k * 0.25
        line([1.2, y, 0], [-0.2, y, 0])
    for ang in (157.5, 135.0, 112.5):
        t = math.radians(ang)
        line([1, 2, 0], [1 + 2 * math.cos(t), 2 + 2 * math.sin(t), 0])
    for k in range(7):
        x = 1.0 + k * 0.25
        line([x, 1.8, 0], [x, 3.2, 0])
    path = [[0.5, 0, 0], [0.5, 2.5, 0], [4, 2.5, 0]]
    n = len(edges)
    return [outer, inner], verts, edges, path, 0.0, n * 0.17


def curved_risers(n=8):
    """each riser a three point bent chain"""
    a = [[0, 0, 0], [0, 3, 0]]
    b = [[1.2, 0, 0], [1.2, 3, 0]]
    verts, edges = [], []
    for k in range(n):
        y = 0.4 + k * 0.27
        base = len(verts)
        verts += [[-0.1, y, 0], [0.6, y + 0.08, 0], [1.3, y, 0]]
        edges += [[base, base + 1], [base + 1, base + 2]]
    path = [[0.6, 0, 0], [0.6, 3, 0]]
    return [a, b], verts, edges, path, 0.0, n * 0.18


# --------------------------------------------------------------------------- mesh checks

def closed_and_outward(test, verts, faces):
    directed = {}
    for f in faces:
        test.assertGreaterEqual(len(f), 3)
        for k in range(len(f)):
            e = (f[k], f[(k + 1) % len(f)])
            directed[e] = directed.get(e, 0) + 1
    for (u, v), c in directed.items():
        test.assertEqual(c, 1, f"edge {u}-{v} used {c} times in one direction")
        test.assertIn((v, u), directed, f"edge {u}-{v} is open")
    return volume(verts, faces)


def volume(verts, faces):
    v = np.asarray(verts)
    vol = 0.0
    for f in faces:
        for k in range(1, len(f) - 1):
            vol += np.dot(v[f[0]], np.cross(v[f[k]], v[f[k + 1]])) / 6.0
    return vol


def flight_of(sketch):
    return sm.build_flight(*sketch)


# --------------------------------------------------------------------------- tests

class FlightTest(unittest.TestCase):
    def test_straight_rise_and_goings(self):
        f = flight_of(straight())
        self.assertEqual(f.n_risers, 13)
        self.assertAlmostEqual(f.rise, 0.18)
        np.testing.assert_allclose(f.goings, [0.25] * 12)
        self.assertTrue(f.landing)
        self.assertEqual(sm.check(f, 'PRIVATE'), [])

    def test_rough_sketch_is_trimmed_to_the_boundaries(self):
        for short in (False, True):
            f = flight_of(straight(sketch_short=short))
            for c in f.chords:
                self.assertAlmostEqual(c.pts[0][0], 0.0)
                self.assertAlmostEqual(c.pts[-1][0], 1.0)

    def test_order_comes_from_the_path(self):
        sk = list(straight())
        verts, edges = sk[1], sk[2]
        sk[2] = edges[::-1]  # edge order should not matter
        f = sm.build_flight(*sk)
        ys = [c.pts[0][1] for c in f.chords]
        self.assertEqual(ys, sorted(ys))

    def test_steep_flight_says_how_many_risers_are_missing(self):
        sk = list(straight(n=10))
        sk[5] = 2.6  # 0.26 per riser
        notes = sm.check(flight_of(sk), 'PRIVATE')
        self.assertTrue(any("2 more riser" in n for n in notes), notes)

    def test_short_goings_are_reported(self):
        notes = sm.check(flight_of(straight(going=0.2)), 'PRIVATE')
        self.assertTrue(any("going under 220" in n for n in notes), notes)

    def test_winders_measure_going_on_the_walking_line(self):
        f = flight_of(quarter_turn())
        self.assertEqual(f.n_risers, 17)
        self.assertTrue(all(g > 0.2 for g in f.goings), f.goings)

    def test_errors(self):
        sk = list(straight())
        sk[3] = [[5, 0, 0], [5, 4, 0]]
        with self.assertRaisesRegex(sm.StairError, "does not cross"):
            sm.build_flight(*sk)
        sk = list(straight())
        sk[4], sk[5] = 2.0, 0.0
        with self.assertRaisesRegex(sm.StairError, "Level End"):
            sm.build_flight(*sk)
        sk = list(straight())
        sk[1] = sk[1] + [[0.5, 3, 0], [0.6, 3, 0]]
        sk[2] = sk[2] + [[0, len(sk[1]) - 2], [0, len(sk[1]) - 1]]
        with self.assertRaisesRegex(sm.StairError, "branches"):
            sm.build_flight(*sk)
        with self.assertRaisesRegex(sm.StairError, "two vertex lists"):
            sm.build_flight([[[0, 0, 0], [0, 1, 0]]], *straight()[1:])


class SolidsTest(unittest.TestCase):
    sketches = {'straight': straight(), 'no landing': straight(landing=False),
                'quarter turn': quarter_turn(), 'curved risers': curved_risers()}

    def test_concrete_is_one_closed_solid(self):
        for name, sk in self.sketches.items():
            with self.subTest(name):
                f = flight_of(sk)
                pieces = sm.concrete(f, waist=0.15)
                self.assertEqual(len(pieces), 1)
                vol = closed_and_outward(self, *pieces[0])
                self.assertGreater(vol, 0)

    def test_concrete_volume_straight(self):
        # steps (triangles) + a 0.15 waist slab under the pitch line, plus the landing slab
        f = flight_of(straight())
        vol = volume(*sm.concrete(f, waist=0.15)[0])
        steps = 12 * 0.5 * 0.18 * 0.25
        slab = 0.15 / math.cos(math.atan(0.18 / 0.25)) * 3.0
        self.assertGreater(vol, steps + slab)
        self.assertLess(vol, steps + slab + 0.18 * 0.5 + 0.15)

    def test_timber_and_precast_pieces_are_closed(self):
        for name, sk in self.sketches.items():
            for kind in ('TIMBER', 'PRECAST'):
                for toe in ('SQUARE', 'CHAMFER', 'ROUND'):
                    with self.subTest(name=name, kind=kind, toe=toe):
                        f = flight_of(sk)
                        pieces = sm.build(kind, f, toe=toe, toe_size=0.01, nosing=0.02)
                        for verts, faces in pieces:
                            self.assertGreater(closed_and_outward(self, verts, faces), 0)

    def test_timber_counts_and_heights(self):
        f = flight_of(straight())
        treads = sm.timber(f, risers=False, tread=0.04)
        self.assertEqual(len(treads), 12)
        z = np.array(treads[0][0])[:, 2]
        self.assertAlmostEqual(z.max(), 0.18)
        self.assertAlmostEqual(z.min(), 0.14)
        both = sm.timber(f, risers=True)
        self.assertEqual(len(both), 12 + 13)
        self.assertEqual(len(sm.timber(flight_of(straight(landing=False)))), 12 + 12)

    def test_nosing_reaches_past_the_riser_line(self):
        f = flight_of(straight())
        verts, _ = sm.timber(f, nosing=0.03, risers=False)[0]
        self.assertAlmostEqual(min(v[1] for v in verts), 0.5 - 0.03)


if __name__ == "__main__":
    unittest.main()
