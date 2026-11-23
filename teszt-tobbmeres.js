#!/usr/bin/env node
// ==============================================================
//  FLORUM 1.33.2 · teszt: naponta több mérés + napszak + évszak
//  Fájl:    teszt-tobbmeres.js
//
//  A kérés: „Naponta akár több mérési eredmény is rögzíthető lenne,
//  ugyanoda. A statisztikák is változnának akár délelőtti-esti /
//  helyiség, nyári-téli / helyiség stb.”
//
//  Amit ez a teszt őriz:
//    · a nap értéke az ÁTLAG (nem a nap utolsó mérése)
//    · a napszak az időből jön, nem kézzel kell megadni
//    · egy napszakból / egy évszakból nem hazudik statisztikát
//    · a grafikon és a táblázat ugyanazt az átlagot mutatja
// ==============================================================
const {JSDOM}=require((function(){for(const p of ['/home/user/jsd/node_modules/jsdom','jsdom']){try{require.resolve(p);return p;}catch(e){}}return 'jsdom';})());const fs=require('fs');
let html=fs.readFileSync('/home/user/florum/florum.html','utf8');
const EXPORT=`;window.__T={applyState,render,renderTemp,switchView,state,todayISO,addDays,
tempAdd,tempNapiAtlagok,tempAvg,tempOrasProfil,tempNapszakAtlag,tempEvszakTabla,tempEvszak,
tempNapszak,tempOra,tempIdo,tempNapiEgy,tempChartSor,tempChartHTML,tempProfilHTML,tempEvszakHTML,tempCardHTML};`;
const b=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
const big=b.sort((x,y)=>y.length-x.length)[0];const i=big.lastIndexOf('})();');
const dom=new JSDOM(html.replace(big,big.slice(0,i)+EXPORT+big.slice(i)),{runScripts:'dangerously',url:'http://127.0.0.1:8777/',pretendToBeVisual:true,
 beforeParse(w){w.fetch=()=>Promise.reject(1);w.scrollTo=()=>{};w.matchMedia=()=>({matches:false,addEventListener(){},addListener(){}});}});
const w=dom.window,d=w.document;
let ok=0,bad=0;
function check(nev,fn){ try{ const r=fn(); ok++; console.log('  ✓ '+nev+(r?'   → '+r:'')); }catch(e){ bad++; console.log('  ✗ '+nev+'   → '+e.message); } }
function assert(c,m){ if(!c) throw new Error(m||'hamis'); }

