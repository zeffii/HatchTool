"""python3 tools/stairs_preview.py out.png  -- renders the test sketches with matplotlib, for eyeballing"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "sverchok", "utils"))
sys.path.insert(0, os.path.join(ROOT, "sverchok", "tests"))
import stairs_module as sm  # noqa: E402
import test_stairs as t  # noqa: E402

LIGHT = np.array([0.4, -0.6, 0.7]) / np.linalg.norm([0.4, -0.6, 0.7])


def draw(ax, pieces, colour, title):
    polys, shades = [], []
    allv = []
    for verts, faces in pieces:
        v = np.asarray(verts)
        allv.append(v)
        for f in faces:
            p = v[f]
            n = np.cross(p[1] - p[0], p[2] - p[0])
            ln = np.linalg.norm(n)
            n = n / ln if ln > 1e-12 else n
            polys.append(p)
            shades.append(0.35 + 0.65 * max(float(np.dot(n, LIGHT)), 0.0))
    base = np.array(matplotlib.colors.to_rgb(colour))
    pc = Poly3DCollection(polys, facecolors=[base * s for s in shades], edgecolors=(0, 0, 0, 0.25), linewidths=0.3)
    ax.add_collection3d(pc)
    v = np.vstack(allv)
    lo, hi = v.min(axis=0), v.max(axis=0)
    c, r = (lo + hi) / 2, (hi - lo).max() / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=28, azim=-62)
    ax.set_axis_off()
    ax.set_title(title, fontsize=10)


def main(out):
    cases = [
        ("Concrete, straight", t.straight(), 'CONCRETE', {}, "#b9b4aa"),
        ("Concrete, quarter turn winders", t.quarter_turn(), 'CONCRETE', {}, "#b9b4aa"),
        ("Timber, winders, round toe", t.quarter_turn(), 'TIMBER', dict(toe='ROUND', toe_size=0.012), "#c49a6c"),
        ("Timber, open risers, chamfer", t.straight(), 'TIMBER', dict(toe='CHAMFER', toe_size=0.008, risers=False), "#c49a6c"),
        ("Precast, curved risers", t.curved_risers(), 'PRECAST', dict(nosing=0.02, lap=0.05), "#9aa3a8"),
        ("Concrete, no landing", t.straight(landing=False), 'CONCRETE', {}, "#b9b4aa"),
    ]
    fig = plt.figure(figsize=(15, 10))
    for k, (title, sk, kind, opts, col) in enumerate(cases):
        f = sm.build_flight(*sk)
        ax = fig.add_subplot(2, 3, k + 1, projection='3d')
        draw(ax, sm.build(kind, f, **opts), col, title)
    fig.tight_layout()
    fig.savefig(out, dpi=110)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "preview.png")
