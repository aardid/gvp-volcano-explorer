"""
build_skytour_version.py
------------------------
Derive `index_skytour.html` from `index.html`: the same GVP Volcano Explorer,
plus a 3D "sky tour" (ArcGIS SceneView fly-in / orbit / free flight) that opens
when you click a volcano. All 3D code lives in `skytour.js`; this script only
inserts the hooks, so re-run it whenever index.html changes:

    python build_skytour_version.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "index.html"), encoding="utf-8").read()


def patch(text, old, new, count=1):
    assert text.count(old) == count, f"anchor not found exactly {count}x: {old[:60]!r}"
    return text.replace(old, new)


out = src
out = patch(out,
    "<title>GVP Volcano Explorer — terminology, exposure &amp; time</title>",
    "<title>GVP Volcano Explorer — with 3D sky tour</title>")

# header: sky-tour mode toggle (outside .tabs so the tab handler ignores it)
out = patch(out,
    '<span class="sub" id="hsub"></span>',
    '<span class="sub" id="hsub"></span>\n'
    '  <button id="skymode" class="btn" title="When on, clicking a volcano opens the 3D sky tour directly">'
    '🛩 Sky tour on click: <b>off</b></button>')

# marker click: sky-tour mode opens the 3D view directly, otherwise the popup
out = patch(out,
    'm.on("click",()=>openPopup(m));',
    'm.on("click",()=>(window.SKY&&SKY.mode)?SKY.open(m._v.n):openPopup(m));')

# popup: add a Sky tour button next to the GVP link
out = patch(out,
    'html+=`<div style="margin-top:6px"><a href="https://volcano.si.edu/volcano.cfm?vn=${v.n}" target="_blank">GVP profile #${v.n} ↗</a></div></div>`;',
    'html+=`<div style="margin-top:8px;display:flex;gap:8px;align-items:center">'
    '<button class="skybtn" onclick="SKY.open(${v.n})">🛩 Sky tour in 3D</button>'
    '<a href="https://volcano.si.edu/volcano.cfm?vn=${v.n}" target="_blank">GVP #${v.n} ↗</a></div></div>`;')

# load the sky-tour module after the main script
out = patch(out,
    "</script>\n</body>",
    '</script>\n<script src="skytour.js"></script>\n</body>')

dst = os.path.join(HERE, "index_skytour.html")
open(dst, "w", encoding="utf-8").write(out)
print("wrote", dst, len(out), "bytes")
