<!-- FLORUM 1.33.4 · otthoni növénygondozó · fájl: README.md (leírás) -->

# 🌿 Florum – otthoni növénygondozó (PC-re, CachyOS/Arch)

**Verzió: 1.33.4** · adatbázis: v2026.10.9 (82 növény)

## 🔎 Új növény egy linkről – nem neked kell beírni mindent

A **+ Új növény** ablakban a név alatt van egy „adatlap kiolvasása” sáv. Beírod a
növény nevét, mellé a **gondozási útmutató linkjét** (szobakertesz.hu, tropusinoveny.hu,
hu.wikipedia.org – bármi), és a Florum **kitölti az űrlapot**:

| Amit kiolvas | Példa (Elefántláb, szobakertesz.hu) |
|---|---|
| Öntözés nyáron | 14 naponta |
| Öntözés télen | 35 naponta (szinte szárazon) |
| Tápoldat | havonta · **télen semmi** |
| Permetezés | nem szereti (nincs permetezés-teendő) |
| Átültetés | 24 hónaponta |
| Fény / hőmérséklet | Napos, déli ablak · 18–27 °C (télen legalább 10 °C) |
| Talaj, páratartalom | kaktuszföld + tőzeg · 30–50% |
| Betegségek, kártevők | szárrothadás, bakteriális levélfoltosság · pajzstetű, takácsatka |

Amit **nem** talál meg, azt **üresen hagyja** – nem talál ki adatot. A talált értékek
mindegyike `[biztos]` (a szöveg kimondja) vagy `[becsült]` (a szövegből számolva, pl.
„kéthetente” → 14 nap); a „Mit találtam?” linken átnézheted, a mezőket bármikor átírhatod.

**Robotvédett oldal?** A szobakertesz.hu „One moment, please…” fedőlapot ad a gépi
letöltésnek. Ilyenkor a Florum **nem áll meg**, hanem felajánlja a **Szöveg beillesztése**
gombot:

1. megnyitod a linket a böngészőben, `Ctrl+A`, `Ctrl+C`,
2. a Florumban **Szöveg beillesztése** → `Ctrl+V`,
3. **Adatok kiolvasása** – ugyanaz az eredmény.

A régi adatbázis-bejegyzés továbbra is működik (név begépelése → automatikus keresés),
és az **Elefántláb** már benne van a 82 növény között, tehát nála elég a nevet beírni.

Parancssor: `python3 novenykereso.py --url "https://…"`, `--fajl cikk.txt`,
`--szoveg "…"`, illetve `--onteszt` (11 beépített minta, hálózat nélkül).

## 🩺 Ha valami nem működik (Napló, lenyílók, verzió)

### A Napló fül üres maradt

**Nem te rontottad el.** Az 1.25.0-ig volt egy hiba: ha egy naplóbejegyzésből
hiányzott az időbélyeg (`ts`), a Napló rajzolója *„Invalid time value”* hibával
elhasalt, és a fül **üresen maradt** – hibaüzenet nélkül. Ez a javított változatban javítva:

- a napot a bejegyzés **`date` mezőjéből** is ki tudja venni, a `ts` nem kötelező;
- a hibás/hiányos bejegyzés **nem borítja fel** az egész fület (kiszűri, illetve
  „Dátum nélküli bejegyzés” címszó alá teszi);
- ha mégis baj lenne, **látszik**: a fül a hibaüzenetet és egy *„Szűrők törlése és
  újrapróbálás”* gombot mutat, nem néma ürességet.

Új elemek a Naplón: **szűrők törlése** gomb, *„N bejegyzés / M összesen”* számláló,
és külön üzenet arra az esetre, ha a szűrő miatt nincs találat (nem az van, hogy
„nincs bejegyzés”).

### A lenyílók (legördülők) nem nyílnak ki KDE-ben

**Ez sem a te hibád.** A KDE-s natív ablak (`florum-kde.py`) QtWebEngine-t használ,
és abban a böngésző beépített `<select>` legördülője bizonyos környezetekben
egyszerűen nem nyílik ki. Ezért a Florum **a javított változattól nem használ natív lenyílót**:
minden legördülő saját gomb + saját lista (`.fsel`), ami böngészőben, a KDE-ablakban
és a fájlból megnyitott lapon is ugyanúgy működik, egerrel és billentyűzettel is
(↑ ↓, Enter, Esc).

A régi `<select>` a lapon marad (rejtve), ezért a mentett adatok és a meglévő
működés nem változott.

> Ha mégis gond van, a **Beállítások → „Rendszer – KDE-ablak / böngésző”** panel
> megmutatja, mit lát a program (környezet, verzió, lenyílók, `<dialog>`, dátummező,
> naplóbejegyzések száma), és van rajta **Napló-ellenőrzés** gomb is.

### „Felül 1.30.6-t ír, lent 1.22-t” – mit rontottam el? Semmit.

Két ártatlan ok van, és mindkettő ugyanarra vezethető vissza: **a futó példány régi**.

| Hol látod | Honnan jön a szám |
|---|---|
| felül (fejléc) | a **megnyitott HTML-fájlból** – ez már az új |
| lent (lábléc) | a **futó Python-szerver** `/api/info` válaszából – ez még a régi, mert a Python a kódot **indításkor a memóriába tölti** |

Vagyis a fájl már új, de a háttérben futó folyamat még a régi kóddal válaszol.
Amit ilyenkor tenni kell (egy sor):

```bash
bash florum-verzio.sh              # megmutatja: mi van a fájlban, mi fut, melyik porton
bash florum-verzio.sh --leallit    # a régi példány leállítása
bash florum-verzio.sh --ujraindit  # leállít + háttérben elindít
```

kézzel ugyanez:

```bash
python3 florum.py --leallit        # minden futó Florum leáll
python3 florum.py --szerver        # az új indul (háttérben)
systemctl --user restart florum-szerver   # ha szolgáltatásként fut
```

Utána a böngészőben **Ctrl+Shift+R**, vagy zárd be a KDE-ablakot és nyisd újra.

#### Ha a régi verzió minden indításnál visszatér

Akkor az **automatikus indítás** vagy a **szolgáltatás** még a RÉGI mappára mutat.
Nézd meg, mit tartalmaz:

```bash
grep -H Exec ~/.config/autostart/florum.desktop
systemctl --user cat florum-szerver | grep ExecStart
```

Ha ott egy másik mappa szerepel (pl. `~/florum-1.22/`), akkor az indul minden
bejelentkezéskor. Javítás az **új** mappából:

```bash
bash install.sh                    # menüparancs + autostart újra, a mostani mappára
bash florum-szolgaltatas.sh telepit  # ha szolgáltatásként használod
```

**A javított változatban a felület egy kattintással meg is oldja:** a piros sávban ott a
**„↻ Újraindítás most”** gomb – leállítja a régi példányt, elindítja az újat, megvárja,
amíg az válaszol, és újratölti az oldalt. (Szolgáltatásként futó Florumnál nem indítja
magát újra, hanem a `systemctl --user restart florum-szerver` parancsot ajánlja.)

**A javított változatban a felület ezt magától jelzi:** ha a futó szerver verziója eltér a
fájétól, piros sáv jelenik meg alul a régi verzióval és a leállítás parancsával,
a lábléc pedig **mindig a fájl verzióját** írja (a futóét csak külön, „futó szerver:”
előtaggal). Az 1.22-es verzió ezt még nem tudta megmutatni – ezért tűnt rejtélynek.

## 🩺 Ha valami nem működik (Napló, lenyílók, verzió)

### A Napló fül üresen marad, vagy nem lehet szűrni

A Napló akkor „nem működik”, ha a fül megnyitásakor nem rajzolódik ki. Ezt a javított változat
teljesen átépítette, mert három hiba volt benne:

| Hiba | Mi történt | Javítás |
|---|---|---|
| **Üres fül** | a fület megnyitáskor nem rajzolta újra (csak akkor, ha közben változott valami) | a fül megnyitása **mindig** friss rajzot ad |
| **Elrontott szűrő** | ha egy szűrő egy már törölt növényre mutatott, minden bejegyzés kiesett | a szűrő magától visszaáll „Minden növény”-re |
| **Hiányzó időbélyeg** | egy régi bejegyzés időbélyeg nélkül **hibára futott**, és a fül üresen maradt | hiányzó dátum nem állít meg semmit – a bejegyzés a „Dátum nélkül” csoportba kerül |

Új a fülön: **szűrők törlése** gomb, **darabszám** (hány bejegyzés, hány növény), és
külön üzenet arra, hogy *„nincs bejegyzés”* vagy *„nincs találat a szűrővel”*.

Ha a Napló mégis üresen maradna, a Beállításokban van **Rendszer** panel
(*„Napló-ellenőrzés”* / *„Napló újrarajzolása”*), és a fül tetején egy piros hibaüzenet
mutatja a hiba okát ahelyett, hogy csendben üresen maradna.

### A lenyílók (legördülők) nem nyílnak ki KDE-ben

A KDE-s ablak (QtWebEngine) a böngésző saját legördülő listáját néha nem tudja
megjeleníteni – ezért a Florumban **a javított változattól minden legördülő saját** (a program rajzolja,
nem a böngésző). Így ugyanúgy működik a KDE-ablakban, Chromiumban és Firefoxban:

- kattints a mezőre → kinyílik a lista (a képernyő alján **felfelé** nyílik),
- nyílbillentyűkkel is választhatsz, `Enter` = kiválasztás, `Esc` = bezárás,
- a natív `<select>` a háttérben marad, csak nem látszik – ezért minden mentés és
  visszatöltés ugyanúgy működik, mint eddig.

Érintett mezők: **Hely**, **Fény**, **Permetezés vize**, **Tápoldat típusa**, a hónapok
(Tápoldat tól–ig, Szezon tól–ig), valamint a Napló szűrői és a Beállítások keresője.

### „Felül új verziót ír, lent régi” – mit rontottam el? Semmit.

Ez a legtöbbször látott „hiba”, és **soha nem a te hibád**. A felső szám a **megnyitott
fájlból** jön (ez már az új), az alsó a **futó Python-szerverből** – a Python pedig a kódot
**indításkor** tölti be a memóriába, tehát a fájl cseréje után is a régi kód fut, amíg újra
nem indítod. Ezen felül a böngésző is megjegyzi a régi oldalt.

Három lépés, ebben a sorrendben:

```bash
bash florum-verzio.sh              # 1) megmutatja: mi van a fájlban, mi fut, melyik porton
bash florum-verzio.sh --ujraindit  # 2) leállít + háttérben elindít
```

3. a böngészőben **Ctrl+Shift+R** (a KDE-ablaknál zárd be és nyisd újra).

A `florum-verzio.sh` minden verzióval működik (csak `bash` és `curl` kell hozzá), és
külön megkeresi az **elárvult régi példányt** több porton (8777–8780) is. Ha a lábléc
továbbra is régi számot mutat, akkor az **autostart vagy a szolgáltatás** indít régi
mappából – ezt is kiírja a script:

```bash
grep -H Exec ~/.config/autostart/florum.desktop
systemctl --user cat florum-szerver | grep ExecStart
```

**A javított változatban a felület is segít:** a lábléc mindig a **fájl** verzióját írja, és ha a futó
szerver eltér, piros sáv jelenik meg a régi verzióval és a `systemctl --user restart`
paranccsal.

## 🕒 KDE panel – Digitális óra és figyelmeztetés

A Florum teendői **iCalendar (`.ics`) naptárfájlba** kerülnek, amit a KDE Plasma
**Digitális órája** eseményként listáz – a panel órájának naptárnézetében és a
felugró naptárban is látszik, mi esedékes. Az események **egész naposak**, és a
számítás ugyanaz, mint a felületen: **téli 1,5×-ös öntözés**, **tápoldat-szünet**
(október–február), **áthelyezett (szundi) teendők** és a **lejárt** tételek (ezek a
mai napra kerülnek, „(lejárt)” jelöléssel).

### Egységes kinézet (a „kék” példány)

A Florum felülete **ugyanazt a közös témát** használja, mint a csomag többi
HTML-appja: sötét alap, jelölt (accent) szín, és jobb alsó sarokban
**Világos / Sötét** váltó. A téma **bele van építve a `florum.html`-be** – nincs
külön `.css` vagy `.js`, a fájl internet nélkül, önmagában is működik.

A beépítés ismételhető (a meglévő témablokkot lecseréli):

```bash
bash kinezet-egyesites.sh                 # sötét az alap
bash kinezet-egyesites.sh --theme light   # világos az alap
```

A választás a böngészőben tárolódik (`florum-ui-theme`), és a `naptar-*.html`,
`linkek-elonezet.html` stb. előnézetek ugyanígy néznek ki.

### Mit ír ki a Florum?

| Fájl / cím | Mit tartalmaz |
|---|---|
| `~/.local/share/florum/florum.ics` | a naptárfájl – **minden mentésnél automatikusan frissül** |
| `http://127.0.0.1:<port>/api/calendar.ics` | ugyanaz élőben, a szerverből (a Beállításokban a **„Naptár (.ics) letöltése”** gombbal) |
| `http://127.0.0.1:<port>/api/calendar` | rövid JSON: hány esemény van, hol a fájl |

Beállítások → **KDE panel – Digitális óra és figyelmeztetés**: itt állítod, hány
**napra előre** (alap: 90) kerüljenek be a teendők, és hány **órakor** szóljon a
naptár-emlékeztető (alap: 8). Mellette látod, hány esemény lesz az időszakban, a
fájl útvonalát („Útvonal másolása” gombbal a vágólapra), és a lépésenkénti
KDE-útmutatót.

### Beállítás a KDE panelen (4 lépés)

1. **Naptár-plugin** telepítése (ez tartalmazza a *PIM Events Plugin*-t):

   ```bash
   sudo pacman -S kdepim-addons
   ```

2. **Jobb klikk a panel Digitális órájára → Beállítások → Naptár** fül →
   jelöld be a **PIM Events Plugin**-t („naptáradatok megjelenítése”).

3. Ugyanott a **PIM** fülön vedd fel a Florum naptárát: **Akonadi → iCal-fájl**
   erőforrás, útvonal:

   ```
   file:///home/<felhasználó>/.local/share/florum/florum.ics
   ```

   (Ha az `akonadiconsole`-t használod: *Agent → Configure → Path*. A
   `~/.config/akonadi_ical_resource_*.rc` fájlban a `Path[$e]=file://…` sor.)
   A Florum újraírja a fájlt, az Akonadi pedig a `REFRESH-INTERVAL` miatt
   óránként újraolvassa – a beállított naptár megjelenik az óra naptárában.

4. **Figyelmeztetés (aszta­li értesítés)** – két lehetőség, bármelyik elég:

   - a Florum saját emlékeztetője: `python3 emlekezteto.py --daemon`
     (vagy a telepített szolgáltatás: `systemctl --user enable --now florum-emlekezteto`),
   - vagy hagyd a KDE-re: az `.ics`-ben minden eseményhez tartozik **VALARM**
     emlékeztető, ezt a KDE naptár-értesítője jeleníti meg.

### Az emlékeztető démon (`emlekezteto.py`)

A `florum-data.json`-ból dolgozik, **nem kell futnia a Florumnak**.

```bash
python3 emlekezteto.py                    # egy kör (ha ma van teendő, szól)
python3 emlekezteto.py --daemon           # folyamatosan, 30 percenként
python3 emlekezteto.py --daemon --intervallum 15
python3 emlekezteto.py --lista            # a mai teendők szövegesen
python3 emlekezteto.py --json             # JSON (panel-szöveg, feed, plasmoid)
python3 emlekezteto.py --panel            # egysoros összefoglaló
python3 emlekezteto.py --ics              # csak a naptárfájl újragenerálása
python3 emlekezteto.py --teszt            # próbaértesítés
python3 emlekezteto.py --elore 3          # a következő 3 napot is jelezze
```

- Az értesítés a **KDE saját értesítési rendszerén** jelenik meg
  (`notify-send -a Florum`), lejárt teendőnél **kritikus** fontossággal.
- **Naponta egyszer** szól (a `emlekezteto-allapot.json` tárolja, miről szólt már),
  így nem zavar ismételten; új teendő esetén viszont újra jelez.
- Minden kimenő értesítés bekerül az `esemenyek.jsonl` naplóba.
- Ha nincs `notify-send` / `kdialog` / `zenity`: `sudo pacman -S libnotify`.

**Rendszerindításkor:** `install.sh` létrehozza a
`~/.config/systemd/user/florum-emlekezteto.service` egységet és be is kapcsolja.
Kézzel:

```bash
systemctl --user enable --now florum-emlekezteto
systemctl --user status florum-emlekezteto
journalctl --user -u florum-emlekezteto -n 30
```

## 📅 Event Calendar widget – a teendők a panelen (Akonadi nélkül)

Ha a beépített Digitális óra PIM pluginja nem használható (lásd lent), a
**Event Calendar** plasmoid (Plasma 6) a jó út: közvetlenül az `.ics` **fájlt**
olvassa, tehát nincs Akonadi, nincs plugin, nincs fagyás.

### Miért nem mutatta semmit?

A widget biztonsági okból **csak a saját adatmappájában** lévő naptárfájlt
hajlandó beolvasni (`package/contents/scripts/icsjson.py` → `parse_calendar_url()`,
`LOCAL_ICS_DIR`). Minden más helyre ezt írja: *„Local calendar file path is
invalid”* – és nem jelenít meg semmit. A Florum saját mappája
(`~/.local/share/florum/`) ebbe nem tartozik bele.

**A Florum 1.15.0 óta ezért minden mentésnél készül egy másolat ide:**

```
~/.local/share/plasma_org.kde.plasma.eventcalendar/florum.ics
```

Ezt az útvonalat kell megadni a widgetben:

1. `bash kde-eventcalendar-telepites.sh` – telepíti a plasmoidot (AUR vagy
   `.plasmoid`) és a Python-függőségeket (`icalendar`, `recurring-ical-events`)
2. Jobb klikk a widgetre → **Configure Event Calendar…** → **Calendars** →
   **Add** → **ICS file**
3. Útvonal: `~/.local/share/plasma_org.kde.plasma.eventcalendar/florum.ics`
   (a Florum Beállítások → KDE panel alatt is látszik, másolás gombbal)

A másolat a Beállításokban kikapcsolható (**„Másolat a widgetnek”**), de akkor
a widget nem fog eseményt mutatni. A Florum az eredeti fájlt változatlanul
továbbra is a saját mappájában írja.

> Ellenőrizve a widget saját beolvasójával: a másolatból a szkriptje
> (13 esemény a 60 napos mintában) hibátlanul listázza a teendőket – a Florum
> saját mappájából viszont `Local calendar file path is invalid` hibát ad.

### Ha a widget mégsem mutatja a teendőket

A widget beállítás-oldala **csendben elutasítja** a nem megfelelő útvonalat: ha a
mezőbe írt szöveg nem `…/plasma_org.kde.plasma.eventcalendar/*.ics` alakú (pl.
`~/.local/…` vagy a Florum saját mappája), akkor **nem történik semmi** – a
naptár `url` mezője üres marad, és a widget nem tölt be semmit. Ugyanígy nem
jelenik meg semmi, ha a naptár nincs beikszelve (`show=false`), vagy ha a
widgetnek nincs meg a Python-függősége.

Ezeket egy lépésben ellenőrzi és javítja a diagnosztika:

```bash
bash kde-eventcalendar-diagnosztika.sh            # csak vizsgál (nem módosít)
bash kde-eventcalendar-diagnosztika.sh --javitas  # a naptár-beállítás rendbetétele
bash kde-eventcalendar-diagnosztika.sh --javitas --restart
```

Mit néz meg:

| Vizsgálat | Mit jelent, ha hibás |
|---|---|
| telepített widget + `icsjson.py` | a widget-változat nem tud `.ics`-t olvasni (másik fork) |
| a widget `icalCalendarList` beállítása | nincs felvéve naptár, üres az útvonal, vagy `show=false` |
| az útvonal szabálya (`/home/<user>/…plasma_org.kde.plasma.eventcalendar/*.ics`) | ezt az útvonalat a widget nem fogadja el |
| a fájl megléte + eseményszáma | nincs másolat, vagy üres a naptár |
| **a widget saját beolvasója** (`icsjson.py`, pontosan úgy hívva, ahogy ő hívja) | a beolvasó hibát ad (pl. hiányzó modul, érvénytelen útvonal) |
| `icalendar`, `recurring-ical-events` modul | a widget nem tud `.ics`-t olvasni |

A `--javitas` biztonsági mentést készít a beállításfájlról
(`…appletsrc.florum-<dátum>.bak`), majd a Florum naptárát **beírja a widget
beállításába** a helyes útvonallal, névvel (`Florum`), színnel és
`show=true`-val – a többi naptár érintetlen marad.

Ha a Python-modul hiányzik, ezzel a widget **saját** mappájába telepíthető
(az `icsjson.py` mindig elsőként innen importál):

```bash
bash kde-eventcalendar-fuggoseg.sh
# → ~/.local/share/plasma_org.kde.plasma.eventcalendar/python
```

### A Florum saját panel-widgetje (ez mindig működik)

A Florumhoz tartozik egy **saját Plasma 6 panel-widget** (`florum-panel/`), ami
nem függ az Event Calendar plasmoidtól, az Akonaditól, a PIM Events Plugintól
vagy a Python `icalendar` modultól. A futó Florumtól kéri el az adatokat:

```
http://127.0.0.1:8777/api/panel.json
```

Telepítés:

```bash
bash telepites-florum-panel.sh              # widget + panel újraindítása
bash florum-szolgaltatas.sh indit           # háttérszerver indítása (és bekapcsolása)
bash telepites-florum-panel.sh --autostart  # widget + háttérszerver egy lépésben
bash telepites-florum-panel.sh --eltavolitas
```

Utána: jobb klikk a panelen → **Panel beállítása → Widgetek hozzáadása →
Florum naptár**.

