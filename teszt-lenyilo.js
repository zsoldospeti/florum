#!/usr/bin/env node
/* ==============================================================
   FLORUM 1.33.2  ·  teszt: Napló fül + saját lenyílók
   Fájl:  teszt-lenyilo.js

   Valódi DOM-motorral (jsdom) nyitja meg a florum.html-t, és
   végigkattintja, amit a felhasználó tenne:

     · átvált a Napló fülre        → látszik-e a tartalom
     · kinyit egy lenyílót         → megjelenik-e a lista
     · választ egy növényt         → szűr-e a napló
     · törli a szűrőket            → minden visszajön-e
     · dátum nélküli bejegyzés     → nem száll-e el a fül

   Ha nincs jsdom, a teszt kihagyja magát (nem hiba):
     npm install jsdom      (a florum mappában vagy bárhol)
   ============================================================== */

const fs = require('fs');
const path = require('path');

const HTML = process.argv[2] || path.join(__dirname, 'florum.html');

// ---- jsdom megkeresése
let JSDOM = null;
for (const hol of ['jsdom', '/home/user/jsd/node_modules/jsdom', '/tmp/jsd/node_modules/jsdom', path.join(__dirname, 'node_modules/jsdom')]) {
  try { JSDOM = require(hol).JSDOM; break; } catch (e) {}
}
if (!JSDOM) {
  console.log('\n  jsdom nincs telepítve – a teszt kihagyva.');
  console.log('  Telepítés:  npm install jsdom\n');
  process.exit(0);
}

let ok = 0, bad = 0;
const problems = [];
function check(cim, fn) {
  try {
    const r = fn();
    ok++;
    console.log('  ✓ ' + cim + (r ? '   → ' + String(r).slice(0, 120) : ''));
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
  renderSettings: (typeof renderSettings!=='undefined'?renderSettings:null),
  switchView: (typeof switchView!=='undefined'?switchView:null),
  fselRefresh: (typeof fselRefresh!=='undefined'?fselRefresh:null),
  logDiagnozis: (typeof logDiagnozis!=='undefined'?logDiagnozis:null),
  openDialog: (typeof openDialog!=='undefined'?openDialog:null),
  fillSelects: (typeof fillSelects!=='undefined'?fillSelects:null),
  checkVersion: (typeof checkVersion!=='undefined'?checkVersion:null),
  FILE_VERSION: (typeof FILE_VERSION!=='undefined'?FILE_VERSION:null),
  state: (typeof state!=='undefined'?state:null),
  store: (typeof store!=='undefined'?store:null) };
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
    win.prompt = () => null;
    if (win.HTMLDialogElement && !win.HTMLDialogElement.prototype.showModal) {
      win.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
      win.HTMLDialogElement.prototype.close = function () { this.open = false; };
    }
    win.scrollTo = () => {};
    win.matchMedia = () => ({ matches: false, addEventListener() {}, addListener() {} });
  }
});
const win = dom.window;
const doc = win.document;
const T = win.__T;

const P1 = { id: 'p1', name: 'Klívia', species: 'Clivia miniata', room: 'Nappali', light: 'Világos, szórt',
  waterDays: 7, waterWinter: 21, fertDays: 14, mistDays: 0, repotMonths: 30,
  lastWatered: '2026-10-20', lastFertilized: '2026-10-20', lastRepotted: '2026-08-01' };
const P2 = { id: 'p2', name: 'Fikusz', species: 'Ficus elastica', room: 'Dolgozó', light: 'Világos, szórt',
  waterDays: 10, waterWinter: 21, fertDays: 30, mistDays: 7, repotMonths: 24,
  lastWatered: '2026-10-22', lastFertilized: '2026-10-01', lastRepotted: '2026-05-01' };

function betolt(hist) {
  T.applyState({ plants: [P1, P2], history: hist, settings: { winterMode: 'auto' }, meta: {}, customDb: [] });
  T.render();
}

