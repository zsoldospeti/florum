#!/usr/bin/env node
/* ==============================================================
   FLORUM 1.33.2  ·  teszt: dátummezők és a kiolvasott adatlap
   Fájl:  teszt-datum.js

   Két hibát őriz:

   1) „Váratlan hiba történt a felületben: Uncaught ReferenceError:
       entry is not defined (:6466)”
      → a kiolvasott adatlap („Mit találtam?”) rajzolásakor a tápoldat-
        és kerti blokk egy nem létező `entry` változóra hivatkozott.

   2) „kde ablakban a naptárválasztó felugrik és azonnal eltűnik”
      → a natív <input type="date"> felugrója nem a lap része volt.
        Most saját naptár van: a lapon belül, fix pozícióval,
        görgetésre nem csukódik be.

   Ha nincs jsdom, a teszt kihagyja magát (npm install jsdom).
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

let html = fs.readFileSync(HTML, 'utf8');
const EXPORT = `
;window.__T = { applyState: (typeof applyState!=='undefined'?applyState:null),
  render: (typeof render!=='undefined'?render:null),
  switchView: (typeof switchView!=='undefined'?switchView:null),
  openDialog: (typeof openDialog!=='undefined'?openDialog:null),
  openInfoFetched: (typeof openInfoFetched!=='undefined'?openInfoFetched:null),
  dateRefresh: (typeof dateRefresh!=='undefined'?dateRefresh:null),
  state: (typeof state!=='undefined'?state:null) };
`;
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
const big = blocks.sort((a, b) => b.length - a.length)[0];
const idx = big.lastIndexOf('})();');
html = html.replace(big, big.slice(0, idx) + EXPORT + big.slice(idx));

const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'http://127.0.0.1:8777/',
  beforeParse(win) {
    win.fetch = () => Promise.reject(new Error('offline teszt'));
    win.alert = () => {};
    win.confirm = () => true;
    win.scrollTo = () => {};
    win.matchMedia = () => ({ matches: false, addEventListener() {}, addListener() {} });
    if (win.HTMLDialogElement) {
      win.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
      win.HTMLDialogElement.prototype.close = function () { this.open = false; };
    }
  }
});
const win = dom.window;
const doc = win.document;
const T = win.__T;
const hibak = [];
win.onerror = (m) => { hibak.push(String(m)); return true; };
process.on('unhandledRejection', () => {});

setTimeout(() => {
  T.applyState({
    plants: [{ id: 'p1', name: 'Klívia', room: 'Nappali', waterDays: 7,
               lastWatered: '2026-10-20', repotMonths: 30 }],
    history: [], settings: {}, meta: {}, customDb: []
  });
  T.render();

  // ================================================================
  console.log('\n== 1. Kiolvasott adatlap (a ReferenceError helye) ==');

  check('linkről kiolvasott adatlap megnyílik hiba nélkül', () => {
    let dobott = null;
    try {
      T.openInfoFetched({
        name: 'Elefántláb', latin: 'Beaucarnea recurvata', water: 14, waterWinter: 35,
        fertKind: 'level', fertDose: '2 ml/l', fertNpk: 'N-P-K 7-3-5', fertFrom: 3, fertTo: 9,
        garden: true, seasonFrom: 4, seasonTo: 10, sow: 'április', harvest: 'október',
        light: 'Napos', forras: 'https://pelda.hu/cikk'
      });
    } catch (e) { dobott = e.message; }
    assert(!dobott, 'kivétel: ' + dobott);
    const t = doc.getElementById('infoSheet').textContent;
    assert(/Tápoldatozás/.test(t), 'nincs tápoldat-blokk');
    assert(/levélnövények tápoldata/.test(t), 'nincs tápoldat-típus: ' + t.slice(0, 200));
    assert(/2 ml\/l/.test(t), 'nincs adag');
    assert(/Kerti szezon/.test(t), 'nincs kerti szezon-blokk');
    assert(/április/.test(t), 'nincs vetés');
    return 'tápoldat + kerti szezon kirajzolva';
  });

  check('a forrás-linket is kiírja az adatlapra', () => {
    const t = doc.getElementById('infoSheet').textContent;
    assert(/pelda\.hu/.test(t), 'nincs forrás a lapon');
    return 'forrás: pelda.hu';
  });

  check('üres adatlappal sem száll el (nincs adat)', () => {
    let dobott = null;
    try { T.openInfoFetched({}); } catch (e) { dobott = e.message; }
    assert(!dobott, 'kivétel: ' + dobott);
    return 'üres bejegyzés is biztonságos';
  });

  // ================================================================
  console.log('\n== 2. Saját naptár-választó (a KDE-ablak hibája) ==');

  T.openDialog(null);
  const napok = [...doc.querySelectorAll('dialog input[type="date"]')];
  check('a natív dátummezők megvannak és rejtve vannak', () => {
    assert(napok.length >= 4, 'csak ' + napok.length + ' dátummező');
    napok.forEach(n => assert(n.classList.contains('dt-native'), 'nincs elrejtve: ' + n.id));
    return napok.length + ' mező (rejtett natív)';
  });

  const wrap = napok[0].nextSibling;
  check('minden mező mellett saját szövegmező + naptár gomb', () => {
    assert(wrap && wrap.className === 'dt', 'nincs .dt wrapper');
    assert(wrap.querySelector('.dt-input'), 'nincs szövegmező');
    assert(wrap.querySelector('.dt-btn'), 'nincs naptár gomb');
    return '.dt + .dt-input + .dt-btn';
  });

  check('a naptár a LAPON BELÜL nyílik (nem natív felugró)', () => {
    wrap.querySelector('.dt-btn').click();
    const pop = wrap.querySelector('.dt-pop');
    assert(pop, 'nincs .dt-pop');
    assert(!pop.hidden, 'nem nyílt ki');
    const css = html.match(/\.dt-pop\{[^}]*\}/);
    assert(css && /position:\s*fixed/.test(css[0]), 'nem fix pozíciójú');
    return 'nyitva · position: fixed';
  });

  check('a rács 42 napot mutat, hónap-címmel', () => {
    const pop = wrap.querySelector('.dt-pop');
    const napok2 = pop.querySelectorAll('[data-dtday]');
    assert(napok2.length === 42, 'várt 42 nap, van ' + napok2.length);
    const cim = pop.querySelector('.dt-title').textContent;
    assert(/20\d\d/.test(cim), 'nincs év a címben: ' + cim);
    return cim + ' · 42 nap';
  });

  check('görgetésre NEM csukódik be (ez volt a KDE-s tünet)', () => {
    const pop = wrap.querySelector('.dt-pop');
    const ev = new win.Event('scroll', { bubbles: true });
    Object.defineProperty(ev, 'target', { value: doc.body });
    win.dispatchEvent(ev);
    assert(!pop.hidden, 'a görgetés bezárta');
    return 'nyitva maradt';
  });

  check('napra kattintva beírja a dátumot és szól a change', () => {
    const pop = wrap.querySelector('.dt-pop');
    let valtozott = false;
    napok[0].addEventListener('change', () => { valtozott = true; });
    const cel = pop.querySelectorAll('[data-dtday]')[21];
    const iso = cel.getAttribute('data-dtday');
    cel.click();
    assert(napok[0].value === iso, 'natív érték: ' + napok[0].value + ' (várt ' + iso + ')');
    assert(valtozott, 'nem jött change esemény');
    assert(pop.hidden, 'nem záródott be');
    assert(/\./.test(wrap.querySelector('.dt-input').value), 'a szövegmező nem frissült');
    return iso + ' · change megvan';
  });

  check('„Ma” a mai napot írja be', () => {
    wrap.querySelector('.dt-btn').click();
    wrap.querySelector('[data-dtquick="ma"]').click();
    const ma = new Date();
    const iso = ma.getFullYear() + '-' + String(ma.getMonth() + 1).padStart(2, '0') + '-' +
                String(ma.getDate()).padStart(2, '0');
    assert(napok[0].value === iso, 'nem a mai nap: ' + napok[0].value);
    return iso;
  });

  check('„Törlés” üríti a mezőt', () => {
    wrap.querySelector('.dt-btn').click();
    wrap.querySelector('[data-dtquick="torol"]').click();
    assert(napok[0].value === '', 'nem ürült ki: ' + napok[0].value);
    return 'üres';
  });

  check('gépelt dátum (2026. 03. 15.) is jó', () => {
    const inp = wrap.querySelector('.dt-input');
    inp.value = '2026. 03. 15.';
    inp.dispatchEvent(new win.Event('input', { bubbles: true }));
    assert(napok[0].value === '2026-03-15', 'natív érték: ' + napok[0].value);
    return '2026-03-15';
  });

  check('hónap-léptetés működik', () => {
    wrap.querySelector('.dt-btn').click();
    const pop = wrap.querySelector('.dt-pop');
    const cim = () => pop.querySelector('.dt-title').textContent;
    const elotte = cim();
    pop.querySelector('[data-dtnav="1"]').click();
    assert(cim() !== elotte, 'nem lépett: ' + elotte);
    return elotte + ' → ' + cim();
  });

  check('Esc bezárja a naptárt', () => {
    const pop = wrap.querySelector('.dt-pop');
    doc.dispatchEvent(new win.KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    assert(pop.hidden, 'nem záródott be');
    return 'bezárva';
  });

  check('a beállítások dátumai is maguktól átalakulnak', (done) => {
    T.switchView('settings');
    // a MutationObserver kicsit később dolgozik – itt szinkron kérjük
    T.dateRefresh();
    const hol = [...doc.querySelectorAll('#setHolFrom, #setHolTo')];
    assert(hol.length === 2, 'várt 2 dátummező, van ' + hol.length);
    hol.forEach(x => assert(x.classList.contains('dt-native'), 'nem alakult át: ' + x.id));
    return '2 mező átalakítva';
  });

  // ================================================================
  console.log('\n== 3. Nincs futásidejű hiba ==');
  check('a lapon nem volt kezeletlen JS-hiba', () => {
    assert(hibak.length === 0, 'hiba: ' + hibak.join(' / '));
    return 'tiszta';
  });

  console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás\n');
  if (bad) {
    console.log('Hibák:');
    problems.forEach(p => console.log('  - ' + p));
    console.log('');
  }
  try { dom.window.close(); } catch (e) {}
  process.exit(bad ? 1 : 0);
}, 900);
