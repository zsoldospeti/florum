#!/usr/bin/env node
/* ==============================================================
   FLORUM 1.33.2  ·  teszt: a „Kert” fül
   Fájl:  teszt-kert.js

   Amit vizsgál:
     · van-e külön Kert fül és nézet, és vált-e rá
     · üres állapot (még nincs kerti növény) + „+ Kerti növény” gomb
     · szezonban lévő vs. pihenő kerti növény szétválasztása
     · 12 hónapos szezon-csík, „most szedhető” jelzés
     · a pihenő növény nem kap teendő-sort, hanem újraindulás-dátumot
     · a fülön lévő szám-jelző (ma esedékes kerti teendők)
     · a „+ Kerti növény” űrlap kerti alapokkal nyílik
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

// a lapbezárás után befutó késleltetett hívások ne állítsák meg a tesztet
process.on('unhandledRejection', () => {});

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
  switchView: (typeof switchView!=='undefined'?switchView:null),
  renderGarden: (typeof renderGarden!=='undefined'?renderGarden:null),
  collectTasks: (typeof collectTasks!=='undefined'?collectTasks:null),
  gardenPlants: (typeof gardenPlants!=='undefined'?gardenPlants:null),
  inSeason: (typeof inSeason!=='undefined'?inSeason:null),
  seasonText: (typeof seasonText!=='undefined'?seasonText:null),
  harvestNow: (typeof harvestNow!=='undefined'?harvestNow:null),
  isGardenPlant: (typeof isGardenPlant!=='undefined'?isGardenPlant:null),
  dbGardenEntry: (typeof dbGardenEntry!=='undefined'?dbGardenEntry:null),
  findDBByName: (typeof findDBByName!=='undefined'?findDBByName:null),
  openDialog: (typeof openDialog!=='undefined'?openDialog:null),
  saveForm: (typeof saveForm!=='undefined'?saveForm:null),
  GARDEN_ROOMS: (typeof GARDEN_ROOMS!=='undefined'?GARDEN_ROOMS:null),
  state: (typeof state!=='undefined'?state:null) };
`;
const blocks = [...html0.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const big = blocks.sort((a, b) => b.length - a.length)[0];
const idx = big.lastIndexOf('})();');
const html = html0.replace(big, big.slice(0, idx) + EXPORT + big.slice(idx));

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
const RÉPA = {
  id: 'k1', name: 'Sárgarépa', room: 'Kert', waterDays: 5, fertDays: 30, mistDays: 0, repotMonths: 0,
  lastWatered: '2026-07-05', lastFertilized: '2026-06-20',
  garden: true, seasonFrom: 4, seasonTo: 10,
  sow: 'március–június', harvest: 'július–október',
  fertKind: 'komposzt', fertDose: '2–3 marék / m²', fertFrom: 4, fertTo: 7
};
const BORSÓ = {
  id: 'k2', name: 'Zöldborsó', room: 'Kert', waterDays: 4, fertDays: 45, mistDays: 0, repotMonths: 0,
  lastWatered: '2026-07-01', lastFertilized: '2026-05-20',
  garden: true, seasonFrom: 3, seasonTo: 6,
  sow: 'március–április', harvest: 'június–július',
  fertKind: 'komposzt', fertDose: '1 marék / m²', fertFrom: 4, fertTo: 7
};
const SZOBA = {
  id: 'p1', name: 'Monstera', room: 'Nappali', waterDays: 7, fertDays: 30, mistDays: 0, repotMonths: 24,
  lastWatered: '2026-07-05', lastFertilized: '2026-07-01', fertKind: 'tapoldat', fertFrom: 3, fertTo: 9
};

function novenyek(dom, lista) {
  const T = dom.window.__T;
  T.applyState({ plants: lista, history: [], settings: { winterMode: 'auto', horizon: 7 }, meta: {}, customDb: [] });
  T.render();
  return T;
}
function klikk(dom, nev, ertek) {
  const el = dom.window.document.querySelector('[' + nev + '="' + ertek + '"]');
  assert(el, 'nincs ilyen elem: ' + nev + '=' + ertek);
  el.dispatchEvent(new dom.window.MouseEvent('click', { bubbles: true }));
  return el;
}

// ================================================================
console.log('\n== Felépítés: külön fül és nézet ==');
{
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  check('van „Kert” fül a menüsorban', () => {
    const t = d.querySelector('#tabs .tab[data-view="garden"]');
    assert(t, 'nincs ilyen fül');
    assert(/Kert/.test(t.textContent), 'felirat: ' + t.textContent.trim());
    return t.textContent.trim();
  });
  check('van hozzá saját nézet (#view-garden)', () => {
    assert(d.getElementById('view-garden'), 'nincs view-garden');
    assert(d.getElementById('gardenContent'), 'nincs gardenContent');
    return 'megvan';
  });
  check('a Kert fülre kattintva az a nézet lesz aktív', () => {
    klikk(dom, 'data-view', 'garden');
    const v = d.getElementById('view-garden');
    assert(v.classList.contains('active'), 'nem lett aktív');
    const ma = d.getElementById('view-today');
    assert(!ma.classList.contains('active'), 'a Ma nézet is aktív maradt');
    const tab = d.querySelector('#tabs .tab[data-view="garden"]');
    assert(tab.classList.contains('active'), 'a fül nem jelölődött aktívnak');
    return 'átvált';
  });
  check('a Kert nézet nem zavarja a többit (Ma, Naptár, Növények)', () => {
    klikk(dom, 'data-view', 'today');
    assert(d.getElementById('view-today').classList.contains('active'), 'a Ma nem aktív');
    klikk(dom, 'data-view', 'garden');
    assert(d.getElementById('view-garden').classList.contains('active'), 'a Kert nem aktív');
    return 'oda-vissza működik';
  });
  dom.window.close();
}

// ================================================================
console.log('\n== Üres állapot ==');
{
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  novenyek(dom, [SZOBA]);            // csak szobanövény
  check('szobanövénnyel a Kert fül üres állapotot mutat', () => {
    const h = d.getElementById('gardenContent').textContent;
    assert(/Még nincs kerti növényed/.test(h), 'nincs üres állapot');
    assert(/kerti növény hozzáadása/i.test(h), 'nincs gomb');
    return 'üres állapot';
  });
  check('az üres állapot gombja kerti űrlapot nyit', () => {
    klikk(dom, 'data-action', 'addgarden');
    const g = d.getElementById('f_garden');
    assert(g && g.checked, 'a kerti jelölő nincs bekapcsolva');
    assert(d.getElementById('f_seasonFrom').value === '4', 'szezon tól: ' + d.getElementById('f_seasonFrom').value);
    assert(d.getElementById('f_seasonTo').value === '10', 'szezon ig: ' + d.getElementById('f_seasonTo').value);
    assert(d.getElementById('f_fertKind').value === 'komposzt', 'tápoldat típus: ' + d.getElementById('f_fertKind').value);
    return 'kerti mód, szezon 4–10, komposzt';
  });
  dom.window.close();
}

// ================================================================
console.log('\n== Szezonban lévő vs. pihenő ==');
{
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  const T = novenyek(dom, [RÉPA, BORSÓ, SZOBA]);
  const kert = d.getElementById('gardenContent');

  check('csak a kerti növények kerülnek a fülre', () => {
    assert(T.gardenPlants().length === 2, 'kerti növények: ' + T.gardenPlants().length);
    // a kártyákon és a pihenő listán csak kerti növény szerepelhet
    const kartyak = [...kert.querySelectorAll('.card h3, .grest .gnm')].map(x => x.textContent.trim());
    assert(kartyak.every(n => /Sárgarépa|Zöldborsó/.test(n)), 'nem kerti növény a listán: ' + kartyak.join(', '));
    return '2 kerti növény';
  });
  check('júliusban a répa szezonban van, a borsó már pihen', () => {
    assert(T.inSeason(RÉPA, new dom.window.Date('2026-07-10')) === true, 'répa nincs szezonban');
    assert(T.inSeason(BORSÓ, new dom.window.Date('2026-07-10')) === false, 'borsó szezonban van');
    const h = kert.textContent;
    assert(/Szezonban/.test(h), 'nincs „Szezonban” szakasz');
    assert(/Pihen/.test(h), 'nincs „Pihen” szakasz');
    return '1 szezonban · 1 pihen';
  });
  check('a fejléc-összesítő számai stimmelnek', () => {
    const szamok = [...kert.querySelectorAll('.stat .n')].map(n => n.textContent.trim());
    assert(szamok[0] === '1', 'szezonban: ' + szamok[0]);
    assert(szamok[3] === '1', 'pihen: ' + szamok[3]);
    return szamok.join(' / ') + '  (szezonban / ma / szedhető / pihen)';
  });
  check('a szezon-csík 12 hónapos, a szezon hónapjai kiemelve', () => {
    const csik = kert.querySelector('.season-bar');
    assert(csik, 'nincs szezon-csík');
    const mind = csik.querySelectorAll('.smonth');
    assert(mind.length === 12, 'hónapok: ' + mind.length);
    const on = csik.querySelectorAll('.smonth.on');
    assert(on.length === 7, 'kiemelt hónapok: ' + on.length);   // április–október
    return '12 hónap · 7 kiemelve';
  });
  check('a szedési idő alapján „most szedhető” jelzés van', () => {
    assert(T.harvestNow(RÉPA) === true, 'a répánál nincs jelzés');
    // a borsó szedése június–július, tehát júliusban szintén szedhető lenne –
    // de szezonon kívül a fül már nem is mutatja: ezt külön ellenőrizzük
    const korai = Object.assign({}, BORSÓ, { harvest: 'május–június' });
    assert(T.harvestNow(korai) === false, 'a korai fajtánál van jelzés');
    assert(/most szedhető/.test(kert.textContent), 'a szövegben nincs jelzés');
    return 'Sárgarépa: most szedhető';
  });
  check('a szezonban lévő növénynél vannak teendő-sorok Kész gombbal', () => {
    const gomb = kert.querySelector('[data-done="k1"]');
    assert(gomb, 'nincs Kész gomb');
    assert(gomb.getAttribute('data-task'), 'nincs teendő-típus');
    return 'data-done=k1 / ' + gomb.getAttribute('data-task');
  });
  check('a trágya adagja és időszaka is látszik', () => {
    const h = kert.textContent;
    assert(/2–3 marék/.test(h), 'nincs adag');
    assert(/komposzt/.test(h), 'nincs típus');
    assert(/április–július/.test(h), 'nincs hónap-ablak');
    return 'komposzt · 2–3 marék / m² · április–július';
  });
  check('a pihenő növény nem kap teendőt, hanem újraindulás-dátumot', () => {
    const rest = kert.querySelectorAll('.grest');
    assert(rest.length === 1, 'pihenő sorok: ' + rest.length);
    const h = rest[0].textContent;
    assert(/Zöldborsó/.test(h), 'nem a borsó: ' + h);
    assert(/újraindul/.test(h), 'nincs újraindulás: ' + h);
    assert(/nincs teendő/i.test(kert.textContent), 'nem írja, hogy nincs teendő');
    const tasks = T.collectTasks().filter(t => t.plant.id === 'k2');
    assert(tasks.length === 0, 'a pihenő borsónak mégis van ' + tasks.length + ' teendője');
    return h.replace(/\s+/g, ' ').trim().slice(0, 80);
  });
  dom.window.close();
}

// ================================================================
console.log('\n== Téli állapot (október vége) ==');
{
  const dom = lap('2026-10-20');
  const d = dom.window.document;
  const T = novenyek(dom, [RÉPA, BORSÓ]);
  const kert = d.getElementById('gardenContent');
  check('október 20-án a répa még szezonban, a borsó pihen', () => {
    assert(T.inSeason(RÉPA, new dom.window.Date('2026-10-20')) === true, 'répa kiesett');
    assert(T.inSeason(BORSÓ, new dom.window.Date('2026-10-20')) === false, 'borsó bent van');
    return '1 / 1';
  });
  check('november elsején minden kerti növény pihen', () => {
    const dom2 = lap('2026-11-01');
    const T2 = novenyek(dom2, [RÉPA, BORSÓ]);
    const h = dom2.window.document.getElementById('gardenContent').textContent;
    assert(/egyik/.test(h), 'nem írja, hogy egyik sincs szezonban: ' + h.slice(0, 120));
    assert(T2.collectTasks().length === 0, 'mégis van teendő');
    dom2.window.close();
    return 'mindenki pihen';
  });
  dom.window.close();
}

// ================================================================
console.log('\n== Szám-jelző a fülön ==');
{
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  const esedekes = Object.assign({}, RÉPA, { lastWatered: '2026-06-01', lastFertilized: '2026-06-01' });
  novenyek(dom, [esedekes]);
  check('a fülön megjelenik a ma esedékes kerti teendők száma', () => {
    const b = d.getElementById('gardenBadge');
    assert(b, 'nincs gardenBadge');
    assert(b.classList.contains('on'), 'nincs bekapcsolva: ' + b.className);
    const n = parseInt(b.textContent, 10);
    assert(n >= 1, 'a szám: ' + b.textContent);
    return n + ' esedékes';
  });
  check('ha minden teendő a jövőben van, nincs jelzés', () => {
    const dom2 = lap('2026-07-10');
    novenyek(dom2, [Object.assign({}, RÉPA, {
      lastWatered: '2026-07-10', lastFertilized: '2026-06-25'
    })]);
    const b = dom2.window.document.getElementById('gardenBadge');
    assert(!b.classList.contains('on'), 'mégis jelez: ' + b.textContent);
    dom2.window.close();
    return 'nincs';
  });
  dom.window.close();
}


// ================================================================
console.log('\n== „Hely: Kert” → kerti növény ==');
{
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  const T = novenyek(dom, []);

  check('a „Hely” legördülőben van Kert / Kerti ágyás / Üvegház', () => {
    const opciok = [...d.getElementById('f_room').options].map(o => o.value);
    ['Kert', 'Kerti ágyás', 'Üvegház'].forEach(v => {
      assert(opciok.indexOf(v) >= 0, 'hiányzik: ' + v);
    });
    return opciok.filter(v => /Kert|Üvegház/.test(v)).join(' · ');
  });

  check('Kert hely kiválasztásakor a kerti jelölő magától bekapcsol', () => {
    T.openDialog(null);
    const room = d.getElementById('f_room');
    d.getElementById('f_garden').checked = false;
    room.value = 'Kert';
    room.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
    assert(d.getElementById('f_garden').checked, 'nem kapcsolt be');
    return 'igen';
  });

  check('más helyre váltva kikapcsol (ha magától kapcsolt be)', () => {
    const room = d.getElementById('f_room');
    room.value = 'Nappali';
    room.dispatchEvent(new dom.window.Event('change', { bubbles: true }));
    assert(!d.getElementById('f_garden').checked, 'nem kapcsolt ki');
    return 'igen';
  });

  check('mentéskor a Kert hely önmagában is kerti növényt jelent', () => {
    T.openDialog(null);
    d.getElementById('f_name').value = 'Sárgarépa';
    d.getElementById('f_room').value = 'Kert';
    d.getElementById('f_garden').checked = false;   // kézzel kikapcsolva is
    T.saveForm();
    const p = T.state.plants[T.state.plants.length - 1];
    assert(p.garden === true, 'a garden jelölő nem került be');
    assert(p.room === 'Kert', 'a hely: ' + p.room);
    assert(T.gardenPlants().some(x => x.name === 'Sárgarépa'), 'nincs a Kert fülön');
    return p.name + ' · ' + p.room + ' · garden=' + p.garden;
  });

  check('régi adat átkerül: „Kert” helyű növény kerti növénnyé válik', () => {
    const dom2 = lap('2026-07-10');
    const T2 = novenyek(dom2, [{ id: 'o1', name: 'Régi retek', room: 'Kert', waterDays: 4 }]);
    const p = T2.state.plants[0];
    assert(p.garden === true, 'nem lett kerti');
    assert(p.seasonFrom === 4 && p.seasonTo === 10, 'szezon: ' + p.seasonFrom + '-' + p.seasonTo);
    assert(T2.gardenPlants().length === 1, 'nincs a Kert fülön');
    dom2.window.close();
    return 'garden=true, szezon 4–10';
  });

  check('„Áthelyezés a kertbe” gomb egy kattintással átteszi a szobanövényt', () => {
    const dom3 = lap('2026-07-10');
    const d3 = dom3.window.document;
    const T3 = novenyek(dom3, [SZOBA]);
    const gomb = d3.querySelector('[data-makegarden="p1"]');
    assert(gomb, 'nincs áthelyező gomb a Kert fülön');
    gomb.dispatchEvent(new dom3.window.MouseEvent('click', { bubbles: true }));
    const p = T3.state.plants[0];
    assert(p.garden === true, 'nem lett kerti');
    assert(p.room === 'Kert', 'a hely: ' + p.room);
    assert(p.fertKind === 'komposzt', 'trágya: ' + p.fertKind);
    assert(/Sárgarépa|áthelyez|Kert fülre/i.test(d3.getElementById('gardenContent').textContent) ||
           T3.gardenPlants().length === 1, 'nem frissült a fül');
    dom3.window.close();
    return 'p1 → Kert, komposzt';
  });
  dom.window.close();
}



// ================================================================
console.log('\n== Kerti növény más színnel a Növények fülön ==');
check('a Növények fülön a kerti kártya zöld (garden-card)', () => {
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  const T = novenyek(dom, [
    { id: 'g1', name: 'Sárgarépa', room: 'Kert' },
    { id: 's1', name: 'Monstera', room: 'Nappali' }
  ]);
  T.switchView('plants');
  const kartya = (nev) => [...d.querySelectorAll('#plantsContent article.card')]
    .filter(k => k.querySelector('h3').textContent.indexOf(nev) >= 0)[0];
  const kert = kartya('Sárgarépa'), szoba = kartya('Monstera');
  assert(kert, 'nincs Sárgarépa kártya');
  assert(kert.classList.contains('garden-card'), 'a kerti kártya nem zöld');
  assert(!szoba.classList.contains('garden-card'), 'a szobanövény is zöld lett');
  assert(d.querySelector('#plantsContent .chip.garden'), 'nincs „kerti növény” jelölő');
  return 'Sárgarépa = zöld · Monstera = fehér';
});

check('jelmagyarázat a kereső mellett, darabszámmal', () => {
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  novenyek(dom, [{ id: 'g1', name: 'Sárgarépa', room: 'Kert' }, { id: 's1', name: 'Monstera', room: 'Nappali' }]);
  dom.window.__T.switchView('plants');
  const jel = d.querySelector('#plantsContent .kert-legend');
  assert(jel, 'nincs jelmagyarázat');
  assert(/kerti növény/.test(jel.textContent), 'rossz szöveg: ' + jel.textContent);
  assert(/\(1\)/.test(jel.textContent), 'nincs darabszám: ' + jel.textContent);
  return jel.textContent.replace(/\s+/g, ' ').trim();
});

check('ha nincs kerti növény, nincs jelmagyarázat sem', () => {
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  novenyek(dom, [{ id: 's1', name: 'Monstera', room: 'Nappali' }]);
  dom.window.__T.switchView('plants');
  assert(!d.querySelector('#plantsContent .kert-legend'), 'fölöslegesen megjelenik');
  assert(!d.querySelector('#plantsContent .garden-card'), 'zöld kártya sincs');
  return 'tiszta szobanövény-lista';
});

check('a CSS valóban más színt ad a kerti kártyának', () => {
  const html = require('fs').readFileSync(HTML, 'utf8');
  assert(/\.card\.garden-card\{/.test(html), 'nincs .card.garden-card szabály');
  assert(/border-left:5px solid var\(--green\)/.test(html), 'nincs zöld bal szegély');
  assert(/content:'KERT'/.test(html), 'nincs KERT szalag');
  return 'zöld szegély + KERT szalag';
});

// ================================================================
//  Az adatbázis (82 faj) aszinkron töltődik be, ezért ez a szakasz vár rá.
function ZARO(){
  console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás\n');
  if (bad) {
    console.log('Hibák:');
    problems.forEach(p => console.log('  - ' + p));
    console.log('');
    process.exit(1);
  }
  process.exit(0);
}

setTimeout(function(){
  console.log('\n== Magától kerti növény (adatbázis-alapú felismerés) ==');
  const dom = lap('2026-07-10');
  const d = dom.window.document;
  setTimeout(function(){
    const T = novenyek(dom, [
      { id: 'a', name: 'Sárgarépa' },                       // csak név
      { id: 'b', name: 'Paradicsom', room: 'Nappali' },     // szobai hely, kerti faj
      { id: 'c', name: 'Monstera', room: 'Nappali' }        // igazi szobanövény
    ]);
    const kert = d.getElementById('gardenContent');

    check('a csak névből felvett kerti faj magától a Kert fülre kerül', () => {
      assert(T.isGardenPlant({ name: 'Sárgarépa' }) === true, 'nem ismerte fel');
      assert(T.gardenPlants().some(p => p.name === 'Sárgarépa'), 'nincs a fülön');
      const p = T.state.plants.filter(x => x.name === 'Sárgarépa')[0];
      assert(p.seasonFrom && p.seasonTo, 'nincs szezon');
      assert(p.sow && p.harvest, 'nincs vetés/betakarítás');
      return 'Sárgarépa · szezon ' + p.seasonFrom + '–' + p.seasonTo + ' · ' + p.harvest;
    });

    check('a szobai helyen tartott kerti faj is kerti növény', () => {
      assert(T.isGardenPlant({ name: 'Paradicsom', room: 'Nappali' }) === true, 'nem ismerte fel');
      return 'Paradicsom (Nappali) → kerti';
    });

    check('a szobanövény nem kerül a Kert fülre, de egy kattintással áttehető', () => {
      assert(T.isGardenPlant({ name: 'Monstera', room: 'Nappali' }) === false, 'mégis kerti');
      assert(d.querySelector('[data-makegarden="c"]'), 'nincs áthelyező gomb');
      return 'Monstera → áthelyezhető';
    });

    check('a fejléc megmutatja: összes növény / ebből kerti', () => {
      const h = kert.textContent.replace(/\s+/g, ' ');
      assert(/Összes növényed: 3/.test(h), 'nincs összesítő: ' + h.slice(0, 140));
      assert(/ebből kerti: 2/.test(h), 'rossz a kerti darabszám');
      return '3 növény · 2 kerti';
    });

    check('a kártyákon csak kerti növény szerepel', () => {
      const nevek = [...kert.querySelectorAll('.card h3, .grest .gnm')].map(x => x.textContent.trim());
      assert(nevek.length >= 2, 'kevés kártya: ' + nevek.length);
      assert(nevek.every(n => /Sárgarépa|Paradicsom/.test(n)), 'idegen név: ' + nevek.join(', '));
      return nevek.join(' · ');
    });

    check('adatbázisból felismert kerti faj is zöld kártyát kap', () => {
      novenyek(dom, [{ id: 'd1', name: 'Paradicsom', room: 'Nappali' }]);   // se jelölő, se kerti hely
      T.switchView('plants');
      const k = d.querySelector('#plantsContent article.card');
      assert(k, 'nincs kártya');
      assert(k.classList.contains('garden-card'), 'a Paradicsom nem kapott zöld kártyát');
      assert(/kerti növény/.test(k.textContent), 'nincs kerti jelölő');
      return 'Paradicsom (Nappali) → zöld kártya';
    });

    dom.window.close();
    setTimeout(ZARO, 40);
  }, 900);
}, 300);
