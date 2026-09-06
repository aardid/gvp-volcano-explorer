/*  skytour.js — 3D "sky tour" add-on for the GVP Volcano Explorer
 *  ---------------------------------------------------------------
 *  Opens a full-screen ArcGIS SceneView (World Imagery + World Elevation 3D +
 *  OpenStreetMap 3D buildings — the same public services World Sky Tour uses)
 *  over the 2D Leaflet explorer. Fly-in, auto-orbit, free flight (WASD) and
 *  "hop to nearest" through the currently filtered volcanoes.
 *
 *  Expects the globals of index.html: V, DET, HIST, S, TIERS, UNDATED, REF,
 *  yearsSince, tierOf, fmt, fmtYr, reposeText, passFilter, map, markers, openPopup.
 *  The ArcGIS SDK (≈2 MB) is only downloaded the first time a tour is opened.
 *  Exposes window.SKY = {mode, open(vn), close(), toggleMode()}.
 */
(function(){
"use strict";
const SDK = "https://js.arcgis.com/4.34/";
const FULL_APP = "../../../volcano_fly_educational/index.html";   // standalone Volcano Sky Tour (optional)
const INSTANT = new URLSearchParams(location.search).has("instant"); // ?instant -> no fly-in animation (testing / screenshots)
const BYN = Object.fromEntries(V.map(v=>[v.n,v]));

// ---------------------------------------------------------------- CSS + DOM
const css = `
#sky{position:fixed;inset:0;z-index:2000;background:#06090f;display:none;flex-direction:column;color:#e7ecf3;font:13px/1.45 system-ui,Segoe UI,Roboto,sans-serif}
#sky.show{display:flex}
#skyView{position:absolute;inset:0}
#skyTop{position:absolute;left:0;right:0;top:0;z-index:5;display:flex;gap:10px;align-items:center;padding:8px 12px;background:linear-gradient(rgba(6,9,15,.92),rgba(6,9,15,0));pointer-events:none}
#skyTop>*{pointer-events:auto}
#skyTop h2{margin:0;font-size:16px;font-weight:700;display:flex;gap:8px;align-items:center}
#skyTop .meta{color:#9aa6b8;font-size:11.5px}
#skyTop .tierbadge{display:inline-block;padding:1px 8px;border-radius:10px;color:#fff;font-size:11px;font-weight:700}
#skyTop .spacer{flex:1}
.skyb{background:#1b2230;border:1px solid #33405a;color:#e7ecf3;border-radius:6px;padding:6px 11px;cursor:pointer;font-size:12.5px;font-weight:600}
.skyb:hover{border-color:#5aa9ff}
.skyb.on{background:#ff7a3d;color:#1a0d06;border-color:#ff7a3d}
.skyb.x{background:rgba(0,0,0,.5)}
#skyCard{position:absolute;right:12px;bottom:12px;width:340px;max-height:60vh;z-index:5;background:rgba(20,26,37,.94);border:1px solid #33405a;border-radius:10px;overflow:hidden;backdrop-filter:blur(3px)}
#skyCard img{width:100%;max-height:170px;object-fit:cover;display:block}
#skyCard .body{padding:10px 12px;overflow:auto;max-height:calc(60vh - 170px)}
#skyCard .facts{display:grid;grid-template-columns:1fr 1fr;gap:6px 10px;margin:6px 0}
#skyCard .facts div{background:rgba(255,255,255,.05);border-radius:6px;padding:5px 8px}
#skyCard .facts small{display:block;color:#9aa6b8;font-size:10px;text-transform:uppercase;letter-spacing:.5px}
#skyCard .facts b{font-size:13px}
#skyCard details summary{cursor:pointer;color:#9aa6b8;font-size:12px}
#skyCard details div{max-height:130px;overflow:auto;font-size:11.5px;color:#cfd6e2;margin-top:4px}
#skyHud{position:absolute;left:50%;top:56px;transform:translateX(-50%);z-index:5;display:none;gap:16px;background:rgba(6,9,15,.7);border:1px solid #33405a;border-radius:8px;padding:5px 12px;font:12px ui-monospace,Consolas,monospace}
#skyHud.show{display:flex}
#skyHud b{color:#ff7a3d}
#skyHud small{color:#9aa6b8}
#skyHelp{position:absolute;left:12px;bottom:12px;z-index:5;background:rgba(20,26,37,.9);border:1px solid #33405a;border-radius:8px;padding:8px 12px;font-size:11.5px;color:#9aa6b8;max-width:330px}
#skyHelp kbd{background:#0c1018;border:1px solid #33405a;border-bottom-width:2px;border-radius:4px;padding:0 5px;font:11px ui-monospace,Consolas,monospace;color:#e7ecf3}
#skyLoad{position:absolute;inset:0;z-index:6;display:grid;place-items:center;background:#06090f;color:#9aa6b8;font-size:14px}
#skyLoad.hide{display:none}
#skyToast{position:absolute;left:50%;bottom:70px;transform:translateX(-50%);z-index:7;background:rgba(20,26,37,.95);border:1px solid #33405a;border-radius:8px;padding:7px 12px;font-size:12px;opacity:0;transition:opacity .3s;pointer-events:none}
#skyToast.show{opacity:1}
.skybtn{background:#ff7a3d;color:#1a0d06;border:0;border-radius:6px;padding:5px 10px;font-weight:700;cursor:pointer;font-size:12px}
.skybtn:hover{background:#ff9463}
#skymode b{color:#ff7a3d}
#skymode.on{border-color:#ff7a3d;background:#2a1a12}
`;
const style = document.createElement("style"); style.textContent = css; document.head.appendChild(style);

const root = document.createElement("div"); root.id = "sky";
root.innerHTML = `
  <div id="skyView"></div>
  <div id="skyTop">
    <h2 id="skyName"></h2><span class="meta" id="skyMeta"></span><span class="spacer"></span>
    <button class="skyb" id="skyPrev" title="Back to the previous volcano">⏮</button>
    <button class="skyb" id="skyNext" title="Hop to the nearest volcano in the current filter">Nearest next ⏭</button>
    <button class="skyb" id="skyOrbit">⟳ Orbit</button>
    <button class="skyb" id="skyFly">✈ Fly</button>
    <button class="skyb" id="skyFull" title="Open in the standalone Volcano Sky Tour app">Full app ↗</button>
    <button class="skyb x" id="skyClose" title="Back to the map (Esc)">✕ Map</button>
  </div>
  <div id="skyHud"><span><small>SPEED</small> <b id="hSpd">0</b> km/h</span><span><small>ALT</small> <b id="hAlt">0</b> m</span><span><small>AGL</small> <b id="hAgl">0</b> m</span><span><small>HDG</small> <b id="hHdg">000</b>°</span></div>
  <div id="skyCard"></div>
  <div id="skyHelp">Drag to look around, wheel to zoom. <b>Orbit</b> circles the volcano; <b>Fly</b> gives you the controls:
    <kbd>W</kbd>/<kbd>S</kbd> pitch · <kbd>A</kbd>/<kbd>D</kbd> turn · <kbd>↑</kbd>/<kbd>↓</kbd> climb · <kbd>Shift</kbd> turbo · <kbd>Space</kbd> brake · <kbd>Esc</kbd> back.</div>
  <div id="skyLoad">Loading the 3D engine…</div>
  <div id="skyToast"></div>`;
document.body.appendChild(root);
const $ = id => document.getElementById(id);
const toast = (m, ms=2500) => { const t=$("skyToast"); t.textContent=m; t.classList.add("show"); clearTimeout(t._h); t._h=setTimeout(()=>t.classList.remove("show"),ms); };
const esc = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));