| Mit tud | Részlet |
|---|---|
| panelen | naptár-ikon + a **mai és lejárt teendők száma** (lejártnál piros) |
| kinyitva | a következő napok listája: növény · teendő · „ma / holnap / 3 nap múlva” · helyiség |
| frissítés | 2 percenként (Beállításokban állítható), és a widget fejlécében gombbal |
| hiba esetén | „A Florum nem érhető el a 8777-es porton.” + mit kell tenni |
| beállítások | Florum címe (más port esetén), sorok száma, frissítési idő |

Az adatot a Florum `panel_data()` függvénye állítja elő a **felületével azonos**
számításból – ugyanaz a téli ritkítás, tápoldat-szünet (okt.–febr.), szundi és
lejárt-kezelés érvényes itt is.

### Külső naptárak: Google Naptár a Florumban

A Florum a saját teendői mellé be tudja olvasni a **már meglévő naptáraidat**, és
ezeket ugyanabban a panel-widgetben mutatja – nincs OAuth, fiók, Akonadi vagy
PIM-plugin. Elég a naptár **iCal (.ics) címe**.

**Beállítások → Naptár-források → Hozzáadás:**

| Mező | Mit írj be |
|---|---|
| Név | pl. `Google – munka` (ez jelenik meg a panelen) |
| iCal cím | `https://calendar.google.com/calendar/ical/…/basic.ics` vagy egy helyi `.ics` útvonala |

Honnan van a Google címe: Google Naptár → a naptár melletti **⋮** → *Beállítások és
megosztás* → **„A naptár integrálása”** → **Titkos cím iCal formátumban**.
Csak olvasásra jó, bármikor visszavonható. A widget ♻ gombja kipróbálja a címet,
és megmutatja, hány eseményt lát a következő 30 napban.

Amit tud:

* **gyorsítótár**: a letöltött naptár a `~/.local/share/florum/naptar-forrasok/`-ban
  marad, ezért internet nélkül is a legutóbbi állapot látszik (30 percenként frissül);
* **ismétlődések**: napi/heti/havi/évi (INTERVAL, COUNT, UNTIL) + EXDATE;
  ha van `icalendar` + `recurring_ical_events` modul, azt használja, különben a
  beépített feldolgozó (ugyanazt az eredményt adja a gyakori esetekben);
* **keverés**: a naptár-események (📅) és a növény-teendők (💧🌿💦🪴) dátum szerint
  egy listában jelennek meg – a lejárt teendők maradnak legfelül;
* a `.ics` **export** továbbra is csak a Florum teendőit tartalmazza (nincs duplikáció).

#### A naptárnézetben is (1.22.4)

A Google Naptár eseményei nem csak a panelen, hanem a **Florum naptárában** is
megjelennek – a növény-teendőkkel egy rácsban:

| Hol | Mit látsz |
|---|---|
| **hónap/nap rács** | a nap cellájában 📅 sorok (időpont + cím), a nap fejlécében `📅N` jelzés |
| **nap-kártya** (jobbra) | a növény-teendők alatt külön **„📅 Naptár"** szakasz – itt nincs „Kész" gomb, mert ez nem a te teendőd |
| **KPI-sor** | új **„📅 Naptár"** kártya a hónap eseményeinek számával |
| **szűrő** | a 📅 kártyára kattintva csak a naptár-események listája (dátum, időpont, hely, naptár neve) |
| **jelmagyarázat** | `▪ naptár (📅)` – a kék négyzet jelöli |

- A Florum **a látható időszakot kéri le** (`/api/calendars?from=…&days=…`), ezért a
  hónap-rács első napjai – amelyek az előző hónapba esnek – is mutatják az eseményeket.
- **Esemény színe**: ha a naptár-forrásnál megadsz színt (pl. `#e01b24`), a pötty
  és a cella-jelzés azt használja; a színt a Florum ellenőrzi (csak `#rgb` / `#rrggbb`).
- Ha nincs naptár-forrás, a naptárnézet **pontosan úgy néz ki, mint eddig** – nincs
  üres 📅 kártya, nincs felesleges sor.
- Parancssori ellenőrzés: `curl -s "http://127.0.0.1:8777/api/calendars?from=2026-10-01&days=62"`.

Parancssorból:

```bash
python3 naptar_forras.py --lista                  # a beállított források kipróbálása
python3 naptar_forras.py --url "https://…/basic.ics"
```

### Miért nem az Event Calendar? – alternatívák

A divinae-féle Event Calendar a Plasma 6-on több helyen elakad (a beállítása
csendben elutasítja az útvonalat, a Google-szinkron OAuth-ja elavult). Ami helyette
szóba jön:

| Megoldás | Miben más |
|---|---|
| **Florum saját widget** (ez a csomag) | nincs OAuth/Akonadi; a növény-teendők **és** a Google Naptár egy helyen, a Florum adja az adatot |
| **KAgenda** (KDE Store, Plasma 6) | Google + Nextcloud **OAuth 2.0**, natív widget, csak naptár (növények nélkül) |
| **ALikesToCode / Tridentu Event Calendar fork** | az eredeti továbbvitt változata, Google-bejelentkezéssel, több fiókkal |
| **lenonk plasma6-applet-eventcalendar** | a Zren-féle widget újraírt portja, Google OAuth + időjárás |
| **google-calendar-widget / Simple Plasma Agenda** | Akonadi + KDE Google-erőforrás (KOrganizer beállítás kell), Plasma 6.6+ |
| **KOrganizer / Kalendar / GNOME Naptár** | teljes asztali naptárprogram, nem panel-widget |
| **Thunderbird** | a `.ics`-t gond nélkül olvassa (ez volt a kiindulópont) |

Ha a Google Naptár a panelen a legfontosabb, a **Florum widget + Google iCal-cím**
kombináció a legkevesebb mozgó alkatrész: nincs token, nincs Akonadi, nincs plugin.

### Hogyan fut a démon?

Két démon van a csomagban, és **csak az egyiket szabad futtatni** – mindkettő
ugyanazt az értesítést adná:

| Egység | Parancs | Mit tud |
|---|---|---|
| **`florum-szerver.service`** *(ez az ajánlott)* | `python3 florum.py --szerver --notify` | a panel-widget **adatforrása** (8777) **és** az értesítés – a Beállításokban megadott **időpontban** (pl. 08:00), naponta egyszer |
| `florum-emlekezteto.service` | `python3 emlekezteto.py --daemon --intervallum 1800` | csak értesítés, 30 percenként ellenőriz; nem indít szervert |

A telepítők ezt maguktól kezelik: ha bekapcsolod a háttérszervert
(`telepites-florum-panel.sh --autostart`), a **másikat kikapcsolják**, és
fordítva: az `install.sh` nem indítja az emlékeztető démont, ha a
`florum-szerver` már engedélyezve van.

#### Melyik folyamat mit csinál

```
systemd --user (bejelentkezéskor, default.target)
└── florum-szerver.service            Restart=always, RestartSec=3
    └── python3 florum.py --szerver --notify
        ├── HTTP a 127.0.0.1:8777-n  → /api/panel.json (panel-widget)
        │                              /api/info, /api/state, /api/calendar.ics …
        ├── 45 mp-enként: eljött-e az értesítés ideje? (Beállítások → Értesítés)
        ├── mentéskor: florum.ics + másolat a widget mappájába
        └── kiírja: ~/.local/share/florum/szerver.json ({port, url, pid, mode})
```

Az értesítés naponta **egyszer** megy ki: a `notify-state.json` tárolja, hogy
melyik nap szólt már (`lastDate`, `lastCount`, `lastRun`) – ezért nem spammel,
ha a szolgáltatás közben újraindul.

#### Parancsok

```bash
systemctl --user status florum-szerver      # fut-e, mióta, mennyi CPU
systemctl --user restart florum-szerver     # újraindítás (pl. frissítés után)
systemctl --user stop florum-szerver        # leállítás
journalctl --user -u florum-szerver -f      # élő napló
bash telepites-florum-panel.sh --allapot    # port, válaszidő, utolsó értesítés
bash telepites-florum-panel.sh --naplo      # az utolsó 20 naplósor
```

A `--allapot` ezt is megmondja, ha gond van:

| Üzenet | Mit jelent |
|---|---|
| `✗ a florum-szerver szolgáltatás telepítve van, de nem fut` | nem indult el: `bash florum-szolgaltatas.sh indit` |
| `✗ a szolgáltatás NINCS telepítve` | a `.service` fájl hiányzik: `bash florum-szolgaltatas.sh telepit` |
| `Unit florum-szerver.service not found` | ugyanez systemctl-től: a Florum mappájában `bash florum-szolgaltatas.sh indit` |
| `✗ nincs notify-send` | `sudo pacman -S libnotify` – enélkül csak a naplóba ír |
| `a külön emlékeztető démon is fut` | dupla értesítés lesz: `systemctl --user disable --now florum-emlekezteto` |

> Ha az értesítés nem jelenik meg, de a szolgáltatás fut: a Beállításokban az
> **Értesítés** kapcsoló legyen be, és az időpont már elmúlt (pl. 08:00).
> Kézi próba: `notify-send -a Florum "próba" "működik"`.

#### Monokróm panel-ikon

A widget saját, monokróm ikont hoz (`florum-panel/contents/icons/`), nem a naptár-emoji
és nem a `view-calendar`:

| Fájl | Mire való |
|---|---|
| `florum-symbolic.svg` | `currentColor` – a Plasma témaszínére vált, ez a hivatalos „symbolic” változat |
| `florum-sotet.svg` | sötét ikon világos panelre (Breeze Light) |
| `florum-vilagos.svg` | világos ikon sötét panelre (Breeze Dark) |

A widget a **panel szövegszínéből** dönti el, melyiket tölti be
(`Kirigami.Theme.textColor`), tehát téma- vagy panelváltásnál magától átvált.
A telepítő a `florum-symbolic.svg`-t a téma ikonmappájába is bemásolja
(`~/.local/share/icons/hicolor/scalable/apps/`), így a „Widgetek hozzáadása”
listában is ez látszik.

A minta: `panel-ikon.png` (sötét és világos panelen, 22 / 48 / 96 px-en).

#### A port: 8777 – és ami mögötte van

A Florum **1.19.0-tól mindig a 8777-es porton** figyel (korábban véletlenszerű portot
választott, ezért nem találta meg a widget). Ha a 8777 foglalt, akkor 8778, 8779…
következik – a widget ezeket magától végigpróbálja. A futó szerver elérhetőségét
egy leíró fájl is rögzíti:

```
~/.local/share/florum/szerver.json     # {port, url, pid, mode, version, started}
```

Háttérszerver (hogy a widgetnek akkor is legyen adata, ha az ablak zárva van):

```bash
bash florum-szolgaltatas.sh indit             # beírja az egységet + elindítja + bekapcsolja
bash florum-szolgaltatas.sh allapot           # telepítve van? fut? melyik porton?
bash florum-szolgaltatas.sh naplo             # az utolsó 20 naplósor
bash florum-szolgaltatas.sh kikapcsol         # leállít + kiveszi az autostartból
bash florum-szolgaltatas.sh eltavolit         # az egység törlése
```

> **Miért van külön szkript?** A `systemctl --user start florum-szerver` csak
> akkor működik, ha a `florum-szerver.service` már benne van a
> `~/.config/systemd/user` mappában. A `florum-szolgaltatas.sh` ezt magától
> elvégzi, tehát nem jöhet a `Unit florum-szerver.service not found`.
> (A `telepites-florum-panel.sh` 1.22.2-től szintén mindig beírja az egységet,
> csak éppen bekapcsolni nem kapcsolja be `--autostart` nélkül.)

A `florum-szerver.service` így indul: `python3 florum.py --szerver --notify`
(fejetlen mód, nincs böngésző, `Restart=always`). Az emlékeztető démont nem kell
külön indítani mellette – a `--notify` ezt is ellátja.

> Miért van rá szükség? A divinae-féle Event Calendar widget a Plasma 6 újabb
> verzióin gyakran nem hajlandó `.ics`-t megjeleníteni (a beállítása csendben
> elutasítja az útvonalat, vagy a beépített `icsjson.py` hibázik). A Florum saját
> widgetje ezt a láncot teljesen megkerüli.

### Magyar felirat a widgethez

Az Event Calendar plasmoidhoz **nincs magyar fordítás** (a hivatalos
`template.pot` 587 szövegéhez csak da, de, fr, es, … fájl van). A Florum
mellé ezért el[készült a magyarítás](forditas/):

```bash
bash kde-eventcalendar-magyar.sh      # telepítés + panel újraindítás
```

- `forditas/hu.po` – a teljes fordítás (587/587 szöveg, 100%)
- `forditas/plasma_applet_org.kde.plasma.eventcalendar.mo` – a KDE által
  betöltött bináris nyelvi fájl,
- `forditas/keszit.py` – újragenerálja a `.po`/`.mo` párost a sablonból,
  ellenőrzi a `%1`/`%2`/`%u` jelölőket és a többes számot,
- `teszt-forditas.py` – **7/0** teszt (teljesség, jelölők, betölthetőség,
  többes szám, terméknevek),
- `kde-eventcalendar-magyar.sh` – telepíti ide:
  `~/.local/share/locale/hu/LC_MESSAGES/…mo` (rendszer-szintű plasmoidnál is
  működik), és újraindítja a plasmashelt. Visszavonás: a `.mo` törlése.

A hónap- és napnevek a Plasma régió-beállítását követik
(Rendszerbeállítások → Nyelv és régió → Régió: Magyarország).

Az előnézet: `forditas-elonezet.html` (angol → magyar táblázatok a widget
fő felületeiről).

### ⚠ Ha a **PIM fül üres**, vagy a panel **lefagy**

Ez **ismert KDE-hiba**, nem a Florum hibája. A Digitális óra naptár-pluginja
(`PIM Events Plugin`, a `kdepim-addons`-ból) nagy naptárnál vagy tömeges
esemény-változásnál befagyasztja a plasmashelt – a hibajegyek: **526769**
(plasmashell több GB memóriát eszik és az OOM killer leöli), **493415**,
**523046**, **442100** (az első megnyitáskor nem listáz eseményt, ez a 6.7.5-ben
javítva). A `kdepim-addons` és a `korganizer` **telepítése nem oldja meg**: a
KOrganizer is ugyanezt az Akonadi-utat használja, a fagyás a pluginban van.

A Florum oldaláról ezt tudtuk tenni:

- **állandó UID-k** (1.14.1): az esemény-azonosító a *növény + teendő +
  sorszám*, nem a dátum és nem a név. Így ha egy teendőt elvégzel, eltolsz vagy
  átnevezel egy növényt, a naptárbejegyzés **nem tűnik el és nem jelenik meg
  újra** – ez volt a fagyás fő kiváltója (a plugin minden eltűnt UID-nél
  újraépíti a modellt).
- **figyelmeztetés a felületen**, ha 120 fölé megy az események száma, és
  javaslat az előretekintés csökkentésére (30–60 nap).

Amit tehetsz, sorrendben:

**1. Kapcsold ki a PIM plugint – fagyás nélkül.** A kerülőút a KDE-fórumról
származik: a naptár-kijelölést **úgy kell módosítani, hogy a plasmashell közben
ne fusson** (indításkor a plugin csak hozzáad, nem töröl). Ezt a szkript elvégzi
helyetted, biztonsági mentéssel:

```bash
bash kde-pim-kikapcsolas.sh
```

**2. Nézd meg, mit lát a rendszer** (csak olvas, nem módosít): csomagok, fut-e az
Akonadi, van-e iCal-erőforrás, be van-e állítva a plugin, hány esemény van a
Florum naptárában, fut-e az értesítő démon:

```bash
bash kde-allapot.sh
```

Ha ez azt írja, hogy **nincs `akonadictl`** vagy üres az Akonadi, akkor a PIM
fülön tényleg nincs mit választani – nem konfigurációs hiba, egyszerűen nincs
naptárforrás.

**3. Akonadi nélküli panel: Event Calendar plasmoid.** Ez a widget közvetlenül
az `.ics` **fájlt** olvassa (nem Akonadi), tehát nem tud lefagyni:

```bash
bash kde-eventcalendar-telepites.sh   # yay/paru, vagy kézi .plasmoid
```

Majd: jobb klikk az új widgetre → **Configure Event Calendar → Calendars → Add →
ICS file** → `~/.local/share/florum/florum.ics`. (A widget a `icalendar` és a
`recurring-ical-events` Python-csomagot használja, a szkript ezt is telepíti.)

**4. A legbiztosabb út: a Florum saját értesítése.** Nem függ Akonaditól, KDE
plugintól vagy paneltől:

```bash
python3 emlekezteto.py --daemon
systemctl --user enable --now florum-emlekezteto
```

> Ha később mégis vissza akarod kapni a beépített óra naptárát: a szkript kiírja
> a biztonsági mentés útvonalát, onnan visszamásolhatod
> (`cp ~/florum-kde-backup-*/* ~/.config/`), de a fagyás addig visszatérhet,
> amíg a KDE-beli hiba (526769) javítása meg nem érkezik.

### Ha nem a beépített óra-naptárat használod

- **`plasma-applet-eventcalendar`** (Plasma 6) közvetlenül beolvassa az `.ics`
  fájlt – ott a *Calendars → Add → ICS file* alatt add meg ugyanezt az útvonalat.
- **`plasma-calendar-homefeed`** JSON-feedet olvas: a `emlekezteto.py --json`
  kimenetét kiírathatod egy fájlba (pl. `emlekezteto.py --json > feed.json`
  cron/systemd timer-rel), és azt kötheted be.

### Parancssori kapcsolók (a Florum mellett)

```bash
python3 florum.py --ics-days 120 --ics-alarm 7   # előretekintés + emlékeztető órája
python3 florum.py --no-ics                        # ne írjon naptárfájlt
python3 naptar_ics.py --print --days 30            # .ics a képernyőre (ellenőrzéshez)
python3 naptar_ics.py --out ~/naptar.ics           # saját helyre
```

> A `.ics` export és az élő letöltés csak a `florum.py`-val indított módban
> működik (fájlrendszer-hozzáférés kell hozzá); statikus előnézetben a gomb nem
> jelenik meg.


## Naptár – három nézet

A **Naptár** fül ugyanazt az ütemezést mutatja három felbontásban, jobb felső
**Nap / Hónap / Év** kapcsolóval:

| Nézet | Mit ad |
|---|---|
| **Nap** | a hónap rácsában minden napnál látszanak a **növénynevek** (nem csak színes pöttyök), a cella háttere a nap terhelését jelzi, a hét napjai külön sávban nagyíthatók |
| **Hónap** | nagyobb cellák (több név fér el) + **növényenkénti táblázat**: melyik növénynek hány öntözése / tápoldatozása / permetezése / átültetése van a hónapban, és mennyi van kész |
| **Év** | 12 **hónapkártya** terhelés-sávval + 12 oszlopos éves áttekintés: látszik, hogy tavasszal és nyáron sokszoros a munka, télen pedig visszaesik |

**Link-címkék és gyorsgomb:** a linkekhez **címke** adható (a mező kínálja:
*bolt, gondozás, adatlap, fórum, inspiráció, betegség, egyéb* – de bármit beírhatsz, a kis- és
nagybetű nem számít). A címke szerint
- a **menüben csoportosítva** jelennek meg a linkek (csoportfejléc + darabszám, az ismeretlen
  címke a végére, a címke nélküliek legvégül),
- a **növénykártyán** a chip viseli a címkét (`[bolt] Webshop`), és a sorrend is címke szerinti.

**Gyorsgomb a naptárban:** a cellában a név végén (a sorra vive), illetve a nap kártyáján a
**fotó sarkán** van egy kis linkgomb. Egy linknél azonnal megnyitja; több linknél a címkék
szerinti választó jön. Link nélküli növénynél a gomb nem is jelenik meg, tehát nem zsúfolja a naptárat.

**Saját név (ahogy te hívod):** ha a növényt más néven ismered, mint ahogy az
adatbázisban szerepel (pl. a *Békeliliom* nálad *vitorlavirág*), megadhatod a saját nevet:

- a **név menüjében** (`✎ Saját név hozzáadása/módosítása`) vagy a növény
  **szerkesztőjében** („Saját név (ahogy te hívod)” mező);
- a saját név jelenik meg a **listában, a naptárban és a Ma nézetben**, a hivatalos név
  mellette kisebb betűvel – a Beállításokban a sorrend **megfordítható**;
- a **kereső mindkettőre talál** (saját név, hivatalos név, latin név, faj);
- az **adatlap és az adatbázis-kapcsolat** a hivatalos nevet használja, tehát az automatikus
  kitöltés és a gondozási adatok változatlanul működnek;
- új növény felvételekor a **megszokott név is eltalálja a fajt**: a név-kereső a
  részleges egyezést is felajánlja (pl. „vitorlavirág” → *Békeliliom*), és ha nem választod
  ki a találatot, mentéskor akkor is összekapcsolja – de csak akkor, ha egyetlen növényre
  illik, hogy ne keverje össze a fajtákat.

**Linkek a növényekhez + keresés a névre:** minden növényhez felvehetsz **saját
hivatkozásokat** (bolt, gondozási útmutató, fórum, mérgezőség-adatlap…):

- a növény szerkesztőjében a **„＋ Link hozzáadása”** gombbal: megnevezés + webcím
  (a megnevezés maradhat üres, olyankor a domain lesz a címke; ha nincs `https://`,
  kiegészíti; `javascript:`/`data:` linket nem enged be);
- a **Növények** fülön a kártyán **chipként** jelennek meg (max. 3, a többit a „+N” nyitja),
  és **új fülön** nyílnak (`rel="noopener noreferrer"`);
- az **adatlap** alján is ott vannak, akkor is, ha az adatbázisban nincs bejegyzés.

