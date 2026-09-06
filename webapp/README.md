# GVP Volcano Explorer (web app)

Interactive map companion to the terminology paper. Built from the local GVP
catalogue — same tier thresholds, `type_group()` and `REF_YEAR = 2026` as the
figure scripts, so the app and the paper figures never disagree.

## Run
Just **double-click `index.html`** (data is embedded as JS, so no local server
is needed). Only the Leaflet library loads from the web.

The map uses the **Equal Earth** projection (equal-area, Šavrič et al. 2019),
so marker density and land areas are not inflated towards the poles as in Web
Mercator. Because Leaflet raster tiles are Mercator-only, the basemap is drawn
from embedded Natural Earth 1:110m land polygons and country borders
(`data/data_world.js`, public domain; rebuild with `python build_worlddata.py`).

## Rebuild data
After re-running `../build_catalogue.py`, regenerate the embedded data:

```
python build_webdata.py
```

This writes `data/data_core.js` (volcanoes + per-volcano eruption history +
population) and `data/data_details.js` (summaries + photos).

## The three tabs
- **Terminology & tiers** — colour by draft Table 2 tier; drag the
  erupting / high / moderate thresholds and watch the active/dormant counts flip.
- **Population exposure** — marker area ∝ people within 5–100 km; sidebar lists
  the long-repose, high-exposure volcanoes (Tatun, Chichinautzin, Campi Flegrei…).
- **Eruption timeline** — scrub or **play** the reference year to rebuild the
  active-volcano picture through history (last eruption is recomputed from each
  volcano's confirmed eruption record up to that year).

The reference-year slider is shared across all map tabs, the live histogram /
exposure / timeline chart sits bottom-left, and tier counts update top-right.

## Take a 3D tour (link to the Volcano Sky Tour)

Every volcano popup has a **Take a 3D tour** button. It opens the standalone
Volcano Sky Tour app in a **new tab** with `#vn=<GVP number>&tour`: a focused
single-volcano view (legend and side panel hidden) that flies to the volcano
with the teaching note and framing of its tour stop (`tours.js` over there) and
orbits it until you drag. The target is set by `TOUR_APP` in `index.html`: when the page is
opened from disk it uses the sibling repo `../../volcano_fly_educational/`, when
served over http(s) it uses https://aardid.github.io/volcano-sky-tour/.

## Alternative version with a 3D sky tour (`index_skytour.html`)

Same explorer, plus a full-screen 3D fly-through (ArcGIS Maps SDK for
JavaScript SceneView: World Imagery, World Elevation 3D, OpenStreetMap 3D
buildings, all public, no API key). Open `index_skytour.html`:

- every popup has a **Sky tour in 3D** button; or switch **Sky tour on click**
  in the header so clicking a marker opens the 3D view directly;
- the 3D view flies in and orbits the volcano, shows the same tier / repose /
  population card, and offers **Fly** (W/S pitch, A/D turn, arrows climb,
  Shift turbo, Space brake) and **Nearest next** to hop along the arc through
  the currently filtered volcanoes; Esc or **Map** returns to the 2D map;
- deep link: `index_skytour.html#sky=211020` (GVP number); add `?instant` to
  skip the fly-in animation.

The 3D engine (about 2 MB) is downloaded only when the first tour is opened, so
the 2D app is unchanged until then. All 3D code is in `skytour.js`; the HTML
is generated from `index.html` by `python build_skytour_version.py` (re-run it
after editing `index.html`). Marker colours follow the reference year and
thresholds set in the 2D sidebar. A **Full app** button opens the standalone
Volcano Sky Tour (`../../volcano_fly_educational`, github.com/aardid/volcano-sky-tour)
when it sits next to this repo.

## Credits

Powered by **Cloudbreak Analytics**.
