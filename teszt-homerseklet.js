#!/usr/bin/env node
/* ==============================================================
   FLORUM 1.33.2  ·  teszt: HŐMÉRSÉKLET SZERINTI ÖNTÖZÉS
   Fájl:  teszt-homerseklet.js

   A felvetés, amit ez a teszt lefed:
     „Hőmérséklet nem számít? Nyáron 28–30 °C, télen 19–23 °C.”

   Amit vizsgál:
     1. kikapcsolva minden a régi naptár szerint megy (semmi nem tört el)
     2. a hőmérséklet-szorzó iránya: meleg → rövidebb, hűvös → hosszabb időköz
     3. a határok (nem megy 0,70 alá / 1,40 fölé)
     4. a növény saját hőmérséklet-sávja számít (kaktusz vs. trópusi)
     5. a téli szünet sérthetetlen (a hőmérséklet nem kapcsolhatja vissza)
     6. a tápoldatozást NEM skálázza (azt a szezon vezérli)
     7. a kertben szezonon kívül nincs teendő
     8. a felület: kapcsoló, 12 havi mező, gyorsgombok, magyarázat
     9. a teendő-sor és a növénykártya mutatja az eltérést
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
    bad++; problems.push(cim + ': ' + e.message);
    console.log('  ✗ ' + cim + '   → ' + e.message);
    return null;
  }
}
function assert(c, m) { if (!c) throw new Error(m); }
function kozel(a, b, t) { return Math.abs(a - b) <= (t === undefined ? 0.005 : t); }

let html = fs.readFileSync(HTML, 'utf8');
const EXPORT = `
;window.__T = {
  applyState:(typeof applyState!=='undefined'?applyState:null),
  render:(typeof render!=='undefined'?render:null),
  switchView:(typeof switchView!=='undefined'?switchView:null),
  state:(typeof state!=='undefined'?state:null),
  intervalFor:(typeof intervalFor!=='undefined'?intervalFor:null),
  intervalAtDate:(typeof intervalAtDate!=='undefined'?intervalAtDate:null),
  homIndex:(typeof homIndex!=='undefined'?homIndex:null),
  homIndoklas:(typeof homIndoklas!=='undefined'?homIndoklas:null),
  tempSet:(typeof tempSet!=='undefined'?tempSet:null),
  tempAktiv:(typeof tempAktiv!=='undefined'?tempAktiv:null),
  collectTasks:(typeof collectTasks!=='undefined'?collectTasks:null),
  TASK_DEFS:(typeof TASK_DEFS!=='undefined'?TASK_DEFS:null)
};
`;
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const big = blocks.sort((a, b) => b.length - a.length)[0];
const idx = big.lastIndexOf('})();');
html = html.replace(big, big.slice(0, idx) + EXPORT + big.slice(idx));

const dom = new JSDOM(html, {
  runScripts: 'dangerously', pretendToBeVisual: true, url: 'http://127.0.0.1:8777/',
  beforeParse(win) {
    win.fetch = () => Promise.reject(new Error('offline teszt'));
    win.alert = () => {}; win.confirm = () => true;
    win.scrollTo = () => {};
    win.matchMedia = () => ({ matches: false, addEventListener() {}, addListener() {} });
    if (win.HTMLDialogElement) {
      win.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
      win.HTMLDialogElement.prototype.close = function () { this.open = false; };
    }
  }
});
const win = dom.window, doc = win.document, T = win.__T;
const hibak = [];
win.onerror = (m) => { hibak.push(String(m)); return true; };

const nyar = { 1:21, 2:21, 3:22, 4:23, 5:25, 6:27, 7:28, 8:28, 9:26, 10:23, 11:22, 12:21 };
function noveny(extra) {
  return Object.assign({
    id: 'p1', name: 'Klívia', room: 'Nappali',
    waterDays: 7, waterWinter: 12, lastWatered: '2026-10-20', winterSlowdown: true
  }, extra || {});
}

setTimeout(() => {
  const defOntoz = T.TASK_DEFS.find(d => d.key === 'watering');
  const defTap = T.TASK_DEFS.find(d => d.key === 'fertilizing');

  T.applyState({ plants: [noveny()], history: [], settings: {}, meta: {}, customDb: [] });
  T.render();

  // ================================================================
  console.log('\n== 1. Kikapcsolva minden a régi (naptári) módon ==');
  check('hőmérséklet nélkül 12 nap (október = téli időszak)', () => {
    assert(!T.tempAktiv(), 'váratlanul be van kapcsolva');
    const iv = T.intervalFor(noveny(), defOntoz);
    assert(iv === 12, 'időköz: ' + iv + ' (várt 12)');
    return iv + ' nap';
  });
  check('a szorzó kikapcsolva pontosan 1', () => {
    assert(T.homIndex(noveny(), 7) === 1, 'nem 1');
    return '×1';
  });
  check('magyarázat sincs kikapcsolva', () => {
    assert(T.homIndoklas(noveny()) === '', 'van magyarázat');
    return 'nincs magyarázat';
  });

  // ================================================================
  console.log('\n== 2. Bekapcsolva: meleg → sűrűbb, hűvös → ritkább ==');
  T.state.settings.temp = { tied: true, months: Object.assign({}, nyar), ideal: [15, 27] };
  check('bekapcsolva aktív', () => {
    assert(T.tempAktiv(), 'nem aktív');
    return 'aktív';
  });
  check('nyár 28 °C → rövidebb időköz (×0,70, a határon)', () => {
    const i = T.homIndex(noveny(), 7);
    assert(kozel(i, 0.70), 'szorzó: ' + i);
    const iv = T.intervalAtDate(noveny(), defOntoz, '2026-07-15');
    assert(iv === 5, 'nyári időköz: ' + iv + ' (7 × 0,70 = 4,9 → 5)');
    return '×0,70 · 5 nap';
  });
  check('tél 21 °C → a megszokott 12 nap (×1,00–1,03)', () => {
    const i = T.homIndex(noveny(), 1);
    assert(i >= 0.99 && i <= 1.06, 'szorzó: ' + i);
    assert(T.intervalAtDate(noveny(), defOntoz, '2026-01-15') === 12, 'nem 12 nap');
    return '×' + String(i).replace('.', ',') + ' · 12 nap';
  });
  check('hűvös szoba (16 °C) → hosszabb időköz', () => {
    const ment = T.state.settings.temp.months[1];
    T.state.settings.temp.months[1] = 16;
    const i = T.homIndex(noveny(), 1);
    const iv = T.intervalAtDate(noveny(), defOntoz, '2026-01-15');
    T.state.settings.temp.months[1] = ment;
    assert(i > 1.1, 'szorzó: ' + i);
    assert(iv > 12, 'időköz: ' + iv);
    return '×' + String(i).replace('.', ',') + ' · ' + iv + ' nap';
  });
  check('a meleg soha nem megy 0,70 alá, a hűvös 1,40 fölé', () => {
    T.state.settings.temp.months[7] = 45;
    const forro = T.homIndex(noveny(), 7);
    T.state.settings.temp.months[7] = 5;
    const hideg = T.homIndex(noveny(), 7);
    T.state.settings.temp.months[7] = 28;
    assert(forro >= 0.70 - 0.001, 'túl alacsony: ' + forro);
    assert(hideg <= 1.40 + 0.001, 'túl magas: ' + hideg);
    return '45 °C → ×' + forro + ' · 5 °C → ×' + hideg;
  });

  // ================================================================
  console.log('\n== 3. A növény saját hőmérséklet-sávja számít ==');
  check('a meleget kedvelő kaktuszt kevésbé sűríti, mint a trópusit', () => {
    // 28 °C a kaktusznak (18–30) közel ideális, a trópusinak (18–27) meleg.
    // A szorzó mindkettőnél <1, de a kaktusznál kisebb mértékben.
    const kaktusz = noveny({ id: 'p2', name: 'Kaktusz', tempRange: '18–30', waterDays: 14 });
    const trop = noveny({ id: 'p3', name: 'Monstera', tempRange: '18–27' });
    const ik = T.homIndex(kaktusz, 7), it = T.homIndex(trop, 7);
    assert(ik < 1 && it < 1, 'nem sűrít: kaktusz ' + ik + ', trópusi ' + it);
    assert((1 - ik) < (1 - it), 'a kaktuszt jobban sűríti, mint a trópusit: ' + ik + ' vs ' + it);
    return 'kaktusz ×' + ik + ' · trópusi ×' + it;
  });
  check('trópusi (18–27 °C) 28 °C-on sűríti', () => {
    const trop = noveny({ id: 'p3', name: 'Monstera', tempRange: '18–27' });
    const i = T.homIndex(trop, 7);
    assert(i < 0.95, 'szorzó: ' + i);
    return '×' + String(i).replace('.', ',');
  });
  check('a sáv a szövegből is kiolvasható („18–27 °C”)', () => {
    const i = T.homIndex(noveny({ tempRange: '18–27 °C' }), 7);
    assert(i < 0.95, 'nem olvasta ki: ' + i);
    return '×' + String(i).replace('.', ',');
  });
  check('sáv nélkül 15–27 °C az alap', () => {
    T.state.settings.temp.months[7] = 21;
    const a = T.homIndex(noveny({ tempRange: '' }), 7);
    assert(kozel(a, 1, 0.03), 'szorzó: ' + a);
    T.state.settings.temp.months[7] = 28;
    return '×' + String(a).replace('.', ',');
  });

  // ================================================================
  console.log('\n== 4. A téli szünet és a tápoldat sérthetetlen ==');
  check('tél + téli szünet → a téli érték, nem a nyári', () => {
    // januárra kérdezzük (a téli időszak), nem a mai napra
    T.state.settings.temp.months[1] = 21;
    const iv = T.intervalAtDate(noveny(), defOntoz, '2026-01-10');
    assert(iv === 12, 'időköz: ' + iv + ' (a téli 12 nap kell)');
    const nyarIv = T.intervalAtDate(noveny(), defOntoz, '2026-07-10');
    assert(nyarIv < iv, 'a nyári nem sűrűbb: ' + nyarIv);
    return 'január ' + iv + ' nap · július ' + nyarIv + ' nap';
  });
  check('a tápoldatozást a hőmérséklet NEM skálázza', () => {
    const p = noveny({ fertDays: 30 });
    T.state.settings.temp.months[3] = 28;
    const a = T.intervalAtDate(p, defTap, '2026-03-10');
    T.state.settings.temp.months[3] = 10;
    const b = T.intervalAtDate(p, defTap, '2026-03-10');
    T.state.settings.temp.months[3] = 22;
    assert(a === b, 'megváltozott: ' + a + ' vs ' + b);
    return 'mindkettő ' + a + ' nap';
  });
  check('télen a pihenő növény tápoldata továbbra is 0', () => {
    const p = noveny({ fertDays: 30, fertWinter: 0 });
    assert(T.intervalFor(p, defTap) === 0, 'nem 0');
    return '0 (téli tilalom)';
  });
  check('kerti növénynél szezonon kívül nincs öntözés', () => {
    const kerti = noveny({ id: 'p9', name: 'Paradicsom', garden: true, seasonFrom: 4, seasonTo: 10, waterDays: 3 });
    assert(T.intervalAtDate(kerti, defOntoz, '2026-01-20') === 0, 'télen van időköz');
    assert(T.intervalAtDate(kerti, defOntoz, '2026-07-20') > 0, 'nyáron nincs időköz');
    return 'télen 0 · nyáron ' + T.intervalAtDate(kerti, defOntoz, '2026-07-20') + ' nap';
  });

  // ================================================================
  console.log('\n== 5. A felület ==');
  T.switchView('settings');
  setTimeout(() => {
    check('van kapcsoló és 12 havi mező', () => {
      const tied = doc.getElementById('setTempTied');
      const grid = doc.getElementById('setTempGrid');
      assert(tied, 'nincs kapcsoló');
      assert(grid, 'nincs rács');
      const mezok = grid.querySelectorAll('input[data-tempm]');
      assert(mezok.length === 12, 'mezők: ' + mezok.length);
      assert(tied.checked, 'a kapcsoló nem bekapcsolt állapotú');
      return '12 hónap';
    });
    check('a magyarázat kiírja a nyári és téli szorzót', () => {
      const t = doc.getElementById('setTempErtelmezes').textContent;
      assert(/Nyár:/.test(t) && /Tél:/.test(t), 'hiányos: ' + t);
      assert(/×0[.,]70/.test(t), 'nincs benne a nyári szorzó: ' + t);
      return t.slice(0, 80) + '…';
    });
    check('a havi mezők a beállított értékeket mutatják', () => {
      const júl = doc.querySelector('#setTempGrid input[data-tempm="7"]');
      assert(String(júl.value).indexOf('28') === 0, 'július: ' + júl.value);
      return 'július: ' + júliusErtek(júl.value);
    });
    function júliusErtek(v) { return v + ' °C'; }
    check('gyorsgomb: téli átlag 21 °C', () => {
      const b = doc.querySelector('[data-tempquick="tel"]');
      assert(b, 'nincs gyorsgomb');
      b.click();
      return 'kattintva';
    });
    check('a gyorsgomb után december 21 °C', () => {
      const m = T.state.settings.temp.months;
      assert(Number(m[12]) === 21 && Number(m[1]) === 21, 'december: ' + m[12] + ', január: ' + m[1]);
      return 'dec 21 · jan 21 °C';
    });
    check('a beállítás megmarad (mentődik)', () => {
      const t = T.tempSet();
      assert(t.tied === true, 'a kapcsoló elveszett');
      assert(Object.keys(t.months).length === 12, 'nem 12 hónap');
      return '12 hónap, bekapcsolva';
    });

    // a teendő-sor és a kártya jelzése
    T.state.settings.temp.months[10] = 30;   // októberre meleg szoba
    T.render();
    check('a teendő-sorban megjelenik a meleg szoba jelzése', () => {
      const sor = doc.querySelector('.task .chip.hom');
      assert(sor, 'nincs jelzés a teendő-sorban');
      assert(/meleg szoba|hűvös szoba/.test(sor.textContent), 'ismeretlen szöveg: ' + sor.textContent);
      return sor.textContent.trim();
    });
    check('a növénykártyán is látszik a szorzó', () => {
      T.switchView('plants');
      const chip = doc.querySelector('.card .chip.hom');
      assert(chip, 'nincs jelzés a kártyán');
      return chip.textContent.trim();
    });
    check('a jelzés magyarázata is oda van írva (title)', () => {
      const chip = doc.querySelector('.chip.hom');
      const title = chip.getAttribute('title') || '';
      assert(/°C/.test(title) && /öntözés|szárad/.test(title), 'gyenge magyarázat: ' + title);
      return title.slice(0, 90) + '…';
    });

    console.log('\n== 6. Nincs futásidejű hiba ==');
    check('a lapon nem volt kezeletlen JS-hiba', () => {
      assert(hibak.length === 0, 'hiba: ' + hibak.join(' / '));
      return 'tiszta';
    });

    console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás\n');
    if (bad) { console.log('Hibák:'); problems.forEach(p => console.log('  - ' + p)); console.log(''); }
    try { dom.window.close(); } catch (e) {}
    process.exit(bad ? 1 : 0);
  }, 300);
}, 900);
