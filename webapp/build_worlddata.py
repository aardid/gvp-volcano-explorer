"""
build_worlddata.py
------------------
Embed a small world basemap (Natural Earth 1:110m land polygons and country
boundary lines) as `data/data_world.js` so the web app can draw its own map in
the Equal Earth projection without raster tiles (Leaflet tiles are Web
Mercator only). Coordinates are rounded to 0.01 deg (~1 km): the result is
~300 KB. Natural Earth data are public domain.

    python build_worlddata.py            # downloads from GitHub
    python build_worlddata.py <dir>      # uses ne_110m_*.geojson already in <dir>
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/"
FILES = {"land": "ne_110m_land.geojson",
         "borders": "ne_110m_admin_0_boundary_lines_land.geojson"}


def load(name):
    if len(sys.argv) > 1:
        with open(os.path.join(sys.argv[1], name), encoding="utf-8") as f:
            return json.load(f)
    with urllib.request.urlopen(BASE + name, timeout=60) as r:
        return json.load(r)


def rnd(coords):
    if isinstance(coords[0], (int, float)):
        return [round(coords[0], 2), round(coords[1], 2)]
    return [rnd(c) for c in coords]


def slim(fc):
    """Drop properties, round coordinates; keep geometry type + coordinates."""
    out = []
    for ft in fc["features"]:
        g = ft["geometry"]
        if not g:
            continue
        out.append({"type": g["type"], "coordinates": rnd(g["coordinates"])})
    return out


world = {k: slim(load(v)) for k, v in FILES.items()}
dst = os.path.join(HERE, "data", "data_world.js")
with open(dst, "w", encoding="utf-8") as f:
    f.write("// Natural Earth 1:110m land + admin-0 boundary lines (public domain), "
            "coordinates rounded to 0.01 deg. Built by build_worlddata.py\n")
    f.write("window.GVP_WORLD=" + json.dumps(world, separators=(",", ":")) + ";\n")
print("wrote", dst, os.path.getsize(dst) // 1024, "KB;",
      {k: len(v) for k, v in world.items()})