// ---------------------------------------------------------------- geometry
const R=6371008.8, d2r=Math.PI/180, r2d=180/Math.PI;
function destination(lat,lon,brg,dist){
  const f1=lat*d2r,l1=lon*d2r,t=brg*d2r,d=dist/R;
  const f2=Math.asin(Math.sin(f1)*Math.cos(d)+Math.cos(f1)*Math.sin(d)*Math.cos(t));
  const l2=l1+Math.atan2(Math.sin(t)*Math.sin(d)*Math.cos(f1),Math.cos(d)-Math.sin(f1)*Math.sin(f2));
  return {lat:f2*r2d, lon:((l2*r2d+540)%360)-180};
}
function haversine(a,b,c,d){ const p=(c-a)*d2r,q=(d-b)*d2r; const s=Math.sin(p/2)**2+Math.cos(a*d2r)*Math.cos(c*d2r)*Math.sin(q/2)**2; return 2*R*Math.asin(Math.sqrt(s)); }
function bearingTo(a,b,c,d){ const f1=a*d2r,f2=c*d2r,dl=(d-b)*d2r; const y=Math.sin(dl)*Math.cos(f2), x=Math.cos(f1)*Math.sin(f2)-Math.sin(f1)*Math.cos(f2)*Math.cos(dl); return (Math.atan2(y,x)*r2d+360)%360; }
function geomFor(v){
  const broad = v.tg==="Caldera" || v.tg==="Monogenetic / field";
  return {dist:(broad?22:11)*1000, alt:broad?8000:3800, bearing:200, tilt:broad?62:70, orbit:40};
}
function cameraFor(v,g,b){
  b = b ?? g.bearing; const p = destination(v.lat,v.lon,b,g.dist);
  return {position:{longitude:p.lon,latitude:p.lat,z:Math.max(v.elev||0,0)+g.alt,spatialReference:{wkid:4326}}, heading:(b+180)%360, tilt:g.tilt};
}