A **növény nevére kattintva** (Ma nézet, naptár, Növények fül) egy kis menü nyílik:
a saját linkek, majd **Keresés a weben** (a motor a Beállításokban választható:
DuckDuckGo / Google / Bing / Wikipédia), **Képek keresése**, **Wikipédia** – mindegyik a
növény nevével és fajával indul, új fülön –, valamint *Adatlap*, *Link hozzáadása* és
*Szerkesztés*. A Beállításokban a név-kattintás **kikapcsolható** (kényes kattintásnál,
húzásnál hasznos); link meglétekor viszont ilyenkor is kattintható marad. A naptárban a
húzás és a név-kattintás nem ütközik: húzás után 260 ms-ig nem nyílik menü.

**16:9 nézet (PC / TV):** a fejléc `16:9` gombjával (vagy Beállítások → Megjelenés)
a tartalom egy **16:9 arányú lapra** kerül, ami a képernyő magasságához igazodik:
16:9 monitoron kitölti a képet, magasabb ablakban felül-alul keskeny sáv marad. Ilyenkor
- a naptár **rácsa és a nap kártyája egymás mellett** van (széles kép, görgetés nélkül),
- a cellamagasság a kép magasságából számol (`--cal-cell-h`), a jobb oldali lista saját
  görgetősávot kap,
- a térközök, betűméretek és kártyák sűrűbbek lettek, hogy egy hónap elférjen.
A Beállításokban van **⛶ Teljes képernyő** gomb is (a böngésző kerete eltűnik, Esc kilép).
Az `Automatikus` mód változatlanul teljes szélességű, görgethető.

**Fotók a naptárban:** ha egy növényhez van feltöltött kép, a cellában és a nap
kártyáján a **növény fotója** jelenik meg a színes pötty helyett (a keret színe továbbra is a
tevékenységet jelöli). Fotó nélkül marad a pötty, tehát semmi nem törik el.

**Teendő áthelyezése (húzd és ejtsd):** a soron következő teendőt a cellából **át lehet húzni
egy másik napra**, vagy a nap kártyáján a **dátummezővel** pontos napot adni (egér nélkül is
működik). Ez ugyanaz a mechanizmus, mint a „szundi", csak bármelyik mai vagy jövőbeli napra
szól – előrehozni is lehet. Múltbeli napra nem engedi (üzenet jelzi), a soron következő
esedékesség húzható, a távoli jövőbeliek nem, hogy ne lehessen félreérteni. Az áthelyezett
sor „áthelyezve …-ról" jelölést kap, `↺` gombbal visszaáll az eredeti időpontra, a toast
**Visszavonás** gombja is működik, teljesítéskor pedig magától megszűnik.

Ezen felül:
- a cella tetején a **napi teendők száma**, alján színkódolt sáv (öntözés / tápoldat /
  permetezés / átültetés aránya), a kész teendők áthúzott névvel;
- a nap kiválasztva **Kész** és **Szundi 2 nap** gombbal, és „Összes kész" a teljes napra;
- a múlt a **történetből** jön (amit tényleg megcsináltál), a jövő a **számolt ütemezésből** —
  így a naptár visszamenőleg is igazat mutat;
- a KPI-kártyák a nézetnek megfelelően számolnak (havi vagy éves), rájuk kattintva
  az adott tevékenység teljes listája jön;
- hónapkártyára vagy éves oszlopra kattintva **átszűr** az adott hónapra.

## Mentések – előzmény minden módosításról

Minden mentés után **automatikus pillanatkép** készül. A megőrzés szándékosan nem
„minden mentés 30 napig" (az egy szerkesztésből 200 fájlt csinál, és 30 nap múlva mindet
egyszerre törölné), hanem négy szint:

| Szint | Mikor készül | Meddig marad |
|---|---|---|
| `perc-*` | minden módosítás (azonos tartalmat kihagy) | a legutóbbi **20** |
| `napi-*` | a nap **első** mentése | **30 nap** |
| `havi-*` | a hónap **első** mentése | **12 hónap** |
| `kezi-*` | kézi mentés / visszaállítás előtti állapot | **soha nem törlődik** |

Helye: `~/.local/share/florum/mentes/` (`florum-<szint>-<dátum>-<idő>.json`).

- **Beállítások → Mentések**: a mentések listája, **Visszaállítás** gombbal (a mostani
  állapot előbb automatikusan elmentődik, tehát a visszaállítás is visszavonható),
  **Mentés most**, és **Csomag letöltése (.zip)**.
- A törlés **indításkor** fut, csak a saját névmintára illeszkedő fájlokra, és a
  legfrissebb 10 mentést akkor is megtartja, ha elvileg mind lejárt.
- Sérült mentést nem ír ki (írás után visszaolvassa), és a visszaállítás a legfrisseb
  **ép** fájlt választja.
- API: `GET /api/snapshots`, `POST /api/snapshots/create`, `POST /api/snapshots/restore`,
  `GET /api/snapshots/export` (zip).

## Mi van a csomagban? (és mihez kell)

| Fájl | Mi ez? | Kellesz-e futtatáshoz? |
|---|---|---|
| **`florum.html`** | **Maga az alkalmazás** – a felület, a CSS és az összes logika **egyetlen fájlban** | ✅ ez az egyetlen, ami feltétlenül kell |
| `florum.py` | Asztali indító: helyi szerver, **fájlba mentés**, fotók, értesítések | ✅ ajánlott (fájlmentéshez) |
| `mentes.py` | Előzményes mentés-modul (perc/napi/havi/kézi szintek) | ✅ kell a `florum.py` mellé |
| `plants-db.json` | A növény-adatbázis (82 növény, v2026.10.9 · 70 szobanövény + 12 kerti) – cserélhető, frissíthető | ✅ ajánlott |
| `florum-verzio.sh` | **„Mi fut valójában?”** – fájl-, folyamat- és port-verziók egy képernyőn; `--leallit`, `--ujraindit` | ⬜ hibakereséshez |
| `novenykereso.py` | **Új növény adatlapjának kiolvasása linkről vagy bemásolt szövegből** (a „Adatok kiolvasása” gomb motorja) | ✅ a linkről kitöltéshez |
| `build-plant-db.py` | Adatbázis-építő segédszkript (a JSON és a HTML-be ágyazott tartalék újragenerálása) | ⬜ csak ha adatbázist bővítesz |
| `install.sh` | Menüparancs telepítése a programmenübe | ⬜ opcionális |
| `florum.desktop` | Kész menüparancs (kézi telepítéshez) | ⬜ opcionális |
| `florum.svg` | Ikon | ⬜ opcionális |
| `README.md` | Ez a leírás | – |
| `VERSION` | Verziószám | – |
| `teszt-tel.js` | Téli időszak, klívia-ütemezés, februári emlékeztető: `node teszt-tel.js` | ⬜ fejlesztői |
| `teszt-lenyilo.js` | Napló fül + lenyílók tesztje valódi DOM-motorral (jsdom): `node teszt-lenyilo.js` | ⬜ fejlesztői |
| `teszt-dom.js` | Füstteszt ál-DOM-mal, dátum szimulálásával: `FAKE_TODAY=2027-02-10 node teszt-dom.js` | ⬜ fejlesztői |

> **Kell külön `.css` és `.js` fájl? Nem.** A Florum szándékosan egyetlen, önálló HTML-fájl:
> benne van a stíluslap (`<style>`) és a teljes program (`<script>`) is. Így dupla kattintásra,
> internet nélkül, bármilyen böngészőben elindul – nincs telepítés, nincs build, nincs
> függőség. Fejlesztéshez szét lehet bontani `index.html` + `style.css` + `app.js` fájlokra
> (szólj, és elkészítem azt a változatot is), de a használathoz ez nem szükséges.

Minden fájl ugyanazzal a fejléccel kezdődik (név, verzió, szerep, licenc), és a csomag
`florum-1.4.0/` mappába csomagolva érkezik.


Növényazonosítás nélküli gondozás-segítő: beírod a növény nevét, az app **kitölti az
általános adatlapot egy bővíthető adatbázisból** (öntözési időközök, téli érték, fényigény,
páratartalom, hőmérséklet, talaj, mérgezőség, betegségek, kártevők, tippek), és onnantól
számolja, mi mikor esedékes.

**Az adatok nem a böngészőben, hanem a saját mappádban, egy JSON-fájlban vannak.**

```
~/.local/share/florum/
├── florum-data.json       ← növények, napló, beállítások (ezt menti)
├── florum-data.bak.json   ← előző állapot biztonsági másolata
└── plants-db.json         ← letöltött/importált növény-adatbázis (ha van ilyen)
```

---

## 1. Indítás

### Ajánlott: asztali indító (fájlmentéssel)
```bash
cd florum
python3 florum.py --app
```
Ez elindít egy apró, csak a gépeden elérhető webszervert, és **Chrome/Chromium app-módban**
nyitja meg az appot (nincs címsor, saját ablak). A mentés ilyenkor a fenti mappába megy.
Bezárás: `Ctrl+C` a terminálban.

Ha nincs Chromium-alapú böngésződ, sima böngészőablakban nyílik meg:
```bash
python3 florum.py
```

### Programmenübe (CachyOS menü → „Florum”)
```bash
cd florum
./install.sh
```
Csak a `~/.local/share/applications/florum.desktop` fájlt és az ikont hozza létre,
rendszerszinten semmit nem telepít. Utána a menüből indítható, KDE-n kitűzhető.

### Csak a HTML (tartalék mód)
A `florum.html` önmagában is működik – de ilyenkor a böngésző tárhelyére ment, nem fájlba.
A fejlécben ilyenkor sárga **„Helyi tárhely”** jelző látszik.

---

## 2. Növény felvétele – automatikus kitöltés

1. **+ Új növény** → a **Név** mezőbe kezdd el írni: `monst`, `anyós`, `kakt`, `páfr`, `citrom`…
2. A legördülő listából válassz (magyar név, latin név és álnevek alapján is keres).
3. A program **kitölti**: öntözés (nyári/téli), tápoldat, permetezés, átültetés, fényigény,
   latin név – és egy zöld panelben mutatja a betegségeket, kártevőket, öntözést, hőmérsékletet.
4. „Teljes adatlap ›” → részletes kártya: talaj, mérgezőség kisállatokra, tippek.
5. Bármit felülírhatsz. Ha a pontos nevű növény nincs az adatbázisban, kézzel is beírhatod.

A kártyán az **i** gomb bármikor újranyitja az adatlapot, a **mérgező** jelzés pedig
figyelmeztet, ha macska/kutya van a háznál.

**Adatbázis tartalma:** 82 növény (70 szobanövény + 12 kerti), egyenként 13 adatmezővel (+ a permetezés vize).

- **Szobanövények:** Monstera, Anyósnyelv, Aranypothos, Zamioculcas, fikuszok, Orchidea,
  Kalatea, páfrányok, pozsgások, kaktusz, citrus, Dieffenbachia, Hoya…
- **Konyhai maradékból nevelhető dísznövények** (álnevükben „magról nevelhető”, így egy
  kereséssel kilistázhatók): Gyömbér, Kurkuma, Avokádó, Ananász, **Édesburgonya,
  Fokhagyma (hagymazöld), Citrusmag (citrom/narancs), Datolyapálma, Mangófa, Kivi, Maracuja
  (passion fruit)**
- **Cserépben nevelhető fűszernövények** (álnevükben „fűszernövény”): Bazsalikom, Menta,
  Rozmaring, Levendula, **Petrezselyem, Snidling, Oregánó, Kakukkfű, Zsálya, Koriander,
  Citromfű, Majoranna**

- **Virágzó szobanövények közül új:** **Klívia (Clivia miniata)** – szobaliliom, kafferliliom.
  Különlegessége a **téli pihentetés**: októbertől januárig 10–12 °C, szinte semmi víz, és
  **egyáltalán nincs tápoldat** – enélkül tavasszal nem hoz virágot. Az app ezt külön kezeli:
  a „Télen nincs tápoldat (pihenő)” jelölőnégyzettel a naptár a téli hónapokat kihagyja, és
  **március 1-jén** automatikusan újraindítja a 2 hetes tápoldatozást.

### 🧪 Tápoldatozás – mivel, mennyit, mikor

A „30 naponta tápoldat” nem elég pontos. A növény adatlapján most **négy dolgot** lehet
megadni, és a Florum ezekből írja meg a teendőt, a naptárt és az értesítést:

| Mező | Példa | Mire jó |
|---|---|---|
| **Tápoldat típusa** | tápoldat · levéltápoldat · virágzó · kaktusz · szemcsés · komposzt · istállótrágya · **nem tápoldatozom** | az összetétel és a felirat innen jön |
| **Adag** | *2 ml / 1 l víz* · *1–2 marék komposzt / m²* | a teendő sorában ott van, nem kell keresgélni |
| **Összetétel (N-P-K)** | *N-P-K 7-3-5 (univerzális)* · *magas kálium (pl. 5-5-10)* | virágzásnál / termésnél más kell |
| **Melyik hónapokban** | *márciustól szeptemberig* (alap) | **ez dönti el, mikor van egyáltalán tápoldatozás** |

Amit ebből a program csinál:

- a teendő szövege lesz: **„Tápoldatozás · levéltápoldat · 2 ml / 1 l víz · N-P-K 7-3-5 · március–szeptember”**;
- a hónap-ablakon **kívül egyáltalán nem generál tápoldat-teendőt** – se a „Ma” listán, se a
  naptárban, se a panelen, se az értesítésben, se az `.ics`-ben;
- az ablak **átfordulást is kezel** (pl. *novembertől februárig*), tehát a téli pihenő nem
  „eltolódik”, hanem pontosan ott kezdődik, ahol kell;
- **„nem tápoldatozom”** esetén a tápoldatozás teljesen kikapcsol (a többi teendő marad);
- a naptárban a pihenő után **a hónap-ablak első napján** (alapból március 1.) folytatja –
  nem csúszik el hétről hétre;
- az adatbázisból felvett növények **magukkal hozzák a profilt**, tehát a Monstera 7-3-5-öt,
  a Klívia virágzó tápoldatot, a kaktusz 3-5-7-et kap – neked csak ellenőrizni kell.

**Két régi beidegződés, ami már nem kell:** a „télen nincs tápoldat” jelölő és a kézzel
beírt téli napok. A hónap-ablak váltja ki mindkettőt (a klíviánál ez április–szeptember,
illetve a hűvös pihenő miatt március–szeptember).

### 🥕 Kert fül – a kerti növények külön helyen

> **Javítva:** a „Hely” mezőben most már van **Kert**, **Kerti ágyás** és
> **Üvegház** – és ha ezeket választod, a növény **magától kerti növény lesz** (a kerti
> jelölő bekapcsol, a Kert fülre kerül). A korábban felvett, „Kert” helyű növények
> automatikusan átkerülnek. Ha pedig egy növényt utólag tennél át, a Kert fül alján van
> **„Áthelyezés a kertbe”**: egy kattintás, és kész.

A kerti növényeknek **saját fülük** van (**Kert**, a Naptár mellett), mert náluk nem az a
kérdés, hogy „ma mit kell”, hanem hogy **szezonban vagyunk-e**.

| A fülön | Mit mutat |
|---|---|
| Fejléc | *„Most 2 növény van szezonban · 3 pihen · a mai nap: október”* |
| Négy szám | **szezonban** · **ma esedékes** kerti teendő · **szedhető** · **pihen** |
| Szezon-csík | 12 hónapos csík minden növényen; a szezon hónapjai zöldek, a mai hónap bekeretezve |
| Vetés / Betakarítás | a növény saját adatai, szedési időben **„most szedhető”** jelzéssel |
| Trágyázás | *komposzt · 2–3 marék / m² · április–július* (a profil szerint) |
| Teendők | öntözés/trágyázás **Kész** gombbal, ugyanaz, mint a Növények fülön |
| Pihenő lista | *„❄ Zöldborsó · szezon: március–június · újraindul: március 1. (127 nap)”* |

- **A fül ikonján szám-jelző** van, ha kerti teendő esedékes (a „Ma” fül mellett ez a
  leggyorsabb ránézés).
- A **„+ Kerti növény”** gomb az űrlapot már **kerti módban** nyitja: bekapcsolt jelölő,
  szezon április–október, komposzt-trágya, 4 napos öntözés – csak a nevet kell beírni.
- A szezonon kívüli növény **nem tűnik el**, csak a „Pihen” listára kerül, dátummal, hogy
  mikor indul újra. Így a kert sosem „ürül ki” télen.
- A szobanövényeid továbbra is a **Növények** fülön vannak; a kerti növények mindkét helyen
  látszanak (a Növények fülön `🌱 kerti növény` címkével).

### 🥕 Kerti növények – hagyma, répa, saláta, paradicsom

A kert nem szobanövény: **télen nincs dolga**. Ezért a Florum új „kerti növény” módot kapott.

- Az űrlapon a **„Kerti növény (szezonális)”** jelölő bekapcsolja a szezont, és megjelenik
  három plusz mező: **szezon** (tól–ig), **vetés** és **betakarítás** (szövegesen, pl.
  *„március–április (magról vagy dughagymából)”*, *„július–augusztus”*).
- **A szezonon kívül egyetlen teendő sincs** – se öntözés, se trágyázás, se permetezés,
  se átültetés. A naptár a szezon első napján (pl. április 1.) veszi fel újra a fonalat.
- Szezonon belül a felirat **„Trágyázás”** (nem „Tápoldatozás”), és komposzt/istállótrágya
  adag jelenik meg: *„Trágyázás · komposzt · 2–3 marék érett komposzt / m² · április–július”*.
- A növénykártyán `🌱 kerti növény · április–október` címke mutatja a szezont, az adatlapon
  pedig a **Vetés** és **Betakarítás** sor.
- Az adatbázisban **12 kerti növény** van: Vöröshagyma, Kerti fokhagyma, Sárgarépa, Cékla,
  Retek, Fejes saláta, Paradicsom, Paprika, Uborka, Burgonya, Eper, Zöldborsó – mindegyiknél
  kész szezonnal, vetési és szedési idővel, valamint a hozzá illő trágya-profillal
  (a borsó például **nem** kap nitrogént, mert maga köti a levegőből; a burgonya istállótrágyát
  kap **ősszel**, ezért ott az ablak szeptember–október).

> **A szabály egy helyen van.** A felület, a `florum.py` (Ma nézet, panel, értesítő) és a
> `naptar_ics.py` (.ics, Event Calendar) ugyanazt a hónap-ablakot és ugyanazt a szezont
> használja – ezért nem fordulhat elő, hogy a felület mást mond, mint a naptár.

### Téli időszak – automatikusan, a dátum szerint

- **Okt. 1. – febr. 28/29.** között az app magától téli üzemmódba vált
  (**1.17.0-tól ez a határ mindenhol ugyanaz**: a felület, a `.ics` naptár, a
  KDE-panel és a háttér-emlékeztető is októbertől számol – korábban a Python-oldal
  csak novembertől): a téli öntözési
  értékek érvényesek, a „pihenő" növények nem kapnak tápoldatot. **Március 1-jén** visszaáll.
- A Beállításokban három mód választható: **Automatikus** (alap) · **Mindig tél** · **Kikapcsolva**,
  alatta az aktuális állapot: *„Most: TÉLI időszak (2026. 10. 01. – 2027. 02. 28.) · 129 nap van hátra"*.
- A régi „téli ritkítás" kapcsoló beállítása automatikusan átkerül: kikapcsolt → *Kikapcsolva*, egyébként *Automatikus*.

### Növényenként: hűvös telelés + februári emlékeztető

- Az űrlapon külön jelölő: **„Hűvös helyen telel (10–12 °C)"** – a kártyán `❄ hűvös telelés` címke jelzi.
- Az ilyen növényeknél **január–februárban** a „Ma" nézet tetején megjelenik a kérdés:
  **„Klívia: virágszár 10–15 cm?"** – csak akkor vidd melegre (18–20 °C), ha a virágszár elérte a 10–15 cm-t.
  - **„Áthelyeztem – 18–20 °C"** → rögzíti az áthelyezést, és újraindítja a tápoldatozást (a mai nappal).
  - **„Még nem érte el (1 hét)"** → egy hétre elhalasztja az emlékeztetőt.
  - Március elsejétől az emlékeztető magától eltűnik, és a következő szezonban újra jelentkezik.
- Adatlapon a klíviánál külön sor: **Téli tartás: hűvös hely 10–12 °C · virágzáshoz hideghatás kell.**

### Permetezés – milyen vízzel?

A növény adatlapján (**Permetezés vize**) megadható, milyen vizet kér. Ezt a Florum
beleteszi a teendő szövegébe, a naptárba és az értesítésbe, tehát nem kell emlékezni rá:

| Választás | Mit ír ki a teendőnél | Mikor ez a jó |
|---|---|---|
| **nincs megadva** | csak „Permetezés" | nem akarsz javaslatot |
| **csapvíz** | …*állott, szobahőmérsékletű csapvízzel, reggel* | ha nincs más; hagyd állni egy éjszakát (klór) |
| **esővíz** | …*esővízzel, reggel* | a legjobb, ingyen van |
| **ioncserélt víz** | …*ioncserélt vagy desztillált vízzel, reggel* | meszes/vízköves foltokra érzékeny fajok (gumifa, sárkányfa, kalatea, békeliliom) |
| **nem szereti a permetezést** | **nincs permetezés-teendő** | pihés/gyapjas levelű (afrikai ibolya, begónia, muskátli) |

- **Az „ioncserélt” nem a vízlágyított víz!** A sótablettás lágyító nátriumot tesz a vízbe –
  permetezésre nem való. A palackos ioncserélt/desztillált víz viszont ideális: nincs benne mész.
- Aki **nem szereti a permetezést**, annak a Florum **egyáltalán nem** generál permetezés-teendőt:
  se a „Ma" listán, se a naptárban, se a panelen, se az értesítésben. (Korábban hiába írtad be,
  hogy 0 nap – most már a víz típusa is kikapcsolja.)
- Az adatbázisból kitöltött növények **magukkal hozzák a javaslatot**: a mészre érzékeny fajok
  ioncserélt vizet, a többség esővizet, ahol pedig nincs permetezés (pozsgás, kaktusz, fűszer-
  növény, pihés levelű), ott *„nem szereti"*.
