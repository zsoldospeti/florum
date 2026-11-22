#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.22.3  ·  otthoni növénygondozó
#  Fájl:    permetviz.py
#  Szerep:  a permetezéshez ajánlott víz (növényenként)
#  Licenc:  szabadon használható, módosítható és terjeszthető
# ==============================================================

"""
Permetezés – milyen vízzel?

A növény adatlapján megadható, milyen vizet kér a permetezéshez. Ezt a
modult használja a felület (JavaScript-tükre a florum.html-ben van), a
naptár-író (naptar_ics.py), a háttér-démon (emlekezteto.py) és a panel.

Értékek (a növény `mistWater` mezője):
    ""    – nincs megadva (a Florum nem tesz javaslatot, csak emlékeztet)
    "csap"– csapvíz (állott, szobahőmérsékletű)
    "eso" – esővíz
    "ion" – ioncserélt vagy desztillált víz
    "nem" – nem szereti a permetezést → egyáltalán nincs permetezés-teendő

Miért nem mindegy?
  * a meszes csapvíz fehér vízkövet hagy a leveleken (fényes levelűeknél
    feltűnő), és eltömítheti a permetező fúvókáját;
  * a pihés, gyapjas levelű növények (afrikai ibolya, begónia, muskátli)
    nem bírják a nedves levelet: foltosodnak, rothadnak → "nem";
  * a vízlágyítóval lágyított (sós) víz NEM ugyanaz, mint az ioncserélt –
    permetezésre nem ajánlott.

Parancssor:
    python3 permetviz.py --lista
    python3 permetviz.py --noveny "Clivia"
"""

import json
import os
import sys

# ---------------------------------------------------------------- adatok
VIZEK = {
    "": {
        "nev": "nincs megadva",
        "mod": "",                      # „… vízzel” alak
        "rovid": "",                    # panel/teendő-sor
        "ikon": "",
        "tipp": "Válaszd ki, milyen vizet kér – az emlékeztetőbe bekerül.",
    },
    "csap": {
        "nev": "csapvíz",
        "mod": "állott, szobahőmérsékletű csapvízzel",
        "rovid": "csapvíz",
        "ikon": "🚰",
        "tipp": "Hagyd állni egy éjszakát, hogy a klór elmenjen. Hosszú távon "
                "vízköves foltot hagy a leveleken.",
    },
    "eso": {
        "nev": "esővíz",
        "mod": "esővízzel",
        "rovid": "esővíz",
        "ikon": "🌧",
        "tipp": "A legjobb: lágy, enyhén savas, ingyen van. Fedett vödörben gyűjtsd.",
    },
    "ion": {
        "nev": "ioncserélt víz",
        "mod": "ioncserélt vagy desztillált vízzel",
        "rovid": "ioncserélt",
        "ikon": "💧",
        "tipp": "Nincs benne mész, nem hagy foltot. Műanyag flakonban tárold – "
                "a fémből old. Vízlágyítóval „lágyított” víz NEM ez: az sós.",
    },
    "nem": {
        "nev": "nem szereti a permetezést",
        "mod": "",
        "rovid": "",
        "ikon": "🚫",
        "tipp": "Pihés, gyapjas vagy tövétől leveles növény: a nedves levél "
                "foltosodik, rothad. Inkább párásító tálca, nem permetezés.",
    },
}

# A sorrend a felület legördülő listájában is ez (a "" az első, „nincs megadva”)
SORREND = ["", "csap", "eso", "ion", "nem"]

# Rövidítés, ha a naptárban/értesítésben nem fér ki a teljes szöveg
REGGEL = "reggel"


# ---------------------------------------------------------------- segédek
def ertek(plant):
    """A növény beállítása, ellenőrizve (ismeretlen érték → „nincs megadva”)."""
    if not isinstance(plant, dict):
        return ""
    v = str(plant.get("mistWater") or "").strip().lower()
    return v if v in VIZEK else ""


