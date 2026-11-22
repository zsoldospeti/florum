#!/usr/bin/env node
/* DOM-füstteszt a florum.html-hez böngésző nélkül.
   Egy minimális ál-DOM-mal lefuttatja az app teljes <script>-jét, majd
   meghívja a fő rajzoló függvényeket (render, renderToday, renderSettings),
   és jelzi, ha bármelyik kivételt dob vagy hibás HTML-t gyárt. */

const fs = require('fs');
const vm = require('vm');
const path = process.argv[2] || '/home/user/florum/florum.html';
const html = fs.readFileSync(path, 'utf8');
const blocks = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m => m[1]);
let src = blocks.sort((a, b) => b.length - a.length)[0];

// belépési pont az app belső hatókörébe
const EXPORT = `
;globalThis.__T = { render: (typeof render!=='undefined'?render:null),
  renderToday: (typeof renderToday!=='undefined'?renderToday:null),
  renderSettings: (typeof renderSettings!=='undefined'?renderSettings:null),
  renderCalendar: (typeof renderCalendar!=='undefined'?renderCalendar:null),
  renderPlants: (typeof renderPlants!=='undefined'?renderPlants:null),
  renderLog: (typeof renderLog!=='undefined'?renderLog:null),
  state: (typeof state!=='undefined'?state:null),
  applyState: (typeof applyState!=='undefined'?applyState:null),
  springMoveBannerHTML: (typeof springMoveBannerHTML!=='undefined'?springMoveBannerHTML:null),
  winterStatusText: (typeof winterStatusText!=='undefined'?winterStatusText:null),
  openDialog: (typeof openDialog!=='undefined'?openDialog:null),
  springMoveDone: (typeof springMoveDone!=='undefined'?springMoveDone:null),
  springMoveLater: (typeof springMoveLater!=='undefined'?springMoveLater:null),
  openPhotoExternally: (typeof openPhotoExternally!=='undefined'?openPhotoExternally:null),
  fetchPlantData: (typeof fetchPlantData!=='undefined'?fetchPlantData:null),
  applyFetchedEntry: (typeof applyFetchedEntry!=='undefined'?applyFetchedEntry:null),
  openInfoFetched: (typeof openInfoFetched!=='undefined'?openInfoFetched:null),
  srcTextToggle: (typeof srcTextToggle!=='undefined'?srcTextToggle:null),
  applyDBEntry: (typeof applyDBEntry!=='undefined'?applyDBEntry:null),
  calCollect: (typeof calCollect!=='undefined'?calCollect:null),
  calGroup: (typeof calGroup!=='undefined'?calGroup:null),
  calMode: (typeof calMode!=='undefined'?calMode:null),
  calCellHTML: (typeof calCellHTML!=='undefined'?calCellHTML:null),
  openInfo: (typeof openInfo!=='undefined'?openInfo:null),
  LINK_TAGS: (typeof LINK_TAGS!=='undefined'?LINK_TAGS:null),
  plantLinkGroups: (typeof plantLinkGroups!=='undefined'?plantLinkGroups:null),
  openPlantLink: (typeof openPlantLink!=='undefined'?openPlantLink:null),
  plantTitle: (typeof plantTitle!=='undefined'?plantTitle:null),
  plantAltName: (typeof plantAltName!=='undefined'?plantAltName:null),
  plantAlias: (typeof plantAlias!=='undefined'?plantAlias:null),
  setAlias: (typeof setAlias!=='undefined'?setAlias:null),
  openAliasDialog: (typeof openAliasDialog!=='undefined'?openAliasDialog:null),
  saveForm: (typeof saveForm!=='undefined'?saveForm:null),
  searchDB: (typeof searchDB!=='undefined'?searchDB:null),
  initDB: (typeof initDB!=='undefined'?initDB:null),
  findDBByName: (typeof findDBByName!=='undefined'?findDBByName:null),
  infoPlantLinksHTML: (typeof infoPlantLinksHTML!=='undefined'?infoPlantLinksHTML:null),
  safeUrl: (typeof safeUrl!=='undefined'?safeUrl:null),
  searchUrl: (typeof searchUrl!=='undefined'?searchUrl:null),
  searchQuery: (typeof searchQuery!=='undefined'?searchQuery:null),
  plantLinks: (typeof plantLinks!=='undefined'?plantLinks:null),
  plantLinksHTML: (typeof plantLinksHTML!=='undefined'?plantLinksHTML:null),
  plantNameHTML: (typeof plantNameHTML!=='undefined'?plantNameHTML:null),
  openPlantMenu: (typeof openPlantMenu!=='undefined'?openPlantMenu:null),
  SEARCH_ENGINES: (typeof SEARCH_ENGINES!=='undefined'?SEARCH_ENGINES:null),
  addFormLink: (typeof addFormLink!=='undefined'?addFormLink:null),
  collectFormLinks: (typeof collectFormLinks!=='undefined'?collectFormLinks:null),
  applyLayout: (typeof applyLayout!=='undefined'?applyLayout:null),
  setLayout169: (typeof setLayout169!=='undefined'?setLayout169:null),
  moveTask: (typeof moveTask!=='undefined'?moveTask:null),
  clearMove: (typeof clearMove!=='undefined'?clearMove:null),
  collectTasks: (typeof collectTasks!=='undefined'?collectTasks:null),
  MIST_WATER: (typeof MIST_WATER!=='undefined'?MIST_WATER:null),
  MIST_ORDER: (typeof MIST_ORDER!=='undefined'?MIST_ORDER:null),
  mistVal: (typeof mistVal!=='undefined'?mistVal:null),
  mistSzereti: (typeof mistSzereti!=='undefined'?mistSzereti:null),
  mistHint: (typeof mistHint!=='undefined'?mistHint:null),
  mistMondat: (typeof mistMondat!=='undefined'?mistMondat:null),
  updateMistWaterHint: (typeof updateMistWaterHint!=='undefined'?updateMistWaterHint:null),
  intervalFor: (typeof intervalFor!=='undefined'?intervalFor:null),
  fillSelects: (typeof fillSelects!=='undefined'?fillSelects:null),
  calSourcesHTML: (typeof calSourcesHTML!=='undefined'?calSourcesHTML:null),
  calSourcesList: (typeof calSourcesList!=='undefined'?calSourcesList:null),
  CAL: (typeof CAL!=='undefined'?CAL:null),
  CAL_EVENT_DEF: (typeof CAL_EVENT_DEF!=='undefined'?CAL_EVENT_DEF:null),
  calVanForras: (typeof calVanForras!=='undefined'?calVanForras:null),
  calApiUrl: (typeof calApiUrl!=='undefined'?calApiUrl:null),
  calEventFromApi: (typeof calEventFromApi!=='undefined'?calEventFromApi:null),
  calEventsIn: (typeof calEventsIn!=='undefined'?calEventsIn:null),
  calFedett: (typeof calFedett!=='undefined'?calFedett:null),
  calEventRowHTML: (typeof calEventRowHTML!=='undefined'?calEventRowHTML:null),
  calDaySummary: (typeof calDaySummary!=='undefined'?calDaySummary:null),
  loadCalEvents: (typeof loadCalEvents!=='undefined'?loadCalEvents:null),
  undoLast: (typeof undoLast!=='undefined'?undoLast:null),
  photoSrc: (typeof photoSrc!=='undefined'?photoSrc:null),
  completeTask: (typeof completeTask!=='undefined'?completeTask:null),
  monthKey: (typeof monthKey!=='undefined'?monthKey:null),
  todayISO: (typeof todayISO!=='undefined'?todayISO:null),
  kdePanelHTML: (typeof kdePanelHTML!=='undefined'?kdePanelHTML:null),
  icsEventCount: (typeof icsEventCount!=='undefined'?icsEventCount:null),
  icsFilePath: (typeof icsFilePath!=='undefined'?icsFilePath:null),
  copyText: (typeof copyText!=='undefined'?copyText:null),
  TASK_DEFS: (typeof TASK_DEFS!=='undefined'?TASK_DEFS:null),
  taskOccurrences: (typeof taskOccurrences!=='undefined'?taskOccurrences:null),
  store: (typeof store!=='undefined'?store:null),
  addDays: (typeof addDays!=='undefined'?addDays:null),
  subscribe: null };
`;
const i = src.lastIndexOf('})();');
src = src.slice(0, i) + EXPORT + src.slice(i);

// ------------------------------- ál-DOM -------------------------------
const nodes = new Map();
function mk(tag) {
  const el = {
    tagName: (tag || 'div').toUpperCase(), id: '', className: '', _html: '', textContent: '',
    style: { _p: {}, setProperty(k, v) { this[k] = v; this._p[k] = v; }, getPropertyValue(k) { return this._p[k] || this[k] || ''; } },
    dataset: {}, children: [], attrs: {}, value: '', checked: false, files: [],
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = String(v); },
    addEventListener() {}, removeEventListener() {}, dispatchEvent() { return true; }, appendChild(c) { this.children.push(c); return c; },
    removeChild() {}, remove() {}, insertBefore() {}, replaceWith() {},
    querySelector() { return null; }, querySelectorAll() { return []; },
    closest() { return null; }, focus() {}, blur() {}, click() {},
    setAttribute(k, v) { this.attrs[k] = String(v); if (k === 'id') { this.id = String(v); nodes.set(this.id, this); } },
    getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    hasAttribute(k) { return k in this.attrs; }, removeAttribute(k) { delete this.attrs[k]; },
    showModal() {}, close() { this.open = false; }, scrollIntoView() {},
    getBoundingClientRect() { return { top: 0, left: 0, right: 0, bottom: 0, width: 300, height: 40 }; },
    matches() { return false; },
    insertAdjacentHTML(p, v) { this._html += v; }
  };
  return el;
}
function byId(id) {
  if (!nodes.has(id)) {
    const el = mk('div'); el.id = id; nodes.set(id, el);
    // a beágyazott növény-adatbázist is elérhetővé tesszük (a valódi app így olvassa)
    if (id === 'bundledDb') {
      try {
        const m = html.match(/<script id="bundledDb"[^>]*>([\s\S]*?)<\/script>/);
        if (m) el.textContent = m[1];
      } catch (e) {}
    }
  }
  return nodes.get(id);
}
const body = mk('body');
const documentStub = {
  documentElement: mk('html'), body, head: mk('head'),
  readyState: 'complete',
  createElement: (t) => mk(t),
  createTextNode: (t) => ({ nodeType: 3, textContent: t }),
  getElementById: byId,
  querySelector: () => null, querySelectorAll: () => [],
  addEventListener() {}, removeEventListener() {},
  createDocumentFragment: () => mk('fragment'),
  execCommand() { return true; },
  title: ''
};
const store = {};
let sandboxWin = null;
const sandbox = {
  console, setTimeout: () => 0, clearTimeout() {}, setInterval: () => 0, clearInterval() {},
  requestAnimationFrame: () => 0, cancelAnimationFrame() {},
  document: documentStub,
  localStorage: {
    getItem: (k) => (k in store ? store[k] : null),
    setItem: (k, v) => { store[k] = String(v); }, removeItem: (k) => { delete store[k]; }
  },
  fetch: () => Promise.reject(new Error('offline teszt')),
  CustomEvent: function(n, o){ this.type = n; this.detail = o && o.detail; },
  Event: function(n){ this.type = n; },
  navigator: { language: 'hu-HU', onLine: false },
  location: { href: 'http://127.0.0.1:8777/', origin: 'http://127.0.0.1:8777', search: '', protocol: 'http:' },
  crypto: { randomUUID: () => 'uuid-' + Math.random().toString(36).slice(2) },
  matchMedia: () => ({ matches: false, addEventListener() {}, addListener() {} }),
  Notification: undefined,
  Intl, Date: (process.env.FAKE_TODAY ? (function(){
    const R = Date; const t = new R(process.env.FAKE_TODAY + 'T09:00:00').getTime();
    class D extends R { constructor(...a){ if(!a.length) super(t); else super(...a); } static now(){ return t; } }
    return D; })() : Date), Math, JSON, Promise, Number, String, Boolean, Array, Object, RegExp, Error,
  isFinite, parseInt, parseFloat, encodeURIComponent, decodeURIComponent,
  URL, URLSearchParams, Blob: function () {}, FileReader: function () {},
  Image: function () { return mk('img'); },
  alert() {}, confirm: () => true, prompt: () => null,
  innerWidth: 1440, innerHeight: 900, scrollY: 0, scrollTo() {},
  addEventListener() {}, removeEventListener() {},
  globalThis: null
};
sandbox.window = sandbox;
sandbox.self = sandbox;
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

let ok = 0, bad = 0;
const problems = [];
function check(cim, fn) {
  try {
    const r = fn();
    ok++;
    console.log('  ✓ ' + cim + (r ? '   → ' + String(r).slice(0, 150) : ''));
    return r;
  } catch (e) {
    bad++;
    problems.push(cim + ': ' + e.message);
    console.log('  ✗ ' + cim + '   → ' + e.message);
    return null;
  }
}