- A teendő sorában kék kis címke mutatja: *esővízzel, reggel* – a kártyán pedig `💦 esővíz` chip.
- Parancssor: `python3 permetviz.py --lista`, illetve `python3 permetviz.py --noveny "Füge"`
  (mit kap permetezéskor az a növény).

> Kereséshez elég a név egy részlete vagy az alias: „gyöm”, „avok”, „datolya”, „mangó”,
> „passion”, „citrommag”, „édesburgonya”, vagy akár az, hogy **„fűszer”** / **„magról
> nevelhető”** – így egyben kilistázódik a teljes csoport.

> Új növény felvételekor a kereső a **magyar nevet, a latin nevet és az álneveket** is
> figyeli: „gyöm", „gyömbérgyökér", „avok", „avokádó mag", „ananászfej" mind találat.
> Ha korábban letöltött adatbázist használtál, a Beállításokban nyomd meg a
> *Beépített visszaállítása* gombot, hogy ezek is megjelenjenek.

### Új növény egy linkről – nem neked kell beírni mindent

A **+ Új növény** ablakban a név alatt ott van ez a sáv:

```
Nincs az adatbázisban? Tedd ide a gondozási útmutató linkjét
[ https://szobakertesz.hu/elefantlab-gondozasa-reszletes-utmutato/ ]
[ Adatok kiolvasása ]  [ Szöveg beillesztése ]
```

1. Beírod a növény nevét (pl. *Elefántláb*), és mellé a **gondozási útmutató linkjét**
   (szobakertesz.hu, tropusinoveny.hu, kertlap.hu, hu.wikipedia.org – bármi, ahol le van írva,
   hogyan kell tartani).
2. **Adatok kiolvasása** – a Florum letölti az oldalt, kibogozza a magyar szöveget, és
   **kitölti a mezőket**: öntözés, téli öntözés, tápoldat, téli tápoldat, permetezés (és milyen
   vízzel), átültetés, fény, hőmérséklet, páratartalom, talaj, betegségek, kártevők, tippek.
3. Megjelenik egy **összefoglaló** („Kiolvasva. 12 mező…”) és egy **Mit találtam?** link,
   amivel átnézheted az egészet. A mezőket **bármikor átírhatod** – a program javasol, te döntesz.
4. **Mentés.** Ami nem fér be a mezőkbe (talaj, hőmérséklet, betegségek, kártevők, tippek),
   a növényhez kerül, és az adatlapján (a névre kattintva) látszik – a forrás megjelölésével.

**Ha az oldal robotvédelmet használ** (pl. a szobakertesz.hu – „One moment, please…”),
a link nem működik gépi letöltéssel. Ilyenkor a Florum ezt írja, és felajánlja a
**Szöveg beillesztése** gombot – nem zsákutca:

1. nyisd meg a linket a böngészőben,
2. `Ctrl+A`, majd `Ctrl+C` (az egész cikk),
3. a Florumban **Szöveg beillesztése** → `Ctrl+V`,
4. **Adatok kiolvasása** – innentől ugyanaz az eredmény.

**Amit nem talál, azt üresen hagyja** – nem talál ki adatot. Az összefoglalóban külön
felsorolja, mit érdemes kézzel ellenőrizni (pl. *mérgezőség*). A mezők kétfélék:

| Jelzés | Jelentése |
|---|---|
| `[biztos]` | a szöveg kimondottan így írja (pl. „télen hagyjuk el a tápoldatozást”) |
| `[becsült]` | a szövegből számolva (pl. „kéthetente” → 14 nap), érdemes ránézni |

**Az Elefántláb már benne van** az adatbázisban (70. növény), tehát nála elég a nevét
beírni. A linkről/szövegből kiolvasás azokra a fajokra való, amik még nincsenek benne.

Parancssorból is kipróbálható:

```bash
python3 novenykereso.py --url "https://…"            # linkről
python3 novenykereso.py --fajl cikk.txt              # mentett szövegből
python3 novenykereso.py --szoveg "Hetente öntözd…"   # egy soros próba
python3 novenykereso.py --onteszt                    # a beépített minták próbája
```

> **Miért a szerver olvassa le?** A böngésző nem tud más oldalt letölteni (biztonsági ok).
> A `florum.py` viszont igen – ezért a kiolvasás a helyben futó programban történik,
> és a kész adatlap csak utána kerül a felületre.

---

## 3. Adatbázis frissítése

Három út van, mind a **Beállítások → Növény-adatbázis** panelen:

| Gomb | Mit tesz |
|---|---|
| **Frissítés a címről** | Letölt egy `plants-db.json`-t a megadott http(s) címről, és elmenti az adatmappádba (felülírja a beépítettet) |
| **Frissítés fájlból** | Ugyanez helyi JSON-fájlból (pendrive, letöltött csomag) |
| **Beépített visszaállítása** | Törli a letöltött verziót, visszaáll a program melletti `plants-db.json`-ra |

A „frissítési cím” megjegyződik, így legközelebb egy kattintás.

#### Napló fül + lenyílók (KDE-ablak) javítása

- **Napló:** nem hasal el hiányos időbélyeg esetén (`Invalid time value` hiba
  megszüntetve); dátum a `date` mezőből is; selejt bejegyzés kiszűrése;
  „N bejegyzés / M összesen” számláló; **Szűrők törlése** gomb; külön üzenet a
  szűrő miatti ürességre; hiba esetén olvasható kártya, nem néma fül.
- **Lenyílók:** natív `<select>` helyett saját lista (`.fsel`) – a KDE-s
  QtWebEngine-ablakban is működik; billentyűzettel is (↑ ↓, Enter, Esc).
- **Verzió:** a lábléc a **fájl** verzióját írja; eltérésnél piros sáv a régi
  futó verzióval és a leállítás parancsával; a Beállításokban **„Rendszer –
  KDE-ablak / böngésző”** diagnózis-panel.
- **Új segédek:** `florum-verzio.sh` (mi fut valójában?), `teszt-lenyilo.js`
  (21 ellenőrzés valódi DOM-motorral).
- Robusztusabb betöltés: a `null`/hibás naplóbejegyzés vagy növény nem borítja fel
  a felületet; látható hibaüzenő sáv (`#jsError`) minden elkapott hibára.

#### 1.25.0 – új növény linkről vagy bemásolt szövegből

- **Adatlap-kiolvasás**: link vagy beillesztett cikk → kész űrlap (öntözés, tápoldat,
  permetezés, átültetés, fény, hőmérséklet, talaj, betegségek, kártevők, tippek).
- **Új program:** `novenykereso.py` (magyar nyelvi kiolvasás, hálózat nélkül is tesztelhető),
  új végpont: `POST /api/plant/fetch`, önteszt: `python3 novenykereso.py --onteszt` (11 minta).
- **Robotvédelem**: felismeri („One moment, please…”), és **szövegbeillesztést** ajánl fel.
- **70. növény: Elefántláb** (`Beaucarnea recurvata`) – a cikkből kiolvasott adatokkal.
- A kiolvasott adatok a növény adatlapján is megjelennek (forrással), és megőrződnek
  szerkesztéskor.

#### 1.24.1 – „felül új, lent régi”: a futó példány csapdája

**Tünet:** a felület tetején `FLORUM 1.24.1` áll, a láblécben viszont `Florum 1.22.0`.

**Ok (nem telepítési hiba):** a fejléc a **fájlból** jön (statikus szöveg), a lábléc
viszont a **futó szerver** `/api/info` válaszából. A Python-folyamat a kódot indításkor
a memóriába tölti, a HTML-t viszont minden kérésnél a lemezről olvassa – ha tehát
frissítés után **a régi folyamat még él**, pontosan ez a vegyes kép jön ki. Ráadásul
az új példány csendben a **következő szabad portra** (8778) csúszik, a böngésző pedig a
8777-en marad.

**Megoldás – egy parancs:**

```bash
bash florum-frissites.sh        # leállít → újraindít → ellenőriz → megmondja, mit látsz
bash florum-frissites.sh --csak-nez   # csak megmutatja, mi fut
```

vagy kézzel:

```bash
python3 florum.py --leallit     # minden futó Florum-példány leállítása
python3 florum.py --verzio      # program / VERSION fájl / futó szerver
systemctl --user restart florum-szerver   # ha szolgáltatásként fut
```

Utána a böngészőben **Ctrl+Shift+R** (a régi lap a memóriában tartja a régi felületet).

**Amit a program mostantól magától jelez:**

* `/api/info` → új mezők: `fileVersion` (a lemezen lévő VERSION) és `versionMismatch`;
* a felület a `<meta name="florum-version">`-hoz hasonlítja a futó verziót, és ha eltér,
  **piros sávot** tesz az ablak aljára a megoldással (`systemctl --user restart …` /
  `florum.py --leallit`);
* a lábléc ilyenkor **mindkettőt** kiírja: `1.22.0 (fut) / 1.24.1 (fájl)`;
* indításkor, ha a porton már fut egy példány, a terminál **figyelmeztet**, és megmondja
  a régi verziót – nem csúszik el csendben a 8778-ra;
* új kapcsolók: `python3 florum.py --verzio`, `--leallit`, `--ne-indits`.

#### 1.24.0 – KDE-ablak (natív program a böngésző-fül helyett)

A Florum eddig a böngészőben futott. Most van **saját KDE-ablaka** is: külön
ablak, toolbár, tálcaikon, KDE-s kinézet – a felület és az adatok **ugyanazok**
(nem kellett újraírni semmit).

| Fájl | Mit tesz |
|---|---|
| `florum-kde.py` | a KDE-ablak indítója (PySide6 + QtWebEngine); a háttérszervert magától elindítja |
| `florum-kde.qml` | az ablak: toolbár (←, ⟳, 🏠, 📷, 📅), hibasáv, gyorsbillentyűk |
| `florum-kde.desktop` | menübejegyzés (KDE alkalmazásindító), magyar nevekkel |
| `telepites-florum-kde.sh` | telepítés: `~/.local/bin/florum-kde`, menü, ikon |

**Telepítés (CachyOS)**

```bash
sudo pacman -S pyside6 qt6-webengine qt6-declarative
# opcionális, de szebb tőle (KDE-s kinézet):
sudo pacman -S qqc2-desktop-style kirigami
bash telepites-florum-kde.sh          # parancs + menübejegyzés + ikon
bash telepites-florum-kde.sh allapot  # mi van meg?
florum-kde                            # indítás
```

**Mit tud az ablak**

* a háttérszervert **magától elindítja** (ha már fut, csak csatlakozik) – ugyanaz a
  8777-es port, amit a panel-widget is használ;
* **tálcaikon** jobb-klikk menüvel: Megnyitás · Fotók (nagy nézet) · Naptár (.ics) · Kilépés;
* **értesítés** a tálcán, ha lejárt vagy mai teendő van (`/api/panel.json` → `lateCount`,
  `todayCount`); `--nincs-ertesites` kikapcsolja;
* gyorsbillentyűk: **F5 / Ctrl+R** újratöltés, **Ctrl+Q** kilépés, **Alt+←** vissza;
* a belső linkek **nem nyitnak új ablakot**, az ablakon belül töltődnek be;
* belső indítóparancsok: `--csak-ablak` (futó szerverhez), `--noscsak`… `--nincs-talca`,
  `--ellenorzes-perc N`, `--bongeszo` (Qt nélkül), `--teszt` (önellenőrzés Qt nélkül is).

**Ha nincs Qt a gépen** (pl. friss telepítés), a `florum-kde` **nem omlik össze**:
kiírja a `sudo pacman -S pyside6 qt6-webengine qt6-declarative` parancsot, és
felajánlja a böngészős indítást. Ez nem hiba a gépeden – a csomagok alapból nincsenek meg.

> **Miért nem teljes QML-újraírás?** Mert a Florum felülete ~5200 sor HTML/JS
> (naptár, galéria, diagramok, űrlapok), és ez most **működik és tesztelt**.
> A QtWebEngine-es ablak ugyanezt a felületet adja natív keretben, nulla
> újraírással. A teljes Kirigami-átírás külön, nagy projekt – lásd a
> „Merre tovább” részt a README végén.

#### 1.23.0 – fotónézet: feh / chafa / böngésző

A feltöltött növényfotókat eddig csak a Florum kis galériája mutatta. Most három
úton lehet nagyban megnézni őket – **egyik sem kötelező**, és hiányzó programnál
a Florum megmondja, mit kell telepíteni.

| Hol | Mit tud | Kell hozzá |
|---|---|---|
| **Böngészős nagy nézet** – `http://127.0.0.1:8777/foto` | teljes galéria, kattintásra nagy kép, ←/→ lapozás, Esc, letöltés, „Eredeti kép” | semmi (a Florum saját oldala) |
| **Külső nézegető** – „Külső nézegető” / ↗ gomb | a gép **saját** képmegnézője nyílik meg (feh, gwenview, loupe, eog, imv, nsxiv, sxiv, ristretto, xdg-open) | `sudo pacman -S feh` |
| **Terminálos kép** – `--foto "NÉV" --terminal` | a kép ANSI-rajzként a terminálban (chafa, viu, timg, catimg, img2txt) | `sudo pacman -S chafa` |

A böngésző **nem tud programot indítani** (és nem is kell neki): a gomb egy
kérést küld a helyben futó Florumnak (`POST /api/open`), és a szerver indítja el
a nézegetőt.

**Használat**

```bash
# mi van telepítve?
python3 novenykereso.py --onteszt                # új növény kiolvasás – önteszt
python3 novenykereso.py --url "https://…"        # adatlap linkről
python3 novenykereso.py --fajl cikk.txt          # adatlap bemásolt szövegből
python3 fotonezo.py --lista

# kép megnyitása a kedvenc nézegetőben (ha a feh nincs meg, a következőt választja)
python3 florum.py --foto "Monstera"
python3 florum.py --foto "Leopárd" --nezo=gwenview

# kép a terminálban
python3 florum.py --foto "Monstera" --terminal
python3 fotonezo.py /útvonal/kep.jpg --terminal

# böngészős nagy nézet (a futó szerveren)
xdg-open http://127.0.0.1:8777/foto
```

**Új végpontok** (mind helyi, olvasás + egy POST):

| Végpont | Mit ad |
|---|---|
| `GET /foto` | a nagy nézet oldala (a fotólista beágyazva; `?noveny=<id>` szűrés) |
| `GET /api/photos` | `{count, photos:[{plantId, plant, alias, idx, url, taken, bytes, dataUrl}], viewers}` |
| `GET /photo/<növény-id>/<sorszám>` | a fotó bájtjai (JPEG/PNG/WebP) – akkor is, ha `dataUrl`-ként van mentve |
| `POST /api/open` | `{plantId, idx}` vagy `{file}` (+ `terminal`, `viewer`) → elindítja a nézegetőt; `503` + `tipp`, ha nincs |
| `GET /api/info` | új mezők: `photosCount`, `photoPage`, `viewers{grafikus,terminal,tipp}` |

**A felületen** (növény kártya → 📷 galéria) két új gomb van:
„Nagy nézet böngészőben” (az egész galéria) és „Külső nézegető” (az első kép),
valamint minden képen egy **↗** a saját nézegetőjéhez.

#### 1.23.0 – új faj: Leopárdnövény (`Drimiopsis maculata`)

A webshop-adatlap (tropusinoveny.hu) adatai + a hagymás növények szokásai alapján:

| Mező | Érték |
|---|---|
| Név / latin | **Leopárdnövény** · *Drimiopsis maculata* (syn. *Ledebouria petiolata*) |
| Kereshető még | „leopárd”, „pöttyös”, „pettyes”, „ledebouria”, „afrikai pöttyös hagymás” |
| Fény | Világos, szórt (tűző napon a pettyek kifakulnak) |
| Öntözés | **10 nap**, télen **18** (két öntözés között a föld felszíne száradjon ki) |
| Tápoldat | 30 nap, **télen nincs** (okt.–febr. pihenő – hagymás növény) |
| Permetezés | nincs → *nem szereti a permetezést* (húsos levél) |
| Átültetés | 30 hónap (lassan nő, a kisebb cserép jó neki) |
| Hőmérséklet | 18–24 °C |
| Talaj | laza, jó vízelvezetésű: virágföld + perlit + homok |
| BETEGSÉGEK | gyökérrothadás (pangó víz), sárguló-puha levél (télen hideg + nedves föld), barna levélcsúcs (meszes víz) |
| Kártevők | pajzstetű, takácsatka |

> Az adatbázis most **82 növény** (v2026.10.9). A webshop linkjét növényenként a
> kártyán a **linkek** közé tudod felvenni (címke: *bolt*), így egy kattintással
> ott van az adatlap és az ár is. Bármilyen tárhely jó, ami
nyers JSON-t ad (pl. saját webszerver, GitHub „raw” link, Nextcloud nyilvános link).
Ha nincs kedved hosztolni: tedd a `plants-db.json`-t a Florum mappába egy új verzióval,
vagy használd a *Frissítés fájlból* gombot.

### Saját adatbázis bővítése
A formátum egyszerű (`plants` lista). Egy bejegyzés:
```json
{
  "id": "monstera-deliciosa",
  "name": "Monstera",
  "latin": "Monstera deliciosa",
  "aliases": ["lyukas levelű filodendron"],
  "difficulty": "Könnyű",
  "light": "Világos, szórt",
  "water": 7, "waterWinter": 12,
  "fert": 30, "mist": 7, "repot": 24,
  "humidity": "50–60%", "temp": "18–27 °C",
  "soil": "Laza, levegős keverék",
  "toxic": "Mérgező macskára és kutyára",
  "diseases": ["Sárguló alsó levelek – túlöntözés"],
  "pests": ["Pajzstetű", "Takácsatka"],
  "tips": ["Adj neki támasztékot."]
}
```
Bővíthető kézzel a `plants-db.json`-ban, vagy a `build-plant-db.py` nevű segédszkripttel
(ebben egy tömör, soronkénti formátumban vannak az adatok; lefuttatva újragenerálja a
`plants-db.json`-t és a HTML-be ágyazott tartalékot is).

---

## 4. Hogyan számol?

| | |
|---|---|
| **Öntözés** | „Kész” → a mai dátumtól `water` nap múlva esedékes. Télen (nov–feb) a `waterWinter` értékkel; ha nincs megadva, 1,5×-ös szorzó |
| **Tápoldat / permetezés** | 0 = kikapcsolva, nem emlékeztet |
| **Átültetés** | hónapokban (jellemzően 18–36) |
| **Ma nézet** | Lejárt / Ma esedékes / Következő N nap / Hiányzó adat |
| **Hiányzó adat** | ha egy teendőhöz nincs „utolsó alkalom”, ott a **„Ma volt”** gomb egy kattintással elindítja |
| **Visszavonás** | a „Kész” után 6 másodpercig visszavonható |

---

## 5. Adatok, mentés, költözés

- A mentés minden változtatásnál automatikus; a fejléc jelzője mutatja: **Mentve** (zöld =
  fájlba), **Mentés…** (folyamatban), **Mentési hiba** (piros).
- Minden mentés előtt az előző állapot a `florum-data.bak.json`-ba kerül; ha a fő fájl
  megsérül, az app abból állítja helyre.
- **Biztonsági mentés / visszaállítás**: Beállítások → Adatok (JSON export/import).
- **Másik mappa / pendrive**: `python3 florum.py --data-dir /media/pendrive/florum`
- **Adatmappa megnyitása** gombbal fájlkezelőben is megnézheted.

---

## 6. Fájlok

```
florum/
├── florum.html          ← az alkalmazás (önálló, offline; az adatbázis tartaléka beágyazva)
├── florum.py            ← indító: helyi szerver + fájlmentés API + app-mód
├── plants-db.json       ← a növény-adatbázis (ez tölthető felül/frissíthető)
├── build-plant-db.py    ← adatbázis-építő segédszkript (opcionális)
├── install.sh           ← menüparancs telepítése
├── florum.desktop       ← kézi .desktop sablon
├── florum.svg           ← ikon
└── README.md
```

## 7. Kapcsolók

```bash
python3 florum.py --app                  # keret nélküli ablak, fájlmentéssel
python3 florum.py --data-dir ~/florum    # saját adatmappa
python3 florum.py --port 8765            # fix port
python3 florum.py --no-browser           # csak a szerver
```

---

## 8. Új funkciók (1.2)

### Naptár nézet
A **Naptár** fül egy teljes hónapot mutat, minden napra pöttyökkel: öntözés (kék),
tápoldat (zöld), permetezés (lila), átültetés (sárga) – a lejárt piros, a már elvégzett
szürke. Kattints egy napra, és ott rögtön látszik, kinek mi a dolga, a **Kész** gombbal
egy kattintással rögzíthető. Lépegetés hónapok között, „Ma” gomb, és a hónap tetején
egy összesítő (hány öntözés, hány tápoldatozás vár még ebben a hónapban).

Fölötte **szezonális kártya** (tavasz / nyár / ősz / tél) az aktuális hónapra szóló
teendőkkel: átültetés tavasszal, tápoldat indítása, téli ritkítás, kártevő-ellenőrzés
nyáron, hidegérzékenyek behozatala ősszel.

> A naptár a beállított ritmusból előre kiszámolja az esedékességeket, és télen a
> növény saját téli értékével számol – nem csak a nyári időközt ismétli.

### Előzmény-grafikon
A **Napló** fül tetején oszlopdiagram: 30 nap / 90 nap / 1 év kapcsoló, tevékenység
szerinti színezéssel, összesítéssel és **átlagos öntözési időközzel** (hasznos, ha
kiderül, hogy a valóságban kétszer olyan sűrűn locsolsz, mint beállítottad).
A napló szűrői (növény, tevékenység) a grafikonra is hatnak.
Minden növénykártyán van egy apró **8 hetes öntözés-csík** is.