// ---------------------------------------------------------------- state
const K = {ready:false, view:null, layer:null, cur:null, hist:[], visited:new Set(), orbiting:false, flying:false, raf:0, keys:new Set(), F:null};
let A = null;   // ArcGIS modules

function loadSDK(){
  if (K.sdk) return K.sdk;
  K.sdk = new Promise((res,rej)=>{
    const l=document.createElement("link"); l.rel="stylesheet"; l.href=SDK+"esri/themes/dark/main.css"; document.head.appendChild(l);
    const s=document.createElement("script"); s.src=SDK; s.onload=res; s.onerror=()=>rej(new Error("ArcGIS SDK failed to load")); document.head.appendChild(s);
  }).then(()=>new Promise((res,rej)=>window.require(
    ["esri/Map","esri/views/SceneView","esri/layers/FeatureLayer","esri/layers/SceneLayer","esri/Graphic","esri/geometry/Point","esri/Camera"],
    (Map,SceneView,FeatureLayer,SceneLayer,Graphic,Point,Camera)=>{ A={Map,SceneView,FeatureLayer,SceneLayer,Graphic,Point,Camera}; res(); }, rej)));
  return K.sdk;
}

function buildView(){
  const tierColor = v => { const ti=tierOf(yearsSince(v,S.year)); return ti==null?UNDATED.color:TIERS[ti].color; };
  const graphics = V.map((v,i)=>new A.Graphic({
    geometry:new A.Point({longitude:v.lon,latitude:v.lat,spatialReference:{wkid:4326}}),
    attributes:{oid:i,vn:v.n,name:v.name,col:tierColor(v)}}));
  const sym = color => ({type:"point-3d",symbolLayers:[{type:"icon",resource:{primitive:"circle"},size:9,material:{color},outline:{color:[0,0,0,.85],size:.7}}],
    verticalOffset:{screenLength:26,maxWorldLength:2500,minWorldLength:40},callout:{type:"line",size:1,color:[255,255,255,.55]}});
  const cols=[...new Set(graphics.map(g=>g.attributes.col))];
  K.layer = new A.FeatureLayer({source:graphics,objectIdField:"oid",geometryType:"point",spatialReference:{wkid:4326},
    fields:[{name:"oid",type:"oid"},{name:"vn",type:"integer"},{name:"name",type:"string"},{name:"col",type:"string"}],
    elevationInfo:{mode:"relative-to-ground"},popupEnabled:false,screenSizePerspectiveEnabled:true,
    renderer:{type:"unique-value",field:"col",uniqueValueInfos:cols.map(c=>({value:c,symbol:sym(c)}))},
    labelingInfo:[{labelExpressionInfo:{expression:"$feature.name"},labelPlacement:"above-center",
      symbol:{type:"label-3d",symbolLayers:[{type:"text",size:11,material:{color:"white"},halo:{color:[0,0,0,.75],size:1.6}}]}}],labelsVisible:true});
  const buildings = new A.SceneLayer({portalItem:{id:"ca0470dbbddb4db28bad74ed39949e25"},popupEnabled:false});
  K.view = new A.SceneView({container:"skyView", map:new A.Map({basemap:"satellite",ground:"world-elevation",layers:[buildings,K.layer]}),
    qualityProfile:"medium", environment:{atmosphereEnabled:true,starsEnabled:true,lighting:{type:"virtual",directShadowsEnabled:false}},
    ui:{components:["attribution"]}, popup:{defaultPopupTemplateEnabled:false},
    camera:{position:{longitude:0,latitude:0,z:20_000_000,spatialReference:{wkid:4326}},heading:0,tilt:0}});
  K.view.on("click", e=>K.view.hitTest(e,{include:[K.layer]}).then(r=>{ const g=r.results.find(x=>x.graphic?.layer===K.layer)?.graphic; if(g) open(g.attributes.vn); }));
  K.view.on("drag", e=>{ if(e.action==="start"&&K.orbiting) stopOrbit(); });
  K.view.on("key-down", e=>{ if(K.flying) e.stopPropagation(); });
  K.view.on("key-up",   e=>{ if(K.flying) e.stopPropagation(); });
  return K.view.when();
}
function refreshColors(){    // tier colours follow the explorer's reference year / thresholds
  if(!K.layer) return;
  const tierColor = v => { const ti=tierOf(yearsSince(v,S.year)); return ti==null?UNDATED.color:TIERS[ti].color; };
  K.layer.queryFeatures().then(fs=>{ fs.features.forEach(f=>{ f.attributes.col=tierColor(BYN[f.attributes.vn]); }); K.layer.applyEdits({updateFeatures:fs.features}); }).catch(()=>{});
}

