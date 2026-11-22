#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.33.2  ·  új növény adatlapjának kiolvasása
#  Fájl:    novenykereso.py
#
#  MIÉRT VAN EZ?
#    Eddig egy új növénynél mindent kézzel kellett beírni. Mostantól
#    elég egy LINK a gondozási útmutatóhoz – vagy ha az oldal
#    robotvédelmet használ, a cikk SZÖVEGÉNEK beillesztése –, és a
#    program kitölti: öntözés, tápoldat, permetezés, átültetés, fény,
#    hőmérséklet, páratartalom, talaj, mérgezőség, betegségek,
#    kártevők, latin név, tippek.
#
#  ELV:  nem talál ki adatot. Amit nem tud kiolvasni, azt üresen
#        hagyja, és megmondja, mit érdemes kézzel ellenőrizni.
#        Minden mezőnél jelzi: „biztos” (szám szerepelt a szövegben)
#        vagy „becsült” (kulcsszóból következtetett).
#
#  Használat (parancssorban):
#     python3 novenykereso.py --url https://…/elefantlab-gondozasa/
#     python3 novenykereso.py --fajl cikk.txt --nev "Elefántláb"
#     python3 novenykereso.py --szoveg "…" --json
# ==============================================================

import argparse
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

APP_VERSION = "1.33.2"
UA = ("Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0 "
      "Florum/" + APP_VERSION)

# ---------------------------------------------------------------- szótár
# egységek ÉKEZET NÉLKÜL (az ido_nap() előbb lecsupaszítja az ékezeteket)
EGYSEG_NAP = {"nap": 1, "het": 7, "honap": 30, "ev": 365}
SZAVAS_GYAKORISAG = [
    (r"\bkethetente\b|\bket\s+hetente\b|\b2\s+hetente\b", 14),
    (r"\bharomhetente\b|\bharom\s+hetente\b|\b3\s+hetente\b", 21),
    (r"\bnegyedevente\b", 90),
    (r"\bfelevente\b", 180),
    (r"\bminden\s+nap\b|\bnaponkent\b|\bnaponta\b", 1),
    (r"\bhetente\b|\bheti\b", 7),
    (r"\bhavonta\b|\bhavi\b", 30),
    (r"\bevente\b|\bminden\s+evben\b|\bevi\b", 365),
]

FENY_MINTak = [
    (r"\bárnyék|\bsötét\b|\bfénytelen\b|\bészak[i]?\b", "Árnyékos"),
    (r"\bnapos\b|\bdéli\b|\btűző\s+nap|\bnapfény\b|\bnapot\b|\bnap\b", "Napos / déli ablak"),
    (r"\bszórt\b|\bv[ií]lágos,\s*szórt", "Világos, szórt"),
    (r"\bfélárnyék|\bközepes\s+fény", "Közepes"),
    (r"\bv[ií]lágos\b", "Világos, szórt"),
]

KARTEVOK = ["pajzstetű", "takácsatka", "levéltetű", "lisztes tetű", "tripsz",
            "meztelen csiga", "gyapjas tetű", "üvegházi molytetű", "molytetű",
            "csigák", "atkák"]
BETEGSEGEK = ["bakteriális levélfoltosság", "levélfoltosság", "szárrothadás",
              "gyökérrothadás", "lisztharmat", "penész", "barna levélcsúcs",
              "sárguló levél", "levélhullás", "gyökérpenész"]

TALAJ_SZAVAK = ["kaktuszföld", "virágföld", "tőzeg", "perlit", "homok", "kavics",
                "kéreg", "kókusz", "levelelföld", "univerzális", "ásványi"]
NEGACIO = (r"nem\s+kell|nem\s+szükséges|nem\s+igényel|elhagyhat|el\s+lehet\s+hagyni|"
           r"nem\s+foglalkoz|nincs\s+rá\s+szükség|hagyjuk\s+el|nem\s+ajánlott|"
           r"ne\s+permetez|nem\s+permetez|kerüld\s+a\s+permetez|nem\s+bírja\s+a\s+permetez")
MERGEZO_KISALLAT = r"(macsk|kuty|kisállat|gyerek|rágcsáló)"