### Saját fajok felvétele (adatbázis-bővítés a felületen)
Beállítások → **Növény-adatbázis → Saját fajok → Új faj felvétele**:
név, latin név, álnevek, fényigény, nehézség, öntözés (nyár/tél), tápoldat, permetezés,
átültetés, páratartalom, hőmérséklet, talaj, mérgezőség, betegségek, kártevők, tippek.

- A saját fajok a `florum-data.json`-ban (`customDb`) tárolódnak, tehát fájlba mentődnek.
- **Mindig a letöltött/beépített adatbázis fölé kerülnek**, és megjelennek a
  név-keresőben is – onnantól ugyanúgy egy kattintással kitöltik az új növény adatlapját.
- Szerkeszthetők, törölhetők, és **Export** gombbal `plants-db.json` formátumban
  kimenthetők (ez a fájl aztán másik gépen „Frissítés fájlból” gombbal betölthető,
  vagy akár fel is tölthető egy tárhelyre, és onnan frissíthető).

### Kattintható KPI-kártyák
A számok nem csak díszek – kattintva szűrnek:

| Nézet | Kártya | Kattintásra |
|---|---|---|
| **Ma** | Lejárt / Ma esedékes / Következő N nap | a lista csak az adott csoportot mutatja; újabb kattintás (vagy „× Szűrő törlése”) visszaállítja |
| **Ma** | Növény | átugrik a Növények fülre |
| **Naptár** | Öntözés / Tápoldat / Átültetés ebben a hónapban | a hónap összes ilyen esedékessége egy listában, dátummal, „Kész” gombbal |
| **Naptár** | Növény | átugrik a Növények fülre |

Az aktív szűrőt zöld keret és pipa jelzi, a kártya jobb felső sarkában pedig nyíl mutatja,
hogy kattintható. A gombok billentyűzettel is elérhetők (Tab + Enter).

---

## 9. Új funkciók (1.3)

### 🔎 Tünet-kereső (Tünetek fül)
Írd be, mit látsz a növényen (pl. „sárguló levél”, „barna levélszél”, „pajzstetű”), vagy
kattints egy előre felkínált tünetre. Az app az adatbázis betegség- és kártevőlistájából
keres, és két csoportra bontja a találatokat:

- **A te növényeid** – amelyek a listádon szerepelnek, vagyis nálad is fennállhat,
- **Más növényeknél is előfordul** – referenciának.

Minden találatnál ott a **valószínű ok** (pl. „túlöntözés”, „száraz levegő”, „huzat”) és a
növény adatlapja egy kattintással. Több szó esetén mindegyiknek szerepelnie kell („sárguló
levél” nem hozza a „levélesés” találatokat).

### 🔔 Asztali értesítések + automatikus indítás
Beállítások → **Értesítések és automatikus indítás**:

- napi emlékeztető beállítható időpontban (alapból 08:00): *„Ma 3 teendő (2 lejárt) – Öntözés:
  Anyósnyelv, Aranypothos; Permetezés: Aranypothos”*
- **Próbaértesítés** gomb (azonnal ellenőrizheted)
- **automatikus indítás** be/ki: `~/.config/autostart/florum.desktop`

A háttérfigyelést a `--notify` kapcsoló indítja (a menüparancs és az autostart is ezt használja).
Naponta legfeljebb egyszer szól, és csak akkor, ha van tényleg esedékes teendő.
Értesítéshez `libnotify` kell: `sudo pacman -S libnotify` (KDE-n a `kdialog`, GNOME-on a
`notify-send` megy; ha egyik sincs, az app szól, hogy nem tud értesíteni).

### ✈ Szabadság / távollét
Beállítások → **Szabadság**: add meg az időszakot.

- a **Ma** nézet figyelmeztet: hány növénynek lesz gondja a távollét alatt, és kik azok,
- a **naptárban** a szabadság napjai lilán jelölve vannak,
- „Hazaértem – mindenki megöntözve” gomb: egy kattintással lezárja az összes öntözést.

### ⏭ Kihagytam / Szundi
Minden teendő mellett a **⋯** gomb menüt nyit:

| | |
|---|---|
| **Kész** | ma megtörtént (ugyanaz, mint a Kész gomb) |
| **Kihagytam** | esős nap, kint van, nem kell – a ciklus nem csúszik el, a naplóban „kihagyva” jelzéssel látszik |
| **Szundi 2 nap / 1 hét** | elhalasztja az adott teendőt, a kártyán „szundi · …” jelzéssel |
| **Szundi törlése** | vissza az eredeti időpontra |
| **Adatlap** | a faj adatlapja (fény, betegségek, kártevők) |

A szundi állapot a növény adataival együtt mentődik, tehát újraindítás után is megmarad.

### 📷 Fotók és növekedési napló
- **Növények** fülön a kártyán a legutóbbi fotó bélyegképe, a 📷 gombbal (vagy a bélyegre
  kattintva) nyílik a **galéria**: dátumozott képek, nagyítás, törlés, új kép hozzáadása.
- Új növény felvételekor vagy szerkesztéskor közvetlenül az űrlapon is csatolhatsz képet.
- A képek a fájlba mentett módban **külön fájlként** kerülnek az adatmappába
  (`~/.local/share/florum/photos/`), nem hizlalják a JSON-t; a növény csak a fájlnevet tárolja.
  A böngészős tartalék módban (fájlként megnyitva) kisebbre méretezett beágyazott képként
  mentődnek.

> A feltöltött képek automatikusan átméreteződnek (max. 1100 px, JPEG), így egy-egy fotó
> tipikusan 100–250 kB.

---

### Merre tovább: mennyire lehet „igazi” KDE-program?

Három szint van. Az első kettő **kész**, a harmadik külön projekt.

| Szint | Mit jelent | Állapot |
|---|---|---|
| **1. Asztali beépülés** | `.desktop` menübejegyzés, saját ikon, saját panel-widget (plasmoid), `.ics` a KDE naptárba, systemd `--user` háttérszerver | ✅ kész (1.14 – 1.24) |
| **2. Natív ablak** | `florum-kde`: Qt Quick ablak + QtWebEngine, KDE-stílus (`org.kde.desktop`), tálcaikon, értesítés – **ugyanaz a felület és adat** | ✅ kész (1.24.0) |
| **3. Teljes QML/Kirigami átírás** | a felület natív Qt Quick elemekből: `Kirigami.ApplicationWindow`, `ScrollablePage`, `Card`, `SwipeListItem`, `Kirigami.InlineMessage`… a HTML/JS eltűnik | ⬜ nincs elkezdve – ez a nagy munka |

**Mennyi munka a 3. szint?** A jelenlegi felület ~5 200 sor HTML/JS (naptárnézet,
galéria, diagramok, űrlapok, beállítások, fordítás). Egy Kirigami-átírás nagyságrendileg
**10–15 QML-fájl, ~4 000–6 000 sor**, és ami a legfontosabb: a **logika** (ütemezés,
téli időszak, `.ics`, adatbázis, mentés) már Pythonban van és tesztelt – azt **nem kell
újraírni**, csak az `florum.py` API-t hívná QML-ből (`XMLHttpRequest`, ahogy a
panel-widget már most is teszi).

**Ajánlott sorrend, ha belevágunk:**

1. `Kirigami.ApplicationWindow` + oldalsáv (`Kirigami.GlobalDrawer`) – a 4 fül:
   Ma / Növények / Naptár / Beállítások;
2. a **Ma** nézet (növénykártyák + gombok) – ez a napi használat 90%-a;
3. növény-szerkesztő űrlap (`Kirigami.FormLayout`);
4. naptárnézet (`MonthGrid`/`DayOfWeekRow` – a 16:9 és a fotós napcellák QML-ben);
5. galéria (`GridView` + `Kirigami.Page`), fotónézet a már meglévő `fotonezo.py`-val;
6. diagramok (`QtCharts`) – a mostani saját SVG-diagramok helyett.

A HTML-es változat **közben is megmarad** (a panel-widget, a böngészős nagy nézet és a
`florum.html` ezt használja), tehát az átállás nem tör el semmit – a kettő ugyanazt az
adatfájlt és ugyanazt a szervert használja.

---

### „A Kert fülön nincs növény” – mit rontottam el? Semmit.

A Kert fül **csak a kerti növényeket** mutatja – ez a lényege. Ha a felvett növény
nem kerti, ott nem is jelenhet meg. A program viszont eddig **némán** hagyta ezt,
ezért tűnt hibának. Ez a javított változatban megváltozott:

- **A faj neve most már elég.** Ha olyan növényt vettél fel, ami az adatbázisban
  kerti faj (hagyma, fokhagyma, répa, cékla, retek, saláta, paradicsom, paprika,
  uborka, burgonya, eper, zöldborsó), akkor **magától kerti növény lesz** – a hely
  és a jelölő nem kell hozzá. A hiányzó szezont, vetést, betakarítást, komposztot
  a program pótolja.
- **Az üres fül nem zsákutca:** a Kert fül alján most **mindig ott a lista az összes
  nem kerti növényedről**, mindegyik mellett „Áthelyezés a kertbe” gombbal.
  Egy kattintás, és ott van a fülön.
- **A fejléc kimondja a számokat:** „Összes növényed: N · ebből kerti: M”.
  Ha M = 0, rögtön látszik, hogy nincs mit mutatni – nem hiba.
- **Hiba esetén kártya:** ha a fül rajzolása mégis elhasal, piros kártya jön a
  hibaüzenettel és két gombbal (Kert újra / Növényeim) – nem üres képernyő.

Ha továbbra sem látod a növényt, kérdezd meg a programot – soronként megmondja,
melyik növény miért nincs a Kert fülön:

```bash
cd ~/florum          # vagy ahol a florum.py van
python3 florum.py --kert
```

Kimenet például:

```
✗ Monstera   Nappali   kerti: nem   ← ezért nincs a Kert fülön
✓ Sárgarépa  Kert      kerti: IGEN · szezon 3–10
kerti növény: 1 / 2
```

A `Hely` mezőben különben is ott van **Kert / Kerti ágyás / Üvegház** – ha ilyet
választasz, a növény azonnal kerti növény lesz.

### „A Napló fül mostoha / egy oszlop van benne” – jelentés-táblázat

A Napló eddig **egyetlen oszlopos, kártyás lista** volt: növény + tevékenység egy
sorban, típus szerint nem lehetett szűrni, és nem lehetett megmondani, melyik
növénynél mi volt a beállítás. Most **jelentés-táblázat**:

| Oszlop | Mit mutat |
|---|---|
| **Dátum** | `2026.10.22.` + időpont + „3 napja” |
| **Növény** | név, alatta a hely (Nappali, Kert, …) |
| **Tevékenység** | Öntözés / Tápoldat / Permetezés / Átültetés (kihagyva jelöléssel) |
| **Részletek** | a növény beállításából: „30 havonta · 18 cm cserép”, „2 ml/l · N-P-K 7-3-5 · március–szeptember”, „permetezés: csapvíz” |

Fölötte:

- **4 szám**: bejegyzés összesen · ebben a hónapban · ma rögzítve · érintett növény,
- **típus-chipek darabszámmal** (pl. „Átültetés 1”) – kattintásra szűr,
- a napok **sávokba** rendezve („2026.10.22. · 2 bejegyzés”),
- az oszlopfejlécre kattintva **rendezés** (dátum / növény / tevékenység),
- **„Napló letöltése (CSV)”**: `Dátum;Idő;Növény;Hely;Tevékenység;Részletek;Kihagyva`
  – pontosvesszős, UTF-8, tehát a magyar Excel/LibreOffice azonnal nyitja.

Ha a fül mégis hibára futna, piros kártya jön a hibaüzenettel és a
„Szűrők törlése és újrapróbálás” / „Mit lát a program?” gombokkal – nem üresség.

### „Ilyen feliratok vannak: water Öntözés” – magyarul

Ez a hiba a **legördülő szűrők** szövegében volt: a rejtett natív `<select>`
opciószövege az ikon **belső neve** volt („water Öntözés”, „fert Tápoldat”…),
a saját legördülő pedig szó szerint azt másolta. Mostantól csak a magyar felirat
látszik: **Öntözés · Tápoldat · Permetezés · Átültetés**. Az ikon a listában is
megjelenik, de képként, nem szövegként.

### „Helyiséget nem lehet böngészni a legördülőben” – böngészhető

Két programhiba okozta, egyik sem a te hibád:

1. a lista a **`position:absolute`** miatt a szerkesztő panel **görgethető dobozába**
   volt zárva, ezért az alsó helyiségek (Kert, Erkély, Üvegház…) **le voltak vágva**;
2. a program **minden görgetésre bezárta** a listát – még akkor is, amikor a listán
   belül akartál görgetni. Ezért lehetett „csak az első pár” helyiséget látni.

Most:

- a lista **fix pozíciójú**, a gombhoz igazítva – semmi nem vágja le, és ha nem fér
  ki lefelé, **felfelé** nyílik;
- a listában **lehet görgetni** (egérkerékkel is), az oldal görgetésekor pedig a lista
  **követi a gombot**, nem csukódik be;
- **13 helyiségnél** a lista tetején **keresőmező** van: írd be, hogy „nap”, „kert”
  vagy akár ékezet nélkül „uveg” → **Üvegház**. Enter = az első találat kiválasztása.
  (Ez minden hosszú listára érvényes: tápoldat-típus, permetezés vize, hónapok.)

### „Minek a panelen 2 Florum?” – egy van

Nem te raktad ki kétszer: **két menübejegyzést telepítettünk**, és mindkettő
kikerülhetett a panelre.

| Mi | Honnan | Most |
|---|---|---|
| `florum.desktop` | `install.sh` | **ez marad** – de már nem közvetlenül indít, hanem a `florum-megnyitas.sh`-t hívja |
| `florum-kde.desktop` | `telepites-florum-kde.sh` | **nem települ többé**; a régi `.regi` végződéssel félrekerül |
| panel-widget | `telepites-florum-panel.sh` | megmarad, és **most már meg is nyitja** az appot |

Vagyis a panelen **egy** Florum-ikon kell legyen: a widget. Az mutatja a számot,
és kattintásra (vagy a lista alján a **Florum megnyitása** gombbal) jön az app.

**Ha most két ikon van a paneleden** (a régi telepítés maradéka):

1. jobb klikk a **fölösleges** ikonon → *Eltávolítás a panelről* (a widgetet hagyd meg),
2. futtasd egyszer: `bash install.sh` – a menüben már csak egy Florum lesz.

Tetszés szerint: a widget beállításaiban **Kattintásra a Florum nyíljon meg** –
ekkor a kattintás rögtön az ablakot hozza, nem a listát. Középső gombbal mindig megnyílik.

Ellenőrzés:

```bash
bash florum-megnyitas.sh --allapot     # mi fut: szerver, KDE-ablak, PySide6
bash florum-megnyitas.sh --dry-run     # mit nyitna meg (nem csinál semmit)
bash florum-megnyitas.sh               # megnyitás (a legjobb móddal)
```

### „Ezzel átteszem saját mappájába: `--data-dir`” – igen, de csak egy indításra

A `python3 florum.py --data-dir /saját/mappa` **abban az egy futásban** használja
a megadott mappát. Ha utána a **menüből vagy a panelről** indítod a Florumot, az
visszaáll az alapértelmezett mappára (`~/.local/share/florum`), és úgy tűnik,
mintha **elveszett volna minden növényed**. Nem veszett el – csak másik mappát néz.

Ezért van rá egy parancs, ami **átmásol és meg is jegyzi**:

```bash
bash florum-atkoltoztetes.sh ~/Florum-adat
```

Amit tesz:

1. leállítja a futó példányt,
2. **átmásolja** az adatokat: `florum-data.json`, a biztonsági másolat, a `photos/`
   (képek), a `mentes/` (pillanatképek), a `notify-state.json` – a naptárfájl
   újraíródik, azt nem kell vinni,
3. **ellenőrzi**, hogy ugyanannyi növény és naplóbejegyzés van-e az új helyen,
4. beírja a mappát a `florum-adat.conf`-ba – onnantól a **megnyitó, a frissítő és a
   háttérszolgáltatás is** ezt használja (nem kell többé kapcsolót beírni),
5. elindítja a háttérszervert az új mappával, és ellenőrzi a `/api/info` válaszban.

A régi mappát **nem törli** – nyugodtan megnézheted, hogy minden átjött, és csak
utána törölheted kézzel.

Hasznos kapcsolók:

```bash
bash florum-atkoltoztetes.sh ~/Florum-adat --dry-run   # csak megmutatja, mit tenne
bash florum-atkoltoztetes.sh --mi                     # melyik mappát használja most?
bash florum-atkoltoztetes.sh --vissza                 # vissza az alapértelmezettre
```

Ha kézzel akarod megjegyzés nélkül: `python3 florum.py --data-dir /saját/mappa
--atkoltoztetes /másik/mappa` csak a másolást végzi el, utána a megnyitókba be
kell írni a mappát (`export FLORUM_DATA=…` a `~/.bashrc` végén).

## 10. Új funkciók – tápoldatozás és kerti növények

### Mit tud most a tápoldatozás?

| Kérdés | Válasz a Florumban |
|---|---|
| **Mivel?** | 8 típus: tápoldat, levéltápoldat, virágzó tápoldat, kaktusz tápoldat, szemcsés műtrágya, komposzt, istállótrágya, „nem tápoldatozom” |
| **Mennyit?** | szabad szöveg, de a teendőben és a naptárban is megjelenik (pl. „2 ml / 1 l víz”, „fél adag”) |
| **Milyen összetétel?** | N-P-K arány (7-3-5 univerzális, 5-7-6 virágzó, 3-5-7 kaktusz, magas kálium terméshez) |
| **Mikor?** | hónap-ablak (tól–ig), átfordulással; ezen kívül nincs tápoldat-teendő |
| **Télen mi van?** | ha az ablak nem tartalmaz téli hónapot: semmi. A pihenő után az ablak első napján indul újra |

Az adatbázis-profilok (82 növény mindegyike kap egyet):

| Profil | Adag | N-P-K | Ablak | Kik kapják |
|---|---|---|---|---|
| `tapoldat` | 2 ml / 1 l | 7-3-5 (univerzális) | március–szeptember | a legtöbb szobanövény, füge, citrus |
| `level` | 1 ml / 1 l (fél adag) | 7-3-5 + magnézium | március–szeptember | fűszernövények, levendula, muskátli |
| `viragzo` | 2 ml / 1 l | 5-7-6 (P + K túlsúly) | március–szeptember | klívia, hibiszkusz, orchidea, leander |
| `kaktusz` | 1 ml / 1 l | 3-5-7 | április–augusztus | kaktusz, pozsgás, aloé |
| `komposzt` | 2–3 marék / m² | – | április–július | kerti zöldségek |
| `istallo` | 3–4 marék / m² | – | szeptember–október | burgonya (őszi talajelőkészítés) |

### Mit tudnak a kerti növények?

- **Szezonális csend:** a szezonon kívül a növény nem szerepel egyetlen teendőlistán sem –
  nem kell „0 naponta” trükközni, és nem kap fölösleges emlékeztetőt januárban.
- **Vetés / betakarítás** az adatlapon és a növénykártyán.
- **Kerti jelölés** a kártyán és a teendő sorában (`🌱 kerti`), hogy egy pillantással látszódjon,
  melyik növény van odakint.
- Ugyanaz a naptár, `.ics`, panel és értesítő működik rájuk is – csak szezonon belül.

### Amit érdemes tudni a frissítésről

- A `plants-db.json` verziója **2026.10.9**, 82 növénnyel (70 szoba + 12 kerti).
  Beállítások → *Adatbázis frissítése* → **Beépített visszaállítása**, ha régebbi fájlod van.
- A meglévő növényeid adatai **nem változnak**; a tápoldat-ablak náluk az alap
  (március–szeptember), amíg át nem írod.

---

## 11. Új funkciók – Kert fül

### Miért külön fül?

A szobanövényeknél a kérdés az, hogy *„ma mit kell csinálni”*. A kertben viszont az első
kérdés az, hogy **van-e egyáltalán szezon** – januárban a kertben nincs dolgunk. Ezért a
kerti növények külön nézetet kaptak, ahol a szezon a fő szervező elv:

1. **fejléc** – hány növény van szezonban, hány pihen, melyik hónap van;
2. **szezon-csík** – egy pillantás: áprilistól októberig zöld, előtte-utána szürke;
3. **szezonban lévő növények** kártyákon, a legsürgősebb elöl, Kész gombokkal;
4. **pihenő növények** külön listán, az újraindulás dátumával.

### Mi marad ugyanaz?

- Ugyanaz az adat, ugyanaz a `.ics`, ugyanaz a KDE-panel és emlékeztető: a Kert fül csak
  **nézet**, nem külön adatbázis.
- A kerti növények a **Ma** fülön is megjelennek, ha szezonban vannak – ott a napi teendők
  között látod őket.
- A **Naptár** fülön a szezonon kívüli hónapok üresek maradnak (a naptár a szezon első
  napján veszi fel újra a fonalat).

### Gyors útmutató

1. **Kert** fül → **+ Kerti növény**;
2. írd be a nevet (pl. „sárgarépa”) – az adatbázisból jön a szezon, a vetés, a szedés, a
   trágya és az öntözés;
3. ellenőrizd a **szezont** (április–október) és a **szedési időt**, majd **Mentés**.
4. Szezonon kívül a fül a „Pihen” listán mutatja, nem generál teendőt.

---

## 12. Új funkciók – Napló, lenyílók, verzió

### Napló fül – újraépítve
- a fül megnyitása **mindig** friss rajzot ad (eddig csak bizonyos esetekben),
- **hiányzó/hibás időbélyeg** nem borítja fel a fület: az ilyen bejegyzés a
  *„Dátum nélkül”* csoportba kerül,
- **szűrők törlése** gomb + darabszám (bejegyzés / növény),
- a szűrő magától visszaáll, ha egy törölt növényre mutatott,
- hiba esetén **piros hibaüzenet** a fülön (nem néma üresség), és a Beállítások →
  *Rendszer* panelen **Napló-ellenőrzés / Napló újrarajzolása**.

