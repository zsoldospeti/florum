#!/usr/bin/env node
/* ==============================================================
   FLORUM 1.33.2  ·  teszt: Napló = többoszlopos jelentés-táblázat
   Fájl:  teszt-naplo.js

   A panasz, amit ez a teszt őriz (47/1.:
     „A napló fül még mindig mostoha. Report: Átültetés.
      Ilyenek vannak benne, és továbbra is egy oszlopot mutat.”

   Amit vizsgál:
     1. a napló TÖBB oszlopos táblázat (Dátum · Növény · Tevékenység · Részletek)
     2. nap-sávok (dátum szerint), darabszámmal
     3. felső számsor (összes / e havi / mai / érintett növény)
     4. típus-chipek: „Átültetés 1” → kattintásra szűr
     5. oszlopfejléc-rendezés (dátum / növény / tevékenység)
     6. „Részletek” oszlop: növény-beállításból származó adat
     7. CSV-letöltés (Dátum;Idő;Növény;Hely;Tevékenység;Részletek)
     8. hibás/üres napló nem töri el a fület

   Ha nincs jsdom, a teszt kihagyja magát:
     npm install jsdom
   ============================================================== */

const fs = require('fs');
const path = require('path');

const HTML = process.argv[2] || path.join(__dirname, 'florum.html');

let JSDOM = null;
for (const hol of ['jsdom', '/home/user/jsd/node_modules/jsdom', '/tmp/jsd/node_modules/jsdom',
                   path.join(__dirname, 'node_modules/jsdom')]) {
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
    bad++;
    problems.push(cim + ': ' + e.message);
    console.log('  ✗ ' + cim + '   → ' + e.message);
    return null;
  }
}
function assert(cond, msg) { if (!cond) throw new Error(msg); }

// ---- a lap betöltése, a belső függvények kiemelésével
let html = fs.readFileSync(HTML, 'utf8');
const EXPORT = `
;window.__T = { applyState: (typeof applyState!=='undefined'?applyState:null),
  render: (typeof render!=='undefined'?render:null),
  renderLog: (typeof renderLog!=='undefined'?renderLog:null),
  switchView: (typeof switchView!=='undefined'?switchView:null),
  state: (typeof state!=='undefined'?state:null),
  logDetail: (typeof logDetail!=='undefined'?logDetail:null),
  logCSV: (typeof logCSV!=='undefined'?logCSV:null) };
`;
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const big = blocks.sort((a, b) => b.length - a.length)[0];
const idx = big.lastIndexOf('})();');
html = html.replace(big, big.slice(0, idx) + EXPORT + big.slice(idx));

let csvSzoveg = null;
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'http://127.0.0.1:8777/',
  beforeParse(win) {
    win.fetch = () => Promise.reject(new Error('offline teszt'));
    win.alert = () => {};
    win.confirm = () => true;
    win.prompt = () => null;
    if (win.HTMLDialogElement && !win.HTMLDialogElement.prototype.showModal) {
      win.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
      win.HTMLDialogElement.prototype.close = function () { this.open = false; };
    }
    win.scrollTo = () => {};
    win.matchMedia = () => ({ matches: false, addEventListener() {}, addListener() {} });

    // a CSV-t ne fájlba írjuk, csak fogjuk el a tartalmát
    const EredetiBlob = win.Blob;
    win.Blob = function (parts, o) {
      try { csvSzoveg = String((parts || []).join('')); } catch (e) {}
      return new EredetiBlob(parts, o);
    };
    win.URL.createObjectURL = () => 'blob:teszt';
    win.URL.revokeObjectURL = () => {};
  }
});
const win = dom.window;
const doc = win.document;
const T = win.__T;
process.on('unhandledRejection', () => {});

const P1 = { id: 'p1', name: 'Klívia', room: 'Nappali', waterDays: 7, fertDays: 14, repotMonths: 30, pot: 18,
             fertKind: 'tapoldat', fertDose: '2 ml/l', fertFrom: 3, fertTo: 9 };
const P2 = { id: 'p2', name: 'Fikusz', room: 'Dolgozó', waterDays: 10, mistWater: 'csap', repotMonths: 24 };

const NAPLÓ = [
  { id: 'h1', plantId: 'p1', plantName: 'Klívia', type: 'repotting', date: '2026-10-22', ts: 1761150000000 },
  { id: 'h2', plantId: 'p1', plantName: 'Klívia', type: 'watering', date: '2026-10-22', ts: 1761153600000 },
  { id: 'h3', plantId: 'p2', plantName: 'Fikusz', type: 'misting', date: '2026-10-20' },
  { id: 'h4', plantId: 'p2', plantName: 'Fikusz', type: 'fertilizing', date: '2026-10-18', skipped: true },
  { id: 'h5', plantId: 'p1', plantName: 'Klívia', type: 'watering', date: '2026-09-01' }
];