MAGANHANGZOK = "aáeéiíoóöőuúüű"


def nfc(szoveg):
    """Ékezet-normalizálás: a másolt szöveg és a minták mindig összeilljenek.

    Ugyanaz a magyar szó kétféleképp is kódolható (NFC: „á” = 1 karakter,
    NFD: „a” + ékezetjel). Ha a minta és a szöveg eltér, a keresés csendben
    nem talál – ezért mindent erre az alakra hozunk.
    """
    return unicodedata.normalize("NFC", str(szoveg or ""))


class RobotVedelem(Exception):
    """Az oldal robotvédelmet használ (a tartalom csak böngészőben jelenik meg)."""


# ---------------------------------------------------------------- segédek
def ekezet_nelkul(szoveg):
    tabla = str.maketrans("áÁéÉíÍóÓöÖőŐúÚüÜűŰ", "aAeEiIoOoOoOuUuUuU")
    return str(szoveg or "").translate(tabla).lower()


def slug(nev):
    s = ekezet_nelkul(nev)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "uj-noveny"


def _url_nelkul(szoveg):
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", szoveg)          # kép
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)           # link → címke
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s


def mondatok(szoveg):
    """SZÖVEG → mondatok listája (a markdown-fejléceket is kezeli)."""
    s = _url_nelkul(szoveg or "")
    s = re.sub(r"(?m)^\s*#+\s*", "\n", s)
    s = re.sub(r"\s*\n\s*", " ", s)
    darabok = re.split(r"(?<=[.!?])\s+|\n+", s)
    return [d.strip() for d in darabok if len(d.strip()) > 3]


def ido_nap(szoveg):
    """„kéthetente”, „10 naponta”, „2-3 évente” → napokban (vagy None).

    Előbb az ékezetes, majd az ékezet nélküli alakon próbálja – így a
    „hónaponta/ havonta”, „évente/ evente” alakok is működnek.
    """
    for valtozat in (str(szoveg or "").lower(), ekezet_nelkul(szoveg)):
        # 2-3 évente / 1–2 hetente
        m = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*(nap|h[eé]t|h[oó]nap|honap|é?v|ev)\b", valtozat)
        if m:
            egyseg = ekezet_nelkul(m.group(3))
            atlag = (int(m.group(1)) + int(m.group(2))) / 2.0
            return int(round(atlag * EGYSEG_NAP[egyseg]))
        m = re.search(r"(\d+)\s*(nap|h[eé]t|h[oó]nap|honap|é?v|ev)"
                      r"(?:onta|ente|onta|ja|ig|ban|ben|onta)?\b", valtozat)
        if m:
            egyseg = ekezet_nelkul(m.group(2))
            return int(m.group(1)) * EGYSEG_NAP[egyseg]
        for minta, nap in SZAVAS_GYAKORISAG:
            if re.search(minta, valtozat):
                return nap
    return None


def ido_napok(szoveg):
    """A szövegben előforduló összes időköz napokban, balról jobbra."""
    darabok = re.split(r"[,;]|\bvagy\b|\bés\b", str(szoveg or ""))
    ki = []
    for d in darabok:
        n = ido_nap(d)
        if n:
            ki.append(n)
    return ki


def _van(szoveg, minta):
    return re.search(nfc(minta), nfc(szoveg), re.I) is not None


def _rovid(szoveg, max_hossz=180):
    s = re.sub(r"\s+", " ", szoveg).strip()
    if len(s) <= max_hossz:
        return s
    vag = s[:max_hossz]
    if " " in vag:
        vag = vag[:vag.rfind(" ")]
    return vag.rstrip(",;:") + "…"