// ---------------------------------------------------------------- card
function card(v){
  const d=DET[v.n]||{}, ys=yearsSince(v,S.year), ti=tierOf(ys);
  const tcol=ti==null?UNDATED.color:TIERS[ti].color, tlab=ti==null?"Undated":TIERS[ti].label;
  $("skyName").innerHTML=`${esc(v.name)} <span class="tierbadge" style="background:${tcol};${(ti==2||ti==null)?"color:#111":""}">${tlab}</span>`;
  $("skyMeta").textContent=`${v.type} · ${v.cty} · ${v.elev!=null?v.elev.toLocaleString()+" m":""} · as of ${S.year}`;
  $("skyCard").innerHTML=(d.photo?`<img src="${esc(d.photo)}" referrerpolicy="no-referrer" onerror="this.remove()" alt="">`:"")+
    `<div class="body"><div class="facts">
      <div><small>Last eruption</small><b>${fmtYr(v.ley)}</b></div><div><small>Repose</small><b>${reposeText(ys)}</b></div>
      <div><small>People within 30 km</small><b>${fmt(v.p30)}</b></div><div><small>People within 100 km</small><b>${fmt(v.p100)}</b></div>
      <div><small>Confirmed eruptions</small><b>${v.ne}</b></div><div><small>Setting</small><b style="font-size:11.5px">${esc((v.tec||"").split("/")[0].trim()||"—")}</b></div></div>
      ${d.cap?`<div style="font-size:11px;color:#9aa6b8">${esc(d.cap).slice(0,160)}${d.cap.length>160?"…":""} <i>${esc(d.credit||"")}</i></div>`:""}
      ${d.sum?`<details style="margin-top:6px"><summary>Geological summary (GVP)</summary><div>${esc(d.sum)}</div></details>`:""}
      <div style="margin-top:8px"><a href="https://volcano.si.edu/volcano.cfm?vn=${v.n}" target="_blank">GVP profile #${v.n} ↗</a></div></div>`;
}