def szereti(plant):
    """False, ha a növény nem szereti a permetezést (akkor nincs teendő sem)."""
    return ertek(plant) != "nem"


def nev(plant):
    """A víz neve (pl. „esővíz”), vagy üres, ha nincs megadva / nem szereti."""
    return VIZEK[ertek(plant)]["nev"] if szereti(plant) and ertek(plant) else ""


def rovid(plant):
    """Rövid jelzés a teendő-sorban: „esővíz, reggel” (vagy üres)."""
    v = ertek(plant)
    if not v or v == "nem":
        return ""
    return VIZEK[v]["rovid"] + ", " + REGGEL


def hint(plant):
    """A teendő/panel sorába illeszthető toldalék: „esővízzel, reggel”."""
    v = ertek(plant)
    if not v or v == "nem":
        return ""
    return VIZEK[v]["mod"] + ", " + REGGEL


def mondat(plant):
    """Teljes mondat az értesítésbe / .ics-leírásba."""
    v = ertek(plant)
    if not v or v == "nem":
        return ""
    return "Permetezés %s, %s." % (VIZEK[v]["mod"], REGGEL)


def tipp(plant):
    """Segítő szöveg a beállításhoz (a felülethez)."""
    return VIZEK[ertek(plant)]["tipp"]


def ellenorzes():
    """Önellenőrzés (a tesztekhez): a tábla hiánytalan és konzisztens."""
    hibak = []
    for kulcs in SORREND:
        if kulcs not in VIZEK:
            hibak.append("hiányzó kulcs: %r" % kulcs)
    for kulcs, adat in VIZEK.items():
        for mezo in ("nev", "mod", "rovid", "ikon", "tipp"):
            if mezo not in adat:
                hibak.append("%r: hiányzó mező %r" % (kulcs, mezo))
    # a "nem" és a "" nem adhat toldalékot, a többi viszont igen
    for kulcs in SORREND:
        proba = {"mistWater": kulcs}
        van = bool(hint(proba))
        if kulcs in ("", "nem") and van:
            hibak.append("%r: nem adhat toldalékot" % kulcs)
        if kulcs not in ("", "nem") and not van:
            hibak.append("%r: kell toldalék" % kulcs)
    return hibak


# ---------------------------------------------------------------- CLI
def _allapot_olvas(ut):
    with open(ut, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--lista" in argv:
        print("Permetezés – választható víz:")
        for kulcs in SORREND:
            a = VIZEK[kulcs]
            print("  %-6s %-28s %s" % (kulcs or "(üres)", a["nev"], a["tipp"]))
        return 0
    if "--noveny" in argv:
        i = argv.index("--noveny")
        nev_keres = argv[i + 1] if i + 1 < len(argv) else ""
        ut = os.path.join(os.path.expanduser("~"), ".local", "share", "florum", "florum-data.json")
        for arg in argv:
            if arg.startswith("--data-dir="):
                ut = os.path.join(arg.split("=", 1)[1], "florum-data.json")
        if not os.path.exists(ut):
            print("Nincs adatfájl: %s" % ut)
            return 1
        allapot = _allapot_olvas(ut)
        talalt = 0
        for plant in allapot.get("plants") or []:
            cim = str(plant.get("alias") or plant.get("name") or "")
            if nev_keres.lower() not in cim.lower() and \
                    nev_keres.lower() not in str(plant.get("name") or "").lower():
                continue
            talalt += 1
            print("%s – %s" % (cim, plant.get("name") or ""))
            print("   beállítás: %s" % (VIZEK[ertek(plant)]["nev"]))
            print("   teendő:    %s" % (mondat(plant) or "nincs permetezés-emlékeztető"))
        if not talalt:
            print("Nincs ilyen növény: %s" % nev_keres)
            return 1
        return 0
    hibak = ellenorzes()
    if hibak:
        print("HIBA:")
        for h in hibak:
            print("  - " + h)
        return 1
    print("Rendben (%d víztípus)." % len(VIZEK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