// ================================================================
console.log('\n== A lap betöltődött? ==');
if (!T || !T.render) {
  console.log('  ✗ az app nem indult el jsdom-ban');
  process.exit(1);
}
check('az app elindult, a belső függvények elérhetők', () => 'ok');

// ================================================================
console.log('\n== Napló fül: üres és teli állapot ==');
betolt([]);
check('nincs bejegyzés → „Még nincs bejegyzés”', () => {
  T.switchView('log');
  const t = doc.getElementById('logContent').textContent;
  assert(/Még nincs bejegyzés/.test(t), 'nem az üres állapot látszik: ' + t.slice(0, 80));
  return 'üres állapot';
});

betolt([
  { id: 'h1', plantId: 'p1', plantName: 'Klívia', type: 'watering', date: '2026-10-22', ts: 1761100000000 },
  { id: 'h2', plantId: 'p2', plantName: 'Fikusz', type: 'fertilizing', date: '2026-10-20', ts: 1761000000000 },
  { id: 'h3', plantId: 'p1', plantName: 'Klívia', type: 'watering', date: '2026-10-18' } // ts NÉLKÜL!
]);
check('3 bejegyzés megjelenik (köztük dátum nélküli időbélyeggel)', () => {
  T.switchView('log');
  const sok = doc.querySelectorAll('#logContent .log-item').length;
  assert(sok === 3, 'várt 3 bejegyzés, van ' + sok);
  return sok + ' bejegyzés';
});
check('a fül a napló-tartalmat mutatja, nem üres', () => {
  const h = doc.getElementById('logContent').innerHTML;
  assert(h.length > 500, 'túl rövid a tartalom');
  assert(doc.getElementById('view-log').classList.contains('active'), 'a nézet nem aktív');
  return h.length + ' karakter';
});

// ================================================================
console.log('\n== Lenyílók (a natív <select> helyett) ==');
function fselWrap(selId) {
  const sel = doc.getElementById(selId);
  assert(sel, 'nincs ilyen select: ' + selId);
  const w = sel.nextElementSibling;
  assert(w && w.classList.contains('fsel'), 'nincs lenyíló a ' + selId + ' mellett');
  return { sel, w };
}
check('a Napló szűrői lenyílóvá alakultak', () => {
  T.fselRefresh();
  const a = fselWrap('logPlant'), b = fselWrap('logType');
  assert(a.sel.classList.contains('fsel-native'), 'a natív select nincs elrejtve');
  return 'logPlant + logType';
});
check('a gomb a kiválasztott értéket mutatja', () => {
  const { w } = fselWrap('logPlant');
  const lab = w.querySelector('.fsel-label').textContent;
  assert(lab === 'Minden növény', 'várt „Minden növény”, van: ' + lab);
  return lab;
});
check('kattintásra kinyílik a lista', () => {
  const { w } = fselWrap('logPlant');
  w.querySelector('.fsel-btn').click();
  assert(w.classList.contains('open'), 'nem nyílt ki');
  assert(w.querySelector('.fsel-pop').hidden === false, 'a lista rejtve maradt');
  const n = w.querySelectorAll('.fsel-opt').length;
  assert(n === 3, 'várt 3 opció (mind + 2 növény), van ' + n);
  return n + ' opció';
});
check('a lista tartalmazza mindkét növényt', () => {
  const { w } = fselWrap('logPlant');
  const t = w.querySelector('.fsel-pop').textContent;
  assert(t.includes('Klívia') && t.includes('Fikusz'), 'hiányzik valamelyik növény');
  return 'Klívia, Fikusz';
});
check('választásra szűr a napló', () => {
  const { w, sel } = fselWrap('logPlant');
  const opt = [...w.querySelectorAll('.fsel-opt')].find(o => o.textContent.trim() === 'Klívia');
  assert(opt, 'nincs Klívia-opció');
  opt.click();
  assert(sel.value === 'p1', 'a select értéke nem p1: ' + sel.value);
  assert(T.state.ui.logPlant === 'p1', 'a szűrő nem állt be');
  const sok = doc.querySelectorAll('#logContent .log-item').length;
  assert(sok === 2, 'várt 2 klívia-bejegyzés, van ' + sok);
  return '2 bejegyzés (Klívia)';
});
check('a lista választás után bezárul', () => {
  const { w } = fselWrap('logPlant');
  assert(!w.classList.contains('open'), 'nyitva maradt');
  return 'bezárult';
});
check('a gomb felirata az új értékre vált', () => {
  const { w } = fselWrap('logPlant');
  const lab = w.querySelector('.fsel-label').textContent;
  assert(lab === 'Klívia', 'várt „Klívia”, van: ' + lab);
  return lab;
});
check('a típus-szűrő is működik', () => {
  const { w, sel } = fselWrap('logType');
  w.querySelector('.fsel-btn').click();
  const opt = [...w.querySelectorAll('.fsel-opt')].find(o => /Öntözés/.test(o.textContent));
  assert(opt, 'nincs Öntözés-opció');
  opt.click();
  assert(sel.value === 'watering', 'a típus nem watering: ' + sel.value);
  return 'öntözés-szűrő beállítva';
});
check('„Szűrők törlése” gomb látszik és működik', () => {
  const g = doc.querySelector('#logContent [data-logclear]');
  assert(g, 'nincs Szűrők törlése gomb');
  g.click();
  assert(T.state.ui.logPlant === 'all' && T.state.ui.logType === 'all', 'a szűrők nem törlődtek');
  const sok = doc.querySelectorAll('#logContent .log-item').length;
  assert(sok === 3, 'várt 3 bejegyzés, van ' + sok);
  return 'visszaállt mind a 3 bejegyzésre';
});