# ---------------------------------------------------------------- letöltés
def letolt(url, timeout=20):
    """A cikk szövege a linkről. Robotvédelem esetén RobotVedelem kivétel."""
    if not re.match(r"^https?://\S+$", url or ""):
        raise ValueError("ez nem http(s) link: %s" % url)
    ker = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.5",
        "Accept-Encoding": "identity",
    })
    try:
        with urllib.request.urlopen(ker, timeout=timeout) as r:
            nyers = r.read()
            ctype = r.headers.get("Content-Type", "")
            cim = r.geturl()
    except urllib.error.HTTPError as exc:
        raise RuntimeError("a kiszolgáló %s hibát adott (%s)" % (exc.code, url))
    except (urllib.error.URLError, OSError) as exc:
        raise RuntimeError("nem sikerült elérni: %s (%s)" % (url, exc))
    if "charset=" in ctype.lower():
        kodek = ctype.lower().split("charset=")[1].split(";")[0].strip() or "utf-8"
    else:
        kodek = "utf-8"
    try:
        html = nyers.decode(kodek, "replace")
    except LookupError:
        html = nyers.decode("utf-8", "replace")
    szoveg = htmlbol_szoveg(html)
    if _van(szoveg, r"one moment, please|request is being verified|"
                   r"checking your browser|enable javascript|"
                   r"ellenőrizzük|kérjük, várjon"):
        raise RobotVedelem(
            "Az oldal robotvédelmet használ (a tartalom csak böngészőben jelenik meg). "
            "Nyisd meg a linket, jelöld ki a cikket (Ctrl+A, Ctrl+C), és illeszd be ide.")
    return szoveg, cim


