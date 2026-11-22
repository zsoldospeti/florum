#!/usr/bin/env node
/* ==============================================================
   FLORUM 1.33.2  ·  teszt: pontos tápoldatozás + kerti növények
   Fájl:  teszt-tragyazas.js

   Dátumhoz kötött viselkedést vizsgál (január / június / október),
   ezért a belső órát előre beállítja:

     · szobanövény: tápoldat CSAK március–szeptember között
     · kerti növény: szezonon kívül egyetlen teendő sincs
     · kerti növénynél a felirat „Trágyázás”, és komposzt/istállótrágya
     · a teendő szövegében ott az adag és az összetétel
     · az űrlap menti a tápoldat-profilt és a szezont
   ============================================================== */

const fs = require('fs');
const path = require('path');
const HTML = process.argv[2] || path.join(__dirname, 'florum.html');

let JSDOM = null;
for (const hol of ['jsdom', '/home/user/jsd/node_modules/jsdom', '/tmp/jsd/node_modules/jsdom', path.join(__dirname, 'node_modules/jsdom')]) {
  try { JSDOM = require(hol).JSDOM; break; } catch (e) {}
}
if (!JSDOM) {
  console.log('\n  jsdom nincs telepítve – a teszt kihagyva.  (npm install jsdom)\n');
  process.exit(0);
}

let ok = 0, bad = 0;
const problems = [];
function check(cim, fn) {
  try {
    const r = fn();
    ok++;
    console.log('  ✓ ' + cim + (r ? '   → ' + String(r).slice(0, 130) : ''));
    return r;
  } catch (e) {
    bad++; problems.push(cim + ': ' + e.message);
    console.log('  ✗ ' + cim + '   → ' + e.message);
    return null;
  }
}
function assert(c, m) { if (!c) throw new Error(m); }