// ================================================================
console.log('\n== Hibatűrés (a régi hiba: „Invalid time value”) ==');
check('dátum és időbélyeg nélküli bejegyzés nem töri el a fület', () => {
  betolt([{ id: 'x1', plantId: 'p1', plantName: 'Klívia', type: 'watering' }]);
  T.switchView('log');
  const t = doc.getElementById('logContent').textContent;
  assert(/Dátum nélküli/.test(t), 'nem jelzi a dátum nélküli bejegyzést');
  return 'megjelenik, nem száll el';
});
check('selejt bejegyzés (null / szöveg) kihagyható', () => {
  betolt([null, 'hibás', { id: 'x2', plantId: 'p1', plantName: 'Klívia', type: 'watering', date: '2026-10-22' }]);
  T.renderLog();
  const sok = doc.querySelectorAll('#logContent .log-item').length;
  assert(sok === 1, 'várt 1 érvényes bejegyzés, van ' + sok);
  return '1 érvényes bejegyzés';
});
check('törölt növényre mutató szűrő visszaáll', () => {
  betolt([{ id: 'x3', plantId: 'p1', plantName: 'Klívia', type: 'watering', date: '2026-10-22' }]);
  T.state.ui.logPlant = 'nincs-ilyen';
  T.renderLog();
  assert(T.state.ui.logPlant === 'all', 'a szűrő nem állt vissza');
  return 'Visszaállt „Minden növény”-re';
});