### Lenyílók (KDE-ablak)
- minden legördülő **saját** (nem a böngésző natív listája) → QtWebEngine alatt is kinyílik,
- automatikusan **felfelé** nyílik, ha nincs elég hely lefelé,
- billentyűzet: ↑/↓, Enter, Esc; kattintáson kívül bezárul,
- a natív `<select>` a háttérben marad (a mentés/betöltés logikája változatlan).

### Verzió-átláthatóság
- a lábléc **mindig a fájl** verzióját írja, a futóét csak külön jelzi,
- eltérésnél piros sáv a `systemctl --user restart florum-szerver` paranccsal,
- új `florum-verzio.sh`: megmutatja a fájlok és a futó példány verzióját, több porton
  is keresi az elárvult példányt, és `--ujraindit` kapcsolóval leállít + indít.

## 13. Új funkciók (1.30.0) – a Kert fül soha nem lesz üres

### Mi volt a baj?

A 44. óta a Kert fül csak azt mutatta, ami **kerti növény** – de kerti növénnyé
csak akkor vált valami, ha a *Hely* mezőben kert volt, vagy be volt kapcsolva a
kerti jelölő. Aki egyszerűen felvett egy „Sárgarépát”, az a **Növényeim** listában
látta, a Kert fülön nem – magyarázat nélkül. Ez programoldali hiány volt, nem a
felhasználó hibája.

### Mi változott?

| Hol | Mit tud most |
|---|---|
| Kerti besorolás | három lépcső: kerti jelölő → helynév (Kert / Kerti ágyás / Üvegház) → **adatbázis** (a faj kerti faj) |
| Önjavítás | a kerti növény megkapja a szezont (4–10 vagy a faj sajátja), a vetés/betakarítás idejét, a komposzt-adagot és a tápoldat-ablakot |
| Üres állapot | **az összes** nem kerti növény listázva, egy kattintásos „Áthelyezés a kertbe” gombbal (akár 200 növényig) |
| Fejléc | „Összes növényed: N · ebből kerti: M” |
| Hiba | a fül nem tud némán elhasalni: piros hiba-kártya az üzenettel + „Kert újra” / „Növényeim” gomb |
| Parancssor | `python3 florum.py --kert` – soronként ✓/✗, hogy melyik növény miért nincs a fülön |

### Kipróbálás

1. Vegyél fel egy kerti fajt (pl. *Sárgarépa*) – a nevén kívül semmit nem kell megadni.
2. Nyisd meg a **Kert** fület: ott van, szezonnal, vetéssel, betakarítással.
3. Ha valami mégsem stimmel: `python3 florum.py --kert`, illetve a fül alján az
   áthelyező lista.

## 14. Új funkciók (1.30.1) – a Napló jelentés-táblázat

### Mi volt a baj?

A Napló „mostoha” volt: egy oszlopos kártyasorok, benne „Átültetés” feliratok,
de semmi mögötte (mennyi, mivel, mikor esedékes), és nem lehetett áttekinteni,
mi történt egy növénnyel. A fül a 46. körben már nem hasalt el, de **jelentésként
nem volt használható**.

### Mit tud most?

| Új | Mit jelent |
|---|---|
| Többoszlopos táblázat | Dátum · Növény · Tevékenység · Részletek · (törlés) |
| Nap-sávok | naponta csoportosítva, darabszámmal, ragadós fejléccel |
| Számsor | összes · e havi · mai · érintett növény |
| Típus-chipek | Öntözés 5 / Tápoldat 2 / Permetezés 2 / Átültetés 2 – kattintásra szűr |
| Rendezés | fejlécre kattintva; dátumnál a legfrissebb elöl, szövegnél ABC |
| Részletek oszlop | a növény beállításaiból: adag, N-P-K, hónap-ablak, cserépméret, permetező víz |
| CSV-letöltés | `florum-naplo-2026-10-25.csv`, pontosvesszős, UTF-8 BOM-mal |
| Kihagyva jelzés | a „kihagyott” tevékenység is látszik, de megjelölve |
| Görgethetőség | keskeny ablakban az oszlopok összecsúsznak, a táblázat vízszintesen görgethető |

### Kipróbálás

1. Nyisd meg a **Napló** fület – fent a négy szám, alatta a típus-chipek.
2. Kattints az „Átültetés” chipre: csak az átültetések maradnak, a Részletek
   oszlopban ott van, hogy „30 havonta · 18 cm cserép”.
3. Kattints a **Dátum** fejlécére: megfordul a sorrend.
4. **Napló letöltése (CSV)** – a fájl a letöltések közé kerül, Excelben nyitható.

## 15. Új funkciók (1.30.2) – lenyílók: feliratok és böngészés

### A két hiba

| Tünet | Ok | Javítás |
|---|---|---|
| „water Öntözés” felirat a listában | a rejtett `<select>` opciójában az ikon belső neve volt a szöveg | csak a magyar felirat kerül az opcióba |
| „Helyiséget nem lehet böngészni” | `position:absolute` a görgethető panelben → levágva; és minden scroll be is zárta | `position:fixed` + újrapozicionálás + görgethető lista |

### Ami új még ezen kívül

- **Keresőmező** a listában, ha 8-nál több elem van (Helyiség, tápoldat-típus,
  permetezés vize, hónapok): gépelésre szűr, **ékezet nélkül is** talál
  („uveg” → Üvegház, „nap” → Nappali).
- **„N / M látszik”** és „Nincs találat” visszajelzés.
- **Enter** a keresőmezőben: az első találat kiválasztása; **↑/↓** csak a látható
  elemek között lépked; **Esc** bezár.
- Felfelé nyitás, ha lefelé nincs hely; az oldal görgetésekor a lista követi a gombot.

### Kipróbálás

1. Növényeim → **+ Új növény** → *Helyiség*: kattints a listára, írd be: `kert`.
2. Látszik: **Kert, Kerti ágyás** – Enter, és a kerti jelölő magától bekapcsol.
3. A **Napló** fülön a tevékenység-szűrőben már csak magyar feliratok vannak.

## 16. Új funkciók (1.30.3) – a kerti növény más színű a Növények fülön

### Mit látni?

A **Növények** fülön a kerti növény kártyája **zöld**:

| Jel | Jelentés |
|---|---|
| zöld **bal szegély** (5 px) + halványzöld felső átmenet | ez a növény kerti |
| **KERT** szalag a név mellett | ugyanez szóban is, hogy ne a szín legyen az egyetlen jel |
| 🌱 **kerti növény · március–október** jelölő | a szezonablak (a kerti növényé) |
| kereső melletti **jelmagyarázat**: „zöld szegély = kerti növény (N)” | csak akkor jelenik meg, ha van kerti növényed |

A szobanövények kártyája marad a megszokott fehér – a két csoport így egy pillantással
elválik, akkor is, ha a kereső egy listába teszi őket.

### Miért kap zöldet az is, amit nem jelöltél be kerti növénynek?

Mert a program **háromféleképpen** ismeri fel a kerti növényt (1.30.0 óta):

1. be van kapcsolva a „Kerti növény” jelölő,
2. a **Helyiség** Kert / Kerti ágyás / Üvegház,
3. a **faj** maga kerti faj az adatbázisban (répa, hagyma, paradicsom, paprika,
   uborka, cékla, retek, saláta, burgonya, eper, zöldborsó, fokhagyma).

Ha tehát egy „Paradicsomot” vettél fel a Nappaliba, az **zöld kártyát kap**, mert a
növény kerti faj. Ha mégsem akarod kertiként látni, írd át a nevét (pl. „Paradicsom
(cserép)”) vagy válassz másik fajt – a Kert fülről pedig az „Áthelyezés” listával
bármi átvihető.

### Kipróbálás

1. **Növények** fül → a kerti növények zöldek, a szobanövények fehérek.
2. A zöld kártyán a **KERT** szalag és a szezon-jelölő is látszik.
3. Sötét témában (Beállítások → Megjelenés) a zöld sötétebb tónusra vált.

## 17. Új funkciók (1.30.4) – egy panel-elem: a widget és az app együtt

### Mit jelent ez?

A panel-widget eddig **csak mutatott**: a számot és a listát. Az app megnyitásához
külön programindító kellett a panelre – ezért látszott két Florum. Most a widget
**meg is nyitja** a Florumot, és a menüben csak egy bejegyzés van.

| Hol | Mit tud |
|---|---|
| panel-ikon | szám + lista (mint eddig) |
| lista alja | **Florum megnyitása** gomb |
| fejléc | **Megnyitás** gomb (a Frissítés mellett) |
| kattintás | alapból lista; beállítható: „Kattintásra a Florum nyíljon meg” |
| középső gomb | mindig megnyitás |
| hibánál | a widget azt írja: „a lenti gomb el is indítja” – és tényleg elindítja |

### Hogyan nyílik meg?

A widget a futó Florumtól kéri: `GET /api/megnyitas` (csak helyi gépről). A Florum
ezt a `florum-megnyitas.sh`-t futtatja le, ami ebben a sorrendben dönt:

1. ha a háttérszerver nem fut → elindítja (port 8777),
2. ha a **KDE-ablak már nyitva** van → előtérbe hozza (`kdotool` / `wmctrl` / `xdotool`),
3. ha van **PySide6** → a saját KDE-ablakot indítja (`florum-kde.py`),
4. különben **böngésző / Chromium app-mód** (`florum.py --app`).

Így nem lesz két ablak és két szerver sem: a második kattintás csak előtérbe hozza
a már futó ablakot.

### Áttérés két ikonról

1. jobb klikk a fölösleges panel-ikonon → *Eltávolítás a panelről*,
2. `bash install.sh` (a régi második menübejegyzést `.regi` végződéssel félreteszi),
3. `bash telepites-florum-panel.sh` (a widget frissül; a régi QML-gyorsítástat törli),
4. a panel újraindul, és már egy Florum van.

## 18. Új funkciók (1.30.5) – az adatok saját mappába, tartósan

### Mi a különbség a `--data-dir` és az átköltöztetés között?

| | `--data-dir` | `florum-atkoltoztetes.sh` |
|---|---|---|
| meddig érvényes | **csak arra az indításra** | **állandóan** (a `florum-adat.conf`-ba írja) |
| átmásolja a meglévő adatokat | nem | igen (JSON + képek + mentések) |
| ellenőrzi az átvitelt | – | növény- és naplószám egyezés |
| újraindítja a szervert | nem | igen, az új mappával |
| a panel/menü is ezt használja | nem | igen |

### Hol van a beállítás?

`florum-adat.conf` a program mellett, egyetlen sor:

```
DATA_DIR="/home/…/Florum-adat"
```

Ezt olvassa a `florum-megnyitas.sh` (és ezen át a menü, a panel, a frissítő), valamint
a `florum-frissites.sh`. A háttérszolgáltatásnál a `FLORUM_DATA` környezeti változó
ugyanezt jelenti – kézzel: `systemctl --user edit florum-szerver`.

### Mit visz át pontosan?

| Átvitt | Nem vitt (miért) |
|---|---|
| `florum-data.json` + `.bak.json` | `browser-profile/` – újragenerálódik |
| `photos/` (összes kép) | `florum.ics` – indításkor újraíródik |
| `mentes/` (perc/napi/havi pillanatképek) | maga a program és az adatbázis (az a program mellett van) |
| `notify-state.json` | |

### Kipróbálás

```bash
bash florum-atkoltoztetes.sh --mi                      # most melyik mappát használja?
bash florum-atkoltoztetes.sh ~/Florum-adat --dry-run   # mi történne?
bash florum-atkoltoztetes.sh ~/Florum-adat             # átköltöztetés
```

---

## 19. Új funkciók (1.30.6) – a naptárválasztó a KDE ablakban + a „Váratlan hiba” megszüntetése

Két hibajelentés érkezett; **egyik sem a te hibád volt**, mindkettő a programban volt.

### 19.1. „kde ablakban a naptárválasztó felugrik és azonnal eltűnik”

**Mi volt az ok?** A dátummezők natív `<input type="date">` mezők voltak. Az ilyen mező
választója nem a lap része, hanem a böngészőmotor (Chromium / QtWebEngine) **külön
felugró ablaka**. A KDE-s ablakban (WebEngine) ez az ablak elveszti a fókuszt, amint a
Florum újrarajzol vagy a laphoz nyúlsz – és ilyenkor azonnal be is zárul. Ez pontosan a
jelentett tünet: *felugrik és eltűnik*. Böngészőben ez nem látszik, ezért nem volt
észrevehető.

**Megoldás: saját naptár-választó, a lapon belül.**

* a natív dátummező megmarad, de rejtve → minden más kód (mentés, `.value`) változatlanul működik;
* helyette szövegmező + naptár gomb: `2026. 11. 15.`
* a naptár `position: fixed` – nem vágja le egy görgethető doboz, és **görgetésre nem csukódik be**, csak követi a mezőt;
* hétfővel kezdődő hónaprács, hónap- és év-léptetés (`‹ ›`, `« »`), a mai nap bekeretezve;
* gyorsgombok: **Ma**, **Holnap**, **Törlés**;
* a dátum beírható kézzel is: `2026. 11. 15.`, `2026-11-15`, `2026/11/15` – érvénytelen beírásnál visszaáll az előző értékre;
* `Esc` vagy a mezőn kívülre kattintás zárja be;
* minden dátummező magától átalakul, akkor is, ha később rajzolódik ki (naptár-tábla, beállítások) – ezt egy `MutationObserver` figyeli.

Az érintett mezők: növény hozzáadása/szerkesztése (utolsó öntözés, utolsó tápoldatozás,
utolsó permetezés, utolsó átültetés), a naptár „Ugrás dátumra”, a beállítások ünnepnapjai.

### 19.2. „Váratlan hiba történt a felületben: Uncaught ReferenceError: entry is not defined (:6466)”

**Mi volt az ok?** A „Mit találtam?” – linkről kiolvasott adatlap rajzolója (`openInfoFetched`)
a tápoldat- és kerti blokkban egy `entry` nevű változóra hivatkozott, miközben a függvény
paramétere `e` volt. Amint a kiolvasott adatban tápoldat vagy kerti adat volt, a rajzolás
elhasalt, és a felület a piros „Váratlan hiba” sávot mutatta.

**Megoldás:** `var entry = e || {};` a függvény elején. A paraméter nevét **nem** írtuk át,
mert a `e.latin`, `e.forras`, `e.megjegyzes` hivatkozások sok helyen szerepelnek.

### 19.3. Új teszt

`node teszt-datum.js` – 16 ellenőrzés:

| Mit néz? | Miért? |
|---|---|
| kiolvasott adatlap (tápoldat + kerti szezon) hiba nélkül kirajzolódik | a `ReferenceError` nem jöhet vissza |
| üres adatlappal sem száll el | `var entry = e || {}` véd |
| a natív dátummezők rejtve vannak, mellette saját szövegmező + gomb | itt nem lehet natív felugró |
| a naptár `position: fixed`, a lapon belül nyílik | nem tűnhet el |
| görgetésre **nem** csukódik be | ez volt a KDE-s tünet |
| napra kattintás → érték + `change` esemény | a mentés működik |
| „Ma” / „Törlés” / gépelt dátum / hónap-léptetés / `Esc` | minden út járható |
| a beállítások dátumai is átalakulnak | ne maradjon natív mező |
| nincs kezeletlen JS-hiba | a „Váratlan hiba” sáv ne jelenjen meg |

```bash
node teszt-datum.js        # 16/0
```

### 19.4. Ha a régi példány fut

A javítás csak újraindítás után látszik:

```bash
bash florum-verzio.sh --ujraindit
```

---

## 20. Új funkciók (1.31.0) – a hőmérséklet végre számít

> **A kérdés:** „Hőmérséklet nem számít? Nyáron 28–30 °C, télen 19–23 °C.”
> **A válasz eddig:** nem számított. A Florum a naptárból dolgozott.
> **Mostantól:** igen, ha bekapcsolod – és alapból nem borít fel semmit.

### 20.1. Miért volt eddig naptári?

Az adatbázis két öntözési értéket ismer: **nyár** (pl. 7 nap) és **tél** (pl. 12 nap),
és a program az **október 1. – február vége** téli időszakhoz kötötte a váltást.
A növény adatlapján a „18–27 °C” csak **felirat** volt, nem számított bele semmibe.

Ez a gyakorlatban jól működik (a naptári téli szünet a fényhiányt is leköveti), de
nem veszi figyelembe, hogy **nyáron 30 °C-on a föld 2–3 nap alatt kiszárad**, télen
20 °C-on viszont 10–14 napig is eláll a víz.

### 20.2. Mit tud most

A **Beállítások → Szoba hőmérséklete** panelen:

* egy kapcsoló: **„Hőmérséklet szerinti igazítás”** (alapból **kikapcsolva** – a megszokott működés nem változik),
* **12 havi mező** a szoba átlaghőmérsékletével (előre kitöltve egy tipikus magyar szobával:
  nyár 27–28 °C, tél 21 °C),
* gyorsgombok: **Nyári átlag (27–28 °C)**, **Téli átlag (21 °C)**, **Vissza az alapértékre**,
* egy magyarázó sor, ami kiírja a nyári és a téli szorzót,
* a növény űrlapján a **„Hőmérséklet, amit szeret (°C)”** mező (pl. 15–27), amit a
  linkről kiolvasott adat („18–27 °C”) magától kitölt.

A számolás:

```
időköz = alap_időköz × hőmérséklet-szorzó
szorzó = 1 + (a növény ideális sávjának közepe − szoba hőmérséklete) × 0,055
```

* meleg szoba → **kisebb** szorzó → **sűrűbb** öntözés,
* hűvös szoba → **nagyobb** szorzó → **ritkább** öntözés,
* a szorzó **0,70 … 1,40** közé van szorítva – ennél nagyobb eltérést nem enged,
  mert akkor a naptári téli szünetet írná felül (az a fényhiány miatt kell).

Példa a te számaiddal (öntözés nyáron 7 nap, télen 12 nap, a növény sávja 15–27 °C):

| Szoba | Szorzó | Nyári időköz | Téli időköz |
|---|---|---|---|
| 28–30 °C (nyár) | ×0,70 | 7 → **5 nap** | – |
| 23 °C (átmenet) | ×0,94 | 7 → 7 nap | 12 → 11 nap |
| 19–21 °C (tél) | ×1,00–1,06 | – | 12 → **12–13 nap** |

A **tápoldatozást szándékosan nem** igazítja: azt a szezon és a tápoldat-típus vezérli,
a téli tilalom sérthetetlen. A **permetezést** igen (a meleg szobában a levelek is
gyorsabban száradnak).

### 20.3. Hol látszik a felületen?

* a **teendő-sorban**: `🌡 meleg szoba, hamarabb (×0,70)` – egérrel fölé menve a magyarázat:
  `28 °C (a növénynek 15–27 °C) · melegebb a szokásosnál → hamarabb szárad, sűrűbb öntözés · ×0,70`,
* a **Növények fülön** a kártyán egy kis jelzés: `🌡 ×0,70`,
* az űrlapon a mező alatt: „Most 23 °C van beállítva erre a hónapra → az öntözési időköz ×1,06.”

### 20.4. Mit NE várj tőle

* Nem helyettesíti a **föld-ellenőrzést**: ha a cserép alján áll a víz, hiába 30 °C.
* Nem kér **hőmérőt** és internetet – kézzel megadott havi átlagokkal dolgozik.
* A **kerti növényeknél** a szezon (április–október) az erősebb szabály: szezonon kívül
  akkor sincs öntözés, ha a szoba meleg lenne.

### 20.5. Ellenőrzés

```bash
node teszt-homerseklet.js     # 26/0
```

A teszt azt is ellenőrzi, hogy **kikapcsolva minden a régi marad**, a szorzó iránya jó,
a határok tartanak, a téli szünetet nem lehet felülírni, és a felület kiírja a magyarázatot.

---

## 21. Új funkciók (1.32.0) – hőmérséklet modul: helyiségenkénti mérés

> **A kérés:** „Az összes helyiségben mérem a hőmérsékletet, és tudnám rögzíteni.
> Ennek változását lehetne figyelembe venni.”

Eddig a hőmérséklet vagy a naptárból jött, vagy a Beállításokban megadott **havi átlagból**.
Most van **mért adat**: új **Hőmérséklet fül**, ahol helyiségenként rögzíted, amit a hőmérőn látsz.

### 21.1. Mit tud a fül

* **Mérés rögzítése**: helyiség (a növények helyiségei + „+ Új helyiség…”), hőmérséklet,
  páratartalom (nem kötelező), nap, megjegyzés. A magyar **vessző is jó**: `22,5`.
* **Kártya minden helyiségre**: mai érték, `kényelmes / meleg / hűvös` besorolás,
  7 és 30 napos átlag, **hőingás** (nappal–éjjel), **trend** (`↗ melegszik 1,4 °C / hét`),
  és egy 14 napos kis grafikon.
* **Napi kép**: az utolsó 14 nap helyiségenként, a mai nap bekeretezve.
* **Előzmény-táblázat**: a legutóbbi 60 mérés, egyenként törölhető.
* **„Minden helyiség ma”**: sorban bekéri a mai értékeket (amelyik helyiségben már van mai mérés, azt kihagyja).
* **CSV letöltés**: `nap; helyiseg; homerseklet_C; paratartalom_szazalek; megjegyzes` – táblázatkezelőbe betölthető.

### 21.2. Hogyan számol bele az öntözésbe

A sorrend szigorú:

1. **van mérés az utóbbi 10 napból** a növény helyiségére → **az számít** (a legutóbbi),
   a **trend felével** előrevetítve (a cserép földje lassan követi a szobát, max ±2 °C),
2. nincs mérés → a Beállítások **havi átlaga** (ha bekapcsoltad),
3. az sincs → **naptári** működés (ahogy eddig).

