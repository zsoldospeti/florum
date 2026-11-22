#!/usr/bin/env node
/* ==============================================================
   FLORUM 1.33.2  ·  teszt: HŐMÉRSÉKLET MODUL
   Fájl:  teszt-homerseklet-modul.js

   A kérés, amit ez lefed:
     „Az összes helyiségben mérem a hőmérsékletet, és tudnám rögzíteni.
      Ennek változását lehetne figyelembe venni.”

   Amit vizsgál:
     1. rögzítés (felületről és programból), magyar vessző, hibás érték
     2. helyiségenkénti statisztika: mai, 7/30 napos átlag, hőingás, trend
     3. az öntözés a MÉRÉSHEZ igazodik (nem a havi átlaghoz, nem a naptárhoz)
     4. a trend számít (melegszik → sűrűbb), ésszerű határok között
     5. 10 napnál régebbi mérés nem számít „most”
     6. a hőmérséklet fül: űrlap, kártyák, előzmény-táblázat, grafikon
     7. a Ma fül kockái + a naptár hőmérséklet-sávja
     8. mentés/újratöltés: a mérések megmaradnak
     9. törlés, CSV
    10. nincs futásidejű hiba
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

let html = fs.readFileSync(HTML, 'utf8');
const EXPORT = `
;window.__T = {
  applyState, render, state, switchView, renderCalendar,
  tempAdd:(typeof tempAdd!=='undefined'?tempAdd:null),
  tempAddFromForm:(typeof tempAddFromForm!=='undefined'?tempAddFromForm:null),
  tempDelete:(typeof tempDelete!=='undefined'?tempDelete:null),
  tempRooms:(typeof tempRooms!=='undefined'?tempRooms:null),
  tempRoomLog:(typeof tempRoomLog!=='undefined'?tempRoomLog:null),
  tempLast:(typeof tempLast!=='undefined'?tempLast:null),
  tempAvg:(typeof tempAvg!=='undefined'?tempAvg:null),
  tempTrend:(typeof tempTrend!=='undefined'?tempTrend:null),
  tempIngadozas:(typeof tempIngadozas!=='undefined'?tempIngadozas:null),
  tempChartHTML:(typeof tempChartHTML!=='undefined'?tempChartHTML:null),
  tempSetAblak:(typeof tempSetAblak!=='undefined'?tempSetAblak:null),
  tempChartSor:(typeof tempChartSor!=='undefined'?tempChartSor:null),
  tempChartOsztas:(typeof tempChartOsztas!=='undefined'?tempChartOsztas:null),
  TEMP_CHART:(typeof TEMP_CHART!=='undefined'?TEMP_CHART:null),
  tempPlantNow:(typeof tempPlantNow!=='undefined'?tempPlantNow:null),
  tempHatásos:(typeof tempHatásos!=='undefined'?tempHatásos:null),
  homIndex:(typeof homIndex!=='undefined'?homIndex:null),
  intervalFor:(typeof intervalFor!=='undefined'?intervalFor:null),
  TASK_DEFS:(typeof TASK_DEFS!=='undefined'?TASK_DEFS:null),
  todayISO, addDays, snapshot
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
    win.alert = () => {}; win.confirm = () => true; win.prompt = () => null;
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

const ma = () => T.todayISO();
function noveny(id, nev, room, extra) {
  return Object.assign({ id, name: nev, room, waterDays: 7, waterWinter: 12,
                         lastWatered: ma(), winterSlowdown: true }, extra || {});
}

setTimeout(() => {
  const def = T.TASK_DEFS.find(d => d.key === 'watering');

  T.applyState({
    plants: [noveny('p1', 'Klívia', 'Nappali'), noveny('p2', 'Monstera', 'Hálószoba')],
    history: [], settings: {}, meta: {}, customDb: []
  });
  T.render();

  // ================================================================
  console.log('\n== 1. Rögzítés ==');
  check('mérés nélkül a régi (naptári) működés', () => {
    assert(T.state.tempLog.length === 0, 'váratlan mérés');
    assert(T.intervalFor(T.state.plants[0], def) === 12, 'nem 12 nap');
    assert(T.tempPlantNow(T.state.plants[0]) === null, 'van hőmérséklet-adat');
    return '12 nap, nincs hőmérséklet-adat';
  });
  check('rögzítés programból', () => {
    const r = T.tempAdd('Nappali', 26.5, 44, ma(), 'délutáni mérés');
    assert(r.ok, 'nem sikerült');
    assert(T.state.tempLog.length === 1, 'nincs 1 mérés');
    return T.tempLast('Nappali').t + ' °C · ' + T.tempLast('Nappali').hum + '% pára';
  });
  check('hibás érték elutasítva (60 °C felett)', () => {
    const r = T.tempAdd('Nappali', 75, '', ma(), '');
    assert(!r.ok, 'elfogadta a 75 °C-ot');
    assert(T.state.tempLog.length === 1, 'mégis bekerült');
    return 'elutasítva: ' + r.hibak[0];
  });
  check('helyiség nélkül elutasítva', () => {
    const r = T.tempAdd('', 22, '', ma(), '');
    assert(!r.ok, 'elfogadta helyiség nélkül');
    return 'elutasítva';
  });

  // ================================================================
  console.log('\n== 2. Statisztika helyiségenként ==');
  T.tempAdd('Nappali', 20, 50, T.addDays(ma(), -3), '');
  T.tempAdd('Nappali', 19, 52, T.addDays(ma(), -6), '');
  // az ELŐZŐ hét is kell, különben nincs mihez hasonlítani a trendet
  T.tempAdd('Nappali', 15, 60, T.addDays(ma(), -10), 'hűvös volt');
  T.tempAdd('Nappali', 16, 60, T.addDays(ma(), -12), '');
  T.tempAdd('Nappali', 17, 58, T.addDays(ma(), -8), '');
  T.tempAdd('Hálószoba', 18, 55, ma(), '');
  check('a legutóbbi mérés a mérvadó', () => {
    assert(T.tempLast('Nappali').t === 26.5, 'nem 26,5: ' + T.tempLast('Nappali').t);
    return '26,5 °C';
  });
  check('7 napos átlag (napi utolsó mérés)', () => {
    const a = T.tempAvg('Nappali', 7);
    assert(a !== null && a > 19 && a < 27, 'gyanús átlag: ' + a);
    return a + ' °C';
  });
  check('hőingás az utolsó 7 napból', () => {
    const i = T.tempIngadozas('Nappali', 7);
    assert(i !== null && i > 5, 'gyanús ingás: ' + i);
    return i + ' °C';
  });
  check('trend: az utolsó és az előző hét különbsége', () => {
    const tr = T.tempTrend('Nappali');
    assert(tr !== null, 'nincs trend');
    return (tr > 0 ? '+' : '') + tr + ' °C/hét';
  });
  check('a helyiségek között van a növények helyisége is', () => {
    const r = T.tempRooms();
    assert(r.indexOf('Nappali') >= 0 && r.indexOf('Hálószoba') >= 0, 'hiányos: ' + r.join(', '));
    return r.join(' · ');
  });

  // ================================================================
  console.log('\n== 3. Az öntözés a méréshez igazodik ==');
  check('28 °C-os nappali → rövidebb időköz, mint a 18 °C-os szobában', () => {
    T.tempAdd('Nappali', 28, 40, ma(), 'kánikula');
    const ivNappali = T.intervalFor(T.state.plants[0], def);
    const ivHalo = T.intervalFor(T.state.plants[1], def);
    assert(ivNappali < ivHalo, 'nem a mérés dönt: ' + ivNappali + ' vs ' + ivHalo);
    return 'Nappali ' + ivNappali + ' nap · Hálószoba ' + ivHalo + ' nap';
  });
  check('a mérés felülírja a beállított havi átlagot', () => {
    T.state.settings.temp = { tied: true, months: { 1:21,2:21,3:22,4:23,5:25,6:27,7:28,8:28,9:26,10:30,11:22,12:21 }, ideal: [15,27] };
    const elotte = T.intervalFor(T.state.plants[0], def);
    T.tempAdd('Nappali', 18, 60, ma(), 'lehűlt');
    const utana = T.intervalFor(T.state.plants[0], def);
    assert(utana > elotte, 'a mérés nem vette át az irányítást: ' + elotte + ' → ' + utana);
    return elotte + ' → ' + utana + ' nap (mért 18 °C)';
  });
  check('a hőmérséklet-szorzó a mérésből is számol', () => {
    const i = T.homIndex(T.state.plants[0]);
    assert(i > 1, 'nem hűvös: ' + i);
    return '×' + String(i).replace('.', ',');
  });
  check('a trend számít: melegedés → kicsit sűrűbb, mint a nyers mérés', () => {
    T.applyState({ plants: [noveny('p3', 'Teszt', 'Dolgozó')], history: [], settings: {}, meta: {}, customDb: [],
                   tempLog: [
                     { room:'Dolgozó', date:T.addDays(ma(),-13), t:18, ts:1 },
                     { room:'Dolgozó', date:T.addDays(ma(),-10), t:18.5, ts:2 },
                     { room:'Dolgozó', date:T.addDays(ma(),-6), t:24, ts:3 },
                     { room:'Dolgozó', date:T.addDays(ma(),-3), t:25, ts:4 },
                     { room:'Dolgozó', date:ma(), t:26, ts:5 }
                   ] });
    const p = T.state.plants[0];
    const h = T.tempHatásos(p);
    assert(h && h.trend !== null && h.trend > 1, 'nincs melegedési trend: ' + (h && h.trend));
    assert(h.t > 26, 'a trend nem emelte a hatásos hőmérsékletet: ' + h.t);
    return 'mért 26 °C · trend +' + h.trend + ' → hatásos ' + h.t + ' °C';
  });

  // ================================================================
  console.log('\n== 4. A régi mérés nem számít örökre ==');
  check('10 napnál régebbi mérés → vissza a naptári működésre', () => {
    T.applyState({ plants: [noveny('p4', 'Régi', 'Padlás')], history: [], settings: {}, meta: {}, customDb: [],
                   tempLog: [{ room:'Padlás', date:T.addDays(ma(), -30), t:35, ts:1 }] });
    const p = T.state.plants[0];
    assert(T.tempPlantNow(p) === null, 'mégis számít a 30 napos mérés');
    assert(T.intervalFor(p, def) === 12, 'nem a naptári érték: ' + T.intervalFor(p, def));
    return '30 napos mérés figyelmen kívül · 12 nap';
  });

  // ================================================================
  console.log('\n== 5. A hőmérséklet fül ==');
  T.applyState({
    plants: [noveny('p1', 'Klívia', 'Nappali'), noveny('p2', 'Monstera', 'Hálószoba')],
    history: [], settings: {}, meta: {}, customDb: []
  });
  T.tempAdd('Nappali', 26.5, 44, ma(), 'délutáni');
  T.tempAdd('Nappali', 21, 50, T.addDays(ma(), -4), '');
  T.tempAdd('Hálószoba', 18, 55, ma(), '');
  T.switchView('temp');

  setTimeout(() => {
    check('van űrlap (helyiség, hőmérséklet, pára, nap, jegyzet)', () => {
      ['t_room', 't_temp', 't_hum', 't_date', 't_note'].forEach(id => {
        assert(doc.getElementById(id), 'hiányzik: ' + id);
      });
      return '5 mező';
    });
    check('helyiségenként kártya, a mai értékkel', () => {
      const kartyak = [...doc.querySelectorAll('#tempContent .tcard')];
      assert(kartyak.length >= 2, 'kártyák: ' + kartyak.length);
      const nappali = kartyak.find(k => /Nappali/.test(k.textContent));
      assert(nappali && /26,5/.test(nappali.textContent), 'nincs 26,5 a nappali kártyán');
      return kartyak.length + ' kártya · Nappali 26,5 °C';
    });
    check('a kártyán ott a 7 napos átlag és a besorolás', () => {
      const k = [...doc.querySelectorAll('#tempContent .tcard')].find(x => /Nappali/.test(x.textContent));
      assert(/7 nap:/.test(k.textContent), 'nincs heti átlag');
      assert(k.querySelector('.ty'), 'nincs besorolás-jelző');
      return (k.querySelector('.ty') || {}).textContent;
    });
    check('grafikon (14 napos sáv) is van', () => {
      const sp = doc.querySelector('#tempContent .tspark');
      assert(sp, 'nincs grafikon');
      return sp.querySelectorAll('i').length + ' oszlop';
    });
    check('előzmény-táblázat sorai', () => {
      const sorok = doc.querySelectorAll('#tempContent .ttable tbody tr');
      const elvart = T.state.tempLog.length;
      assert(sorok.length === elvart, 'sorok: ' + sorok.length + ' (mérés: ' + elvart + ')');
      return sorok.length + ' sor';
    });
    check('űrlapon rögzítés magyar vesszővel (24,5)', () => {
      doc.getElementById('t_room').value = 'Nappali';
      doc.getElementById('t_temp').value = '24,5';
      doc.getElementById('t_hum').value = '48';
      doc.querySelector('[data-tempadd]').click();
      const u = T.tempLast('Nappali');
      assert(u.t === 24.5, 'nem 24,5: ' + u.t);
      assert(u.hum === 48, 'pára: ' + u.hum);
      return '24,5 °C · 48%';
    });
    check('hibás beírásnál üzenet, nem ment', () => {
      const elotte = T.state.tempLog.length;
      doc.getElementById('t_temp').value = 'nem szám';
      doc.querySelector('[data-tempadd]').click();
      assert(T.state.tempLog.length === elotte, 'mégis mentett');
      assert((doc.getElementById('tErr').textContent || '').length > 0, 'nincs hibaüzenet');
      return 'elutasítva';
    });
    check('törlés', () => {
      const elotte = T.state.tempLog.length;
      const cel = T.state.tempLog[T.state.tempLog.length - 1];
      doc.querySelector('[data-tempdel="' + cel.id + '"]').click();
      assert(T.state.tempLog.length === elotte - 1, 'nem törlődött');
      return elotte + ' → ' + T.state.tempLog.length;
    });

    // ==============================================================
    console.log('\n== 6. Hőmérséklet-grafikon ==');
    check('van SVG grafikon, tengelyekkel és °C-beosztással', () => {
      const svg = doc.querySelector('#tempContent .chart-svg');
      assert(svg, 'nincs .chart-svg');
      const cimkek = [...svg.querySelectorAll('text.grid-t')].map(t => t.textContent);
      assert(cimkek.length >= 3, 'kevés °C-címke: ' + cimkek.join(','));
      assert(cimkek.every(x => /^-?\d+([.,]\d)?$/.test(x)), 'nem számok: ' + cimkek.join(','));
      return cimkek.join(' · ');
    });
    check('helyiségenként külön vonal', () => {
      // ehhez helyiségenként legalább KÉT mérés kell (egy pontból nincs vonal)
      if (T.tempRoomLog('Hálószoba').length < 2){
        T.tempAdd('Hálószoba', 17, 56, T.addDays(ma(), -2), '');
        T.switchView('temp');
      }
      const vonalak = doc.querySelectorAll('#tempContent .chart-svg polyline.line');
      assert(vonalak.length >= 2, 'vonalak: ' + vonalak.length);
      const szinek = [...vonalak].map(v => v.getAttribute('stroke'));
      assert(new Set(szinek).size === szinek.length, 'a vonalak színe nem különbözik');
      return vonalak.length + ' vonal, külön színnel';
    });
    check('a pontokon rajta a mérés (egérrel látszik)', () => {
      const pontok = doc.querySelectorAll('#tempContent .chart-svg circle.dot');
      assert(pontok.length >= 3, 'pontok: ' + pontok.length);
      const cim = pontok[0].querySelector('title');
      assert(cim && /°C/.test(cim.textContent), 'nincs címke a ponton');
      return pontok.length + ' pont · „' + cim.textContent + '”';
    });
    check('a növények ideális sávja zölden ott van', () => {
      const sav = doc.querySelector('#tempContent .chart-svg rect.ideal');
      assert(sav, 'nincs ideális sáv');
      assert(/ideális sáv/.test(doc.querySelector('.chart-legend').textContent), 'nincs a jelmagyarázatban');
      return 'sáv: ' + sav.getAttribute('height').slice(0, 6) + ' px magas';
    });
    check('a mai nap jelölve van', () => {
      assert(doc.querySelector('#tempContent .chart-svg line.today-l'), 'nincs mai jelölés');
      return 'szaggatott vonal';
    });
    check('az időtartam váltható (7/14/30/90 nap)', () => {
      const gombok = [...doc.querySelectorAll('[data-tempwin]')];
      assert(gombok.length === 4, 'gombok: ' + gombok.length);
      gombok.find(b => b.getAttribute('data-tempwin') === '30').click();
      assert(T.TEMP_CHART.napok === 30, 'nem váltott: ' + T.TEMP_CHART.napok);
      const aktiv = doc.querySelector('[data-tempwin].on');
      assert(aktiv && aktiv.getAttribute('data-tempwin') === '30', 'nem az aktív gomb');
      gombok2();
      return '7 · 14 · 30 · 90 nap, most: 30';
    });
    function gombok2(){ doc.querySelector('[data-tempwin="14"]').click(); }
    check('az összegzés kiírja a min/max/átlag/ingást', () => {
      const t = doc.querySelector('#tempContent .chart-sum').textContent;
      assert(/min/.test(t) && /max/.test(t) && /átlag/.test(t) && /ingás/.test(t), 'hiányos: ' + t);
      return t.replace(/\s+/g, ' ').trim().slice(0, 110) + '…';
    });
    check('mérés nélkül is mond valamit (nem üres doboz)', () => {
      const ment = T.state.tempLog;
      T.state.tempLog = [];
      const h = T.tempChartHTML();
      T.state.tempLog = ment;
      assert(/Még nincs mérés/.test(h), 'nem szól: ' + h.slice(0, 80));
      return '„Még nincs mérés…”';
    });
    check('a tengely-osztás ésszerű (nem 0,3 fokonként)', () => {
      const o = T.tempChartOsztas(17.1, 25.4);
      assert([1, 2, 5, 10].indexOf(o.lepes) >= 0, 'lépés: ' + o.lepes);
      assert(o.felso > 25.4 && o.also < 17.1, 'nem fogja közre: ' + o.also + '…' + o.felso);
      return o.also + ' … ' + o.felso + ' °C, ' + o.lepes + '-onként';
    });

    // ==============================================================
    console.log('\n== 7. Ma fül + naptár ==');
    T.render();
    check('a Ma fülön helyiségenként kocka', () => {
      const k = doc.querySelectorAll('#todayContent .tcard');
      assert(k.length >= 2, 'kockák: ' + k.length);
      assert(/Hőmérséklet – mérés rögzítése/.test(doc.getElementById('todayContent').innerHTML),
        'nincs gomb a hőmérséklet fülre');
      return k.length + ' kocka + gomb';
    });
    check('a naptárban hőmérséklet-sáv (hónap nézet)', () => {
      T.state.ui.calMode = 'honap';
      T.renderCalendar();
      const c = doc.getElementById('calendarContent').innerHTML;
      assert(/Hőmérséklet ebben a hónapban/.test(c), 'nincs sáv a naptárban');
      assert(/átlag/.test(c), 'nincs átlag');
      return 'sáv + havi átlag';
    });
    check('a naptár-sáv a rács ELŐTT van (látszik)', () => {
      const c = doc.getElementById('calendarContent').innerHTML;
      const sav = c.indexOf('Hőmérséklet ebben a hónapban');
      const racs = c.indexOf('cal-grid');
      assert(sav >= 0 && racs > sav, 'a sáv a rács után van');
      return 'sáv ' + sav + ' < rács ' + racs;
    });

    // ==============================================================
    console.log('\n== 8. Mentés és megmaradás ==');
    check('a mérések benne vannak a mentendő állapotban', () => {
      const snap = T.snapshot();
      assert(Array.isArray(snap.tempLog) && snap.tempLog.length >= 2, 'nincs tempLog a mentésben');
      return snap.tempLog.length + ' mérés a mentésben';
    });
    check('újratöltés után is megvannak (applyState)', () => {
      const mentett = JSON.parse(JSON.stringify(T.snapshot()));
      T.applyState({ plants: [], history: [], settings: {}, meta: {}, customDb: [], tempLog: [] });
      assert(T.state.tempLog.length === 0, 'nem ürült');
      T.applyState(mentett);
      assert(T.state.tempLog.length === mentett.tempLog.length, 'nem jött vissza');
      return T.state.tempLog.length + ' mérés visszatöltve';
    });
    check('selejt mérés kiszűrése (rossz adat nem borít fel semmit)', () => {
      T.applyState({ plants: [], history: [], settings: {}, meta: {}, customDb: [],
                     tempLog: [
                       { room:'Nappali', date:'2026-11-01', t:'22' },
                       { room:'', date:'2026-11-01', t:22 },
                       { room:'Nappali', t:22 },
                       { room:'Nappali', date:'2026-11-01', t:'nem szám' },
                       null
                     ] });
      assert(T.state.tempLog.length === 1, 'szűrés hibás: ' + T.state.tempLog.length);
      return '1 érvényes maradt az 5-ből';
    });

    console.log('\n== 9. Nincs futásidejű hiba ==');
    check('a lapon nem volt kezeletlen JS-hiba', () => {
      assert(hibak.length === 0, 'hiba: ' + hibak.join(' / '));
      return 'tiszta';
    });

    console.log('\nEredmény: ' + ok + ' sikeres, ' + bad + ' hibás\n');
    if (bad) { console.log('Hibák:'); problems.forEach(p => console.log('  - ' + p)); console.log(''); }
    try { dom.window.close(); } catch (e) {}
    process.exit(bad ? 1 : 0);
  }, 400);
}, 900);
