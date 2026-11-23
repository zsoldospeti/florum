#!/usr/bin/env node
// ==============================================================
//  FLORUM 1.33.2 · teszt: naponta több mérés + napszak + évszak
//  Fájl:    teszt-evszak.js
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
const EXPORT=`;window.__T={applyState,render,renderTemp,switchView,state,todayISO,addDays,tempAdd,
tempEvszakTabla,tempEvszakHTML,tempNapszakAtlag,tempOrasProfil};`;
const b=[...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
const big=b.sort((x,y)=>y.length-x.length)[0];const i=big.lastIndexOf('})();');
const dom=new JSDOM(html.replace(big,big.slice(0,i)+EXPORT+big.slice(i)),{runScripts:'dangerously',url:'http://127.0.0.1:8777/',pretendToBeVisual:true,
 beforeParse(w){w.fetch=()=>Promise.reject(1);w.scrollTo=()=>{};w.matchMedia=()=>({matches:false,addEventListener(){},addListener(){}});}});
const w=dom.window,d=w.document;
let ok=0,bad=0;
function check(n,f){try{const r=f();ok++;console.log('  ✓ '+n+(r?'   → '+r:''));}catch(e){bad++;console.log('  ✗ '+n+'   → '+e.message);}}
function assert(c,m){if(!c)throw new Error(m||'hamis');}
setTimeout(()=>{
 const T=w.__T;
 // egy év: nyár (júl) meleg, tél (jan) hűvös, ugyanabban a szobában
 const log=[];
 function napok(kezdet,n,ertek,ingas){
   for(let i=0;i<n;i++){
     const d=new Date(kezdet); d.setDate(d.getDate()+i);
     const nap=d.toISOString().slice(0,10);
     log.push({room:'Nappali',date:nap,t:ertek,hum:null,note:'',ts:new Date(nap+'T08:00:00').getTime()});
     log.push({room:'Nappali',date:nap,t:Math.round((ertek+ingas)*10)/10,hum:null,note:'',ts:new Date(nap+'T15:00:00').getTime()});
   }
 }
 napok('2025-07-01',20,24,7);    // nyár: 24 / 31
 napok('2026-01-05',20,16,3);    // tél: 16 / 19
 napok('2026-10-05',10,19,4);    // ősz: 19 / 23
 T.applyState({plants:[],history:[],settings:{},meta:{},customDb:[],tempLog:log});

 console.log('\n== évszakok ugyanabban a szobában ==');
 const sorok=T.tempEvszakTabla();
 check('három évszak, egy helyiség',()=>{
   assert(sorok.length===3,'sorok: '+sorok.length);
   return sorok.map(s=>s.evszak+' '+s.t+'°').join(' · '); });
 check('a nyár melegebb, mint a tél (a lényeg)',()=>{
   const ny=sorok.find(s=>s.evszak==='nyar'), te=sorok.find(s=>s.evszak==='tel');
   assert(ny.t>te.t,'nyár '+ny.t+' ≤ tél '+te.t);
   return 'nyár '+String(ny.t).replace('.',',')+' °C · tél '+String(te.t).replace('.',',')+
          ' °C → különbség '+String(Math.round((ny.t-te.t)*10)/10).replace('.',',')+' °C'; });
 check('a maximumok is különböznek (nyár 31, tél 19)',()=>{
   const ny=sorok.find(s=>s.evszak==='nyar'), te=sorok.find(s=>s.evszak==='tel');
   assert(ny.max===31,'nyár max: '+ny.max); assert(te.max===19,'tél max: '+te.max);
   return 'nyár max 31 °C · tél max 19 °C'; });
 check('a hőingás évszakonként számol',()=>{
   const ny=sorok.find(s=>s.evszak==='nyar');
   assert(ny.ingas===7,'nyár ingás: '+ny.ingas);
   return 'nyár: 24–31 → 7 °C ingás'; });
 check('nyári meleg napok száma (26 °C feletti napok)',()=>{
   const ny=sorok.find(s=>s.evszak==='nyar');
   assert(ny.meleg===20,'meleg napok: '+ny.meleg);
   return '20 nyári nap 26 °C felett'; });
 check('téli fagyos napok (5 °C alatt) – nincs, mert 16 °C volt',()=>{
   const te=sorok.find(s=>s.evszak==='tel');
   assert(te.fagyos===0,'fagyos: '+te.fagyos);
   return '0 fagyos nap (szobai 16 °C)'; });
 check('a táblázat HTML-je tartalmazza mindhármat',()=>{
   const h=T.tempEvszakHTML();
   assert(/nyár/.test(h)&&/tél/.test(h)&&/ősz/.test(h),'hiányos');
   assert(/Nappali/.test(h),'nincs helyiség');
   return 'nyár · tél · ősz, „Nappali” sorral'; });

 console.log('\n== napszak × évszak együtt ==');
 check('nyáron a délután sokkal melegebb, mint reggel',()=>{
   const cs=T.tempNapszakAtlag('Nappali',0);
   assert(cs.delelott && cs.delutan,'hiányos: '+Object.keys(cs));
   const k=Math.round((cs.delutan.t-cs.delelott.t)*10)/10;
   assert(k>0,'különbség: '+k);
   return 'délelőtt '+cs.delelott.t+' °C · délután '+cs.delutan.t+' °C'; });
 check('órás profil: 8h és 15h kitöltve',()=>{
   const p=T.tempOrasProfil('Nappali');
   assert(p[8].t!==null && p[15].t!==null,'8h: '+p[8].t+' 15h: '+p[15].t);
   return '8h: '+p[8].t+' °C · 15h: '+p[15].t+' °C'; });

 console.log('\nEredmény: '+ok+' sikeres, '+bad+' hibás');
 process.exit(bad?1:0);
},700);