// ================================================================
console.log('\n== Lenyílók az Űrlapban (Új növény) ==');
check('az Új növény ablak lenyílói is sajátok', () => {
  T.fselRefresh();
  doc.getElementById('btnAdd').click();
  const sel = doc.getElementById('f_light');
  assert(sel, 'nincs f_light');
  const w = sel.nextElementSibling;
  assert(w && w.classList.contains('fsel'), 'a fény-mező nem lenyíló');
  assert(w.querySelectorAll('.fsel-opt').length > 2, 'kevés opció');
  return w.querySelectorAll('.fsel-opt').length + ' fény-opció';
});
check('választás beírja a fényigényt a mentendő adatba', () => {
  const sel = doc.getElementById('f_light');
  const w = sel.nextElementSibling;
  w.querySelector('.fsel-btn').click();
  const opt = [...w.querySelectorAll('.fsel-opt')].find(o => /Napos/.test(o.textContent));
  assert(opt, 'nincs Napos opció');
  opt.click();
  assert(sel.value === 'Napos / déli ablak', 'a select értéke: ' + sel.value);
  assert(w.querySelector('.fsel-label').textContent === 'Napos / déli ablak', 'a felirat nem frissült');
  return sel.value;
});
check('az űrlap mentése a lenyílókkal együtt működik', () => {
  const elotte = T.state.plants.length;
  doc.getElementById('f_name').value = 'Teszt Növény';
  doc.getElementById('f_water').value = '7';
  doc.getElementById('plantForm').dispatchEvent(new win.Event('submit', { bubbles: true, cancelable: true }));
  assert(T.state.plants.length === elotte + 1, 'nem került be az új növény');
  const uj = T.state.plants[T.state.plants.length - 1];
  assert(uj.light === 'Napos / déli ablak', 'a fény nem mentődött: ' + uj.light);
  return uj.name + ' · ' + uj.light;
});

console.log('\n== Verzió: „felül új, lent régi” ==');
check('a fájl verziója olvasható a lapról', () => {
  assert(T.FILE_VERSION && /^\d+\.\d+\.\d+$/.test(T.FILE_VERSION), 'nincs verzió: ' + T.FILE_VERSION);
  return T.FILE_VERSION;
});
check('eltérő futó szerver esetén figyelmeztető sáv jelenik meg', () => {
  T.checkVersion({ appVersion: '1.22.0' });
  const b = doc.getElementById('verBanner');
  assert(b, 'nincs #verBanner');
  assert(/Két verzió fut egyszerre/.test(b.textContent), 'nincs benne a magyarázat');
  assert(/1\.22\.0/.test(b.textContent), 'nem írja ki a régi verziót');
  assert(/florum-verzio\.sh|--leallit|restart/.test(b.textContent), 'nincs benne a megoldás parancsa');
  return 'piros sáv a régi verzióval + paranccsal';
});
check('azonos verzió esetén nincs felesleges figyelmeztetés', () => {
  const b = doc.getElementById('verBanner');
  if (b) b.remove();
  T.checkVersion({ appVersion: T.FILE_VERSION });
  assert(!doc.getElementById('verBanner'), 'feleslegesen figyelmeztetett');
  return 'nincs sáv';
});
check('a lábléc a FÁJL verzióját írja, nem a mentett régit', () => {
  T.state.meta.appVersion = '1.22.0';       // régi mentett érték
  T.switchView('settings');
  const t = doc.getElementById('settingsContent').textContent;
  assert(t.includes(T.FILE_VERSION), 'a lábléc nem a fájl verzióját mutatja');
  return 'lábléc: ' + T.FILE_VERSION;
});

console.log('\n== Egyéb nézetek és a rendszer-panel ==');
check('a Beállítások fül tartalmazza a rendszer-panelt', () => {
  T.switchView('settings');
  const t = doc.getElementById('settingsContent').textContent;
  assert(/Rendszer – KDE-ablak/.test(t), 'nincs rendszer-panel');
  return 'Rendszer – KDE-ablak / böngésző';
});
check('a rendszer-panel ismeri a saját lenyílókat', () => {
  const t = doc.getElementById('settingsContent').textContent;
  assert(/Saját lenyílók/.test(t), 'nincs benne a lenyíló-ellenőrzés');
  return 'igen';
});
check('a Napló-ellenőrzés gomb lefut hiba nélkül', () => {
  T.switchView('settings');
  const g = doc.querySelector('[data-logdiag]');
  assert(g, 'nincs Napló-ellenőrzés gomb');
  g.click();
  return 'lefutott';
});
check('a hibaüzenő sáv helye megvan a lapon', () => {
  assert(doc.getElementById('jsError'), 'nincs #jsError sáv');
  return '#jsError';
});
check('a nézetváltás minden fülön működik', () => {
  const nezetek = ['today', 'calendar', 'plants', 'log', 'diagnosis', 'settings'];
  for (const v of nezetek) {
    T.switchView(v);
    assert(doc.getElementById('view-' + v).classList.contains('active'), v + ' nem aktív');
  }
  return nezetek.join(' → ');
});