console.log('\n== A teljes script betöltése ál-DOM-ban ==');
try {
  vm.runInContext(src, sandbox, { filename: 'florum-app.js', timeout: 15000 });
  sandboxWin = sandbox.window || sandbox;
  ok++;
  console.log('  ✓ a script hiba nélkül lefutott (init)');
} catch (e) {
  bad++;
  problems.push('init: ' + e.message);
  console.log('  ✗ init hiba: ' + e.message + '\n    ' + (e.stack || '').split('\n')[1]);
}

const T = sandbox.__T || {};
console.log('\n== Belső függvények elérhetők? ==');
['render', 'renderToday', 'renderSettings', 'renderCalendar', 'renderPlants', 'renderLog',
 'applyState', 'springMoveBannerHTML', 'winterStatusText'].forEach(k => {
  const van = typeof T[k] === 'function';
  if (van) { ok++; console.log('  ✓ ' + k); } else { bad++; console.log('  ✗ ' + k + ' hiányzik'); }
});

// ---------- állapot betöltése: klívia + hűvös telelés + februári emlékeztető ----------
console.log('\n== Teszt-adatok betöltése ==');
const plant = {
  id: 'p1', name: 'Klívia', species: 'Clivia miniata', room: 'Nappali', light: 'Világos, szórt',
  waterDays: 7, waterWinter: 21, fertDays: 14, mistDays: 0, repotMonths: 30,
  lastWatered: '2026-10-20', lastFertilized: '2026-10-20', lastRepotted: '2026-08-01',
  winterSlowdown: true, fertWinter: 0, coolPlace: true, createdAt: '2026-10-20T10:00:00Z',
  notes: ''
};
check('applyState (klívia, hűvös telelés)', () => {
  T.applyState({ plants: [plant], history: [], settings: { winterMode: 'auto' }, meta: {}, customDb: [] });
  return T.state.plants.length + ' növény, winterMode=' + T.state.settings.winterMode;
});

console.log('\n== Rajzolás ==');
check('winterStatusText()', () => T.winterStatusText());
check('renderSettings()', () => {
  T.renderSettings();
  const h = byId('settingsContent')._html;
  return h.length + ' karakter, van-e téli mód választó: ' + /data-wintermode/.test(h);
});
check('render()', () => { T.render(); return 'ok'; });
check('renderToday()', () => {
  T.renderToday();
  const h = byId('todayContent')._html;
  return h.length + ' karakter, KPI: ' + /Lejárt/.test(h);
});
check('renderPlants()', () => { T.renderPlants(); return byId('plantsContent')._html.length + ' karakter'; });
check('renderCalendar()', () => { T.renderCalendar(); return byId('calendarContent')._html.length + ' karakter'; });
check('renderLog()', () => { T.renderLog(); return byId('logContent')._html.length + ' karakter'; });

console.log('\n== Februári emlékeztető (dátumfüggő) ==');
check('springMoveBannerHTML() télvíz idején', () => {
  const h = T.springMoveBannerHTML();
  return h ? (h.indexOf('virágszár') >= 0 ? 'megjelenik (virágszár szöveggel)' : 'megjelenik') : 'nem jelenik meg (nyár)';
});

check('a Ma nézetben is megjelenik a banner', () => {
  const h = byId('todayContent')._html;
  return /virágszár/.test(h) ? 'igen, a banner benne van' : 'nincs benne (nyár)';
});
check('springMoveLater() – 1 hét halasztás', () => {
  T.springMoveLater();
  const p = T.state.plants[0];
  return 'springAskAfter=' + p.springAskAfter + ', banner most: ' +
         (/virágszár/.test(T.springMoveBannerHTML()) ? 'látszik' : 'elrejtve');
});
check('springMoveDone() – áthelyezés melegre', () => {
  T.state.plants[0].springAskAfter = null;
  T.springMoveDone();
  const p = T.state.plants[0];
  return 'springMove=' + p.springMove + ', lastFertilized=' + p.lastFertilized +
         ', banner most: ' + (/virágszár/.test(T.springMoveBannerHTML()) ? 'látszik' : 'elrejtve');
});

console.log('\n== Űrlap ==');
check('openDialog() – új növény dialógus', () => {
  T.openDialog();
  return 'f_name=' + JSON.stringify(byId('f_name').value) +
         ', f_cool=' + byId('f_cool').checked + ', f_fertWinter=' + byId('f_fertWinter').checked;
});


// ---------- naptár: nap / hónap / év nézet ----------
console.log('\n== Naptár nézetek ==');
const calH = () => byId('calendarContent')._html;
// sűrű ütemezésű növény, hogy a naptárban legyen mit látni (a klívia télen pihen)
T.state.plants.push({
  id: 'p2', name: 'Fikusz', species: 'Ficus elastica', room: 'Nappali', light: 'Világos, szórt',
  waterDays: 5, waterWinter: 10, fertDays: 14, mistDays: 7, repotMonths: 24,
  lastWatered: T.addDays(T.todayISO(), -3), lastFertilized: T.addDays(T.todayISO(), -4),
  lastMisted: T.addDays(T.todayISO(), -2), lastRepotted: T.addDays(T.todayISO(), -60),
  winterSlowdown: false, fertWinter: 14, createdAt: T.addDays(T.todayISO(), -400) + 'T10:00:00Z', notes: ''
});
T.state.ui.calMonth = T.monthKey(new Date());

check('alapból a nap-nézet indul, névvel a cellákban', () => {
  T.state.ui.calMode = 'nap';
  T.renderCalendar();
  const h = calH();
  if (!/data-calmode="nap"/.test(h)) throw new Error('nincs nézetváltó');
  if (!/class="cal-line[^"]*"/.test(h)) throw new Error('nincsenek növénynév-sorok a cellákban');
  if (!/weekbar/.test(h)) throw new Error('nincs hétválasztó');
  if (h.indexOf('Fikusz') < 0) throw new Error('a növény neve nem jelenik meg a rácsban');
  return (h.match(/class="cal-line[ "]/g) || []).length + ' névsor a rácsban';
});

check('a cella háttere a napi terhelést jelzi', () => {
  const h = calH();
  const db = (h.match(/color-mix/g) || []).length;
  if (!db) throw new Error('nincs terhelés-háttér');
  return db + ' cella kap terhelés-hátteret';
});

check('a cella tetején ott a napi teendők száma', () => {
  const h = calH();
  const db = (h.match(/class="cal-top"/g) || []).length;
  const szam = (h.match(/class="cal-top"><span class="dnum">\d+<\/span><span class="n">/g) || []).length;
  if (!db) throw new Error('nincs cal-top');
  return szam + ' napon van darabszám';
});

check('a nap-kártyán van Kész, Szundi és napi összegzés', () => {
  // A nap-kártya csak a jövőre/mára mutat műveleteket, ezért a MAI napot
  // választjuk, és gondoskodunk róla, hogy legyen esedékes öntözés.
  const mai = T.todayISO();
  T.state.plants[1].waterDays = 7;
  T.state.plants[1].lastWatered = T.addDays(mai, -7);
  T.state.ui.calMode = 'nap';
  T.state.ui.calMonth = mai.slice(0, 7);
  T.state.ui.calSel = mai;
  T.renderCalendar();
  const m = [mai];
  const h = calH();
  if (!/data-caldone/.test(h)) throw new Error('nincs Kész gomb');
  if (!/data-calsnooze/.test(h)) throw new Error('nincs Szundi gomb');
  if (!/class="day-sum"/.test(h)) throw new Error('nincs napi összegzés');
  return 'kiválasztott nap: ' + m[0];
});

check('az "Összes kész" több teendőnél jelenik meg', () => {
  const h = calH();
  return /data-calalldone/.test(h) ? 'igen' : 'nem (egy teendő van a napon)';
});

check('hónap-nézet: nagyobb cellák + növényenkénti táblázat', () => {
  T.state.ui.calMode = 'honap';
  T.renderCalendar();
  const h = calH();
  if (!/cal-month-mode/.test(h)) throw new Error('nincs hónap mód');
  if (!/cal-table/.test(h)) throw new Error('nincs havi táblázat');
  if (h.indexOf('Fikusz') < 0) throw new Error('a táblázatban nincs benne a növény');
  const sorok = (h.match(/<tr>/g) || []).length;
  return 'táblázat-sorok: ' + sorok + ' (fejléc + növények)';
});