def htmlbol_szoveg(html):
    """HTML → olvasható szöveg (script/style nélkül, fejlécek megtartásával)."""
    s = re.sub(r"(?is)<(script|style|noscript|svg|iframe)[^>]*>.*?</\1>", " ", html)
    s = re.sub(r"(?is)<h[1-3][^>]*>", "\n## ", s)
    s = re.sub(r"(?is)<(br|/p|/div|/li|/h[1-6])[^>]*>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    import html as _h
    s = _h.unescape(s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def cimbol_nev(cim):
    """„Elefántláb gondozása - Részletes útmutató” → „Elefántláb”."""
    s = re.sub(r"\s*[|\-–—]\s*.*$", "", cim or "").strip()
    s = re.sub(r"(?i)\s+(gondozása|gondozás|ápolása|ütmutató|bemutatása|jellemzése).*$", "", s)
    s = re.sub(r"(?i)^(Így|Hogyan)\s+", "", s)
    return s.strip(" .:—-")


# ---------------------------------------------------------------- kiolvasás
def szovegbol(szoveg, nev="", forras=""):
    """A cikk szövegéből adatlap-mezők. Visszaad: dict (DB-kompatibilis + meta)."""
    szoveg = nfc(szoveg)
    mond = mondatok(szoveg)
    teljes = " ".join(mond)
    kis = teljes.lower()
    csupasz = ekezet_nelkul(teljes)          # ékezet nélküli alak a kereséshez
    bizalom = {}
    eredmeny = {
        "id": "", "name": "", "latin": "", "aliases": [],
        "difficulty": "", "light": "",
        "water": 0, "waterWinter": 0, "fert": 0, "fertWinter": 0,
        "mist": 0, "mistWater": "",
        "repot": 0, "humidity": "", "temp": "", "soil": "", "toxic": "",
        "diseases": [], "pests": [], "tips": [],
        "forras": forras, "bizalom": {}, "bizonytalan": [], "megjegyzes": "",
    }

    # ---- név
    if not nev:
        elso = mond[0] if mond else ""
        nev = cimbol_nev(elso)
    if not nev:
        nev = "Új növény"
    eredmeny["name"] = nev
    eredmeny["id"] = slug(nev)

    # ---- latin név: (Nolina recurvata; Beaucarnea recurvata)
    parok = re.findall(r"\(([^()]{4,90})\)", teljes)
    latinok = []
    for p in parok:
        for darab in re.split(r"[;,]|\s+syn\.?\s+|\s+azaz\s+", p):
            darab = darab.strip(" .")
            m = re.fullmatch(r"([A-Z][a-zéáíóöőúüű\-]{2,})\s+([a-zéáíóöőúüű\-]{3,}(?:\s+[a-z\-]{2,})?)",
                             darab)
            if m:
                latinok.append(darab)
    if not latinok:
        m = re.search(r"\b([A-Z][a-z]{3,}\s+[a-z]{3,})\b", teljes)
        if m and not _van(m.group(1), r"^(Nem|Ez|Az|Ha|A)\b"):
            latinok = [m.group(1)]
    if latinok:
        eredmeny["latin"] = latinok[-1]          # az utolsó a rendszerint elfogadott név
        eredmeny["aliases"] = [x for x in latinok[:-1] if x != latinok[-1]]
        bizalom["latin"] = "biztos"

    # ---- fény: csak olyan mondatból, amelyik tényleg a fényigényről szól
    feny_mondatok = [m for m in mond if _van(m, r"fény|napfény|napos|világos|árnyék|félárnyék")]
    jelolt = [m for m in feny_mondatok
              if _van(m, r"igény|szeret|kell|hely|kedvel|bír|kap|tart|ideális")]
    for m in (jelolt or []):
        for minta, ertek in FENY_MINTak:
            if _van(m, minta):
                eredmeny["light"] = ertek
                bizalom["light"] = "becsült"
                break
        if eredmeny["light"]:
            break
    if _van(teljes, r"napos\s+vagy\s+világos|világos,\s*kellemesen\s+meleg|"
                     r"sok\s+napfény|napi\s+pár\s+óra\s+nap"):
        eredmeny["light"] = "Napos / déli ablak"
        bizalom["light"] = "biztos"

    # ---- öntözés (nyári és téli)
    viz_mondatok = [m for m in mond if _van(m, r"öntöz|locsol|vízigény|vizet\s+ad|"
                                                 r"öntözz|nedvesség")]
    if viz_mondatok:
        nyari = [m for m in viz_mondatok if not _van(m, r"\btél|október|november|december|január")]
        for m in nyari:
            nap = ido_nap(m)
            if nap:
                eredmeny["water"] = nap
                bizalom["water"] = "biztos"
                break
        if not eredmeny["water"]:
            # nincs szám, de van ráutalás
            if _van(teljes, r"mérsékelten\s+öntöz|keveset\s+öntöz|ritkán\s+öntöz|alacsony\s+vízigény"):
                eredmeny["water"] = 14
                bizalom["water"] = "becsült"
            elif _van(teljes, r"rendszeresen\s+öntöz|gyakran\s+öntöz"):
                eredmeny["water"] = 7
                bizalom["water"] = "becsült"
        # téli
        teli = [m for m in mond if _van(m, r"\btél|október|november|december|január")
                and _van(m, r"öntöz|locsol|vízigény|nedvesség|száraz|földj|földje")]
        for m in teli:
            nap = ido_nap(m)
            if nap:
                eredmeny["waterWinter"] = nap
                bizalom["waterWinter"] = "biztos"
                break
        if not eredmeny["waterWinter"] and teli:
            if _van(" ".join(teli), r"száraz|alig|nagyon\s+kevés|szinte\s+semmi"):
                if eredmeny["water"]:
                    eredmeny["waterWinter"] = max(30, int(round(eredmeny["water"] * 2.5)))
                    bizalom["waterWinter"] = "becsült"
            else:
                eredmeny["waterWinter"] = eredmeny["water"]
                bizalom["waterWinter"] = "becsült"

    # ---- tápoldat
    tap_mondatok = [m for m in mond if _van(m, r"tápoldat|tápoz|tápoldatoz|műtrágya")]
    if tap_mondatok:
        for m in tap_mondatok:
            if _van(m, r"\btél|október"):
                continue
            nap = ido_nap(m)
            if nap:
                eredmeny["fert"] = nap
                bizalom["fert"] = "biztos"
                break
        if not eredmeny["fert"] and _van(teljes, r"tápoldatoz|tápoz"):
            eredmeny["fert"] = 30
            bizalom["fert"] = "becsült"
        if _van(" ".join(tap_mondatok), r"\btél[^\n]{0,80}(" + NEGACIO + r")|(" +
                                       NEGACIO + r")[^\n]{0,40}tápoldat"):
            eredmeny["fertWinter"] = 0
            bizalom["fertWinter"] = "biztos"
            # a tápoldatozás ablaka: tavasztól őszig (a felület ezt használja)
            eredmeny.setdefault("fertFrom", 3)
            eredmeny.setdefault("fertTo", 9)
            bizalom["fertFrom"] = bizalom["fertTo"] = "biztos"
        elif eredmeny["fert"]:
            eredmeny["fertWinter"] = eredmeny["fert"]
            bizalom["fertWinter"] = "becsült"

    # ---- permetezés / párásítás
    par_mondatok = [m for m in mond if _van(m, r"permetez|párásít|párologtat")]
    if par_mondatok:
        szoveg_par = " ".join(par_mondatok)
        if _van(szoveg_par, NEGACIO + r"|nem\s+bírja|kerüld"):
            eredmeny["mist"] = 0
            eredmeny["mistWater"] = "nem"
            bizalom["mist"] = "biztos"
        else:
            nap = None
            for m in par_mondatok:
                nap = ido_nap(m)
                if nap:
                    break
            eredmeny["mist"] = nap or 7
            bizalom["mist"] = "biztos" if nap else "becsült"
            if _van(teljes, r"esővíz|esővízzel"):
                eredmeny["mistWater"] = "eso"
            elif _van(teljes, r"szűrt|langyos|ioncserélt|desztillált"):
                eredmeny["mistWater"] = "ion"
    elif _van(teljes, r"páratartalm|párásít|párás"):
        # csak annyi derül ki, hogy nem kell vele bajlódni
        if _van(teljes, r"alacsonyabb\s+páratartalm|nem\s+kell\s+foglalkoz"):
            eredmeny["mist"] = 0
            eredmeny["mistWater"] = "nem"
            bizalom["mist"] = "becsült"

    # ---- átültetés (hónapokban)
    at_mondatok = [m for m in mond if _van(m, r"átültet|ültessük\s+át|átültessük|"
                                               r"cserépbe|növénytartó")]
    if at_mondatok:
        jeloltek = []
        for m in at_mondatok:
            jeloltek.extend(ido_napok(m))
        jeloltek = sorted(set(n for n in jeloltek if 180 <= n <= 365 * 6))   # 6 hónap … 6 év
        if jeloltek:
            # ha a cikk két ütemet ad („évente, ha nagyobb legyen / 2-3 évente”),
            # a kettő közepét vesszük – így nem leszünk sem túl sűrűek, sem túl ritkák
            kozep = (jeloltek[0] + jeloltek[-1]) / 2.0 if len(jeloltek) > 1 else jeloltek[0]
            ho = int(round(kozep / 30.0))
            eredmeny["repot"] = max(6, min(48, ho))
            bizalom["repot"] = "biztos" if len(jeloltek) == 1 else "becsült"
        if not eredmeny["repot"]:
            eredmeny["repot"] = 24
            bizalom["repot"] = "becsült"

    # ---- hőmérséklet
    hom = re.findall(r"(-?\d{1,2})\s*(?:–|-|tól|és)\s*(-?\d{1,2})\s*°\s*C", teljes)
    legalabb = re.findall(r"legalább\s+(\d{1,2})\s*°\s*C", teljes)
    if hom:
        eredmeny["temp"] = "%s–%s °C" % (hom[0][0], hom[0][1])
        bizalom["temp"] = "biztos"
    if legalabb and not hom:
        eredmeny["temp"] = "%s °C felett (télen hűvös, világos hely)" % legalabb[0]
        bizalom["temp"] = "biztos"
    elif legalabb and hom:
        eredmeny["temp"] = "%s–%s °C (télen legalább %s °C)" % (hom[0][0], hom[0][1], legalabb[0])

    # ---- páratartalom (függetlenül attól, hogy van-e permetezés)
    par = re.search(r"(\d{2,3})\s*[–-]\s*(\d{2,3})\s*%", teljes)
    if par:
        eredmeny["humidity"] = "%s–%s%%" % (par.group(1), par.group(2))
        bizalom["humidity"] = "biztos"
    elif _van(teljes, r"alacsonyabb\s+páratartalm|száraz\s+levegőt?\s+is\s+bír|"
                      r"nem\s+igényel\s+párásít|jól\s+bírja\s+a\s+száraz"):
        eredmeny["humidity"] = "30–50%"
        bizalom["humidity"] = "becsült"

    # ---- talaj
    talaj_szavak = []
    for m in mond:
        if not _van(m, r"föld|talaj|ülés\s+közeg|szubsztrát"):
            continue
        for sz in TALAJ_SZAVAK:
            if _van(m, sz) and sz not in talaj_szavak:
                talaj_szavak.append(sz)
    if talaj_szavak:
        eredmeny["soil"] = " + ".join(talaj_szavak[:4])
        bizalom["soil"] = "biztos"

    # ---- mérgezőség
    if _van(teljes, r"nem\s+mérgező|nem\s+ismert\s+mérgező|kisállatbarát|nem\s+toxikus"):
        eredmeny["toxic"] = "Nem mérgező"
        bizalom["toxic"] = "biztos"
    elif _van(teljes, r"mérgező|toxikus"):
        m = re.search(r"[^.]{0,80}mérgező[^.]{0,80}", teljes, re.I)
        eredmeny["toxic"] = _rovid(m.group(0), 110) if m else "Mérgező – a cikk szerint"
        bizalom["toxic"] = "becsült"

    # ---- betegségek / kártevők
    # ékezet nélkül keresünk, hogy a „takácsatkák / pajzstetvek” többes szám is meglegyen
    for beteg in BETEGSEGEK:
        if ekezet_nelkul(beteg) in csupasz:
            eredmeny["diseases"].append(beteg[0].upper() + beteg[1:])
    # ha van pontosabb (hosszabb) változat, a rövid általánost ne írjuk ki
    betegek = [b for b in eredmeny["diseases"]]
    eredmeny["diseases"] = [b for b in betegek
                            if not any(b != o and b.lower() in o.lower() for o in betegek)]
    for kart in KARTEVOK:
        csup = ekezet_nelkul(kart)
        torzs = csup.rstrip("aeiou")            # takácsatka → takacsatk, pajzstetű → pajzstet
        if len(torzs) >= 4 and re.search(r"\b" + re.escape(torzs) + r"\w*", csupasz):
            nev_kart = kart[0].upper() + kart[1:]
            if nev_kart not in eredmeny["pests"]:
                eredmeny["pests"].append(nev_kart)
    # az általánosabb kártevő ne maradjon benne, ha a hosszabb már megvan
    kartevok = list(eredmeny["pests"])
    eredmeny["pests"] = [k for k in kartevok
                         if not any(k != o and ekezet_nelkul(k).rstrip("aeiou")
                                    in ekezet_nelkul(o) for o in kartevok)]

    # ---- nehézség
    if _van(teljes, r"ellenálló|egyszerűen\s+kezelhető|kezdőknek|nem\s+igényes|igénytelen"):
        eredmeny["difficulty"] = "Könnyű"
        bizalom["difficulty"] = "becsült"
    elif _van(teljes, r"nagyon\s+érzékeny|nehéz|igényes|kényes"):
        eredmeny["difficulty"] = "Nehéz"
        bizalom["difficulty"] = "becsült"
    elif _van(teljes, r"közepesen\s+igényes|közepes"):
        eredmeny["difficulty"] = "Közepes"
        bizalom["difficulty"] = "becsült"

    # ---- tippek
    tipp_mondatok = []
    for m in mond:
        if len(tipp_mondatok) >= 5:
            break
        if _van(m, r"cikkünk|további\s+részében|bízunk\s+benne|olvasható|"
                   r"kép\s+forrása|megosztás"):
            continue
        if _van(m, r"figyelj|öntözzük|tartsuk|érdemes|szereti|jól\s+bírja|"
                   r"ne\s+válassz|kerüld|javasolt|meghálálja"):
            if 20 < len(m) < 260:
                tipp_mondatok.append(_rovid(m, 200))
    eredmeny["tips"] = tipp_mondatok

    # ---- mi az, amit érdemes kézzel ellenőrizni
    for mezo, cimke in (("water", "öntözés (nap)"), ("waterWinter", "téli öntözés"),
                        ("fert", "tápoldat (nap)"), ("mist", "permetezés"),
                        ("repot", "átültetés (hónap)"), ("light", "fény"),
                        ("temp", "hőmérséklet"), ("soil", "talaj"),
                        ("toxic", "mérgezőség"), ("humidity", "páratartalom")):
        if mezo not in bizalom and not eredmeny[mezo]:
            eredmeny["bizonytalan"].append(cimke)
    if not eredmeny["pests"]:
        eredmeny["bizonytalan"].append("kártevők")
    if not eredmeny["diseases"]:
        eredmeny["bizonytalan"].append("betegségek")

    eredmeny["bizalom"] = bizalom
    talalt = len(bizalom)
    eredmeny["megjegyzes"] = ("%d mező kiolvasva a szövegből (%d biztos, %d becsült)."
                              % (talalt,
                                 len([v for v in bizalom.values() if v == "biztos"]),
                                 len([v for v in bizalom.values() if v == "becsült"])))
    return eredmeny


def urlbol(url, nev=""):
    """Link → adatlap. Visszaad: (dict, hibauzenet) – hiba esetén (None, szöveg)."""
    try:
        szoveg, vegso_url = letolt(url)
    except RobotVedelem as exc:
        return None, str(exc)
    except (RuntimeError, ValueError) as exc:
        return None, str(exc)
    if len(mondatok(szoveg)) < 4:
        return None, ("az oldalon nem találtam elég szöveget (lehet, hogy kép vagy "
                      "JavaScript mögött van a tartalom) – illeszd be a cikk szövegét")
    adat = szovegbol(szoveg, nev=nev, forras=vegso_url)
    return adat, ""


# ---------------------------------------------------------------- önteszt
ONTESZT_ESETEK = [
    # (szöveg, mező, elvárt)
    ("Ezért tavasztól őszig mérsékelten öntözzük, télen tartsuk szinte teljesen szárazon.",
     "water", 14),
    ("Ezért tavasztól őszig mérsékelten öntözzük, télen tartsuk szinte teljesen szárazon.",
     "waterWinter", 35),
    ("Tavasztól őszig meghálálja, ha havonta tápoldatozzuk, télen hagyjuk el a tápoldatozást.",
     "fert", 30),
    ("Tavasztól őszig meghálálja, ha havonta tápoldatozzuk, télen hagyjuk el a tápoldatozást.",
     "fertWinter", 0),
    ("Jól bírja az alacsonyabb páratartalmat is, ezért párásítással nem kell foglalkoznunk.",
     "mist", 0),
    ("Jól bírja az alacsonyabb páratartalmat is, ezért párásítással nem kell foglalkoznunk.",
     "humidity", "30–50%"),
    ("Ha nagyobb legyen, ültessük át minden évben, ha kisebb, elég 2-3 évente átültetni.",
     "repot", 24),
    ("Az elefántláb a napos vagy világos, kellemesen meleg helyiségek ideális szobanövénye.",
     "light", "Napos / déli ablak"),
    ("A leveleit hetente permetezd langyos vízzel.", "mist", 7),
    ("A virágzás titka: 10–12 °C, szinte semmi víz, nulla tápoldat.", "temp", "10–12 °C"),
    ("Télen világos, hűvös, de legalább 10 °C hőmérsékletű szobában tartsuk.",
     "temp", "10 °C felett (télen hűvös, világos hely)"),
]


def ontellenorzes():
    """Az ismert minták próbája – elkapja, ha egy szabály elromlik.

    Visszaad: (sikeres, hibás, hibalista)
    """
    ok = hiba = 0
    hibalista = []
    for szoveg, mezo, elvart in ONTESZT_ESETEK:
        kapott = szovegbol(szoveg, nev="Teszt növény")[mezo]
        if kapott == elvart:
            ok += 1
        else:
            hiba += 1
            hibalista.append("%s: %r (elvárt: %r) ← %s" % (mezo, kapott, elvart, szoveg[:40]))
    return ok, hiba, hibalista


# ---------------------------------------------------------------- parancssor
def kiir(adat):
    print("\n  🌿 %s  (%s)" % (adat["name"], adat["latin"] or "latin név nélkül"))
    print("  " + "-" * 56)
    sorok = [
        ("Fény", adat["light"] or "—"),
        ("Öntözés", "%s naponta" % adat["water"] if adat["water"] else "—"),
        ("Téli öntözés", "%s naponta" % adat["waterWinter"] if adat["waterWinter"] else "—"),
        ("Tápoldat", "%s naponta" % adat["fert"] if adat["fert"] else "—"),
        ("Téli tápoldat", "nincs" if adat["fert"] == 0 or adat["fertWinter"] == 0 else
         ("%s naponta" % adat["fertWinter"] if adat["fertWinter"] else "—")),
        ("Permetezés", ("%s naponta" % adat["mist"]) if adat["mist"] else
         ("nem szereti" if adat["mistWater"] == "nem" else "—")),
        ("Átültetés", "%s havonta" % adat["repot"] if adat["repot"] else "—"),
        ("Hőmérséklet", adat["temp"] or "—"),
        ("Páratartalom", adat["humidity"] or "—"),
        ("Talaj", adat["soil"] or "—"),
        ("Mérgezőség", adat["toxic"] or "—"),
        ("Nehézség", adat["difficulty"] or "—"),
        ("Betegségek", ", ".join(adat["diseases"]) or "—"),
        ("Kártevők", ", ".join(adat["pests"]) or "—"),
        ("Aliasok", ", ".join(adat["aliases"]) or "—"),
    ]
    for cimke, ertek in sorok:
        biz = adat["bizalom"].get(cimke_kulcs(cimke), "")
        print("  %-15s %s%s" % (cimke + ":", ertek,
                                ("   [%s]" % biz) if biz else ""))
    if adat["tips"]:
        print("  Tippek:")
        for t in adat["tips"]:
            print("    • " + t)
    if adat["bizonytalan"]:
        print("  ⚠ Érdemes kézzel megnézni: " + ", ".join(adat["bizonytalan"]))
    print("  " + adat["megjegyzes"])
    if adat["forras"]:
        print("  Forrás: " + adat["forras"])
    print()


def cimke_kulcs(cimke):
    return {"Fény": "light", "Öntözés": "water", "Téli öntözés": "waterWinter",
            "Tápoldat": "fert", "Téli tápoldat": "fertWinter", "Permetezés": "mist",
            "Átültetés": "repot", "Hőmérséklet": "temp", "Páratartalom": "humidity",
            "Talaj": "soil", "Mérgezőség": "toxic", "Nehézség": "difficulty"}.get(cimke, "")


def main(argv=None):
    p = argparse.ArgumentParser(description="Florum – új növény adatlapjának kiolvasása")
    forrás = p.add_mutually_exclusive_group(required=False)
    forrás.add_argument("--url", help="a gondozási útmutató linkje")
    forrás.add_argument("--fajl", help="a cikk szövege fájlban")
    forrás.add_argument("--szoveg", help="a cikk szövege parancssorban")
    p.add_argument("--nev", default="", help="a növény neve (ha a szövegből nem derül ki)")
    p.add_argument("--json", action="store_true", help="csak a JSON (a felületnek)")
    p.add_argument("--onteszt", action="store_true",
                   help="a beépített minták próbája (hálózat nélkül)")
    args = p.parse_args(argv)

    if args.onteszt:
        ok, hiba, lista = ontellenorzes()
        print("  Novénykereső – önteszt: %d rendben, %d hiba" % (ok, hiba))
        for h in lista:
            print("   ✗ " + h)
        return 0 if not hiba else 1

    if args.url:
        adat, hiba = urlbol(args.url, args.nev)
        if hiba:
            print("  ✗ " + hiba)
            print("  (a link megnyitásához böngésző kell – utána illeszd be a szöveget)")
            return 1
    else:
        if args.fajl:
            with open(args.fajl, encoding="utf-8") as fh:
                szoveg = fh.read()
        else:
            szoveg = args.szoveg
        adat = szovegbol(szoveg, nev=args.nev,
                         forras=("fájl: " + os.path.basename(args.fajl)) if args.fajl
                         else "beillesztett szöveg")
    if args.json:
        print(json.dumps(adat, ensure_ascii=False, indent=1))
    else:
        kiir(adat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