const html0 = fs.readFileSync(HTML, 'utf8');
const EXPORT = `
;window.__T = { applyState: (typeof applyState!=='undefined'?applyState:null),
  render: (typeof render!=='undefined'?render:null),
  collectTasks: (typeof collectTasks!=='undefined'?collectTasks:null),
  intervalFor: (typeof intervalFor!=='undefined'?intervalFor:null),
  fertLine: (typeof fertLine!=='undefined'?fertLine:null),
  defLabel: (typeof defLabel!=='undefined'?defLabel:null),
  inSeason: (typeof inSeason!=='undefined'?inSeason:null),
  applyDBEntry: (typeof applyDBEntry!=='undefined'?applyDBEntry:null),
  fillSelects: (typeof fillSelects!=='undefined'?fillSelects:null),
  openInfo: (typeof openInfo!=='undefined'?openInfo:null),
  TASK_DEFS: (typeof TASK_DEFS!=='undefined'?TASK_DEFS:null),
  state: (typeof state!=='undefined'?state:null),
  store: (typeof store!=='undefined'?store:null) };
`;
const blocks = [...html0.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const big = blocks.sort((a, b) => b.length - a.length)[0];
const idx = big.lastIndexOf('})();');
const html = html0.replace(big, big.slice(0, idx) + EXPORT + big.slice(idx));

/** A lap betöltése rögzített dátummal (pl. '2026-06-15'). */
function lap(datum) {
  const dom = new JSDOM(html, {
    runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://127.0.0.1:8777/',
    beforeParse(win) {
      const R = win.Date;
      const t = new R(datum + 'T09:00:00').getTime();
      class FakeDate extends R {
        constructor(...a) { if (!a.length) super(t); else super(...a); }
        static now() { return t; }
      }
      win.Date = FakeDate;
      win.fetch = () => Promise.reject(new Error('offline teszt'));
      win.alert = () => {}; win.scrollTo = () => {};
      win.matchMedia = () => ({ matches: false, addEventListener() {}, addListener() {} });
      if (win.HTMLDialogElement && !win.HTMLDialogElement.prototype.showModal) {
        win.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
        win.HTMLDialogElement.prototype.close = function () { this.open = false; };
      }
    }
  });
  return dom;
}

// ---------------------------------------------------------------- növények
const SZOBA = {
  id: 'p1', name: 'Monstera', room: 'Nappali', light: 'Világos, szórt',
  waterDays: 7, waterWinter: 12, fertDays: 30, mistDays: 7, repotMonths: 24,
  lastWatered: '2026-06-10', lastFertilized: '2026-06-01', lastMisted: '2026-06-08', lastRepotted: '2026-04-01',
  fertKind: 'level', fertDose: '2 ml / 1 l víz', fertNpk: 'N-P-K 7-3-5', fertFrom: 3, fertTo: 9,
  fertNote: 'csak nedves földre'
};
const KERTI = {
  id: 'k1', name: 'Sárgarépa', room: 'Kert', light: 'Napos / déli ablak',
  waterDays: 5, waterWinter: 0, fertDays: 30, mistDays: 0, repotMonths: 0,
  lastWatered: '2026-06-12', lastFertilized: '2026-06-01',
  garden: true, seasonFrom: 4, seasonTo: 10, sow: 'március–április', harvest: 'július–szeptember',
  fertKind: 'komposzt', fertDose: '2–3 marék / m²', fertFrom: 4, fertTo: 7,
  fertNote: 'ültetés előtt a talajba dolgozva'
};

function novenyek(dom, lista) {
  const T = dom.window.__T;
  T.applyState({ plants: lista, history: [], settings: { winterMode: 'auto', horizon: 7 }, meta: {}, customDb: [] });
  T.render();
  return T;
}
function targy(dom, nev) {
  const T = dom.window.__T;
  const def = T.TASK_DEFS.find(d => d.key === nev);
  return def;
}

// ================================================================
console.log('\n== Szobanövény: tápoldat csak a szezonban ==');
{
  const dom = lap('2026-06-15');
  const T = novenyek(dom, [SZOBA]);
  const def = targy(dom, 'fertilizing');

  check('júniusban van tápoldat-teendő', () => {
    const iv = T.intervalFor(SZOBA, def);
    assert(iv === 30, 'az intervallum ' + iv);
    return '30 naponta';
  });
  check('a teendő szövegében ott az adag és az összetétel', () => {
    const sor = T.fertLine(SZOBA);
    assert(/2 ml/.test(sor), 'nincs adag: ' + sor);
    assert(/7-3-5/.test(sor), 'nincs összetétel: ' + sor);
    assert(/március–szeptember/.test(sor), 'nincs időszak: ' + sor);
    return sor;
  });
  check('a felirat „Tápoldatozás”', () => {
    const c = T.defLabel(SZOBA, def);
    assert(c === 'Tápoldatozás', 'felirat: ' + c);
    return c;
  });
  dom.window.close();
}
{
  const dom = lap('2026-10-15');
  const T = novenyek(dom, [SZOBA]);
  const def = targy(dom, 'fertilizing');
  check('októberben NINCS tápoldat-teendő (szezonon kívül)', () => {
    const iv = T.intervalFor(SZOBA, def);
    assert(iv === 0, 'mégis van: ' + iv + ' nap');
    const db = T.collectTasks().filter(x => x.def.key === 'fertilizing');
    assert(db.length === 0, 'a teendők között is szerepel');
    return 'nincs';
  });
  check('az öntözés viszont októberben is megvan', () => {
    const iv = T.intervalFor(SZOBA, targy(dom, 'watering'));
    assert(iv > 0, 'nincs öntözés');
    return iv + ' naponta (téli érték)';
  });
  dom.window.close();
}
check('a „nem tápoldatozom” beállítás teljesen kikapcsolja', () => {
  const dom = lap('2026-06-15');
  const T = novenyek(dom, [Object.assign({}, SZOBA, { fertKind: 'semmi' })]);
  const iv = T.intervalFor(Object.assign({}, SZOBA, { fertKind: 'semmi' }), targy(dom, 'fertilizing'));
  assert(iv === 0, 'mégis van: ' + iv);
  dom.window.close();
  return 'kikapcsolva';
});

// ================================================================
console.log('\n== Kerti növény: szezonon kívül nincs teendő ==');
{
  const dom = lap('2026-01-20');
  const T = novenyek(dom, [KERTI]);
  check('januárban egyetlen teendő sincs', () => {
    const t = T.collectTasks();
    assert(t.length === 0, 'van ' + t.length + ' teendő');
    return '0 teendő';
  });
  check('a szezon-ellenőrzés jól dönt', () => {
    assert(T.inSeason(KERTI, new dom.window.Date('2026-06-01')) === true, 'júniusra hamis');
    assert(T.inSeason(KERTI, new dom.window.Date('2026-01-01')) === false, 'januárra igaz');
    return 'áprilistól októberig igaz';
  });
  dom.window.close();
}
{
  const dom = lap('2026-06-20');
  const T = novenyek(dom, [KERTI]);
  check('júniusban vannak teendők (öntözés + trágyázás)', () => {
    const t = T.collectTasks().map(x => x.def.key);
    assert(t.includes('watering'), 'nincs öntözés: ' + t.join(','));
    assert(t.includes('fertilizing'), 'nincs trágyázás: ' + t.join(','));
    return t.join(', ');
  });
  check('kerten a felirat „Trágyázás”, nem „Tápoldat”', () => {
    const c = T.defLabel(KERTI, targy(dom, 'fertilizing'));
    assert(c === 'Trágyázás', 'felirat: ' + c);
    return c;
  });
  check('a trágya adagja is megjelenik (komposzt)', () => {
    const sor = T.fertLine(KERTI);
    assert(/komposzt/.test(sor), 'nincs benne komposzt: ' + sor);
    assert(/marék/.test(sor), 'nincs benne adag: ' + sor);
    return sor;
  });
  check('a növénykártyán „kerti növény” jelölés van', () => {
    const k = dom.window.document.querySelector('#plantsContent').innerHTML;
    assert(/kerti növény/.test(k), 'nincs jelölés');
    assert(/április–október/.test(k), 'nincs szezon a jelölésben');
    return 'kerti növény · április–október';
  });
  dom.window.close();
}
{
  const dom = lap('2026-09-20');
  const T = novenyek(dom, [KERTI]);
  check('szeptemberben még van öntözés, de trágyázás már nincs', () => {
    const t = T.collectTasks().map(x => x.def.key);
    assert(t.includes('watering'), 'nincs öntözés');
    assert(!t.includes('fertilizing'), 'mégis van trágyázás (április–július az ablak)');
    return t.join(', ');
  });
  dom.window.close();
}

// ================================================================
console.log('\n== Űrlap: a profil mentése és visszatöltése ==');
{
  const dom = lap('2026-06-15');
  const T = novenyek(dom, []);
  const doc = dom.window.document;
  check('az űrlapon vannak a tápoldat-mezők', () => {
    ['f_fertKind', 'f_fertDose', 'f_fertNpk', 'f_fertNote', 'f_fertFrom', 'f_fertTo',
     'f_garden', 'f_seasonFrom', 'f_seasonTo', 'f_sow', 'f_harvest'].forEach(id => {
      assert(doc.getElementById(id), 'hiányzik: ' + id);
    });
    return '11 mező';
  });
  check('a tápoldat-típusok legördülője feltöltve', () => {
    const n = doc.querySelectorAll('#f_fertKind option').length;
    assert(n >= 6, 'csak ' + n + ' opció');
    return n + ' típus (tápoldat, kaktusz, virágzó, komposzt, istállótrágya, semmi)';
  });
  check('mentéskor a profil a növényre kerül', () => {
    doc.getElementById('btnAdd').click();
    doc.getElementById('f_name').value = 'Kerti retek';
    doc.getElementById('f_water').value = '4';
    doc.getElementById('f_fertKind').value = 'komposzt';
    doc.getElementById('f_fertDose').value = '1 marék / m²';
    doc.getElementById('f_fertFrom').value = '4';
    doc.getElementById('f_fertTo').value = '7';
    doc.getElementById('f_garden').checked = true;
    doc.getElementById('f_seasonFrom').value = '3';
    doc.getElementById('f_seasonTo').value = '6';
    doc.getElementById('f_sow').value = 'március–augusztus';
    doc.getElementById('f_harvest').value = 'május–október';
    doc.getElementById('plantForm').dispatchEvent(new dom.window.Event('submit', { bubbles: true, cancelable: true }));
    const p = T.state.plants[T.state.plants.length - 1];
    assert(p.name === 'Kerti retek', 'nem mentődött');
    assert(p.fertKind === 'komposzt', 'fertKind: ' + p.fertKind);
    assert(p.fertDose === '1 marék / m²', 'fertDose: ' + p.fertDose);
    assert(p.fertFrom === 4 && p.fertTo === 7, 'ablak: ' + p.fertFrom + '-' + p.fertTo);
    assert(p.garden === true, 'garden nem mentődött');
    assert(p.seasonFrom === 3 && p.seasonTo === 6, 'szezon: ' + p.seasonFrom + '-' + p.seasonTo);
    assert(p.sow === 'március–augusztus' && p.harvest === 'május–október', 'szöveges mezők');
    return p.name + ' · ' + p.fertKind + ' · ' + p.sow;
  });
  check('adatbázis-bejegyzés betölti a profilt az űrlapra', () => {
    T.applyDBEntry({ id: 'sargarepa', name: 'Sárgarépa', latin: 'Daucus carota', light: 'Napos / déli ablak',
      water: 5, waterWinter: 0, fert: 30, fertWinter: 0, mist: 0, mistWater: 'nem', repot: 0,
      fertKind: 'komposzt', fertDose: '2–3 marék / m²', fertFrom: 4, fertTo: 7,
      garden: true, seasonFrom: 4, seasonTo: 10, sow: 'március–április', harvest: 'július–szeptember' });
    assert(doc.getElementById('f_fertKind').value === 'komposzt', 'fertKind az űrlapon: ' + doc.getElementById('f_fertKind').value);
    assert(doc.getElementById('f_garden').checked === true, 'garden nincs bejelölve');
    assert(doc.getElementById('f_seasonFrom').value === '4', 'seasonFrom: ' + doc.getElementById('f_seasonFrom').value);
    assert(doc.getElementById('f_sow').value === 'március–április', 'sow nincs kitöltve');
    return 'komposzt · április–október · március–április';
  });
  dom.window.close();
}

// ================================================================
console.log('\n== Adatbázis: kerti növények ==');
{
  const dom = lap('2026-06-15');
  const T = novenyek(dom, []);
  check('az adatbázisban vannak kerti növények', () => {
    const kerti = (T.state.customDb || []).length;   // customDb nem kell
    const db = dom.window.document.getElementById('bundledDb');
    const txt = (db && db.textContent) || '';
    assert(txt.length > 1000, 'nincs beágyazott adatbázis');
    const json = JSON.parse(txt);
    const garden = json.plants.filter(p => p.garden === true);
    assert(garden.length >= 10, 'csak ' + garden.length + ' kerti növény');
    const nevek = garden.map(p => p.name);
    assert(nevek.some(n => /hagyma/i.test(n)), 'nincs hagyma');
    assert(nevek.some(n => /répa/i.test(n)), 'nincs répa');
    return garden.length + ' kerti növény (pl. ' + nevek.slice(0, 4).join(', ') + ')';
  });
  check('minden szobanövénynek van tápoldat-profilja', () => {
    const json = JSON.parse(dom.window.document.getElementById('bundledDb').textContent);
    const hiany = json.plants.filter(p => !p.fertKind).map(p => p.name);
    assert(hiany.length === 0, 'hiányzik: ' + hiany.slice(0, 6).join(', '));
    const ablak = json.plants.filter(p => p.fertFrom && p.fertTo);
    assert(ablak.length === json.plants.length, 'néhánynál nincs hónap-ablak');
    return json.plants.length + ' növény, mindegyiknél van profil';
  });
  dom.window.close();
}

console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás');
if (problems.length) { console.log('Hibák:'); problems.forEach(p => console.log('  - ' + p)); }
console.log('');
process.exit(bad ? 1 : 0);