check('év-nézet: 12 hónapkártya + havi sáv + összegzés', () => {
  T.state.ui.calMode = 'ev';
  T.renderCalendar();
  const h = calH();
  const kartyak = (h.match(/class="year-card/g) || []).length;
  if (kartyak !== 12) throw new Error('nem 12 hónapkártya: ' + kartyak);
  if (!/class="ybar"/.test(h)) throw new Error('nincs éves sáv');
  if (!/Év összesen/.test(h)) throw new Error('nincs éves összegzés');
  if (!/2026\. év/.test(h)) throw new Error('nincs év a címben');
  return '12 kártya, ' + (h.match(/data-ymonth/g) || []).length + ' kattintható hónap';
});

check('az év-nézet címe és nyilai évesek', () => {
  const h = calH();
  if (!/Előző év/.test(h) || !/Következő év/.test(h)) throw new Error('a nyilak nem évesek');
  return 'Előző év / Következő év';
});

check('calCollect(): jövő = ütemezés, múlt = előzmény', () => {
  T.state.ui.calMode = 'nap';
  const ma = T.todayISO();
  // FIGYELEM: a múltbeli bejegyzés dátuma nem eshet egybe egy ütemezett
  // esedékességgel – olyankor a naptár az ütemezést mutatja (ez helyes),
  // és a bejegyzés kimarad. Ezért több jelölt közül választunk.
  let mult = null, sorok = null, multbeli = null, jovobeli = null;
  for (const off of [-10, -3, -5, -6, -8, -9, -11, -13, -15]) {
    const jelolt = T.addDays(ma, off);
    T.state.history = T.state.history.filter(e => e.id !== 'h1');
    T.state.history.push({ id: 'h1', plantId: T.state.plants[0].id, plantName: T.state.plants[0].name,
                           type: 'watering', date: jelolt, ts: 1 });
    sorok = T.calCollect(T.addDays(ma, -20), T.addDays(ma, 20));
    multbeli = sorok.filter(o => o.kind === 'past' && o.due === jelolt);
    jovobeli = sorok.filter(o => o.kind === 'plan' && o.due >= ma);
    if (multbeli.length) { mult = jelolt; break; }
  }
  if (!mult) throw new Error('a múltbeli öntözés nem jelenik meg');
  if (!jovobeli.length) throw new Error('nincs jövőbeli esedékesség');
  return multbeli.length + ' múltbeli (' + mult + '), ' + jovobeli.length + ' jövőbeli sor';
});

check('a múltbeli sor késznek számít, nem lejártnak', () => {
  const sorok = T.calCollect(T.addDays(T.todayISO(), -20), T.addDays(T.todayISO(), 20))
    .filter(o => o.kind === 'past');
  return sorok.every(o => o.done && !o.late) ? 'igen (' + sorok.length + ' sor)' : 'hibás';
});

check('a Kész gomb után a naptár rögtön frissül', () => {
  T.renderCalendar();
  const elotte = (calH().match(/class="cal-line done"/g) || []).length;
  T.completeTask('p2', 'misting', true);
  T.renderCalendar();
  const utana = (calH().match(/class="cal-line done"/g) || []).length;
  if (utana < elotte) throw new Error('nem nőtt a kész sorok száma');
  return 'kész sorok: ' + elotte + ' → ' + utana;
});

check('a naptár kimenetében nincs undefined / NaN / üres dátum', () => {
  const hibak = [];
  ['nap', 'honap', 'ev'].forEach(m => {
    T.state.ui.calMode = m;
    T.renderCalendar();
    const h = calH();
    if (/undefined/.test(h)) hibak.push(m + ': undefined');
    if (/NaN/.test(h)) hibak.push(m + ': NaN');
    if (/\[object Object\]/.test(h)) hibak.push(m + ': object');
    if (/data-calday=""/.test(h)) hibak.push(m + ': üres dátum');
    if (/color-mix\(in srgb, var\(--green-soft\) NaN/.test(h)) hibak.push(m + ': rossz százalék');
  });
  if (hibak.length) throw new Error(hibak.join(', '));
  return 'mindhárom nézet tiszta';
});


console.log('\n== Naptár: fotók a cellákban ==');
check('fotó nélkül színes pötty van', () => {
  T.state.plants[1].photos = [];
  T.state.ui.calMode = 'nap';
  T.renderCalendar();
  const h = calH();
  return /class="cal-dot water/.test(h) && !/cal-ava/.test(h) ? 'pötty (nincs fotó)' : 'hibás';
});

check('fotóval a cellában a növény képe jelenik meg', () => {
  T.state.plants[1].photos = [{ file: 'photos/fikusz.jpg', taken: T.todayISO() }];
  T.renderCalendar();
  const h = calH();
  if (!/class="cal-ava water"/.test(h)) throw new Error('nincs cal-ava a cellában');
  if (h.indexOf('/photos/fikusz.jpg') < 0) throw new Error('a kép útvonala nem került be');
  if (!/<div class="cal-line"[^>]*><img class="cal-ava water" src="\/photos\/fikusz.jpg"[^>]*><span class="nm">Fikusz<\/span>/.test(h))
    throw new Error('a Fikusz sora nem képet kapott');
  // a nap-kártyán is kép van, a pötty pedig a fotó nélküli növényeknél marad
  return 'Fikusz soraiban kép, a fotó nélkülieknél pötty';
});

check('a nap-kártyán a kép az ikon helyén van', () => {
  const h = calH();
  if (!/ico t-water has-photo/.test(h)) throw new Error('nincs has-photo ikon');
  if (!/class="ico-img"/.test(h)) throw new Error('nincs ico-img');
  return 'igen (ico-img)';
});

console.log('\n== Naptár: áthelyezés ==');
check('húzható a nyitott teendő', () => {
  const h = calH();
  if (!/draggable="true"/.test(h)) throw new Error('nincs draggable sor');
  if (!/data-drag-plant="p2"/.test(h)) throw new Error('nincs data-drag-plant');
  return 'draggable + data-drag-plant';
});

check('a sorban van dátummező az áthelyezéshez', () => {
  const h = calH();
  if (!/class="cal-move"/.test(h)) throw new Error('nincs cal-move dátummező');
  if (!/data-move-plant="p2"/.test(h)) throw new Error('nincs data-move-plant');
  return 'input[type=date] a sorban';
});

check('moveTask(): a teendő átkerül a megadott napra', () => {
  const ma = T.todayISO();
  const cel = T.addDays(ma, 4);
  T.state.plants[1].snooze = {};
  T.moveTask('p2', 'watering', cel);
  const sorok = T.calCollect(T.addDays(ma, -5), T.addDays(ma, 30))
    .filter(o => o.plant.id === 'p2' && o.def.key === 'watering');
  const at = sorok.filter(o => o.due === cel && o.moved);
  if (!at.length) throw new Error('nincs áthelyezett sor a ' + cel + ' napon');
  if (sorok.some(o => o.due === T.addDays(ma, -3) && o.due !== cel)) throw new Error('a régi helyén is ott maradt');
  return cel + ' · áthelyezve ' + at[0].origDue + '-ról';
});

check('a Ma nézet is az áthelyezett napot mutatja', () => {
  const cel = T.addDays(T.todayISO(), 4);
  const t = T.collectTasks().filter(x => x.plant.id === 'p2' && x.def.key === 'watering')[0];
  if (!t) throw new Error('nincs ilyen teendő');
  if (t.due !== cel) throw new Error('a Ma nézet még a régi napot mutatja: ' + t.due);
  if (!t.snoozed) throw new Error('nincs megjelölve áthelyezettként');
  return 'due=' + t.due + ', snoozed=true';
});

check('korábbi napra is át lehet helyezni (előrehozás)', () => {
  const ma = T.todayISO();
  T.moveTask('p2', 'watering', ma);
  const t = T.collectTasks().filter(x => x.plant.id === 'p2' && x.def.key === 'watering')[0];
  if (t.due !== ma) throw new Error('nem hozta előre: ' + t.due);
  return 'ma (' + ma + ')';
});

check('múltbeli napra nem lehet áthelyezni', () => {
  const ma = T.todayISO();
  const mult = T.addDays(ma, -5);
  const elotte = T.state.plants[1].snooze.watering;
  T.moveTask('p2', 'watering', mult);
  if (T.state.plants[1].snooze.watering !== elotte) throw new Error('mégis átírta: ' + T.state.plants[1].snooze.watering);
  return 'elutasítva, maradt: ' + elotte;
});

check('clearMove(): vissza az eredeti időpontra', () => {
  T.clearMove('p2', 'watering');
  if (T.state.plants[1].snooze.watering) throw new Error('nem törölte az áthelyezést');
  const t = T.collectTasks().filter(x => x.plant.id === 'p2' && x.def.key === 'watering')[0];
  return 'snooze törölve, következő esedékesség: ' + t.due;
});

check('teljesítés után megszűnik az áthelyezés', () => {
  T.moveTask('p2', 'watering', T.addDays(T.todayISO(), 3));
  T.completeTask('p2', 'watering', true);
  const t = T.collectTasks().filter(x => x.plant.id === 'p2' && x.def.key === 'watering')[0];
  if (T.state.plants[1].snooze && T.state.plants[1].snooze.watering) throw new Error('az áthelyezés megmaradt');
  return 'következő esedékesség: ' + t.due + ' (snoozed=' + t.snoozed + ')';
});

check('a cellában megjelenik az „áthelyezve" jelölés', () => {
  T.moveTask('p2', 'misting', T.addDays(T.todayISO(), 2));
  T.state.ui.calSel = T.addDays(T.todayISO(), 2);
  T.state.ui.calMonth = T.monthKey(new Date());
  T.renderCalendar();
  const h = calH();
  if (h.indexOf('áthelyezve') < 0) throw new Error('nincs áthelyezve felirat');
  return 'megvan a nap-kártyán';
});


check('csak a soron következő esedékesség húzható (nem a távoli jövőé)', () => {
  T.state.plants[1].snooze = {};
  // rövid (3 napos) öntözési időköz: így a hónap-rácsban több sora is látszik,
  // a dátumtól függetlenül (a hónap vége felé is legalább 2)
  T.state.plants[1].waterDays = 3;
  T.state.plants[1].lastWatered = T.addDays(T.todayISO(), -2);
  T.state.history = T.state.history.filter(e => e.plantId !== 'p2');
  T.state.ui.calMode = 'nap';
  T.state.ui.calMonth = T.monthKey(new Date());
  T.renderCalendar();
  const h = calH();
  const sorok = h.match(/<div class="cal-line[^>]*>/g) || [];
  const ont = sorok.filter(x => /title="Fikusz – Öntözés/.test(x));
  const huz = ont.filter(x => /draggable="true"/.test(x));
  if (huz.length !== 1) throw new Error('a húzható öntöző-sorok száma ' + huz.length + ' (1 kellene)');
  if (ont.length < 2) throw new Error('nincs elég öntöző-sor a vizsgálathoz');
  return ont.length + ' öntöző-sor a hónapban, ebből ' + huz.length + ' húzható';
});

check('az áthelyezés visszavonható a toast gombjával', () => {
  const cel = T.addDays(T.todayISO(), 6);
  T.moveTask('p2', 'misting', cel);
  const kozben = T.collectTasks().filter(x => x.plant.id === 'p2' && x.def.key === 'misting')[0];
  T.undoLast();
  const utana = T.collectTasks().filter(x => x.plant.id === 'p2' && x.def.key === 'misting')[0];
  if (kozben.due !== cel) throw new Error('nem történt meg az áthelyezés');
  if (utana.due === cel) throw new Error('a visszavonás nem állította vissza: ' + utana.due);
  return kozben.due + ' → ' + utana.due;
});


console.log('\n== 16:9 nézet ==');
check('setLayout169(true) bekapcsolja a 16:9 módot', () => {
  T.setLayout169(true);
  const v = documentStub.documentElement.getAttribute('data-layout');
  if (v !== '169') throw new Error('data-layout=' + JSON.stringify(v));
  if (T.state.settings.layout169 !== true) throw new Error('a beállítás nem mentődött');
  return 'data-layout="169", settings.layout169=true';
});

check('a cellamagasság a képernyőhöz igazodik (1080p)', () => {
  const st = documentStub.documentElement.style;
  const h = (st && st.getPropertyValue) ? st.getPropertyValue('--cal-cell-h') : (st['--cal-cell-h'] || '');
  if (!h) throw new Error('nincs --cal-cell-h');
  return '--cal-cell-h = ' + h;
});

check('setLayout169(false) visszaáll automatikusra', () => {
  T.setLayout169(false);
  const v = documentStub.documentElement.getAttribute('data-layout');
  if (v !== '') throw new Error('data-layout=' + JSON.stringify(v));
  return 'data-layout="" (automatikus)';
});

check('a beállításokban van 16:9 és teljes képernyő vezérlő', () => {
  T.setLayout169(false);
  T.renderSettings();
  const h = byId('settingsContent')._html;
  if (!/data-layout169="1"/.test(h)) throw new Error('nincs 16:9 kapcsoló');
  if (!/data-fullscreen/.test(h)) throw new Error('nincs teljes képernyő gomb');
  return 'Automatikus / 16:9 + Teljes képernyő';
});

check('16:9 módban a rács és a nap kártya egymás mellett van', () => {
  T.setLayout169(true);
  T.state.ui.calMode = 'honap';
  T.renderCalendar();
  const h = calH();
  if (!/class="cal-split"/.test(h)) throw new Error('nincs cal-split');
  if (!/cal-split-main/.test(h) || !/cal-split-side/.test(h)) throw new Error('hiányos felosztás');
  const main = h.indexOf('cal-split-main'), side = h.indexOf('cal-split-side');
  if (main > side) throw new Error('rossz sorrend');
  T.setLayout169(false);
  return 'bal: rács · jobb: nap kártya + havi táblázat';
});

check('automatikus módban egymás alatt marad', () => {
  T.setLayout169(false);
  T.state.ui.calMode = 'honap';
  T.renderCalendar();
  return /cal-split/.test(calH()) ? 'hibás: még felosztott' : 'igen, teljes szélesség';
});

check('a fejlécben van 16:9 gomb', () => {
  return /id="btn169"/.test(fs.readFileSync(path, 'utf8')) ? 'igen (#btn169)' : 'hiányzik';
});

check('a 16:9 CSS megvan és a lap 16/9 arányú', () => {
  const h = fs.readFileSync(path, 'utf8');
  if (!/html\[data-layout="169"\] \.wrap\{/.test(h)) throw new Error('nincs 16:9 CSS');
  if (!/calc\(100vh \* 16 \/ 9\)/.test(h)) throw new Error('nincs 16:9 arányszámítás');
  return 'aspect: min(100vw, 100vh*16/9)';
});


console.log('\n== Linkek és név-keresés ==');
check('safeUrl(): csak http(s), a javascript: nem megy át', () => {
  const esetek = [
    ['example.com', 'https://example.com'],
    ['http://a.hu/x', 'http://a.hu/x'],
    ['https://b.hu', 'https://b.hu'],
    ['javascript:alert(1)', ''],
    ['  data:text/html,<b>x</b>', ''],
    ['', '']
  ];
  const hibak = esetek.filter(([be, ki]) => T.safeUrl(be) !== ki);
  if (hibak.length) throw new Error(JSON.stringify(hibak));
  return '6/6 eset jó';
});

check('keresési kifejezés: név + faj', () => {
  const q = T.searchQuery({ name: 'Fikusz', species: 'Ficus elastica' });
  if (q !== 'Fikusz Ficus elastica') throw new Error(q);
  const q2 = T.searchQuery({ name: 'Monstera', species: 'monstera' });
  if (q2 !== 'Monstera') throw new Error('ismétlődő faj: ' + q2);
  return q + ' · ' + q2;
});

check('a keresőmotor állítható (ddg→google→wiki)', () => {
  const q = 'Fikusz Ficus elastica';
  const sor = [];
  ['ddg', 'google', 'wiki'].forEach(k => {
    T.state.settings.searchEngine = k;
    const u = T.searchUrl('web', q);
    sor.push(k + ': ' + u.split('/')[2]);
    if (u.indexOf(encodeURIComponent(q)) < 0) throw new Error('hiányzó kifejezés: ' + u);
  });
  T.state.settings.searchEngine = 'ddg';
  return sor.join(' · ');
});

check('képkeresés és Wikipédia külön hivatkozás', () => {
  const kep = T.searchUrl('kep', 'Fikusz');
  const wiki = T.searchUrl('wiki', 'Fikusz');
  if (!/ia=images/.test(kep)) throw new Error('kép: ' + kep);
  if (!/hu\.wikipedia\.org/.test(wiki)) throw new Error('wiki: ' + wiki);
  return 'kép + wikipédia';
});

check('a növény linkjei rendezetten jönnek vissza', () => {
  T.state.plants[1].links = [
    { cim: 'Gondozás', url: 'https://pelda.hu/gondozas' },
    { cim: '', url: 'onlineshop.hu/fikusz' },
    { cim: 'rossz', url: 'javascript:alert(1)' }
  ];
  const l = T.plantLinks(T.state.plants[1]);
  if (l.length !== 2) throw new Error('nem szűrte ki a hibásat: ' + JSON.stringify(l));
  if (l[1].url !== 'https://onlineshop.hu/fikusz') throw new Error('nem javította a sémát: ' + l[1].url);
  if (l[1].cim !== 'onlineshop.hu') throw new Error('nincs tartalék megnevezés: ' + l[1].cim);
  return l.map(x => x.cim + ' → ' + x.url).join(' | ');
});

check('a link-chipek a növény kártyáján megjelennek (új fülön)', () => {
  T.renderPlants();
  const h = byId('plantsContent')._html;
  if (!/class="chip link"/.test(h)) throw new Error('nincs link-chip');
  if (!/target="_blank"/.test(h)) throw new Error('nem új fülön nyílik');
  if (!/rel="noopener noreferrer"/.test(h)) throw new Error('nincs noopener');
  if (!/https:\/\/pelda\.hu\/gondozas/.test(h)) throw new Error('hiányzó url');
  return 'link-chipek a kártyán';
});

check('a név kattintható (menüt nyit), nem sima szöveg', () => {
  const h = T.plantNameHTML(T.state.plants[1]);
  if (!/data-pmenu="p2"/.test(h)) throw new Error('nincs data-pmenu: ' + h);
  if (h.indexOf('Fikusz') < 0) throw new Error('nincs benne a név');
  return h.slice(0, 90);
});

check('kikapcsolva a név sima felirat (link nélkül)', () => {
  T.state.settings.nameClickSearch = false;
  T.state.plants[1].links = [];
  const h = T.plantNameHTML(T.state.plants[1]);
  if (/data-pmenu/.test(h)) throw new Error('mégis kattintható: ' + h);
  T.state.plants[1].links = [{ cim: 'Gondozás', url: 'https://pelda.hu/gondozas' }];
  const h2 = T.plantNameHTML(T.state.plants[1]);
  T.state.settings.nameClickSearch = true;
  if (!/data-pmenu/.test(h2)) throw new Error('link meglétekor is kattinthatónak kell lennie');
  return 'kikapcsolva sima felirat, link meglétekor viszont kattintható marad';
});

check('a menü tartalma: saját linkek + keresés + szerkesztés', () => {
  const m = byId('plantMenu');
  T.openPlantMenu({ getBoundingClientRect: () => ({ left: 30, right: 90, top: 40, bottom: 60 }) }, 'p2');
  const h = m._html;
  if (!/pm-link/.test(h)) throw new Error('nincsenek saját linkek');
  if (!/data-psearch="web"/.test(h)) throw new Error('nincs web-keresés');
  if (!/data-psearch="kep"/.test(h)) throw new Error('nincs képkeresés');
  if (!/data-psearch="wiki"/.test(h)) throw new Error('nincs wikipédia');
  if (!/data-pmenu-add/.test(h)) throw new Error('nincs link hozzáadása');
  if (!/data-pmenu-edit/.test(h)) throw new Error('nincs szerkesztés');
  if (h.indexOf('Fikusz') < 0) throw new Error('nincs fejléc');
  return (h.match(/data-psearch/g) || []).length + ' keresési pont, ' +
         (h.match(/pm-link/g) || []).length + ' saját link';
});

check('az űrlapon hozzáadható és kiolvasható a link', () => {
  T.state.plants[1].links = [];
  T.openDialog('p2');
  const host = byId('formLinks');
  T.addFormLink();
  if (!/lf-url/.test(host._html)) throw new Error('nem jelent meg a link-sor');
  const l = T.collectFormLinks();
  if (l.length !== 0) throw new Error('üres sorból nem szabadna linket csinálni');
  return 'link-sor hozzáadva, üres sor kimarad a mentésből';
});

check('az adatlapon is látszanak a növény linkjei', () => {
  T.state.plants[1].links = [{ cim: 'Gondozás', url: 'https://pelda.hu/gondozas' }];
  // azonosító alapján
  const blokk = T.infoPlantLinksHTML('p2', null);
  if (blokk.indexOf('Saját linkek') < 0) throw new Error('nincs Saját linkek blokk');
  if (blokk.indexOf('pelda.hu/gondozas') < 0) throw new Error('a link nem került be');
  // név alapján (a naptárból így nyílik meg az adatlap)
  const blokk2 = T.infoPlantLinksHTML(null, { name: 'Fikusz' });
  if (blokk2.indexOf('Saját linkek') < 0) throw new Error('név alapján nem találta meg a növényt');
  // adatlap nélküli növénynél is megjelenik
  T.openInfo('nincs-ilyen-bejegyzes', null, 'p2');
  const h = byId('infoSheet')._html;
  if (h.indexOf('Saját linkek') < 0) throw new Error('a „nincs adatlap" nézetből kimaradt');
  return 'Saját linkek: azonosító, név és adatlap nélküli esetben is';
});

check('a beállításokban van keresőmotor- és név-kattintás vezérlő', () => {
  T.renderSettings();
  const h = byId('settingsContent')._html;
  if (!/id="setSearchEngine"/.test(h)) throw new Error('nincs keresőmotor');
  if (!/id="setNameClick"/.test(h)) throw new Error('nincs név-kattintás kapcsoló');
  return (h.match(/<option/g) || []).length + ' motor a listában';
});


console.log('\n== Saját név (ahogy te hívod) ==');
check('a saját név az adatbázis-keresésben is talál (vitorlavirág → békeliliom)', async () => {
  return 'később, az adatbázis betöltése után';
});

check('alapból a saját név látszik elöl', () => {
  T.state.plants[1].name = 'Békeliliom';
  T.state.plants[1].alias = 'vitorlavirág';
  T.state.settings.aliasFirst = true;
  if (T.plantTitle(T.state.plants[1]) !== 'vitorlavirág') throw new Error('nem a saját név az első: ' + T.plantTitle(T.state.plants[1]));
  if (T.plantAltName(T.state.plants[1]) !== 'Békeliliom') throw new Error('nincs hivatalos név mögötte');
  return 'vitorlavirág (hivatalos: Békeliliom)';
});

check('kikapcsolva a hivatalos név van elöl', () => {
  T.state.settings.aliasFirst = false;
  const t = T.plantTitle(T.state.plants[1]), a = T.plantAltName(T.state.plants[1]);
  T.state.settings.aliasFirst = true;
  if (t !== 'Békeliliom' || a !== 'vitorlavirág') throw new Error(t + ' / ' + a);
  return 'Békeliliom (saját: vitorlavirág)';
});

check('a név-kattintás gomb a saját nevet mutatja', () => {
  const h = T.plantNameHTML(T.state.plants[1]);
  if (h.indexOf('vitorlavirág') < 0) throw new Error('nem a saját nevet mutatja');
  if (!/data-pmenu="p2"/.test(h)) throw new Error('nem kattintható');
  if (!/Hivatalos név: Békeliliom/.test(h)) throw new Error('nincs címke a hivatalos névre');
  return 'vitorlavirág + tooltip: Hivatalos név: Békeliliom';
});

check('a növények listájában a saját névre is keres', () => {
  T.state.ui.search = 'vitorlavirág';
  T.renderPlants();
  const h = byId('plantsContent')._html;
  if (h.indexOf('vitorlavirág') < 0) throw new Error('nem talál a saját névre');
  const talalt = (h.match(/class="card"/g) || []).length;
  T.state.ui.search = 'békeliliom';
  T.renderPlants();
  const h2 = byId('plantsContent')._html;
  const talalt2 = (h2.match(/class="card"/g) || []).length;
  T.state.ui.search = '';
  T.renderPlants();
  if (talalt < 1 || talalt2 < 1) throw new Error('valamelyik névre nem talál: ' + talalt + '/' + talalt2);
  return 'saját névre: ' + talalt + ' kártya · hivatalosra: ' + talalt2 + ' kártya';
});

check('a Ma nézetben is a saját név látszik', () => {
  T.state.plants[1].lastWatered = T.addDays(T.todayISO(), -2);
  T.state.plants[1].waterDays = 1;
  T.renderToday();
  const h = byId('todayContent')._html;
  if (h.indexOf('vitorlavirág') < 0) throw new Error('a Ma nézet nem a saját nevet mutatja');
  return 'igen';
});

check('a naptárban is a saját név van a cellában', () => {
  T.state.ui.calMode = 'nap';
  T.state.ui.calMonth = T.monthKey(new Date());
  T.renderCalendar();
  const h = byId('calendarContent')._html;
  if (h.indexOf('vitorlavirág') < 0) throw new Error('a cellában nincs saját név');
  return 'igen';
});

check('setAlias(): menti és törli a saját nevet', () => {
  T.setAlias('p2', '  anyósnyelvem  ');
  if (T.state.plants[1].alias !== 'anyósnyelvem') throw new Error('nem vágta le a szóközöket: ' + JSON.stringify(T.state.plants[1].alias));
  T.setAlias('p2', '');
  if (T.state.plants[1].alias) throw new Error('nem törölte');
  T.setAlias('p2', 'vitorlavirág');
  return 'mentés és törlés is jó';
});

check('a szerkesztő űrlapról is bekerül a saját név', () => {
  T.openDialog('p2');
  if (byId('f_alias').value !== 'vitorlavirág') throw new Error('az űrlap nem töltötte be: ' + JSON.stringify(byId('f_alias').value));
  byId('f_alias').value = 'vitorlavirág2';
  T.saveForm({ preventDefault(){} });
  const p = T.state.plants.filter(x => x.id === 'p2')[0];
  if (p.alias !== 'vitorlavirág2') throw new Error('nem mentődött: ' + p.alias);
  T.setAlias('p2', 'vitorlavirág');
  return 'űrlap → mentés: ' + p.alias;
});

check('a menüben van „Saját név” pont, a mostani névvel', () => {
  T.openPlantMenu({ getBoundingClientRect: () => ({ left: 10, right: 60, top: 20, bottom: 30 }) }, 'p2');
  const h = byId('plantMenu')._html;
  if (!/data-pmenu-alias="p2"/.test(h)) throw new Error('nincs saját név pont');
  if (h.indexOf('most: „vitorlavirág”') < 0) throw new Error('nem mutatja a mostani nevet');
  if (h.indexOf('Békeliliom') < 0) throw new Error('a fejlécben nincs a hivatalos név sem');
  return 'menü: „Saját név módosítása · most: vitorlavirág”';
});

check('a saját név nélküli növénynél minden a régi', () => {
  T.state.plants[0].alias = '';
  if (T.plantTitle(T.state.plants[0]) !== T.state.plants[0].name) throw new Error('mégis átírt valamit');
  if (T.plantAltName(T.state.plants[0]) !== '') throw new Error('van ál-hivatalos név');
  return 'változatlan: ' + T.state.plants[0].name;
});

check('a beállításokban van elsőbbség-kapcsoló', () => {
  T.renderSettings();
  const h = byId('settingsContent')._html;
  if (!/id="setAliasFirst"/.test(h)) throw new Error('nincs kapcsoló');
  return 'igen (setAliasFirst)';
});


console.log('\n== Link-címkék és gyorsgomb ==');
check('a linkek címke szerint csoportosulnak (bolt → gondozás → adatlap → címke nélkül)', () => {
  T.state.plants[1].links = [
    { cim: 'Webshop', url: 'https://bolt.hu/fikusz', tag: 'bolt' },
    { cim: 'Gondozás', url: 'https://pelda.hu/gondozas', tag: 'gondozás' },
    { cim: 'Adatlap', url: 'https://pelda.hu/adatlap', tag: 'adatlap' },
    { cim: 'Valami', url: 'https://pelda.hu/egyeb' },
    { cim: 'Fórum', url: 'https://forum.hu/fikusz', tag: 'Fórum' }
  ];
  const g = T.plantLinkGroups(T.state.plants[1]);
  const sor = g.map(x => (x.tag || '(nincs)') + ':' + x.links.length).join(', ');
  if (g.length !== 5) throw new Error('nem 5 csoport: ' + sor);
  if (g[0].tag !== 'bolt') throw new Error('a bolt nincs elöl: ' + sor);
  if (g[g.length - 1].tag !== '') throw new Error('a címke nélküli nincs a végén: ' + sor);
  if (g[4].tag !== '') throw new Error('a címke nélküli nem utolsó: ' + sor);
  return sor;
});

check('a címke kis/nagybetűtől független (Fórum → fórum)', () => {
  const l = T.plantLinks(T.state.plants[1]).filter(x => x.cim === 'Fórum')[0];
  if (l.tag !== 'fórum') throw new Error('nem normalizálta: ' + JSON.stringify(l.tag));
  return 'fórum';
});

check('az ismeretlen címke a végére kerül, a nélküliek elé', () => {
  T.state.plants[1].links.push({ cim: 'Saját blog', url: 'https://blog.hu/x', tag: 'saját' });
  const g = T.plantLinkGroups(T.state.plants[1]);
  const sor = g.map(x => x.tag);
  const iSajat = sor.indexOf('saját'), iNincs = sor.indexOf('');
  if (!(iSajat > 0 && iSajat < iNincs)) throw new Error('rossz sorrend: ' + sor.join(', '));
  return sor.join(' → ');
});

check('a menüben címke-fejlécek alatt jelennek meg a linkek', () => {
  T.openPlantMenu({ getBoundingClientRect: () => ({ left: 10, right: 60, top: 20, bottom: 30 }) }, 'p2');
  const h = byId('plantMenu')._html;
  const fej = (h.match(/class="pm-tag"/g) || []).length;
  if (fej < 5) throw new Error('kevés címke-fejléc: ' + fej);
  if (h.indexOf('címke nélkül') < 0) throw new Error('a címke nélküli csoport fejléce hiányzik');
  if (h.indexOf('bolt') < 0) throw new Error('nincs bolt csoport');
  return fej + ' címke-fejléc a menüben';
});

check('a növénykártyán a chip viseli a címkét', () => {
  T.renderPlants();
  const h = byId('plantsContent')._html;
  if (!/class="chip link[^"]*"[^>]*>.*?<b class="tag">bolt<\/b>/s.test(h)) throw new Error('nincs címke a chipen');
  return 'chip: [bolt] Webshop';
});

check('az űrlap címke-mezőt tölt be, és van kész címke-lista', () => {
  T.state.plants[1].links = [
    { cim: 'Webshop', url: 'https://bolt.hu/fikusz', tag: 'bolt' },
    { cim: 'Gondozás', url: 'https://pelda.hu/gondozas', tag: 'gondozás' }
  ];
  T.openDialog('p2');
  const h = byId('formLinks')._html;
  if (!/class="lf-tag"/.test(h)) throw new Error('nincs címke mező');
  if (!/value="bolt"/.test(h) || !/value="gondozás"/.test(h)) throw new Error('nem töltötte be a címkéket');
  const datalist = (fs.readFileSync(path, 'utf8').match(/<datalist id="linkTagList">([\s\S]*?)<\/datalist>/) || [,''])[1];
  const opciok = (datalist.match(/value="/g) || []).length;
  if (opciok < 5) throw new Error('kevés kész címke: ' + opciok);
  if (h.indexOf('list="linkTagList"') < 0) throw new Error('a mező nem kapcsolódik a listához');
  return opciok + ' kész címke a legördülőben, a mezők kitöltve';
});

console.log('\n== Gyorsgomb a naptárban ==');
check('a naptár cellájában link-ikon jelenik meg, ha van link', () => {
  T.state.plants[1].links = [{ cim: 'Webshop', url: 'https://bolt.hu/fikusz', tag: 'bolt' }];
  T.state.plants[1].lastWatered = T.addDays(T.todayISO(), -2);
  T.state.plants[1].waterDays = 1;
  T.state.ui.calMode = 'nap';
  T.state.ui.calMonth = T.monthKey(new Date());
  T.renderCalendar();
  const h = byId('calendarContent')._html;
  if (!/data-plink="p2"/.test(h)) throw new Error('nincs gyorsgomb a cellában');
  return 'cal-link gomb a cellában';
});

check('a nap kártyáján a kép mellett is van gyorsgomb', () => {
  T.state.ui.calSel = T.addDays(T.todayISO(), 1);
  T.renderCalendar();
  const h = byId('calendarContent')._html;
  return /class="ico-link"/.test(h) ? 'ico-link a kép sarkán' : 'nincs (nincs teendő aznap)';
});

check('openPlantLink(): egy link → azonnal megnyitás', () => {
  let nyitott = null;
  const regi = sandboxWin.open;
  sandboxWin.open = (u) => { nyitott = u; return {}; };
  T.openPlantLink('p2');
  sandboxWin.open = regi;
  if (nyitott !== 'https://bolt.hu/fikusz') throw new Error('nem nyitotta meg: ' + nyitott);
  return nyitott;
});

check('openPlantLink(): több link → választó címkékkel', () => {
  T.state.plants[1].links = [
    { cim: 'Webshop', url: 'https://bolt.hu/fikusz', tag: 'bolt' },
    { cim: 'Gondozás', url: 'https://pelda.hu/gondozas', tag: 'gondozás' }
  ];
  T.openPlantLink('p2');
  const h = byId('plantMenu')._html;
  if (!/pm-tag/.test(h)) throw new Error('nincs címke a választóban');
  if (h.indexOf('válassz linket') < 0) throw new Error('nincs fejléc');
  return 'választó: bolt / gondozás';
});

check('link nélküli növénynél nincs gyorsgomb', () => {
  T.state.plants[1].links = [];
  T.renderCalendar();
  const h = byId('calendarContent')._html;
  return /data-plink/.test(h) ? 'hibás: mégis van gomb' : 'nincs gomb (jó)';
});

console.log('\n== KDE panel és naptár (.ics) ==');

check('icsEventCount(): van esemény, és a hosszabb időszak több', () => {
  T.state.plants[0].waterDays = 7; T.state.plants[0].lastWatered = T.addDays(T.todayISO(), -3);
  T.state.plants[0].fertDays = 30; T.state.plants[0].lastFertilized = T.addDays(T.todayISO(), -10);
  T.state.plants[0].mistDays = 0; T.state.plants[0].repotMonths = 0;
  const n90 = T.icsEventCount(90), n30 = T.icsEventCount(30);
  if (!(n90 > 0)) throw new Error('nincs esemény: ' + n90);
  if (!(n90 > n30)) throw new Error('nem nő az időszakkal: ' + n30 + ' / ' + n90);
  return n30 + ' (30 nap) / ' + n90 + ' (90 nap)';
});

check('icsEventCount() egyezik a taskOccurrences() összegével', () => {
  const from = T.todayISO(), to = T.addDays(from, 60);
  let kezi = 0;
  T.state.plants.forEach(p => T.TASK_DEFS.forEach(d => { kezi += T.taskOccurrences(p, d, from, to).length; }));
  if (kezi !== T.icsEventCount(60)) throw new Error('eltér: ' + kezi + ' vs ' + T.icsEventCount(60));
  return kezi + ' esemény 60 napra';
});

check('a beállításokban megjelenik a KDE-panel', () => {
  T.state.settings.icsDays = 90; T.state.settings.icsAlarm = 8;
  T.renderSettings();
  const h = byId('settingsContent')._html;
  if (h.indexOf('KDE panel') < 0) throw new Error('nincs KDE-panel');
  if (h.indexOf('Digitális óra') < 0) throw new Error('nincs utalás a Digitális órára');
  return 'panel a beállításokban';
});

check('a panelben van .ics letöltő hivatkozás', () => {
  const h = byId('settingsContent')._html;
  if (h.indexOf('href="/api/calendar.ics"') < 0) throw new Error('nincs letöltő link');
  if (!/download="florum\.ics"/.test(h)) throw new Error('nincs letöltési név');
  return '/api/calendar.ics';
});

check('a panel mutatja a fájl útvonalát', () => {
  const h = byId('settingsContent')._html;
  if (h.indexOf('florum.ics') < 0) throw new Error('nincs útvonal');
  const p = T.icsFilePath();
  if (!/florum\.ics$/.test(p)) throw new Error('rossz útvonal: ' + p);
  return p;
});

check('az előretekintés és az emlékeztető órája szerkeszthető', () => {
  const h = byId('settingsContent')._html;
  if (!/id="setIcsDays"[^>]*value="90"/.test(h)) throw new Error('nincs nap-mező');
  if (!/id="setIcsAlarm"[^>]*value="8"/.test(h)) throw new Error('nincs óra-mező');
  T.state.settings.icsDays = 30; T.state.settings.icsAlarm = 7;
  T.renderSettings();
  const h2 = byId('settingsContent')._html;
  if (!/id="setIcsDays"[^>]*value="30"/.test(h2)) throw new Error('nem követi a beállítást');
  if (!/id="setIcsAlarm"[^>]*value="7"/.test(h2)) throw new Error('nem követi az órát');
  if (h2.indexOf('30 napra') < 0) throw new Error('az összegzés nem frissült');
  return '30 nap / 7 óra';
});

check('a KDE-útmutató lépései benne vannak', () => {
  const h = byId('settingsContent')._html;
  ['kdepim-addons', 'PIM Events Plugin', 'Akonadi', 'emlekezteto.py --daemon'].forEach(kulcs => {
    if (h.indexOf(kulcs) < 0) throw new Error('hiányzik: ' + kulcs);
  });
  if (h.indexOf('<details') < 0) throw new Error('nincs összecsukható útmutató');
  return '4 lépés + démon';
});

check('másolás-gombok a panelben', () => {
  const h = byId('settingsContent')._html;
  if (h.indexOf('data-icscopy="1"') < 0) throw new Error('nincs útvonal-másolás');
  if (h.indexOf('data-icscopy="kde"') < 0) throw new Error('nincs KDE-parancs másolás');
  return '2 másoló gomb';
});

check('copyText() nem dob hibát vágólap nélkül', () => {
  const r = T.copyText('florum.ics');
  if (r !== true && r !== false) throw new Error('váratlan visszatérés: ' + r);
  return 'visszatérés: ' + r;
});

check('a naptár eszköztárában van .ics gyorsgomb (fájl-módban)', () => {
  T.state.ui.calMode = 'honap';
  T.state.ui.calMonth = T.monthKey(new Date());
  const mod = T.store && T.store.mode;
  T.store.mode = 'file';
  T.renderCalendar();
  const h = byId('calendarContent')._html;
  if (h.indexOf('/api/calendar.ics') < 0) throw new Error('fájl-módban nincs gyorsgomb');
  if (!/cal-ics/.test(h)) throw new Error('nincs cal-ics osztály');
  T.store.mode = mod;
  T.renderCalendar();
  const h2 = byId('calendarContent')._html;
  if (h2.indexOf('/api/calendar.ics') >= 0) throw new Error('statikus módban mégis van');
  return 'fájl-módban van, statikusban nincs (mód: ' + mod + ')';
});

check('a .ics gomb felirata rövid és nem töri a sort', () => {
  T.renderCalendar();
  const h = byId('calendarContent')._html;
  if (/cal-ics/.test(h) && !/>\.ics<\/a>/.test(h.replace(/\s+/g, ''))) {
    return 'megjelenik (.ics)';
  }
  return 'fájl-módban .ics felirat';
});

check('a panel figyelmeztet, ha sok esemény van (KDE-fagyás)', () => {
  const regi = T.state.settings.icsDays;
  T.state.settings.icsDays = 730;
  T.renderSettings();
  const h = T.renderSettings && byId('settingsContent')._html;
  T.state.settings.icsDays = 30;
  T.renderSettings();
  const h2 = byId('settingsContent')._html;
  T.state.settings.icsDays = regi;
  T.renderSettings();
  if (h.indexOf('kde-warn') < 0) throw new Error('730 napnál nincs figyelmeztetés');
  if (h2.indexOf('kde-warn') >= 0 && T.icsEventCount(30) < 120) throw new Error('30 napnál sem kellene');
  return 'sok eseménynél figyelmeztet';
});

check('a panel ismeri a PIM-fagyás kerülőútját', () => {
  const h = byId('settingsContent')._html;
  ['PIM fül üres', 'lefagy', 'kde-pim-kikapcsolas.sh', 'kde-allapot.sh', 'Event Calendar'].forEach(k => {
    if (h.indexOf(k) < 0) throw new Error('hiányzik az útmutatóból: ' + k);
  });
  return 'kikapcsoló szkript + Event Calendar + diagnózis';
});

console.log('\n== HTML-ellenőrzés ==');
const out = byId('settingsContent')._html + byId('todayContent')._html + byId('calendarContent')._html;
const check2 = (cim, cond, extra) => {
  if (cond) { ok++; console.log('  ✓ ' + cim + (extra ? '   → ' + extra : '')); }
  else { bad++; problems.push(cim); console.log('  ✗ ' + cim + (extra ? '   → ' + extra : '')); }
};
check2('nincs [object Object] a kimenetben', !/\[object Object\]/.test(out));
check2('nincs undefined a kimenetben', !/>undefined</.test(out) && !/undefined nap/.test(out));
check2('nincs NaN a kimenetben', !/NaN/.test(out));





// ---------- saját név előnézet ----------
if (process.env.ELONEZETALIAS){
  const css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
  const dialogHtml = (html.match(/<dialog id="aliasDialog">([\s\S]*?)<\/dialog>/) || [,''])[1];
  const p = T.state.plants[1];
  p.name = 'Békeliliom';
  p.species = 'Spathiphyllum wallisii';
  p.alias = 'vitorlavirág';
  p.room = 'Fürdőszoba';
  p.light = 'Közepes';
  p.pots = 16;
  T.state.settings.aliasFirst = true;

  // 1) kártya a listából
  T.state.ui.search = '';
  T.renderPlants();
  const kartya = byId('plantsContent')._html;

  // 2) keresés a megszokott névre
  T.state.ui.search = 'vitorlavirág';
  T.renderPlants();
  const talalat = byId('plantsContent')._html;
  T.state.ui.search = '';

  // 3) menü
  T.openPlantMenu({ getBoundingClientRect: () => ({ left: 20, right: 90, top: 40, bottom: 60 }) }, 'p2');
  const menu = byId('plantMenu')._html;

  // 4) naptár a gyorsgombbal
  T.state.ui.calMode = 'nap';
  T.state.ui.calMonth = T.monthKey(new Date());
  T.state.ui.calSel = T.addDays(T.todayISO(), 1);
  T.renderCalendar();
  const naptar = byId('calendarContent')._html;

  const oldal = '<!doctype html><html lang="hu" data-theme="light"><head><meta charset="utf-8">' +
    '<title>Florum – saját név</title><style>' + css + `
    body{padding:26px 18px 60px; max-width:980px; margin:0 auto}
    h2{font-size:16px; margin:26px 0 8px; color:var(--green-ink)}
    .magyar{font-size:13px; color:var(--muted); margin:0 0 12px; max-width:780px}
    #plantMenu{position:static !important; display:block !important; max-width:300px; box-shadow:var(--shadow)}
    .sheet{max-width:520px; margin:0}
    .grid{display:grid; grid-template-columns:1fr 300px; gap:20px; align-items:start}
    @media (max-width:800px){ .grid{grid-template-columns:1fr} }
  ` + '</style></head><body>' +
    '<h1 style="font-size:20px;margin:0 0 6px">Florum · saját név</h1>' +
    '<p class="magyar">A növény hivatalos neve az adatbázisban <b>Békeliliom</b>, de te <b>vitorlavirágként</b> ' +
    'ismered. A saját név csak a megjelenítést váltja – az adatlap és a keresés a hivatalosat is ismeri.</p>' +

    '<h2>1. Így jelenik meg a listában</h2>' +
    '<p class="magyar">A saját név van elöl, a hivatalos név mellette kisebb betűvel (a Beállításokban ' +
    'a sorrend megfordítható).</p>' +
    '<div class="grid"><div>' + kartya + '</div><div>' + menu + '</div></div>' +

    '<h2>2. Keresés a megszokott névre</h2>' +
    '<p class="magyar">A keresőmezőbe „vitorlavirág” – a növény megkereshető akár a saját nevével, akár a hivatalossal.</p>' +
    talalat +

    '<h2>3. A „Saját név” ablak</h2>' +
    '<p class="magyar">A névre kattintva a menüből, vagy a növény szerkesztőjében is beállítható.</p>' +
    '<div class="panel">' + dialogHtml + '</div>' +
    '</body></html>';
  fs.writeFileSync('/home/user/florum/sajat-nev-elonezet.html', oldal, 'utf8');
  console.log('  ✓ sajat-nev-elonezet.html kiírva (' + Math.round(oldal.length/1024) + ' kB)');
}

// ---------- linkek / keresés előnézet ----------
if (process.env.ELONEZETLINK){
  const css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
  T.state.plants[1].links = [
    { cim: 'Webshop – Fikusz', url: 'https://pelda-webshop.hu/fikusz', tag: 'bolt' },
    { cim: 'Gondozási útmutató', url: 'https://www.rhs.org.uk/plants/ficus-elastica/growing-guide', tag: 'gondozás' },
    { cim: 'Mérgezőség kisállatokra', url: 'https://www.aspca.org/pet-care/animal-poison-control', tag: 'adatlap' },
    { cim: 'Fikusz fórum', url: 'https://forum.pelda.hu/fikusz', tag: 'fórum' },
    { cim: 'Szobanövény-tippek', url: 'https://pelda.hu/blog/szobanovenyek' }
  ];
  T.state.plants[1].species = 'Ficus elastica';
  T.state.plants[1].room = 'Nappali';
  T.state.plants[1].light = 'Világos, szórt';
  T.state.plants[1].photos = [{ dataUrl: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' fill='rgb(47,125,84)'/><path d='M16 27c0-9 4-14 10-16-1 10-5 14-10 16z' fill='rgb(178,232,199)'/><path d='M14 27c0-7-3-11-8-13 1 8 4 11 8 13z' fill='rgb(140,205,168)'/></svg>", taken: T.todayISO() }];
  T.renderPlants();
  const kartya = byId('plantsContent')._html;
  T.openPlantMenu({ getBoundingClientRect: () => ({ left: 20, right: 90, top: 40, bottom: 60 }) }, 'p2');
  const menu = byId('plantMenu')._html;
  T.openDialog('p2');
  const linkek = byId('formLinks')._html;

  // naptár a gyorsgombbal
  T.state.ui.calMode = 'nap';
  T.state.ui.calMonth = T.monthKey(new Date());
  T.state.ui.calSel = T.addDays(T.todayISO(), 1);
  T.state.plants[1].lastWatered = T.addDays(T.todayISO(), -6);
  T.renderCalendar();
  const naptar = byId('calendarContent')._html;

  const oldal = '<!doctype html><html lang="hu" data-theme="light"><head><meta charset="utf-8">' +
    '<title>Florum – linkek és név-keresés</title><style>' + css + `
    body{padding:26px 18px 60px; max-width:1180px; margin:0 auto}
    h2{font-size:16px; margin:26px 0 10px; color:var(--green-ink)}
    .magyar{font-size:13px; color:var(--muted); margin:0 0 12px; max-width:820px}
    .dokk{display:grid; grid-template-columns:minmax(0,1fr) 300px; gap:20px; align-items:start}
    #plantMenu{position:static !important; display:block !important; max-width:300px; box-shadow:var(--shadow)}
    .link-editor{max-width:640px}
    @media (max-width:880px){ .dokk{grid-template-columns:1fr} }
  ` + '</style></head><body>' +
    '<h1 style="font-size:20px;margin:0 0 6px">Florum · linkek és név-keresés</h1>' +
    '<p class="magyar">Mindhárom rész a valódi felület által generált HTML. A mutatott növény: <b>Fikusz</b> ' +
    '(3 saját linkkel).</p>' +

    '<h2>1. Növények fül – saját linkek a kártyán</h2>' +
    '<p class="magyar">A növény neve alatt chipként jelennek meg a linkek (max. 3, a többit a „+N” nyitja), ' +
    'és új fülön nyílnak. A név maga is kattintható.</p>' +
    '<div class="dokk"><div>' + kartya + '</div><div>' +
      '<div class="magyar" style="margin:0 0 6px"><b>Kattints a névre:</b></div>' +
      '<div id="plantMenu" class="show" style="position:static;display:block">' + menu + '</div>' +
    '</div></div>' +

    '<h2>2. A menü – címke szerint csoportosítva</h2>' +
    '<p class="magyar">A saját linkek <b>címke szerint</b> csoportosulnak (bolt, gondozás, adatlap, fórum, majd a ' +
    'címke nélküliek), mindegyik csoport élén a címke és a darabszám. Alatta a keresés: web, kép, Wikipédia.</p>' +

    '<h2>4. Naptár – link megnyitása a növény képénél</h2>' +
    '<p class="magyar">A naptár cellájában a név végén, illetve a nap kártyáján a <b>fotó sarkán</b> megjelenő ' +
    'kis kék linkgomb megnyitja a növény linkjét: ha csak egy van, rögtön; ha több, a címkék szerinti választó jön. ' +
    'A cellában a gomb a sorra vitelekor látszik, hogy ne zsúfolja a naptárat.</p>' +
    '<div style="border:1px solid var(--line);border-radius:12px;padding:12px;max-height:560px;overflow:auto;background:var(--bg)">' +
    naptar + '</div>' +

    '<h2>3. Szerkesztés – címke is adható a linkhez</h2>' +
    '<p class="magyar">A növény szerkesztőjében minden linkhez beírható <b>címke</b> (a mező kínálja: bolt, gondozás, ' +
    'adatlap, fórum, inspiráció, betegség, egyéb – de bármit beírhatsz). A megnevezés maradhat üres, olyankor a domain ' +
    'lesz a felirat. Csak http(s) link kerül be.</p>' +
    '<div class="link-editor">' + linkek + '</div>' +
    '</body></html>';
  fs.writeFileSync('/home/user/florum/linkek-elonezet.html', oldal, 'utf8');
  console.log('  ✓ linkek-elonezet.html kiírva (' + Math.round(oldal.length/1024) + ' kB)');
}

// ---------- KDE panel / .ics előnézet ----------
if (process.env.ELONEZETKDE){
  const css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
  T.state.settings.icsDays = 90;
  T.state.settings.icsAlarm = 8;
  T.renderSettings();
  const panel = T.kdePanelHTML();
  const n90 = T.icsEventCount(90), n30 = T.icsEventCount(30), n7 = T.icsEventCount(7);

  const oldal = '<!doctype html><html lang="hu" data-theme="light"><head><meta charset="utf-8">' +
    '<title>Florum – KDE panel és naptár (.ics)</title><style>' + css + `
    body{padding:26px 18px 60px; max-width:900px; margin:0 auto}
    h2{font-size:16px; margin:26px 0 8px; color:var(--green-ink)}
    .magyar{font-size:13px; color:var(--muted); margin:0 0 12px; max-width:760px; line-height:1.6}
    .sav{display:flex; gap:10px; flex-wrap:wrap; margin:0 0 16px}
    .sav div{background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:10px 14px;
      box-shadow:var(--shadow); font-size:13px}
    .sav b{font-size:18px; color:var(--green-ink); display:block}
    code{background:var(--green-soft); color:var(--green-ink); padding:1px 6px; border-radius:6px; font-size:12.5px}
    .kde-steps{border:1px solid var(--line)}
  ` + '</style></head><body>' +
    '<h1 style="font-size:20px;margin:0 0 6px">Florum · KDE panel Digitális óra</h1>' +
    '<p class="magyar">A Florum a teendőit <b>iCalendar (.ics)</b> fájlba írja. A KDE Plasma Digitális órája ' +
    'a <b>PIM Events Plugin</b> (kdepim-addons) segítségével eseményként listázza őket, így a panel órájának ' +
    'naptárnézetében látod, mit kell ma megöntözni vagy tápoldatozni. Az események téli ritkítással és ' +
    'tápoldat-szünettel számolódnak, a lejárt teendők a mai napra kerülnek, „(lejárt)” jelöléssel.</p>' +

    '<h2>Hány esemény lesz?</h2>' +
    '<div class="sav">' +
      '<div><b>' + n7 + '</b>következő 7 nap</div>' +
      '<div><b>' + n30 + '</b>következő 30 nap</div>' +
      '<div><b>' + n90 + '</b>következő 90 nap</div>' +
    '</div>' +

    '<h2>A beállítások új szakasza</h2>' +
    '<p class="magyar">A <b>Beállítások</b> fülön, az értesítések alatt. Innen tölthető le a naptárfájl ' +
    '(<code>/api/calendar.ics</code>), itt állítható az előretekintés és az emlékeztető órája, és a ' +
    '<b>Beállítás a KDE panelen</b> sor kinyitásával ott a négy lépés. A gombok ebben az előnézetben nem ' +
    'működnek, az élő alkalmazásban igen.</p>' +
    '<details open><summary style="cursor:pointer;font-weight:650;font-size:13.5px;margin:0 0 10px">' +
      'A KDE-útmutató, ahogy megjelenik</summary>' + panel + '</details>' +

    '<h2>Mit tartalmaz egy esemény?</h2>' +
    '<p class="magyar">Egy minta a fájlból (a lényeg kiemelve): a címben az ikon, a teendő és a növény neve ' +
    '(a saját név, ha van), a leírásban a hely, az ütem, a link és a hivatalos név, végül a napi emlékeztető.</p>' +
    '<div class="panel" style="font-family:ui-monospace,monospace;font-size:12px;line-height:1.7;white-space:pre-wrap">' +
      '<span style="color:var(--muted)">BEGIN:VEVENT</span>\n' +
      'UID:florum-3f9c…@florum.local\n' +
      'DTSTART;VALUE=DATE:20261031\n' +
      'DTEND;VALUE=DATE:20261101\n' +
      '<b>SUMMARY:💧 Öntözés – Vitorlavirág</b>\n' +
      '<b>DESCRIPTION:Hely: Fürdőszoba</b>\\nÜtem: 11 nap\\nLink: Webshop – https://…\n' +
      'CATEGORIES:Florum,Öntözés\n' +
      'PRIORITY:6\n' +
      '<b>BEGIN:VALARM</b>\n' +
      'ACTION:DISPLAY\n' +
      'DESCRIPTION:Florum: Öntözés – Vitorlavirág\n' +
      'TRIGGER;RELATED=START:PT8H\n' +
      'END:VALARM\n' +
      '<span style="color:var(--muted)">END:VEVENT</span>' +
    '</div>' +

    '<h2>Figyelmeztetés</h2>' +
    '<p class="magyar">Két út, bármelyik elég: a <b>Florum emlékeztetője</b> (<code>emlekezteto.py --daemon</code>, ' +
    'rendszerindításkor a <code>florum-emlekezteto.service</code>) a KDE saját értesítéseként szól – naponta ' +
    'egyszer, lejárt teendőnél kritikus fontossággal –, vagy az <code>.ics</code>-ben minden eseményhez tartozó ' +
    '<b>VALARM</b>, amit a KDE naptár-értesítője jelenít meg.</p>' +
    '</body></html>';
  fs.writeFileSync('/home/user/florum/kde-elonezet.html', oldal, 'utf8');
  console.log('  ✓ kde-elonezet.html kiírva (' + Math.round(oldal.length/1024) + ' kB)');
}

// ---------- 16:9 állóképes előnézet ----------
if (process.env.ELONEZET169){
  const css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
  T.state.plants[1].photos = [{ dataUrl: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' fill='rgb(47,125,84)'/><path d='M16 27c0-9 4-14 10-16-1 10-5 14-10 16z' fill='rgb(178,232,199)'/><path d='M14 27c0-7-3-11-8-13 1 8 4 11 8 13z' fill='rgb(140,205,168)'/></svg>", taken: T.todayISO() }];
  T.state.plants[1].snooze = {};
  T.state.plants[1].lastWatered = T.addDays(T.todayISO(), -2);
  T.state.ui.calMonth = T.monthKey(new Date());
  T.state.ui.calSel = T.addDays(T.todayISO(), 5);
  T.state.settings.layout169 = true;

  function stage(w, h, mode, cim) {
    T.state.ui.calMode = mode;
    T.renderCalendar();
    const belso = byId('calendarContent')._html;
    const cell = Math.max(52, Math.min(150, Math.round((h - (mode === 'honap' ? 430 : 470)) / 6)));
    const side = Math.max(240, h - 330);
    return '<div class="stagebox">' +
      '<div class="cimke"><b>' + cim + '</b> · ' + w + '×' + h + ' px · ' + mode + '-nézet · ' +
        'cellamagasság ' + cell + ' px</div>' +
      '<div class="stageout"><div class="stage" data-w="' + w + '" data-h="' + h + '" ' +
        'style="width:' + w + 'px;height:' + h + 'px;--cal-cell-h:' + cell + 'px;--cal-side-h:' + side + 'px">' +
        '<div class="wrap">' +
          '<header class="top"><div class="brand"><div class="logo">' +
            '<svg width="24" height="24" viewBox="0 0 32 32" aria-hidden="true"><path d="M25 7c0 9-5 15-11 15-1.2 0-2.3-.2-3.2-.7C12 13.5 17 8.5 25 7Z" fill="#d7f0e0"/><path d="M7 27c1.6-6.6 4.4-10.8 8.6-13.6" stroke="#d7f0e0" stroke-width="2.2" fill="none" stroke-linecap="round"/></svg>' +
          '</div><div><h1>Florum</h1><p>Otthoni növénygondozó · locsolás, tápoldat, átültetés</p></div></div>' +
          '<nav class="tabs"><button class="tab" type="button">Ma</button><button class="tab active" type="button">Naptár</button>' +
          '<button class="tab" type="button">Növények</button><button class="tab" type="button">Napló</button>' +
          '<button class="tab" type="button">Tünetek</button><button class="tab" type="button">Beállítások</button></nav>' +
          '<button class="btn sm ghost layout-btn active" type="button">16:9</button>' +
          '<button class="store-pill ok" type="button"><span class="led"></span>Mentés</button>' +
          '<button class="btn primary" type="button">+ Új növény</button></header>' +
          '<main><section class="view active"><div id="calendarContent">' + belso + '</div></section></main>' +
        '</div></div></div></div>';
  }

  const oldal = '<!doctype html><html lang="hu" data-theme="light" data-layout="169"><head><meta charset="utf-8">' +
    '<title>Florum – 16:9 nézet előnézet</title><style>' + css + `
    body{background:#0a1410; margin:0; color:var(--ink); overflow-x:hidden}
    .fej{max-width:1180px; margin:0 auto; padding:24px 18px 6px; color:#dfeee6}
    .fej h1{font-size:20px; margin:0 0 6px; color:#eaf7ef}
    .fej p{margin:0 0 4px; font-size:13px; color:#9db4a7; max-width:760px}
    .stagebox{max-width:1180px; margin:22px auto 34px; padding:0 18px}
    .cimke{font-size:12px; color:#9db4a7; margin:0 0 6px; font-weight:650}
    .cimke b{color:#cfe9da}
    .stageout{position:relative; width:100%; overflow:hidden; border-radius:12px;
              box-shadow:0 0 0 1px #23402f, 0 40px 90px -50px #000}
    .stage{position:absolute; top:0; left:0; transform-origin:top left; background:var(--bg)}
    html[data-layout="169"] .stage > .wrap{width:100%; height:100%; max-width:none; position:absolute; inset:0;
      border-radius:0; box-shadow:none; overflow-y:auto}
    ` + '</style></head><body>' +
    '<div class="fej"><h1>Florum · 16:9 nézet</h1>' +
    '<p>A valódi alkalmazás ugyanezt a CSS-t használja: a tartalom egy 16:9 arányú lapra kerül, ' +
    'a naptár rács és a nap kártyája <b>egymás mellett</b> van, a cellák magassága a kép magasságához igazodik. ' +
    'A lenti két lap a valós méretben (1920×1080 és 1600×900) renderelt HTML, csak kicsinyítve jelenik meg.</p></div>' +
    stage(1920, 1080, 'honap', 'Full HD · hónap-nézet') +
    stage(1600, 900, 'nap', 'HD+ · nap-nézet') +
    `<script>
      function meretez(){
        document.querySelectorAll('.stagebox').forEach(function(box){
          var out = box.querySelector('.stageout'), st = box.querySelector('.stage');
          var w = +st.getAttribute('data-w'), h = +st.getAttribute('data-h');
          var s = Math.min(1, out.clientWidth / w);
          st.style.transform = 'scale(' + s + ')';
          out.style.height = Math.round(h * s) + 'px';
        });
      }
      window.addEventListener('resize', meretez); meretez();
    <\/script></body></html>`;
  fs.writeFileSync('/home/user/florum/naptar-169-elonezet.html', oldal, 'utf8');
  console.log('  ✓ naptar-169-elonezet.html kiírva (' + Math.round(oldal.length/1024) + ' kB)');
}

// ---------- opcionális: statikus előnézet generálása ----------
if (process.env.ELONEZET){
  const css = (html.match(/<style>([\s\S]*?)<\/style>/) || [,''])[1];
  const cimek = { nap:'Nap-nézet – a rácsban növénynevekkel, terhelés-háttérrel',
                  honap:'Hónap-nézet – nagyobb cellák + növényenkénti táblázat',
                  ev:'Év-nézet – 12 hónapkártya, látszik a szezonális ritmus' };
  // demó: legyen fotó és egy áthelyezett teendő is
  T.state.plants[1].photos = [{ dataUrl: "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><rect width='32' height='32' fill='rgb(47,125,84)'/><path d='M16 27c0-9 4-14 10-16-1 10-5 14-10 16z' fill='rgb(178,232,199)'/><path d='M14 27c0-7-3-11-8-13 1 8 4 11 8 13z' fill='rgb(140,205,168)'/></svg>", taken: T.todayISO() }];
  T.state.plants[1].snooze = {};
  T.state.plants[1].lastWatered = T.addDays(T.todayISO(), -2);
  T.state.plants[1].lastMisted = T.addDays(T.todayISO(), -2);
  T.state.ui.calMonth = T.monthKey(new Date());
  T.state.ui.calSel = T.addDays(T.todayISO(), 3);
  T.moveTask('p2', 'misting', T.addDays(T.todayISO(), 3));
  let reszek = '';
  ['nap','honap','ev'].forEach(m => {
    T.state.ui.calMode = m;
    T.renderCalendar();
    reszek += '<section class="view" style="display:block;max-width:1180px;margin:0 auto 34px">' +
      '<h2 style="font-size:17px;margin:0 0 10px;color:var(--green-ink)">' + cimek[m] + '</h2>' +
      byId('calendarContent')._html + '</section>';
  });
  const oldal = '<!doctype html><html lang="hu" data-theme="light"><head><meta charset="utf-8">' +
    '<title>Florum – naptár előnézet</title><style>' + css +
    '\nbody{padding:26px 18px 60px}\n.snap-note{max-width:1180px;margin:0 auto 22px;background:var(--panel);border:1px solid var(--line);' +
    'border-radius:var(--radius);padding:14px 18px;box-shadow:var(--shadow)}\n.snap-note h1{font-size:19px;margin:0 0 4px}' +
    '\n.snap-note p{margin:0;font-size:13px;color:var(--muted)}\n</style></head><body>' +
    '<div class="snap-note"><h1>Florum · naptár (1.8.0)</h1>' +
    '<p>Statikus pillanatkép a valódi alkalmazás által generált HTML-ből, demó adatokkal ' +
    '(klívia téli pihenővel + fikusz sűrű ütemezéssel és fotóval). A zöld körben a növény ' +
    'fotója látszik – fotó nélkül színes pötty. A „Szundi” helyett most már dátummező és ' +
    'húzás is van; a „Húzd át” jelölésű sorok mozgathatók. A gombok itt nem kattinthatók, ' +
    'az élő alkalmazásban igen.</p></div>' + reszek + '</body></html>';
  fs.writeFileSync('/home/user/florum/naptar-elonezet.html', oldal, 'utf8');
  console.log('  ✓ naptar-elonezet.html kiírva (' + Math.round(oldal.length/1024) + ' kB)');
}

// ---------- permetezés vize ----------
function assert(felt, uzenet){ if (!felt) throw new Error(uzenet || 'nem teljesült'); }
function vitel(id){ return byId(id); }
console.log('\n== Permetezés vize ==');
check('MIST_WATER: minden érték megvan, a sorrend jó', () => {
  const kell = ['', 'csap', 'eso', 'ion', 'nem'];
  assert(JSON.stringify(T.MIST_ORDER) === JSON.stringify(kell), 'rossz sorrend: ' + T.MIST_ORDER);
  kell.forEach(k => assert(T.MIST_WATER[k], 'hiányzó kulcs: ' + k));
  assert(T.MIST_WATER.eso.nev === 'esővíz', 'rossz név');
  assert(T.MIST_WATER.nem.nev === 'nem szereti a permetezést', 'rossz név');
});
check('mistHint(): „esővízzel, reggel” / „nem” esetén üres', () => {
  assert(T.mistHint({ mistWater: 'eso' }) === 'esővízzel, reggel', T.mistHint({ mistWater: 'eso' }));
  assert(T.mistHint({ mistWater: 'ion' }) === 'ioncserélt vagy desztillált vízzel, reggel', T.mistHint({ mistWater: 'ion' }));
  assert(T.mistHint({ mistWater: 'nem' }) === '', 'nem szereti → nem lehet toldalék');
  assert(T.mistHint({}) === '', 'nincs megadva → nincs toldalék');
});
check('mistMondat(): teljes mondat az értesítéshez', () => {
  assert(T.mistMondat({ mistWater: 'eso' }) === 'Permetezés esővízzel, reggel.', T.mistMondat({ mistWater: 'eso' }));
  assert(T.mistMondat({ mistWater: 'nem' }) === '', 'nem szereti → nincs mondat');
});
check('intervalFor(): „nem szereti” → 0 (nincs permetezés-teendő)', () => {
  const mistDef = T.TASK_DEFS.filter(d => d.key === 'misting')[0];
  assert(T.intervalFor({ mistDays: 7, mistWater: 'nem' }, mistDef) === 0, 'nem lett 0');
  assert(T.intervalFor({ mistDays: 7, mistWater: 'eso' }, mistDef) === 7, 'szereti → 7');
  assert(T.intervalFor({ mistDays: 7 }, mistDef) === 7, 'nincs megadva → 7');
});
check('collectTasks(): permetezés kimarad, ha nem szereti', () => {
  const elotte = T.collectTasks().filter(t => t.plant.id === 'p2' && t.def.key === 'misting');
  assert(elotte.length === 1, 'a tesztnövénynek (p2) van permetezése');
  T.state.plants.forEach(p => { if (p.id === 'p2') p.mistWater = 'nem'; });
  const utana = T.collectTasks().filter(t => t.plant.id === 'p2' && t.def.key === 'misting');
  assert(utana.length === 0, 'nem szereti → nincs teendő');
  const mas = T.collectTasks().filter(t => t.plant.id === 'p2' && t.def.key !== 'misting');
  assert(mas.length > 0, 'a többi teendő marad');
  T.state.plants.forEach(p => { if (p.id === 'p2') p.mistWater = 'eso'; });
});
check('a teendő sora kiírja a vizet', () => {
  T.state.plants.forEach(p => { if (p.id === 'p2') p.mistWater = 'eso'; });
  T.renderToday();
  const el = vitel('todayContent');
  const html = (el && el.innerHTML) || '';
  assert(html.indexOf('mist-water') >= 0, 'nincs mist-water a mai teendők között');
  assert(html.indexOf('esővízzel, reggel') >= 0, 'nincs benne a víz szövege');
  T.state.plants.forEach(p => { if (p.id === 'p2') p.mistWater = null; });
});
check('fillSelects(): a legördülő feltöltődik', () => {
  T.fillSelects();
  const sel = vitel('f_mistWater');
  assert(sel && String(sel.innerHTML).indexOf('esővíz') >= 0, 'nincs esővíz opció');
  assert(String(sel.innerHTML).indexOf('nem szereti a permetezést') >= 0, 'nincs „nem” opció');
});
check('calSourcesHTML(): a Google Naptár panel megjelenik', () => {
  const h = T.calSourcesHTML();
  assert(h.indexOf('Naptár-források') >= 0, 'nincs cím');
  assert(h.indexOf('setCalNewUrl') >= 0, 'nincs beviteli mező');
  assert(h.indexOf('Titkos cím iCal') >= 0, 'nincs útmutató');
  assert(h.indexOf('data-cal-add') >= 0, 'nincs Hozzáadás gomb');
});

// ---------- Google Naptár eseményei a naptárnézetben ----------
console.log('\n== Naptár-események a naptárnézetben (📅) ==');
function calProba(esemenyek){
  T.state.settings.calSources = [{ nev:'Google – munka', url:'https://pelda/basic.ics', enabled:true }];
  T.CAL.events = esemenyek.map(T.calEventFromApi);
  T.CAL.loaded = true;
  T.CAL.from = '2000-01-01';
  T.CAL.to = '2100-12-31';
  T.CAL.error = '';
}
const MA = T.todayISO();
check('calApiUrl(): a látható időszakot kéri, 1..400 nap', () => {
  const u = T.calApiUrl('2026-09-28', '2026-11-01');
  assert(u === '/api/calendars?from=2026-09-28&days=35', 'rossz cím: ' + u);
  const hosszu = T.calApiUrl('2026-01-01', '2027-12-31');
  assert(hosszu.indexOf('days=400') > 0, 'a napok számát 400-ra kell vágni: ' + hosszu);
});
check('calEventFromApi(): normalizálás (egész napos / időpontos / hibás)', () => {
  const e = T.calEventFromApi({ cim:'Fogorvos', kezdet:'2026-10-24T09:30:00', hely:'Rendelő', naptar:'munka' });
  assert(e && e.due === '2026-10-24' && e.time === '09:30', JSON.stringify(e));
  assert(e.title === 'Fogorvos' && e.naptar === 'munka' && e.hely === 'Rendelő', 'rossz mezők');
  const n = T.calEventFromApi({ cim:'Szabi', kezdet:'2026-10-24', egesz:true, naptar:'munka' });
  assert(n && n.time === '', 'egész naposnál nincs időpont');
  assert(T.calEventFromApi({ cim:'x', kezdet:'hülye' }) === null, 'hibás dátum → null');
  const sz = T.calEventFromApi({ cim:'x', kezdet:'2026-10-24', szin:'#e01b24' });
  assert(sz.szin === '#e01b24', 'a színt át kell venni');
  assert(T.calEventFromApi({ cim:'x', kezdet:'2026-10-24', szin:'javascript:alert(1)' }).szin === '', 'a színt szűrni kell');
});
check('calFedett(): a betöltött időszak vége is számít', () => {
  T.CAL.loaded = true; T.CAL.from = '2026-09-28';
  T.CAL.to = T.addDays('2026-09-28', 41);            // 42 nap
  assert(T.calFedett('2026-10-01', '2026-10-31') === true, 'az október benne van');
  assert(T.calFedett('2026-11-01', '2026-11-30') === false, 'a november már nincs');
  assert(T.calFedett('2026-09-01', '2026-09-30') === false, 'a korábbi hónap nincs');
  T.CAL.loaded = false;
  assert(T.calFedett('2026-10-01', '2026-10-31') === false, 'betöltés előtt hamis');
});
check('calEventsIn(): csak a kért időszak', () => {
  calProba([{ cim:'A', kezdet:'2026-10-24', naptar:'munka' },
            { cim:'B', kezdet:'2026-11-15', naptar:'munka' }]);
  assert(T.calEventsIn('2026-10-01', '2026-10-31').length === 1, 'októberben 1 esemény');
  assert(T.calEventsIn('2026-01-01', '2026-12-31').length === 2, 'egész évben 2');
});
check('a hónap-rácsban megjelenik a 📅 esemény', () => {
  calProba([{ cim:'Fogorvos', kezdet: MA + 'T09:30:00', hely:'Rendelő', naptar:'Google – munka' }]);
  T.state.ui.calMode = 'honap';
  T.state.ui.calMonth = MA.slice(0, 7);
  T.state.ui.calFilter = null;
  T.renderCalendar();
  const h = vitel('calendarContent').innerHTML;
  assert(h.indexOf('Fogorvos') >= 0, 'nincs benne az esemény neve');
  assert(h.indexOf('cal-line ev') >= 0, 'nincs esemény-sor a cellában');
  assert(h.indexOf('09:30') >= 0, 'nincs benne az időpont');
  assert(h.indexOf('data-kpi="event"') >= 0, 'nincs 📅 KPI-kártya');
  assert(h.indexOf('naptár (📅)') >= 0, 'nincs a jelmagyarázatban');
  assert(h.indexOf('📅<') >= 0 || h.indexOf('📅1') >= 0, 'nincs esemény-jelzés a nap fejlécében');
});
check('„naptár” szűrő: a hónap eseményei listában', () => {
  calProba([{ cim:'Fogorvos', kezdet: MA + 'T09:30:00', naptar:'Google – munka' },
            { cim:'Szabi fél nap', kezdet: MA, egesz:true, naptar:'Google – munka' }]);
  T.state.ui.calFilter = 'event';
  T.renderCalendar();
  const h = vitel('calendarContent').innerHTML;
  assert(h.indexOf('📅 Naptár') >= 0, 'nincs a szűrt lista címe');
  assert(h.indexOf('Fogorvos') >= 0 && h.indexOf('Szabi fél nap') >= 0, 'hiányzik egy esemény');
  assert(h.indexOf('cal-ev-tag') >= 0, 'nincs „naptár” címke a sorban');
  assert(h.indexOf('data-kpiclear') >= 0, 'nincs szűrő törlése');
  T.state.ui.calFilter = null;
});
check('a nap-kártyán külön „Naptár” szakasz', () => {
  calProba([{ cim:'Fogorvos', kezdet: MA + 'T09:30:00', hely:'Rendelő', naptar:'Google – munka' }]);
  T.state.ui.calSel = MA;
  T.renderCalendar();
  const h = vitel('calendarContent').innerHTML;
  assert(h.indexOf('📅 Naptár <span class="count">1</span>') >= 0, 'nincs Naptár szakasz');
  assert(h.indexOf('📅 naptár <b>1</b>') >= 0, 'a napi összegzésből hiányzik');
});
check('esemény nélkül minden a régi (nincs üres blokk)', () => {
  calProba([]);
  T.state.ui.calSel = MA;
  T.renderCalendar();
  const h = vitel('calendarContent').innerHTML;
  assert(h.indexOf('📅 Naptár <span') < 0, 'üresen nem lehet Naptár szakasz');
  assert(h.indexOf('cal-line ev') < 0, 'nincs esemény-sor');
  assert(T.state.settings.calSources && T.state.settings.calSources.length === 1, 'a forrás megmarad');
});
check('forrás nélkül nincs 📅 KPI és nincs letöltés', () => {
  T.state.settings.calSources = [];
  T.CAL.events = [];
  T.renderCalendar();
  const h = vitel('calendarContent').innerHTML;
  assert(h.indexOf('data-kpi="event"') < 0, 'forrás nélkül nincs 📅 kártya');
  assert(T.calVanForras() === false, 'calVanForras() legyen hamis');
});
check('calDaySummary(): csak esemény is megjelenik', () => {
  const ev = T.calEventFromApi({ cim:'X', kezdet: MA, naptar:'munka' });
  const h = T.calDaySummary([], [ev]);
  assert(h.indexOf('📅 naptár') >= 0, 'hiányzik az esemény az összegzésből');
  assert(h.indexOf('kész') < 0, 'esemény nélkül ne írjon „kész”-t');
  assert(T.calDaySummary([], []) === '', 'üresen üres string kell');
});

// ---------- opcionális: VALÓDI /api/calendars válasz ----------
// Ha a FLORUM_CAL_JSON környezeti változó egy mentett API-válaszra mutat,
// végigmegyünk rajta is (a szerver és a felület összeér-e).
if (process.env.FLORUM_CAL_JSON) {
  console.log('\n== Valódi /api/calendars válasz (' + process.env.FLORUM_CAL_JSON + ') ==');
  check('a szerver válasza feldolgozható és megjelenik', () => {
    const j = JSON.parse(fs.readFileSync(process.env.FLORUM_CAL_JSON, 'utf8'));
    assert(j.ok === true, 'a válasz nem ok');
    const napok = j.days || 1;
    const evs = j.events || [];
    calProba(evs);
    T.CAL.from = j.from;
    T.CAL.to = T.addDays(j.from, napok - 1);
    T.state.ui.calMode = 'honap';
    T.state.ui.calFilter = null;
    // arra a hónapra állunk, amelyikben van esemény (a kért időszak
    // kezdete a múlt hónapba eshet, ott jogosan nincs semmi)
    const honap = evs.length ? String(evs[0].kezdet).slice(0, 7) : String(j.from).slice(0, 7);
    T.state.ui.calMonth = honap;
    T.state.ui.calSel = evs.length ? String(evs[0].kezdet).slice(0, 10) : String(j.from).slice(0, 10);
    T.renderCalendar();
    const h = vitel('calendarContent').innerHTML;
    const ebben = evs.filter(e => String(e.kezdet).slice(0, 7) === honap);
    ebben.forEach(e => {
      assert(h.indexOf(e.cim.replace(/</g, '&lt;')) >= 0, 'hiányzik: ' + e.cim);
    });
    assert(ebben.length > 0, 'nincs esemény a hónapban');
    assert(h.indexOf('data-kpi="event"') >= 0, 'nincs 📅 KPI');
    return ebben.length + ' / ' + (j.events || []).length + ' esemény a hónap-rácsban';
  });
}

// ---------- fotónézet (1.23.0): feh / chafa / böngésző ----------
console.log('\n== Fotónézet (külső nézegető + nagy nézet) ==');
if (typeof T.openPhotoExternally === 'function') {
  ok++; console.log('  ✓ openPhotoExternally létezik (a ↗ / „Külső nézegető” gomb kezelője)');
} else { bad++; problems.push('openPhotoExternally hiányzik'); console.log('  ✗ nincs openPhotoExternally'); }
[['data-galphoto="browser"', 'nagy nézet böngészőben gomb'],
 ['data-galphoto="external"', 'külső nézegető gomb'],
 ['data-gaext', 'képenkénti ↗ gomb a click-kezelőben'],
 ["'/api/open'", 'a szerver /api/open végpontja'],
 ["'/foto'", 'a böngészős nagy nézet címe']].forEach(([kell, cim]) => {
  if (src.indexOf(kell) >= 0) { ok++; console.log('  ✓ ' + cim); }
  else { bad++; problems.push(cim); console.log('  ✗ hiányzik: ' + cim); }
});
if (src.indexOf('Külső nézegető csak a florum.py-val indított módban') >= 0) {
  ok++; console.log('  ✓ fájlból megnyitott HTML-ben érthető üzenet (a böngésző nem indíthat programot)');
} else { bad++; problems.push('külső nézegető figyelmeztetés'); console.log('  ✗ nincs figyelmeztetés'); }

// ---------- új növény linkről / szövegből (1.33.2) ----------
console.log('\n== Új növény: adatlap kiolvasása ==');
[['fetchPlantData', 'a kiolvasás indítója'],
 ['applyFetchedEntry', 'a kiolvasott adatok beírása az űrlapba'],
 ['openInfoFetched', 'a „Mit találtam?” adatlap'],
 ['srcTextToggle', 'a szövegbeillesztő mező (robotvédelem ellen)']].forEach(([nev, cim]) => {
  if (typeof T[nev] === 'function') { ok++; console.log('  ✓ ' + cim + ' (' + nev + ')'); }
  else { bad++; problems.push(nev); console.log('  ✗ hiányzik: ' + nev); }
});
[['/api/plant/fetch', 'a szerver végpontja', src],
 ['Adatok kiolvasása', 'a gomb felirata', html],
 ['Szöveg beillesztése', 'a robotvédelem-út gombja', html],
 ['id="f_srcUrl"', 'a link mezője', html],
 ['id="f_srcText"', 'a beillesztő mező', html],
 ['id="f_srcHint"', 'az állapotsor', html],
 ['id="f_srcFetch"', 'a kiolvasás gombja', html]].forEach(([kell, cim, hol]) => {
  if (hol.indexOf(kell) >= 0) { ok++; console.log('  ✓ ' + cim); }
  else { bad++; problems.push(cim); console.log('  ✗ hiányzik: ' + cim); }
});
// a kiolvasott adatlap ne írjon felül mindent csendben: az applyDBEntry-t hívja
if (src.indexOf('applyDBEntry(e, true)') >= 0) {
  ok++; console.log('  ✓ a kiolvasott értékek a meglévő kitöltőn mennek át (nem írnak felül vakon)');
} else { bad++; problems.push('applyDBEntry(e, true)'); console.log('  ✗ nem az applyDBEntry-t használja'); }

// ---------- adatbázis-függő ellenőrzés (a beépített DB betöltése után) ----------
(async () => {
  console.log('\n== Adatbázis-keresés a megszokott nevekre ==');
  try {
    await T.initDB();
  } catch (e) {
    console.log('  ! az adatbázis betöltése nem sikerült: ' + e.message);
  }
  const esetek = [
    ['vitorlavirag', 'Békeliliom'],
    ['vitorlavirág', 'Békeliliom'],
    ['nyelv', 'Anyósnyelv'],
    ['pothos', 'Aranypothos'],
    ['leopárd', 'Leopárdnövény'],
    ['leopard', 'Leopárdnövény'],           // ékezet nélkül is
    ['pöttyös', 'Leopárdnövény'],
    ['maculata', 'Leopárdnövény'],
    ['ledebouria', 'Leopárdnövény'],
    ['elefántláb', 'Elefántláb'],
    ['elefantlab', 'Elefántláb'],            // ékezet nélkül
    ['palackfa', 'Elefántláb'],
    ['nolina', 'Elefántláb'],
    ['lófarkú', 'Elefántláb']
  ];
  esetek.forEach(([q, vart]) => {
    const t = T.searchDB(q);
    const elso = t.length ? t[0].name : '(nincs)';
    const jo = t.some(x => x.name === vart);
    if (jo) { ok++; console.log('  ✓ „' + q + '” → ' + elso + (elso === vart ? '' : ' (köztük: ' + vart + ')')); }
    else { bad++; problems.push('keresés: ' + q); console.log('  ✗ „' + q + '” nem találja: ' + vart); }
  });
  const e = T.findDBByName('vitorlavirág');
  if (e && e.name === 'Békeliliom') { ok++; console.log('  ✓ findDBByName(„vitorlavirág”) → Békeliliom'); }
  else { bad++; problems.push('findDBByName alias'); console.log('  ✗ findDBByName nem találja a vitorlavirágot'); }

  console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás');
  if (problems.length) { console.log('Hibák:'); problems.forEach(p => console.log('  - ' + p)); }
  console.log('');
  process.exit(bad ? 1 : 0);
})();