function betolt(hist) {
  T.applyState({ plants: [P1, P2], history: hist, settings: {}, meta: {}, customDb: [] });
  T.render();
  T.switchView('log');
}

// ================================================================
console.log('\n== A napló többoszlopos táblázat ==');
betolt(NAPLÓ);

check('a napló TÁBLÁZAT, legalább 4 hasznos oszloppal', () => {
  const th = [...doc.querySelectorAll('#logContent table.log-table thead th')]
    .map(x => x.textContent.replace(/[↕▲▼]/g, '').trim()).filter(Boolean);
  assert(th.length >= 4, 'csak ' + th.length + ' oszlop: ' + th.join(' | '));
  for (const kell of ['Dátum', 'Növény', 'Tevékenység', 'Részletek']) {
    assert(th.indexOf(kell) >= 0, 'hiányzik az oszlop: ' + kell + ' (' + th.join(' | ') + ')');
  }
  return th.join(' | ');
});

check('minden bejegyzés egy sorban, nap-sávokkal', () => {
  const sorok = doc.querySelectorAll('#logContent table.log-table tr.log-item');
  assert(sorok.length === 5, 'várt 5 sor, van ' + sorok.length);
  const savok = doc.querySelectorAll('#logContent table.log-table tr.log-dayrow');
  assert(savok.length === 4, 'várt 4 nap-sáv, van ' + savok.length);
  return sorok.length + ' sor · ' + savok.length + ' nap-sáv';
});

check('a nap-sáv kiírja a darabszámot', () => {
  const t = doc.querySelector('#logContent .log-dayrow').textContent;
  assert(/bejegyzés/.test(t), 'nincs darabszám: ' + t);
  return t.replace(/\s+/g, ' ').trim();
});

check('az „Átültetés” sora megvan, és látszik a típus neve', () => {
  const sor = [...doc.querySelectorAll('#logContent tr.log-item')]
    .filter(r => /Átültetés/.test(r.textContent))[0];
  assert(sor, 'nincs Átültetés sor');
  const cellak = [...sor.children].map(c => c.textContent.replace(/\s+/g, ' ').trim());
  assert(/Klívia/.test(cellak[1]), 'a növény oszlop nem Klívia: ' + cellak[1]);
  assert(cellak[2].indexOf('Átültetés') === 0, 'a tevékenység oszlop: ' + cellak[2]);
  return cellak.slice(0, 4).join(' ‖ ');
});

check('a „Részletek” oszlop a növény beállításaiból dolgozik', () => {
  const reszletek = [...doc.querySelectorAll('#logContent tr.log-item')]
    .map(r => r.children[3].textContent.trim());
  assert(reszletek.some(x => /havonta/.test(x)), 'nincs átültetés-adat a részletekben');
  assert(reszletek.some(x => /tápoldat/i.test(x)), 'nincs tápoldat-adat a részletekben');
  assert(reszletek.some(x => /permetezés/i.test(x)), 'nincs permetezés-adat a részletekben');
  return reszletek.filter(Boolean).slice(0, 3).join(' / ');
});

check('a kihagyott bejegyzés jelölve van', () => {
  const t = doc.querySelector('#logContent table.log-table').textContent;
  assert(/kihagyva/i.test(t), 'nincs „kihagyva” jelzés');
  return 'kihagyva jelzés megvan';
});

// ================================================================
console.log('\n== Számsor + típus-chipek ==');
check('4 szám a napló tetején', () => {
  const statok = [...doc.querySelectorAll('#logContent .log-stat')];
  assert(statok.length === 4, 'várt 4 stat-kártya, van ' + statok.length);
  return statok.map(x => x.textContent.replace(/\s+/g, ' ').trim()).join(' / ');
});
check('típus-chipek darabszámmal (Öntözés 2, Átültetés 1)', () => {
  const chipek = [...doc.querySelectorAll('#logContent .log-chip')].map(x => x.textContent.replace(/\s+/g, ' ').trim());
  assert(chipek.some(c => /Öntözés\s*2/.test(c)), 'nincs Öntözés 2: ' + chipek.join(' / '));
  assert(chipek.some(c => /Átültetés\s*1/.test(c)), 'nincs Átültetés 1: ' + chipek.join(' / '));
  return chipek.join(' / ');
});
check('chipre kattintva csak az a típus marad', () => {
  doc.querySelector('#logContent [data-logtype="repotting"]').click();
  const sorok = doc.querySelectorAll('#logContent tr.log-item');
  assert(sorok.length === 1, 'várt 1 sor, van ' + sorok.length);
  assert(/Átültetés/.test(sorok[0].textContent), 'nem az átültetés maradt');
  return '1 sor: Átültetés';
});
check('a chip újra „mindent” mutat', () => {
  doc.querySelector('#logContent [data-logtype="all"]').click();
  const sorok = doc.querySelectorAll('#logContent tr.log-item');
  assert(sorok.length === 5, 'várt 5 sor, van ' + sorok.length);
  return '5 sor vissza';
});