// ---------------------------------------------------------------- open / navigate
async function open(vn, push=true){
  const v=BYN[vn]; if(!v) return;
  root.classList.add("show");
  try{
    if(!K.ready){ $("skyLoad").classList.remove("hide"); await loadSDK(); await buildView(); K.ready=true; }
    $("skyLoad").classList.add("hide");
  }catch(e){ $("skyLoad").textContent="Could not load the 3D engine: "+e.message; console.error(e); return; }
  stopOrbit(); stopFlight();
  if(push && K.cur && K.cur.n!==vn) K.hist.push(K.cur.n);
  K.cur=v; K.visited.add(vn); card(v); refreshColors();
  location.hash="sky="+vn;
  const g=geomFor(v), cam=cameraFor(v,g);
  const far=haversine(K.view.camera.position.latitude,K.view.camera.position.longitude,v.lat,v.lon);
  if(INSTANT){ K.view.camera=new A.Camera({position:new A.Point(cam.position),heading:cam.heading,tilt:cam.tilt}); return; }
  try{ await K.view.goTo(cam,{speedFactor:far>3e6?.9:.7,easing:"in-out-cubic",maxDuration:9000}); }catch(e){ return; }
  if(K.cur===v) startOrbit();
}
function close(){
  stopOrbit(); stopFlight(); root.classList.remove("show"); K.visited.clear(); K.hist=[];
  if(location.hash.startsWith("#sky=")) history.replaceState(null,"",location.pathname+location.search);
  if(K.cur){ const m=markers.find(m=>m._v.n===K.cur.n); if(m){ map.setView(m.getLatLng(),Math.max(map.getZoom(),6)); openPopup(m); } }
}
function nearestNext(){
  if(!K.cur) return;
  const pool=V.filter(v=>passFilter(v)&&!K.visited.has(v.n));
  const src=pool.length?pool:V.filter(v=>v.n!==K.cur.n);
  if(!pool.length) K.visited.clear();
  let best=null,bd=Infinity; for(const v of src){ const d=haversine(K.cur.lat,K.cur.lon,v.lat,v.lon); if(d<bd){bd=d;best=v;} }
  if(best){ toast(`${best.name} · ${(bd/1000).toFixed(0)} km away`); open(best.n); }
}
function prev(){ const n=K.hist.pop(); if(n!=null) open(n,false); else toast("No previous volcano"); }

// ---------------------------------------------------------------- orbit
function startOrbit(){
  if(!K.cur) return; stopFlight(); K.orbiting=true; $("skyOrbit").classList.add("on");
  const v=K.cur, g=geomFor(v), t0=performance.now();
  const b0=bearingTo(v.lat,v.lon,K.view.camera.position.latitude,K.view.camera.position.longitude);
  const step=now=>{ if(!K.orbiting) return; const b=(b0+(now-t0)/(g.orbit*1000)*360)%360; const c=cameraFor(v,g,b);
    K.view.camera=new A.Camera({position:new A.Point(c.position),heading:c.heading,tilt:c.tilt}); K.raf=requestAnimationFrame(step); };
  K.raf=requestAnimationFrame(step);
}
function stopOrbit(){ K.orbiting=false; cancelAnimationFrame(K.raf); $("skyOrbit").classList.remove("on"); }