A számolás ugyanaz a szorzó, mint eddig: `× (1 + (a növény ideális sávjának közepe − hőmérséklet) × 0,055)`,
**0,70 … 1,40** között. A tápoldatozást továbbra sem igazítja (szezon + téli tilalom), a téli
szünet sérthetetlen, és kerti növénynél a szezon az erősebb szabály.

Példa (öntözés nyáron 7 nap, télen 12 nap):

| Helyiség | Mért | Szorzó | Időköz |
|---|---|---|---|
| Nappali (délután) | 28 °C | ×0,70 | 7 → **5 nap** |
| Hálószoba | 18 °C | ×1,17 | 12 → **14 nap** |
| Nappali, melegedő trenddel | 26 °C, +1,4 °C/hét | ×0,70 | 7 → **5 nap** |

### 21.3. Hol látszik még

* **Ma fül** tetején helyiségenként egy kocka (`Nappali 26,5 °C – ma mérve`) + gomb a fülre,
* **Naptár** (Nap/Hónap nézet): a rács **fölött** „Hőmérséklet ebben a hónapban” – helyiségenként
  havi átlag, hőingás és a napi értékek sávja,
* **Növények** fül: a kártyán `🌡 ×0,70`,
* **teendő-sor**: `🌡 meleg szoba, hamarabb (×0,70)`, fölé menve a mért értékkel és a trenddel,
* **Beállítások**: ha van friss mérés, kiírja, hogy **az számít, nem a havi átlag**.

### 21.4. Adat, mentés, korlátok

* a mérések a mentett állapot részei (`tempLog`), tehát a `florum-data.json`-ba kerülnek,
  a `florum.py` menti és visszatölti őket, és a `florum-atkoltoztetes.sh` is átviszi a mappával;
* legfeljebb **4000 mérés** őrződik meg (kb. 5 év, napi 2 mérés 6 helyiségből) – a legrégebbiek fogynak;
* a hibás sor (rossz szám, üres helyiség) **kiszűrődik**, nem borít fel semmit;
* 10 napnál régebbi mérés nem számít „most” – onnantól a havi átlag lép be, hogy egy elfelejtett
  mérés ne vezesse félre hónapokig.

### 21.5. Hőmérséklet-grafikon (1.33.4)

> **A kérés:** „Valamiféle hőmérséklet grafikon jó lenne.”

A fül tetején, a helyiség-kártyák alatt **összefüggő görbe** mutatja a méréseket – nem külön
kis csíkok, hanem egy közös diagram, ahol a helyiségek egymáshoz is hasonlíthatók.

* **Helyiségenként külön vonal**, saját színnel; a jelmagyarázat megmondja, melyik melyik.
* **°C-tengely** kerek beosztással (1 / 2 / 5 / 10 fokos lépés, a hőingáshoz igazodva) és
  vízszintes rácsvonalakkal; a napok a vízszintes tengelyen.
* **Zöld ideális sáv**: a növények `tempRange` értékeinek uniója (pl. 15–27 °C), szaggatott
  határvonallal – egy pillantásra látszik, mikor csúszott ki a hőmérséklet a jó tartományból.
* **A mérések között egyenesen vezet át** a vonal: a szoba hőmérséklete nem ugrik, csak lassan
  változik; a mérés helyét pont jelöli. A ponton egérrel a dátum és az érték is látszik.
* **Időtartam-választó**: `7 / 14 / 30 / 90 nap` gombok (alapból 14 nap).
* **Mai nap** szaggatott függőleges vonallal jelölve.
* **Összegzés** sorban, helyiségenként: utolsó érték, min, max, átlag, **ingás**.
* Ha még nincs mérés, a grafikon helyén **magyar magyarázat** áll, nem üres doboz.

A kártyákon lévő kis csík továbbra is 14 napot mutat – az a gyors ránézés, a nagy grafikon a műszer.
A grafikon **beépített SVG**, semmilyen külső könyvtár nem kell hozzá, és a zipben is ugyanígy
működik internet nélkül.

### 21.6. Ellenőrzés

```bash
node teszt-homerseklet-modul.js    # 38/0 (benne a grafikon 9 ellenőrzése)
node teszt-homerseklet.js          # 26/0 (a havi átlagos mód)
```

A teszt lefedi a rögzítést (magyar vessző, hibás érték), a statisztikát (átlag, ingás, trend),
a mérés elsőbbségét a napi átlaggal szemben, a trend hatását, a 10 napos korlátot, a fül
minden elemét, a **grafikont** (tengely, helyiségenkénti vonal, mérési pontok, ideális sáv,
mai jelölés, időtartam-váltás, összegzés, üres állapot, tengely-osztás), a Ma fül kockáit,
a naptár-sávot, a mentést/visszatöltést és a selejt-szűrést.

---

## 22. Docker és Arcane (1.33.4) – konténerben, felülettel

> **A kérdés:** „ez dockerben fut. Hogyan frissítsem legjobban? Arcane is fent van.”

Rövid válasz: **ne a felületről indított konténert frissítsd kézzel** – két dolgot kell elválasztani:
a **programot** (kép) és az **adatokat** (kötet). Ha az adat köteten van, a frissítés egy kattintás,
és semmi nem veszik el. A Florumhoz most már van kész Docker-kép és Arcane-barát compose fájl.

### 22.1. Mi került a csomagba

| Fájl | Mire való |
|---|---|
| `docker/Dockerfile` | a kép: `python:3.13-slim`, **nem root** (uid 1000), `/data` kötet, healthcheck, `TZ=Europe/Budapest` |
| `docker/compose.yaml` | `docker compose` / **Arcane stack** (port `127.0.0.1:8777`, `./data:/data`, napló-korlát) |
| `docker/florum-docker.sh` | egyparancsos segéd: `epites`, `indit`, `allapot`, `mentes`, `frissit`, `naplo`, `leallit`, `torol`, `ellenorzes` |
| `docker/proba-docker.py` | a docker-fájlok ellenőrzése **docker nélkül is** (43 ellenőrzés) |
| `.dockerignore` | teszt/patch/előnézet/zip ne kerüljön a képbe |

### 22.2. A legfontosabb szabály: az adat köteten legyen

A Florum mindent egy fájlba ment (`florum-data.json`, benne a növények, napló, **hőmérséklet-mérések**),
plusz `photos/`, `mentes/`. A konténeren belül ez a `/data`. Ha ez **nincs** köteten, a konténer
újrahúzásakor minden elvész.

```yaml
volumes:
  - ./data:/data     # bal: a gazdagép mappája (Arcane alatt a stack mappájában), jobb: a konténerben
```

Ellenőrzés bármikor:

```bash
bash docker/florum-docker.sh allapot     # hol van az adat, mekkora, fut-e
bash docker/florum-docker.sh mentes      # ZIP a kötetből (pl. frissítés előtt)
```

### 22.3. Frissítés – három út, a legjobb elöl

**A) Git-szinkron Arcane-ban (ez a „legjobb”, ha van repód)**

1. tedd a Florum mappát Gitbe (a `docker/compose.yaml` már benne van),
2. Arcane → **Git Syncs** → repository + branch, *compose path*: `docker/compose.yaml`,
   *Auto Sync* be,
3. új verzió = `git push` → Arcane újraépít és újraindít. A `./data` kötet **megmarad**,
   mert a compose fájl nem változik, csak a kép.

**B) Kézi frissítés a segédszkripttel (ma este ez a legegyszerűbb)**

```bash
unzip -o florum-1.33.4-tiszta.zip -d ~/florum-uj     # az új verzió
cd ~/florum-uj/florum
bash docker/florum-docker.sh frissit                # mentés NEM kell: az adat a köteten van
```

A `frissit` ezt teszi: új kép építése → `compose up -d --build` → `/api/info` ellenőrzés.
Az adat a `docker/data` mappában marad, a régi kép visszaállítható.

**C) Arcane-ban kézzel**

Arcane → **Projects/Stacks** → a Florum stack → *Pull/Rebuild* (ha a compose-ból épül),
vagy **Images** → *Pull* (ha regisztrációs képből húzod: `image: florum:…` → cseréld saját címkére).

> ⚠️ Ha csak a **container**-t indítod újra Arcane-ban, az **nem** frissít: a régi képet indítja újra.

### 22.4. Amit érdemes tudni a beállításokról

* **Port**: `127.0.0.1:8777:8777` – csak a helyi gépről érhető el. Ha a hálózaton is kell,
  `"8777:8777"`, de tedd tűzfal mögé: a Florum **hitelesítés nélküli** helyi app.
* **`--host 0.0.0.0`** a konténerben **kötelező** (különben kívülről nem érhető el) – a compose
  ezt már tartalmazza.
* **időzóna**: `TZ=Europe/Budapest`, különben a napi emlékeztetők elcsúsznak.
* **jogosultság**: a konténer uid 1000, a `docker/data` mappát egyszer kell írhatóvá tenni
  (`chmod 775`), ezt a szkript megteszi.
* **emlékeztetők**: a `notify-send` a konténerben nincs – a naptárfájl (`.ics`) és a felület
  emlékeztetője viszont működik. Asztali értesítéshez a Florumot a gazdagépen kell futtatni.
* **KDE panel / KDE ablak**: a widget a gazdagép KDE-jében fut, és a `http://127.0.0.1:8777`-et
  nézi – így a konténeres Florummal is működik, ha a port a helyi gépre van leképezve.

### 22.5. Ellenőrzés

```bash
python3 docker/proba-docker.py        # 43/0 – docker nélkül is fut
bash docker/florum-docker.sh ellenorzes
```

A `proba-docker.py` azt is megnézi, hogy a program **valóban elindul** a konténernek szánt
kapcsolókkal (`--host 0.0.0.0 --data-dir …`), és hogy a `/api/info` válaszol.

### 22.6. „Conflict. The container name "/florum" is already in use” – mit tegyek?

Ez a leggyakoribb hiba, és **nem hiba, csak névütközés**: a gépen már van egy `florum` nevű
konténer (korábbi `docker run`, vagy egy másik mappából indított compose), és az új compose
ugyanezt a nevet akarja használni. Fontos: **a konténer törlése az adatot is viszi, ha az nincs
köteten** – ezért a sorrend: *mentés → törlés → indítás*.

**A legjobb: egy parancs, ami mindent jól csinál**

```bash
cd ~/florum-uj/florum            # az új verzió mappája
bash docker/florum-docker.sh atvesz
```

Ez ezt teszi:

1. megnézi, hova csatolja a régi konténer az adatot (**van-e kötete**),
2. ha **nincs** kötet (az adat a konténeren belül van) → `docker cp`-vel **kimásolja** a
   `docker/data` mappába, és kiírja, mi van benne: `növény: 12 · napló: 340 · mérés: 56`,
3. ha az új mappában **már** van adat (mert közben elindult üresen), a kettőt
   **egyesíti** – növény azonosító, napló (növény+típus+nap), mérés-azonosító szerint,
   a régi fájl `florum-data.json.elotte.json` néven megmarad,
4. **csak ezután** törli a régi konténert (`docker rm -f florum`),
5. elindítja az újat, és ellenőrzi a `/api/info`-t.

**Kézzel, ha inkább lépésenként**

```bash
bash docker/florum-docker.sh utkozes      # megmutatja: mi fut, hova van kötve az adat
bash docker/florum-docker.sh mentes-regi  # a régi konténer adatai → docker/regi-kontener-mentes-…
docker rm -f florum                       # ← CSAK a mentés után!
bash docker/florum-docker.sh indit
```

Vagy a nyers docker-parancsokkal:

```bash
docker ps -a --filter name=florum         # létezik-e
docker cp florum:/data/. ./docker/data/   # adat ki (ha nincs köteten)
docker rm -f florum                       # régi konténer törlése
docker compose -f docker/compose.yaml up -d --build
```

**Honnan tudom, hogy az adat megvan?** A felület bal alsó sarkában a „Mentés" állapot, vagy:

```bash
bash docker/florum-docker.sh allapot      # kiírja az adatmappa tartalmát és méretét
python3 docker/kontener-adat.py --vizsgal docker/data
```

**Ha az adat máshol van** (a régi konténer saját kötete volt):

```bash
docker inspect florum --format '{{json .Mounts}}'   # itt látszik a gazdagép-mappa
cp -a /az/a/mappa/. ./docker/data/                  # átmásolás
```

> Miért nem elég a `docker rm`? Mert a `florum` név a konténerhez tartozik, a **kötet nem**.
> A `docker rm` a kötetet nem törli – de a *konténer rétegében* lévő fájlokat igen.
> Ezért megy előbb a mentés.

### 22.9. Arcane: hogyan frissül a Florum?

> **A kérdés:** „Arcane hogyan frissül? (GitHubra felraktam.)”

Az Arcane **Git Sync**-kel követi a repót: beállítod egyszer, utána a `git push` = frissítés.
De a Florum compose fájljában volt egy csapda, amibe az Arcane **belefut** – ezt előbb meg kell
oldani, különben a szinkron „sikeres”, a konténer mégsem indul.

#### A hiba, amit el kell kerülni

A `docker/compose.yaml`-ban ez áll:

```yaml
build:
  context: ..            # ← a repó gyökere EGY szinttel feljebb
  dockerfile: docker/Dockerfile
```

Ez kézi `docker compose`-nál jó, mert a `docker/` mappából indítod. Az Arcane viszont
**csak a compose fájlt (vagy a saját mappáját) másolja** a saját projekt-mappájába – a
szülőmappa nem a repó gyökere lesz, így a build ezt adja:

```
failed to read dockerfile: open Dockerfile: no such file or directory
```

#### A megoldás: külön compose fájl az Arcane-hez

```bash
cd ~/florum
bash docker/florum-docker.sh compose-frissit
```

Ez létrehozza a **`docker/arcane/compose.yaml`** fájlt – `build:` **nélkül**, kész képpel:

```yaml
image: florum:${FLORUM_VERSION:-1.33.4}
volumes:
  - ./data:/data
```

és mellé a `docker/arcane/.env` fájlt (`FLORUM_VERSION=1.33.4`). A képet a **gazdagépen**
építed, az Arcane csak lefuttatja – neki nem kell Dockerfile-t fordítania.

#### Beállítás az Arcane-ban (egyszer)

**Git Syncs → Git Repositories → Add Repository**
– URL: `https://github.com/zsoldospeti/florum.git` (vagy SSH), hitelesítés: **HTTP + token**
(ha privát a repó; a tokenhez `Contents: Read` elég).

**Projects → Create Project → From Git Repo** (vagy *Git Syncs → Add Sync → Pull*):

| Mező | Érték |
|---|---|
| Sync Name | `florum` (ez lesz a projekt neve) |
| Target Type | Project |
| Project | *Create a new project* |
| Branch | `main` |
| **Compose File Path** | **`docker/arcane/compose.yaml`** |
| **Sync Files** | **BE** (a `./data` mappa és a `.env` miatt) |
| **Auto Sync** | BE, intervallum **5–15 perc** |
| **Pull Image After Sync** | BE |
| **Redeploy After Sync** | BE |

> ⚠️ Ha a `docker/compose.yaml`-t adod meg, a build elhasal (lásd fent).
> A `docker/arcane/compose.yaml` az, ami Arcane alatt működik.

#### A frissítés menete onnantól

```bash
cd ~/florum
bash florum-kiadas.sh --uj 1.33.4 --epit --csomag
bash docker/florum-docker.sh compose-frissit    # az Arcane compose + .env az új verzióra
git add -A && git commit -m "Florum 1.33.4" && git push
bash docker/florum-docker.sh epites             # helyben megépíted a képet
```

…majd az Arcane a **következő Auto Sync**-nél behúzza és újraindítja (5–15 perc).
Azonnali frissítés: Arcane → a projekt → **Sync from Git** → **Redeploy**.

#### Az adat: mi történik az első szinkronnál

A kép adatkönyvtára a compose **melletti `./data`** mappa. Két eset:

* **Ha eddig is a repó mappájából indítottad** – ugyanaz a `docker/data` lesz, az adat a helyén;
* **Ha eddig máshonnan** – az Arcane **új projekt-mappát** hoz létre, és az új `./data`
  **üres** lesz. Ilyenkor előbb ments ki:

```bash
bash docker/florum-docker.sh arcane-mentes      # zip a ~/ mappába, a futó konténerből
# majd az első szinkron után:
docker stop florum
unzip -o ~/florum-arcane-mentes-*.zip -d /tmp/florum-vissza
cp -a /tmp/florum-vissza/florum-data/. <arcane-projekt-mappa>/data/
docker start florum
```

> A compose `name: florum` és a `container_name: florum` miatt a régi és az új konténer
> **ugyanazt a nevet** akarja – ezért az első szinkron előtt állítsd le az Arcane-on kívül
> indított példányt (`bash docker/florum-docker.sh leallit`), különben:
> `Conflict. The container name "/florum" is already in use`.

#### Ha a szinkron „sikeres”, de a régi verzió fut

Ezt a leggyakrabban a **kép** okozza: a compose ugyanazt a címkét kéri, a Docker pedig
a meglévő képet használja. Ellenőrzés:

```bash
curl -s http://127.0.0.1:8777/api/info | python3 -c "import json,sys;print(json.load(sys.stdin)['appVersion'])"
docker images | grep florum      # a kép dátuma egyezzen az új builddel
```

Megoldás: **Pull Image After Sync = BE**, vagy az Arcane-ban *Redeploy* + *Pull image*,
illetve a gazdagépen `bash docker/florum-docker.sh epites`.

#### Hogyan NE csináld

* ne add meg a `docker/compose.yaml`-t az Arcane-nak (build-kontextus hiba);
* ne kapcsold ki a **Sync Files**-t (a `./data` és a `.env` nem kerül oda);
* ne használj **név nélküli kötetet** (`volumes: data:`) – az adat a kötetben nehezen
  található meg, a `./data` mappa látszik, menthető, másolható;
* az Arcane „container restart” **nem** frissít – a projektet kell újra deploy-olni.

---

## 23. Hol van az új verzió? (1.33.4) – a munkaterület és a három példány

> **A panasz:** „workspace nem frissül.”

Nem a felület hibája volt. A munkaterületen **három `florum.html`** van, és eddig
kettő maradt vissza a grafikon bevezetésekor. Ez a fejezet rendet tesz köztük – és a
`teszt-verzio.py` mostantól **elbukik**, ha bármelyik példány elcsúszik. Ez az a fajta hiba,
amit nem szabad észrevenni: nem a felhasználó rontja el, hanem a build marad félbe.

### 23.1. Melyik fájl melyik

| Mappa | Mi ez | Ki írja |
|---|---|---|
| `florum/florum.html` | **ez fut**, ezt szolgálja ki a 8777-es port, ez van a zipben | `kinezet-egyesites.sh` |
| `minden_html-original/florum/florum.html` | **tiszta forrás** (téma nélkül) – ide ír a `build-plant-db.py --html` | te / a build |
| `minden_html-egyesitett/florum/florum.html` | a gyűjtemény egyesített példánya (nem fut) | `kinezet-egyesites.sh` |

**A helyes sorrend minden módosítás után:**

```bash
cd ~/florum
python3 build-plant-db.py --html ~/minden_html-original/florum/florum.html   # 1. forrás
bash kinezet-egyesites.sh                                                    # 2. futó fájl + egyesített
```

> Ha a 2. lépés kimarad, a felület a **régit** mutatja – hiába van benne a forrásban az új dolog.
> A `kinezet-egyesites.sh` a `minden_html-original`-ból dolgozik, ezért a forrás az igazság.

### 23.2. Ellenőrzés egy paranccsal

```bash
python3 teszt-verzio.py     # 31/0 – többek között ez is:
```

A teszt mostantól azt is nézi, hogy

* a három `florum.html` **ugyanazt a verziót** írja-e a `<meta name="florum-version">`-ben;
* a `minden_html-egyesitett` példány **nem maradt-e el** a forrástól (a verzió és a
  legfontosabb új funkciók – jelenleg a `tempChartHTML` grafikon – megvannak-e benne);
* a munkaterületen **csak a legfrissebb zip** van-e meg (`florum-1.33.4-tiszta.zip`);
* a `florum/florum.html` és a `VERSION` egyezik-e.

Ha bármelyik elbukik, a hibaüzenet megmondja, **melyik fájl** maradt el és **melyik
parancsot** kell lefuttatni. Új verzió kiadásakor ezt a tesztet futtasd először.

### 23.3. Ha a böngésző mégis a régit mutatja

A szerver `Cache-Control: no-store, must-revalidate` fejlécet küld, tehát a HTML nem
gyorsítótárazódik. Ha mégis a régi látszik:

```bash
curl -s http://127.0.0.1:8777/api/info | python3 -m json.tool | head -6
# appVersion / fileVersion / versionMismatch: false  → jó
```

Ha itt a régi verzió van, akkor nem a böngésző a hibás, hanem egy régi példány fut:

```bash
bash florum-verzio.sh --ujraindit     # egy kattintás, a régi helyett az új indul
```

Ha viszont itt is az új verzió van, csak a böngésző fülét kell újratölteni (Ctrl+Shift+R).

---

## 24. GitHub – verziókövetés és frissítés (1.33.4)

> **A kérdés:** „GitHubra hogyan tudom eltenni, hogy frissüljön ha kell?”

A GitHub itt nem látvány, hanem **frissítési csatorna**. Három dolgot ad:

1. **Verziótörténet** – minden kiadás visszakereshető, bármikor visszaállítható;
2. **Egyparancsos frissítés** a saját gépeden (`git pull`) – nem kell zipet cserélgetni;
3. **Arcane Git Sync** – a dockeres Florum magától frissül, az adat megmarad.

A repó a **programot** tartalmazza. A növényeid, méréseid, fotóid a saját gépeden maradnak
(`~/.local/share/florum`, illetve dockerben `docker/data`) – a `.gitignore` ezeket kizárja.

### 24.1. Egyszeri beállítás (kb. 3 perc)