// ======================================================================
//  Verzió-ellenőrzés: „felül új, lent régi” eset – a felhasználó ezt látja
// ======================================================================
{
  // a régi példány azt vallja magáról, hogy 1.22.0 – a fájl már új
  const regiVerzio = new JSDOM(html, {
    runScripts: 'dangerously', url: 'http://127.0.0.1:8777/', pretendToBeVisual: true,
    beforeParse(w) {
      w.scrollTo = () => {};
      w.matchMedia = () => ({ matches: false, addEventListener() {}, addListener() {} });
      w.fetch = (url) => {
        if (String(url).indexOf('/api/state') >= 0) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({
            state: { plants: [], history: [], settings: {}, meta: {}, customDb: [] },
            info: { appVersion: '1.22.0', versionMismatch: true }
          }) });
        }
        if (String(url).indexOf('/api/info') >= 0) {
          return Promise.resolve({ ok: true, json: () => Promise.resolve({ appVersion: '1.22.0' }) });
        }
        return Promise.reject(new Error('offline'));
      };
      if (w.HTMLDialogElement && !w.HTMLDialogElement.prototype.showModal) {
        w.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
      }
    }
  });

  setTimeout(() => {
    const d = regiVerzio.window.document;
    check('eltérő verziójú futó példánynál piros figyelmeztető sáv jelenik meg', () => {
      const b = d.getElementById('verBanner');
      assert(b, 'nincs verBanner');
      assert(/1\.22\.0/.test(b.textContent), 'nincs benne a régi verzió');
      return b.textContent.replace(/\s+/g, ' ').slice(0, 70);
    });
    check('a sávban ott az „Újraindítás most” gomb', () => {
      const b = d.getElementById('verBanner');
      assert(b && b.querySelector('#verRestart'), 'nincs gomb');
      return '↻ Újraindítás most';
    });
    check('a lábléc mindkét verziót kiírja: fut / fájl', () => {
      const lablec = [...d.querySelectorAll('.saved')].map(x => x.textContent).join(' ');
      assert(/\(fut\)/.test(lablec), 'nincs (fut): ' + lablec.slice(0, 80));
      assert(/\(fájl\)/.test(lablec), 'nincs (fájl)');
      assert(/1\.22\.0/.test(lablec), 'nincs benne a futó verzió');
      return lablec.replace(/\s+/g, ' ').slice(0, 70);
    });


    // ================================================================
    console.log('\n== A lenyílók feliratai és böngészhetősége (1.33.2) ==');

    check('a legördülőkben NINCS ikon-név szöveg („water Öntözés”)', () => {
      const rossz = [];
      [...d.querySelectorAll('.fsel-opt')].forEach(o => {
        const t = (o.textContent || '').trim();
        if (/^(water|fert|mist|repot|note|book)\b/.test(t)) rossz.push(t);
      });
      assert(rossz.length === 0, 'ikon-név a szövegben: ' + rossz.join(' / '));
      return 'nincs ikon-név a feliratokban';
    });

    check('a Napló típus-szűrője magyar feliratokat mutat', () => {
      const sel = [...d.querySelectorAll('#logType option')].map(o => o.textContent.trim());
      assert(sel.indexOf('Öntözés') >= 0, 'nincs Öntözés: ' + sel.join(' | '));
      sel.forEach(t => assert(!/^(water|fert|mist|repot)\b/.test(t), 'ikon-név: ' + t));
      return sel.join(' | ');
    });

    check('a lista FIX pozíciójú (a .sheet nem tudja levágni)', () => {
      const css = html.match(/\.fsel-pop\{[^}]*\}/);
      assert(css && /position:\s*fixed/.test(css[0]), 'nem fix: ' + (css ? css[0] : 'nincs .fsel-pop'));
      return 'position: fixed';
    });

    // a Helyiség lenyíló: sok elem → keresőmező
    T.openDialog(null);
    const rooms = d.getElementById('f_room');
    const rwrap = rooms.nextSibling;
    check('a Helyiség lenyílóban van keresőmező (13 hely)', () => {
      rwrap.querySelector('.fsel-btn').click();
      const pop = rwrap.querySelector('.fsel-pop');
      assert(rwrap.classList.contains('open'), 'nem nyílt ki');
      const be = pop.querySelector('.fsel-search');
      assert(be, 'nincs keresőmező');
      assert(/13 elem/.test(be.getAttribute('placeholder') || ''), 'nincs darabszám: ' + be.getAttribute('placeholder'));
      return be.getAttribute('placeholder');
    });

    check('gépeléssel lehet böngészni: „nap” → Nappali', () => {
      const pop = rwrap.querySelector('.fsel-pop');
      const be = pop.querySelector('.fsel-search');
      be.value = 'nap';
      be.dispatchEvent(new win.Event('input', { bubbles: true }));
      const lat = [...pop.querySelectorAll('.fsel-opt')].filter(o => o.style.display !== 'none')
        .map(o => o.textContent.trim());
      assert(lat.length === 1 && lat[0] === 'Nappali', 'találat: ' + lat.join(', '));
      be.value = 'kert';
      be.dispatchEvent(new win.Event('input', { bubbles: true }));
      const lat2 = [...pop.querySelectorAll('.fsel-opt')].filter(o => o.style.display !== 'none')
        .map(o => o.textContent.trim());
      assert(lat2.join() === 'Kert,Kerti ágyás', 'kert-találat: ' + lat2.join(', '));
      return 'nap → Nappali; kert → ' + lat2.join(', ');
    });

    check('a listában görgetve NEM csukódik be a lenyíló', () => {
      const pop = rwrap.querySelector('.fsel-pop');
      const ev = new win.Event('scroll', { bubbles: true });
      Object.defineProperty(ev, 'target', { value: pop });
      win.dispatchEvent(ev);
      assert(rwrap.classList.contains('open'), 'a görgetés bezárta');
      return 'nyitva maradt görgetés után';
    });

    check('a keresőmezőben Enter az első találatot választja', () => {
      const pop = rwrap.querySelector('.fsel-pop');
      const be = pop.querySelector('.fsel-search');
      be.value = 'uveg';
      be.dispatchEvent(new win.Event('input', { bubbles: true }));
      be.focus();
      const ev = new win.KeyboardEvent('keydown', { key: 'Enter', bubbles: true });
      d.dispatchEvent(ev);
      assert(rooms.value === 'Üvegház', 'nem az Üvegház lett: ' + JSON.stringify(rooms.value));
      assert(!rwrap.classList.contains('open'), 'nem záródott be');
      return 'Üvegház kiválasztva Enterrel';
    });

    check('a „Kert” választás kerti növényt jelent (jelölő be)', () => {
      rwrap.querySelector('.fsel-btn').click();
      const pop = rwrap.querySelector('.fsel-pop');
      [...pop.querySelectorAll('.fsel-opt')].filter(o => o.textContent.trim() === 'Kert')[0].click();
      const g = d.getElementById('f_garden');
      assert(rooms.value === 'Kert', 'nem Kert: ' + rooms.value);
      assert(g && g.checked, 'a kerti jelölő nem kapcsolt be');
      return 'Kert + kerti jelölő';
    });

    console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás');
    if (problems.length) { console.log('Hibák:'); problems.forEach(p => console.log('  - ' + p)); }
    console.log('');
    process.exit(bad ? 1 : 0);
  }, 1200);
}