setTimeout(()=>{
 const T=w.__T, ma=T.todayISO();
 T.applyState({plants:[{id:'p1',name:'Klívia',room:'Nappali',waterDays:7,lastWatered:ma,tempRange:'15–27'}],
   history:[],settings:{},meta:{},customDb:[]});
 T.render();

 console.log('\n== 1. Naponta több mérés ugyanoda ==');
 // 3 nap, naponta 3 mérés (reggel 8, délután 14, este 20)
 const napok=[T.addDays(ma,-2),T.addDays(ma,-1),ma];
 const ertekek={ '08:00':18, '14:00':26, '20:00':21 };
 napok.forEach(nap=>Object.keys(ertekek).forEach(ora=>{
   const r=T.tempAdd('Nappali',ertekek[ora],50,nap,'',ora);
   assert(r.ok,'rögzítés hiba: '+JSON.stringify(r.hibak));
 }));
 check('9 mérés rögzítve (3 nap × 3)',()=>{ assert(T.state.tempLog.length===9,'db: '+T.state.tempLog.length); return '9'; });
 check('a nap értéke az ÁTLAG (18/26/21 → 21,7), nem az utolsó (21)',
   ()=>{ const n=T.tempNapiAtlagok('Nappali'); const v=n[ma].t;
         assert(v===21.7,'napi átlag: '+v); assert(n[ma].n===3,'n: '+n[ma].n);
         return '21,7 °C (3 mérésből), min 18, max 26'; });
 check('a régi viselkedés (utolsó mérés) már NEM érvényes',
   ()=>{ const n=T.tempNapiAtlagok('Nappali'); assert(n[ma].t!==21,'még az utolsó mérés nyer'); return 'nem 21'; });
 check('a napi ingás a napon belüli szélső értékekből jön',
   ()=>{ const n=T.tempNapiAtlagok('Nappali'); const ing=Math.round((n[ma].max-n[ma].min)*10)/10;
         assert(ing===8,'ingás: '+ing); return '18–26 → 8 °C'; });

 console.log('\n== 2. Napszak ==');
 check('a napszak az időből jön (óra → napszak)',()=>{
   const m=T.state.tempLog.filter(x=>x.date===ma);
   const m8=m.find(x=>new Date(x.ts).getHours()===8);
   const m14=m.find(x=>new Date(x.ts).getHours()===14);
   assert(T.tempNapszak(m8)==='delelott',T.tempNapszak(m8));
   assert(T.tempNapszak(m14)==='delutan',T.tempNapszak(m14));
   return '8:00 → délelőtt, 14:00 → délután';
 });
 check('az idő kiírható ÓÓ:PP alakban',()=>{
   const m=T.state.tempLog.filter(x=>x.date===ma).find(x=>new Date(x.ts).getHours()===14);
   assert(T.tempIdo(m)==='14:00',T.tempIdo(m)); return '14:00'; });
 check('napszakonkénti átlag: délelőtt 18, délután 26, este 21',()=>{
   const cs=T.tempNapszakAtlag('Nappali');
   assert(cs.delelott.t===18,'délelőtt: '+cs.delelott.t);
   assert(cs.delutan.t===26,'délután: '+cs.delutan.t);
   assert(cs.este.t===21,'este: '+cs.este.t);
   return '18 / 26 / 21 °C (n=3-3-3)'; });
 check('a napszak-különbség 8 °C (ugyanaz a szoba!)',()=>{
   const cs=T.tempNapszakAtlag('Nappali');
   const kulonbseg=Math.round((cs.delutan.t-cs.delelott.t)*10)/10;
   assert(kulonbseg===8,'különbség: '+kulonbseg); return 'délután − délelőtt = 8 °C'; });

 console.log('\n== 3. Órás profil ==');
 check('óránkénti bontás (0–23), csak a mért órákon érték',()=>{
   const p=T.tempOrasProfil('Nappali');
   assert(p.length===24,'órák: '+p.length);
   assert(p[8].t===18 && p[14].t===26 && p[20].t===21,'8/14/20: '+[p[8].t,p[14].t,p[20].t]);
   assert(p[3].t===null,'a 3 óra nem lehet kitöltve: '+p[3].t);
   return '8h: 18° · 14h: 26° · 20h: 21° · üres órák null'; });

 console.log('\n== 4. Évszakok ==');
 check('az évszak a dátumból (12,1,2=tél, 6–8=nyár)',()=>{
   assert(T.tempEvszak('2026-01-15')==='tel');
   assert(T.tempEvszak('2026-07-15')==='nyar');
   assert(T.tempEvszak('2026-10-15')==='osz');
   assert(T.tempEvszak('2026-04-15')==='tavasz');
   return 'jan → tél, júl → nyár, okt → ősz, ápr → tavasz'; });
 check('évszakos tábla: helyiség × évszak, átlaggal',()=>{
   const sorok=T.tempEvszakTabla();
   assert(sorok.length>=1,'sorok: '+sorok.length);
   const s=sorok[0];
   assert(s.room==='Nappali','helyiség: '+s.room);
   assert(Math.abs(s.t-21.7)<0.01,'átlag: '+s.t);
   return s.room+' · '+s.evszak+' · átlag '+String(s.t).replace('.',',')+' °C · ingás '+s.ingas; });

 console.log('\n== 5. A grafikon is a napi átlagot rajzolja ==');
 check('a grafikon-pont a nap átlaga',()=>{
   const sor=T.tempChartSor('Nappali',7);
   const mai=sor[sor.length-1];
   assert(mai.t===21.7,'grafikon mai pont: '+mai.t);
   assert(mai.n===3,'n: '+mai.n);
   return '7 napos sor, a mai pont 21,7 °C (3 mérés átlaga)'; });

 console.log('\n== 6. A felület elemei ==');
 T.switchView('temp');
 setTimeout(()=>{
  check('„Mikor meleg?” panel van, oszlopokkal',()=>{
    const p=d.querySelector('#tempContent .tprofil');
    assert(p,'nincs .tprofil');
    const o=d.querySelectorAll('#tempContent .tprofil-oszlop');
    assert(o.length>=2,'oszlopok: '+o.length);
    return o.length+' napszak-oszlop'; });
  check('napszak-oszlopok feliratai magyarok',()=>{
    const t=[...d.querySelectorAll('#tempContent .tprofil-oszlop em')].map(x=>x.textContent);
    assert(t.some(x=>/délután|délutá/.test(x)),t.join(','));
    return t.join(' · '); });
  check('évszak-táblázat a fülön',()=>{
    const t=d.querySelector('#tempContent table.tevszak');
    assert(t,'nincs .tevszak');
    return t.querySelectorAll('tbody tr').length+' sor'; });
  check('a kártyán a mai átlag + ingás látszik',()=>{
    const h=d.querySelector('#tempContent .tcard');
    const txt=h?h.textContent:'';
    assert(/ma:/.test(txt),'nincs „ma:” a kártyán');
    assert(/ingás/.test(txt),'nincs ingás a kártyán');
    return 'ma: 21,7 °C · 3 mérés · ingás 8 °C'; });
  check('a táblázatban van Idő oszlop, napszakkal',()=>{
    const th=[...d.querySelectorAll('#tempContent .ttable:not(.tevszak) thead th')].map(x=>x.textContent);
    assert(th.includes('Idő'),'oszlopok: '+th.join(','));
    const ns=d.querySelector('#tempContent .tnapszak');
    assert(ns,'nincs napszak-felirat');
    return th.join(' | ')+' → „'+ns.textContent+'”'; });
  check('az űrlapon van óra-mező',()=>{
    assert(d.getElementById('t_ido'),'nincs #t_ido'); return '„Idő (óra:perc)” mező'; });

  console.log('\n== 7. Egy mérés / nap esetén nem törik el ==');
  T.applyState({plants:[{id:'p1',name:'Klívia',room:'Háló',waterDays:7,lastWatered:ma}],
    history:[],settings:{},meta:{},customDb:[]});
  T.tempAdd('Háló',20,50,T.addDays(ma,-1),'','08:00');
  T.tempAdd('Háló',20.5,50,ma,'','08:00');
  T.renderTemp();
  check('egy mérés/nap: a napi átlag = a mérés',()=>{
    const n=T.tempNapiAtlagok('Háló');
    assert(n[ma].t===20.5,'napi: '+n[ma].t); assert(n[ma].n===1,'n: '+n[ma].n);
    return '20,5 °C (1 mérés)'; });
  check('egy napszakból nincs órás profil (nem hazudik)',()=>{
    const h=T.tempProfilHTML();
    assert(h==='','van profil egy napszakból: '+h.slice(0,80));
    return 'üres – helyesen (2 napszak kell hozzá)'; });
  check('évszak-táblázat 1 évszakból is látszik, magyarázattal',()=>{
    const h=T.tempEvszakHTML();
    assert(h!=='','nem jelent meg');
    assert(/csak egy évszakból/.test(h),'nincs magyarázat a hiányzó évszakra');
    return 'megvan + „még csak egy évszakból van mérés”'; });
  check('üres adatnál viszont semmi (nem üres tábla)',()=>{
    T.applyState({plants:[],history:[],settings:{},meta:{},customDb:[]});
    assert(T.tempEvszakHTML()==='','üres adatnál is megjelent');
    return 'üres – helyes'; });

  console.log('\n== 8. Régi adat (időbélyeg nélkül) ==');
  T.applyState({plants:[],history:[],settings:{},meta:{},customDb:[],
    tempLog:[{room:'Régi',date:'2026-10-01',t:19},{room:'Régi',date:'2026-10-02',t:21}]});
  check('a régi mérés kap napszakot (nem „most”)',()=>{
    const x=T.state.tempLog[0];
    assert(x.ts>0,'ts: '+x.ts);
    assert(T.tempOra(x)===12,'óra: '+T.tempOra(x));
    return '2026-10-01 → 12:00 (dél), nem a mai dátum'; });

  console.log('\nEredmény: '+ok+' sikeres, '+bad+' hibás');
  process.exit(bad?1:0);
 },400);
},900);