**a) GitHub-fiók és üres repó** – böngészőben: *New repository* → név: `florum` →
**Private** (magán) → **ne** pipáld be a README-t, a `.gitignore`-t és a licencet
(a fájlok már megvannak). Létrehozás.

**b) A program mappájában:**

```bash
cd ~/florum
bash florum-kiadas.sh --git-elokeszites     # git repó + első commit
git remote add origin git@github.com:FELHASZNALONEV/florum.git
git push -u origin main
```

Ha még nincs SSH-kulcsod (a `git push` „Permission denied (publickey)” hibát ad):

```bash
ssh-keygen -t ed25519 -C "florum"          # Enter, Enter, Enter
cat ~/.ssh/id_ed25519.pub                  # ezt másold be GitHub → Settings → SSH keys
```

SSH helyett HTTPS is jó – ekkor a jelszó helyett **tokent** kér (GitHub → Settings →
Developer settings → Personal access tokens → *Fine-grained* → `Contents: Read and write`):

```bash
git remote add origin https://github.com/FELHASZNALONEV/florum.git
```

> A repót **privátnak** vedd fel. Nem azért, mert titok lenne, hanem mert a naptárad
> linkjei, a növényeid nevei a mentésben vannak – a mentés viszont nem megy fel.

### 24.2. Mit tesz fel és mit nem

| Felmegy a repóba | Soha nem megy fel |
|---|---|
| `florum.html`, `florum.py`, a szkriptek | `florum-data.json` (a növényeid, naplód) |
| `plants-db.json` (82 növény) | `photos/` (a fotóid) |
| `docker/` (Dockerfile, compose) | `mentes/`, `docker/data/` |
| `teszt-*.py`, `teszt-*.js` (21 teszt) | `*.zip` (a csomag nem kell a repóba) |
| README, OLVASSEL, `VERSION` | `*_patch.py`, `*-elonezet.html` |
| `.gitignore`, `.dockerignore` | `.env`, tokenek |

Ellenőrizni bármikor:

```bash
bash florum-kiadas.sh --allapot
#  ✔ a repóban nincs adat, fotó, zip és titok
```

### 24.3. Új verzió kiadása (a lényeg)

Amikor változtatsz valamit, **egy sorrend** van, és a szkript betartatja:

```bash
cd ~/florum
bash florum-kiadas.sh --uj 1.33.4 --epit --csomag   # verzió mindenhol + build + teszt + zip
bash florum-kiadas.sh --feltoltes                   # commit + push (teszt és adat-ellenőrzés után)
```

A `--uj` **mindenhol** cseréli a verziót – 35 fájlban, a három `florum.html` példányban is
(forrás, futó, egyesített). Ez azért kell, mert a build a forrásból dolgozik: ha a forrás
marad a régiben, a következő build **visszaírja** a régi verziót. Pontosan ez volt a
„workspace nem frissül” hiba, amit a 23. fejezet ír le.

A `--feltoltes` **előbb lefuttatja a `teszt-verzio.py`-t**, és ha bármi eltér, nem tölt fel.
Így nem kerülhet fel félkész állapot. Ha a VERSION és a HTML eltér (kézi szerkesztés),
a szkript ezt felismeri és mindkettőt cseréli.

### 24.4. Frissítés a gépeden (a másik irány)

```bash
cd ~/florum
git pull                        # új kód
bash florum-frissites.sh        # a futó példány újraindítása + verzió-ellenőrzés
```

Dockerben ugyanez:

```bash
bash docker/florum-docker.sh frissit     # git pull + újraépítés, az adat a köteten marad
```

**Arcane-dal:** *Git Syncs* → a `florum` repó → `docker/compose.yaml` → **Auto Sync**.
Attól kezdve a `git push` = új verzió a gépen, a `docker/data` érintetlen.
(Emlékeztető: Arcane-ban a „container restart” **nem** frissít – a stacket kell újraépíteni.)

### 24.5. „Permission denied (publickey)” – a leggyakoribb hiba

Ez a hibaüzenet **mindig ugyanazt jelenti: a GitHub nem ismeri fel a gépedet.**
Semmi köze a repó jogosultságához, a fájlokhoz vagy a Florumhoz. A sorrend ugyanis ez:

```
1. ssh-kulcs a gépen  →  2. a NYILVÁNOS kulcs fent a GitHubon  →  3. ssh -T próba  →  4. git push
```

Amikor ezt látod:

```
ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'github.com' to the list of known hosts.
git@github.com: Permission denied (publickey).
fatal: Could not read from remote repository.
```

* a **`yes` helyes volt** – az a GitHub valódi host-kulcsa (ez az ujjlenyomat a hivatalos);
* a `known_hosts`-ba bekerült, tehát **a hálózat jó és a github.com elérhető**;
* a 3. lépés hiányzik: **a kulcsod nincs fent a GitHubon** (vagy nem azt a kulcsot kínálja).

Egy paranccsal kiderül, melyik:

```bash
cd ~/florum
bash github-beallitas.sh
```

A diagnózis megmondja, van-e kulcs, van-e `origin`, és lefuttatja a tényleges próbát.
A javítás három útja – a szkript ezeket is elvégzi:

```bash
# ① kulcs készítése + a nyilvános kulcs kiírása (ezt másold a GitHubra)
bash github-beallitas.sh --kulcs
#    → https://github.com/settings/keys → New SSH key → beillesztés

# ② ha a 22-es portot tiltja a hálózat (ritka, de létezik)
#    ~/.ssh/config:
#        Host github.com
#            HostName ssh.github.com
#            Port 443
#            User git

# ③ SSH helyett HTTPS + token (SSH nélkül is működik)
bash github-beallitas.sh --https FELHASZNALONEV/florum
#    → https://github.com/settings/tokens → token → jelszó helyett a token
#    → git config --global credential.helper store
```

Újra ellenőrzés (ennél a siker így néz ki: `Hi FELHASZNALONEV! You've successfully authenticated`):

```bash
bash github-beallitas.sh --proba
```

> **A privát kulcs (`~/.ssh/id_ed25519`) soha nem hagyja el a gépedet.** Csak a `.pub`
> végű nyilvános kulcs megy fel a GitHubra. A szkript a `.pub`-ot írja ki, a privátot soha.

### 24.6. A „Repository not found” – a következő lépcső

Ha az azonosítás már rendben (`Hi FELHASZNALO! You've successfully authenticated`), de a
`--feltoltes` mégis elbukik, szinte mindig **ez** jön:

```
ERROR: Repository not found.
fatal: Could not read from remote repository.
```

Ez azt jelenti: **a repó még nem létezik a GitHubon** (vagy más a neve / más a felhasználónév).
A GitHub szándékosan ugyanezt írja, ha nincs jogosultságod – nem árulja el, melyik a kettő.

**Előbb nézd meg, mi van beállítva:**

```bash
git remote -v
```

Gyakori csapda: **már van egy `origin`**, ami máshova mutat. Ilyenkor a
`git remote add origin …` ezt adja: `error: remote origin already exists.` – a régi cím
megmarad, és a push a rossz helyre indul (innen a „Repository not found”). Ezt nem
`add`-dal, hanem **`set-url`**-lel kell átállítani:

```bash
bash github-beallitas.sh --ssh zsoldospeti/florum     # set-url, felülírja a régit
```

A szkript ezt magától elvégzi – a `--ssh` és a `--https` is `set-url`-t használ, tehát
akárhányszor lefuttatható.

**A repó-ellenőrzés (a commit ELŐTT, hogy ne derüljön ki utólag):**

```bash
bash github-beallitas.sh --repo
#  ✔ a repó létezik, de még ÜRES – ez jó (az első push feltölti)
#  ✘ a repó NEM érhető el ezen a címen   → lent az ok és a megoldás
```

> Az **üres repó nem hiba.** A `git ls-remote` üres repónál 2-es kóddal tér vissza – a
> Florum ezt „üres, de elérhető”-ként kezeli, nem hibaként. Ez pont a friss repó esete.

**A sorrend, ami működik:**

```bash
# 1) a repó létrehozása ÜRESEN (böngészőben!)
#    https://github.com/new
#      Repository name:  florum
#      Private           ✔
#      Add a README file ✗ NE
#      .gitignore/licence ✗ NE

# 2) a név ellenőrzése
git remote -v
#    helyes alak:  git@github.com:ZSOLDOSPETI/florum.git

# 3) ha más a név:
bash github-beallitas.sh --ssh ZSOLDOSPETI/az-igazi-nev

# 4) feltöltés
bash florum-kiadas.sh --feltoltes
```

Egyetlen paranccsal, ha a repó már létezik (az `origin`-t is átállítja):

```bash
bash florum-kiadas.sh --feltoltes --repo zsoldospeti/florum
```

Siker esetén ezt látod:

```
 ✔ a repó elérhető és még üres – az első push feltölti
 * [new branch]      HEAD -> main
 ✔ fent van a GitHubon: git@github.com:ZSOLDOSPETI/florum.git (1.33.4)
```

Ha nincs kedved böngészőzni, a GitHub CLI egy lépésben megcsinálja (létrehozás + push):

```bash
sudo pacman -S github-cli
gh auth login
gh repo create zsoldospeti/florum --private --source=. --remote=origin --push
```

> Ha a repó létrehozásakor **mégis** bepipáltad a README-t, a push ezt adja:
> `! [rejected] main -> main (fetch first)`. Nem kell törölni semmit:
> `git pull --rebase origin main`, majd újra `--feltoltes`. A `--rebase` a te commitjaidat
> teszi a behúzottak **után**, nem töröl semmit.

### 24.7. Ha a git „elakad”

| Hibaüzenet | Mit jelent | Megoldás |
|---|---|---|
| `Permission denied (publickey)` | a GitHub nem ismeri a géped kulcsát | **24.5** (a leggyakoribb) |
| `Authentication failed` | HTTPS + jelszó helyett token kell | 24.1/b, token |
| `rejected – non-fast-forward` | a GitHubon is van új commit | `git pull --rebase && git push` |
| `no changes added to commit` | nincs változás | nincs teendő, csak `git push` |
| `fatal: not a git repository` | nem a `~/florum` mappában vagy | `cd ~/florum` |
| `detected dubious ownership` | más felhasználó birtokolja a mappát | `git config --global --add safe.directory ~/florum` |

Ha egy kiadást vissza kell vonni (mert elrontottál valamit):

```bash
git log --oneline           # melyik commit melyik
git revert <commit>         # biztonságos visszavonás (nem töröl történelmet)
git push
```

### 24.8. Ellenőrzés

```bash
python3 teszt-verzio.py            # 43/0 – verzió, három példány, zip, szkriptek, .gitignore, GitHub-segéd
bash florum-kiadas.sh --allapot
bash github-beallitas.sh           # GitHub-hozzáférés diagnózisa (nem változtat semmit)
```

A `teszt-verzio.py` a **szkriptek futtathatóságát** is nézi (`florum-kiadas.sh`,
`florum-frissites.sh`) – egy `sed -i` ugyanis elveszi a `+x` jogot, és ezt a hiba osztályt
a teszt fogja meg, nem a felhasználó.

---

## 25. GitHub vagy saját meghajtó? – mi ingyenes, és mi elég neked

> **A kérdés:** „GitHub meddig ingyenes? Nem tudom ugyanezt megtenni saját meghajtóról?”

Rövid válasz: **a GitHub Free nem próbaidő, hanem véglegesen 0 Ft** – de nem is kötelező.
A git ugyanazt tudja egy pendrive-on. Alább a pontos tények, aztán a három út összevetve.

### 25.1. Mit ad a GitHub Free (2026. novemberi állapot)

| Mi | Ingyenes korlát | Neked elég? |
|---|---|---|
| Privát repók száma | **korlátlan** | bőven |
| Közreműködők | korlátlan | egyedül dolgozol |
| Tárhely | repó **1 GB alatt** ajánlott, fájlonként **100 MB** a kemény korlát | a Florum 0,5 MB |
| GitHub Actions (CI) | privát repóban **2000 perc/hó**, publikusban korlátlan | nem használjuk |
| Csomag-tárhely | 500 MB | nem használjuk |
| Issues, Projects, Dependabot | ingyenes | nem kötelező |
| Támogatás | csak közösségi fórum | nem kell |

**„Meddig?” – határidő nélkül.** A GitHub a Free csomagot „$0, örökre” alapon hirdeti;
nincs próbaidő, nincs lejárat. Amit **el lehet érni**: 2000 Actions-perc elfogyása (nálad nem
fog, mert nincs CI), 100 MB-nál nagyobb fájl (nálad nincs), vagy szabályzatváltozás – ezért
jó, hogy a repó **standard git**, bármikor átvihető. Ha egyszer fizetőssé válik valami,
a kódod nem esik csapdába: `git clone` és kész.

> Amit **érdemes** tudni: a GitHub a repódat elemzi (privátban is) biztonsági célból, és
> a privát repó sem „titkos széf”. A növényeid adatai viszont nincsenek a repóban
> (`.gitignore`), tehát ez téged nem érint.

### 25.2. Ugyanez saját meghajtóról – igen, működik

A git nem „GitHubhoz” való, hanem **elosztott**: bármelyik mappa lehet „szerver”.
Egy **bare repó** (`.git` végű mappa, munkapéldány nélkül) pont ezt tudja. A Florum mostantól
három GitHub nélküli utat is ismer:

```bash
# 1) pendrive / külső HDD / NAS-mappa  (a leggyorsabb, mindennapi)
bash florum-kiadas.sh --meghajto /run/media/peti/KINGSTON/florum.git

# 2) egyetlen fájl, az egész történettel (pendrive-ra, felhőbe, e-mailbe)
bash florum-kiadas.sh --bundle
#    → ~/florum-1.33.4-20261122.bundle   (kb. 0,5 MB)

# 3) visszaállítás bármelyikből, bármelyik gépre
bash florum-kiadas.sh --visszaallitas /run/media/peti/KINGSTON/florum.git ~/florum-masolat
```

Mindhárom ugyanazt csinálja, mint a GitHub-os út: **tesztel, kiszűri az adatot, commitol,
majd ment** – nem tud félkész állapotot felvinni. És ugyanaz a visszaút:

```bash
cd ~/florum && git pull meghajto main     # a másik gépen/frissen telepítve
```

### 25.3. Melyiket válaszd

| | GitHub (privát) | Pendrive / HDD | Bundle-fájl |
|---|---|---|---|
| Elérhető máshonnan | ✔ bárhonnan | ✘ csak ha nálad van a drive | ✔ (fájl, akár e-mail) |
| Mentés, ha a gép meghal | ✔ | ✔ (ha a drive megvan) | ✔ |
| Két gép szinkronja | ✔ automatikus | ✔ kézi, de egyszerű | ✘ kézi másolgatás |
| Arcane „Git Sync” | ✔ | ✔ lokális útvonal is jó | ✘ |
| Internet kell | ✔ | ✘ | ✘ |
| Kockázat | fiók/szabályzat | elveszik/elnyűtt drive | könnyen elvész |
| Költség | 0 Ft | egyszeri drive-ár | 0 Ft |

**A javaslatom:** a kettő **együtt**, mert nem ugyanazt védi.

* **GitHub** = a kód biztonsági mentése (ha a gép meghal, vagy új gépre költözöl);
* **saját meghajtó** = a **mentéseid** (a `florum-data.json`, a fotók) – ezek soha nem
  mennek fel a GitHubra, és a legfontosabbat, a növényeid történetét a drive védi.

```bash
# ez a kettő együtt a teljes biztonság:
git push                                   # a program
bash docker/florum-docker.sh mentes        # az adat (zip a ~/ mappába)
cp ~/florum-docker-mentes-*.zip /run/media/peti/KINGSTON/
```

### 25.4. Ha a meghajtó exFAT/FAT (a legtöbb pendrive az)

A pendrive-ok többsége exFAT – az nem tárol fájljogosultságot, ezért a git „minden fájl
megváltozott” zajt kelthet. A Florum kiírja, ha ilyet észlel, és a git-et erre beállítja:

```bash
git config core.filemode false
```

Ez nem hiba, csak a jogosultság-bit hiánya. Két dolgot viszont **ne** tegyél pendrive-ra:
a `docker/data` mappát (sok kicsi fájl, lassú) és a `photos/`-t (nagy) – ezekre a
`florum-docker.sh mentes` való, egy tömörített zipben.

### 25.5. Ellenőrzés

```bash
python3 teszt-verzio.py            # 48/0 – benne a meghajtós út valódi próbája
bash florum-kiadas.sh --segitseg   # a három út egy helyen
```

---

## 26. Naponta több mérés – napszak és évszak szerint (1.33.4)

> **A kérés:** „Naponta akár több mérési eredmény is rögzíthető lenne, ugyanoda.
> A statisztikák is változnának akár délelőtti-esti / helyiség, nyári-téli / helyiség stb.”

Eddig a felület ugyan elfogadott napi több mérést, de a statisztika **mindent egyetlen
napi értékre mosott** (a nap utolsó mérése), így a reggeli 18 °C és a délutáni 26 °C
ugyanúgy elveszett. Most ez megváltozott: **minden mérés megmarad, és számít.**

### 26.1. Mit tud most

* **Több mérés egy napra, ugyanabba a helyiségbe** – a rögzítő űrlapon új **Idő (óra:perc)**
  mező; üresen hagyva a mostani idő számít.
* **A nap értéke az átlag**, nem az utolsó mérés. 18 / 26 / 21 °C → a nap **21,7 °C**,
  mellette a napon belüli **min–max** (18–26) és a **hőingás** (8 °C).
* **Napszak fél automatikusan** az órából – nem kell kézzel választani:

  | Napszak | Idő | Miért ez a határ |
  |---|---|---|
  | hajnal | 04:00 – 08:00 | a legkínosabb hűvös, hajnali minimum |
  | délelőtt | 08:00 – 12:00 | melegszik |
  | délután | 12:00 – 18:00 | a napi csúcs |
  | este | 18:00 – 22:00 | hűlni kezd |
  | éjszaka | 22:00 – 04:00 | fűtés/hűlés nélküli állapot |

* **„Mikor meleg?” panel** – napszakonkénti átlag oszlopdiagrammon, helyiségenként, mellette
  a mérésszám (2-3 mérésből még nem trend, 2-3 hétből igen). A panel alatt a lényeg:
  *„hajnal a leghűvösebb · délután a legmelegebb · különbség 8 °C”*.
* **Órás profil** (0–23 óra, a háttérben): óránkénti átlag, csak a mért órákon – ebből derül
  ki, mikor van a szoba csúcsa.
* **Évszakok összevetése** – helyiség × évszak táblázat: **átlag · min–max · hőingás ·
  fagyos napok (5 °C alatt) · meleg napok (26 °C felett) · hány nap adata**. Ugyanaz a szoba
  nyáron és télen, egy táblázatban. Ha még csak egy évszakból van mérés, a táblázat megjelenik,
  de **kiírja**, hogy az összevetéshez másik évszak is kell.
* **A kártyán**: „ma: 21,7 °C · 3 mérés · ingás 8 °C”, alatta a napszakok bontása
  (délelőtt 20,5° · délután 25,5° · este 22,4°).
* **A táblázatban** új **Idő** oszlop a napszakkal („15:00 / délután”).
* **A grafikon** ugyanezt a napi átlagot rajzolja – nem hazudik mást, mint a statisztika.

### 26.2. Mit NEM változtat – és ez szándékos

* **Az öntözés számítása a legutóbbi mérésből indul** (10 napos korláttal), nem a napi
  átlagból. Ha délután 26 °C-ot mértél, a következő öntözésnél az számít – a nap átlaga
  elrejtené a csúcsot. A napi átlag **a statisztikáé**, a „most” érték **az öntözésé**.
* **A téli tápoldat-tilalom és a naptári téli szünet** érintetlen – a hőmérséklet továbbra
  sem írja felül őket.
* **A régi adat megmarad.** A régi méréseknél nincs értelmes időbélyeg (a program a mentés
  pillanatát tárolta), ezért betöltéskor a **nap 12:00-ja** lesz az idejük: napszak = délután
  eleje, nem „éjszaka 3-kor”. Így a napszak-statisztika nem lesz hamis a régi adattól.
* **Egy mérés/nap esetén minden a régi**: a napi átlag = a mérés, az órás profil és az
  évszak-tábla addig nem jelenik meg, amíg nincs mit összevetni.

### 26.3. Gyakorlati tanács

**Elég naponta kétszer mérni** – reggel (a nap indulása) és kora este (a csúcs után).
Ebből már látszik a napi ingás és a napszak-hatás; a délutáni harmadik mérés csak
pontosít. A hőmérőt ne tedd radiátor vagy ablak közelébe, és mindig ugyanoda – különben
a statisztika a hőmérő helyét méri, nem a szobáét.

### 26.4. Adat, korlátok

* a mérések korlátja **12 000** (kb. 5 év, napi 4 mérés 6 helyiségből) – eddig 4000 volt;
* a mérés rekordja: `{id, room, date, t, hum, note, ts}` – a **`ts` mostantól a mérés
  valódi ideje** (nem a mentés pillanata), ebből jön a napszak és az órás profil;
* a régi `florum-data.json` **átalakítás nélkül** betölthető (a hiányzó időt 12:00-ra teszi).

### 26.5. Ellenőrzés

```bash
node teszt-tobbmeres.js      # 23/0 – napi átlag, napszak, órás profil, felület
node teszt-evszak.js         #  9/0 – évszakok: nyár vs. tél ugyanabban a szobában
node teszt-homerseklet-modul.js   # 38/0 – a korábbi modul (visszafelé is jó)
```

A tesztek valódi adatsorral dolgoznak: 3 nap × 3 mérés (18 / 26 / 21 °C), illetve egy
éves minta (nyár 24–31 °C, tél 16–19 °C). Az elvárt értékek konkrétak – nem azt nézik,
hogy „van valami a képernyőn”, hanem hogy a **21,7 °C** és a **10 °C-os évszak-különbség**
tényleg kijön.