// ---------------------------------------------------------------- free flight
const MIN_AGL=120;
function groundZ(lon,lat){ try{ const s=K.view.groundView?.elevationSampler; if(s){ const p=s.queryElevation(new A.Point({longitude:lon,latitude:lat,spatialReference:{wkid:4326}})); if(p&&p.z!=null) return p.z; } }catch(e){} return 0; }
function startFlight(){
  stopOrbit(); const c=K.view.camera;
  K.F={cruise:220,speed:110,lat:c.position.latitude,lon:c.position.longitude,z:c.position.z,heading:c.heading,tilt:Math.max(60,Math.min(95,c.tilt)),last:performance.now()};
  if(K.F.z>60000) K.F.z=12000; K.F.z=Math.max(K.F.z,groundZ(K.F.lon,K.F.lat)+600);
  K.flying=true; K.keys.clear(); $("skyFly").classList.add("on"); $("skyHud").classList.add("show");
  toast("Flying: W/S pitch · A/D turn · ↑/↓ climb · Shift turbo · Space brake · Esc to stop",4000);
  K.raf=requestAnimationFrame(flightStep);
}
function stopFlight(){ if(!K.flying) return; K.flying=false; cancelAnimationFrame(K.raf); $("skyFly").classList.remove("on"); $("skyHud").classList.remove("show"); }
function flightStep(now){
  if(!K.flying) return; const F=K.F, k=K.keys, dt=Math.min((now-F.last)/1000,.1); F.last=now;
  const target=k.has("Space")?0:F.cruise*((k.has("ShiftLeft")||k.has("ShiftRight"))?3.2:1);
  F.speed+=(target-F.speed)*Math.min(dt*1.6,1);
  const turn=38*dt*(0.6+0.4*Math.min(F.speed/F.cruise,1));
  if(k.has("KeyA")||k.has("ArrowLeft")) F.heading-=turn; if(k.has("KeyD")||k.has("ArrowRight")) F.heading+=turn;
  if(k.has("KeyW")) F.tilt=Math.min(F.tilt+28*dt,112); if(k.has("KeyS")) F.tilt=Math.max(F.tilt-28*dt,45);
  let climb=0; if(k.has("ArrowUp")||k.has("KeyE")) climb+=1; if(k.has("ArrowDown")||k.has("KeyQ")) climb-=1;
  F.heading=(F.heading+360)%360;
  const pitch=(90-F.tilt)*d2r, horiz=F.speed*Math.cos(pitch)*dt, vert=F.speed*Math.sin(pitch)*dt+climb*F.speed*.6*dt;
  const p=destination(F.lat,F.lon,F.heading,horiz); F.lat=p.lat; F.lon=p.lon; F.z+=vert;
  const g=groundZ(F.lon,F.lat); if(F.z<g+MIN_AGL){ F.z=g+MIN_AGL; if(F.tilt>92) F.tilt-=20*dt; }
  K.view.camera=new A.Camera({position:new A.Point({longitude:F.lon,latitude:F.lat,z:F.z,spatialReference:{wkid:4326}}),heading:F.heading,tilt:F.tilt});
  $("hSpd").textContent=Math.round(F.speed*3.6); $("hAlt").textContent=Math.round(F.z).toLocaleString(); $("hAgl").textContent=Math.round(F.z-g).toLocaleString(); $("hHdg").textContent=String(Math.round(F.heading)%360).padStart(3,"0");
  K.raf=requestAnimationFrame(flightStep);
}
const FLIGHT_KEYS=new Set(["KeyW","KeyA","KeyS","KeyD","KeyQ","KeyE","ArrowUp","ArrowDown","ArrowLeft","ArrowRight","Space","ShiftLeft","ShiftRight"]);
window.addEventListener("keydown",e=>{
  if(!root.classList.contains("show")||e.target.matches("input,textarea")) return;
  if(e.code==="Escape"){ if(K.flying) stopFlight(); else if(K.orbiting) stopOrbit(); else close(); return; }
  if(!K.flying) return;
  if(e.code==="Equal"||e.code==="NumpadAdd") K.F.cruise=Math.min(K.F.cruise*1.25,1500);
  if(e.code==="Minus"||e.code==="NumpadSubtract") K.F.cruise=Math.max(K.F.cruise/1.25,30);
  if(FLIGHT_KEYS.has(e.code)){ K.keys.add(e.code); e.preventDefault(); }
},true);
window.addEventListener("keyup",e=>K.keys.delete(e.code),true);
window.addEventListener("blur",()=>K.keys.clear());

// ---------------------------------------------------------------- wiring
$("skyClose").onclick=close;
$("skyNext").onclick=nearestNext;
$("skyPrev").onclick=prev;
$("skyOrbit").onclick=()=>K.orbiting?stopOrbit():startOrbit();
$("skyFly").onclick=()=>K.flying?stopFlight():startFlight();
$("skyFull").onclick=()=>{ if(K.cur) window.open(FULL_APP+"#vn="+K.cur.n,"_blank"); };

const SKY = window.SKY = {mode:false, open, close,
  toggleMode(){ SKY.mode=!SKY.mode; const b=document.getElementById("skymode"); if(b){ b.classList.toggle("on",SKY.mode); b.innerHTML=`🛩 Sky tour on click: <b>${SKY.mode?"on":"off"}</b>`; } }};
const modeBtn=document.getElementById("skymode"); if(modeBtn) modeBtn.onclick=SKY.toggleMode;

// deep link: index_skytour.html#sky=211020
const m=location.hash.match(/sky=(\d+)/); if(m&&BYN[+m[1]]) open(+m[1]);
})();