// ================================================================
console.log('\n== Oszlopfejléc-rendezés ==');
check('a dátum-fejlécre kattintva megfordul a sorrend', () => {
  const elotte = doc.querySelectorAll('#logContent tr.log-item').length;
  doc.querySelector('#logContent [data-logsort="date"]').click();
  assert(T.state.ui.logDir === 1, 'nem váltott irányt: ' + T.state.ui.logDir);
  const sorok = doc.querySelectorAll('#logContent tr.log-item');
  assert(sorok.length === elotte, 'a sorok száma megváltozott');
  return 'irány: ' + (T.state.ui.logDir === 1 ? 'növekvő' : 'csökkenő') + ' · ' + sorok.length + ' sor';
});
check('növény szerint rendezve ABC-sorrend', () => {
  doc.querySelector('#logContent [data-logsort="plant"]').click();
  const nevek = [...doc.querySelectorAll('#logContent tr.log-item .log-plant')]
    .map(x => x.textContent.replace(/Nappali|Dolgozó/, '').trim());
  assert(nevek.length === 5, 'várt 5 sor, van ' + nevek.length);
  for (let i = 1; i < nevek.length; i++) {
    assert(nevek[i - 1].toLowerCase() <= nevek[i].toLowerCase(), 'nem ABC: ' + nevek.join(' > '));
  }
  return nevek.join(' > ');
});
check('vissza dátum szerintre: újra vannak nap-sávok', () => {
  const d = T.state.ui;
  d.logSort = 'date'; d.logDir = -1;
  T.renderLog();
  const savok = doc.querySelectorAll('#logContent .log-dayrow').length;
  assert(savok === 4, 'várt 4 nap-sáv, van ' + savok);
  return savok + ' nap-sáv';
});

// ================================================================
console.log('\n== CSV-letöltés ==');
check('a „Napló letöltése” gomb CSV-t ad, fejléccel', () => {
  csvSzoveg = null;
  doc.querySelector('#logContent [data-logcsv]').click();
  assert(csvSzoveg, 'nem készült CSV');
  const sorok = csvSzoveg.replace(/^\ufeff/, '').split('\r\n');
  assert(/Dátum/.test(sorok[0]) && /Növény/.test(sorok[0]) && /Tevékenység/.test(sorok[0]),
    'rossz fejléc: ' + sorok[0]);
  assert(sorok.filter(Boolean).length === 6, 'várt fejléc + 5 sor, van ' + sorok.filter(Boolean).length);
  return sorok[0].replace(/"/g, '') + ' · ' + (sorok.filter(Boolean).length - 1) + ' sor';
});
check('a CSV-ben ott van az átültetés és a hely is', () => {
  assert(/Átültetés/.test(csvSzegmens()), 'nincs Átültetés a CSV-ben');
  assert(/Nappali/.test(csvSzegmens()), 'nincs hely (Nappali) a CSV-ben');
  return 'Átültetés + Nappali a CSV-ben';
});
function csvSzegmens() { return String(csvSzoveg || ''); }

// ================================================================
console.log('\n== Hibatűrés ==');
check('selejt bejegyzés nem töri el a táblázatot', () => {
  betolt([null, 'hibás', { id: 'x1', plantId: 'p1', type: 'watering', date: '2026-10-22' }]);
  const sorok = doc.querySelectorAll('#logContent tr.log-item');
  assert(sorok.length === 1, 'várt 1 sor, van ' + sorok.length);
  assert(doc.querySelector('#logContent table.log-table'), 'nincs táblázat');
  return '1 érvényes sor, táblázat áll';
});
check('dátum nélküli bejegyzés a „Dátum nélküli” sávba kerül', () => {
  betolt([{ id: 'y1', plantId: 'p1', plantName: 'Klívia', type: 'watering' }]);
  const t = doc.querySelector('#logContent').textContent;
  assert(/Dátum nélküli/.test(t), 'nincs jelölés: ' + t.replace(/\s+/g, ' ').slice(0, 90));
  return 'Dátum nélküli bejegyzés';
});
check('üres napló: „Még nincs bejegyzés”, nem üres táblázat', () => {
  betolt([]);
  const t = doc.querySelector('#logContent').textContent;
  assert(/Még nincs bejegyzés/.test(t), 'nem az üres állapot látszik');
  assert(!doc.querySelector('#logContent table.log-table'), 'üres táblázatot rajzolt');
  return 'üres állapot';
});

// ================================================================
console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás\n');
if (bad) {
  console.log('Hibák:');
  problems.forEach(p => console.log('  - ' + p));
  console.log('');
  process.exit(1);
}
process.exit(0);
