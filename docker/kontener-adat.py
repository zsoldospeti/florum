#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM – a régi konténer adatainak felkutatása/átvétele
#  Fájl: docker/kontener-adat.py
#
#  Miért külön fájl: a „docker: name is already in use” hibánál az a
#  legfontosabb kérdés, hogy HOL van az adat. Ezt docker nélkül is meg
#  tudjuk válaszolni, ha a mentett fájl megvan (a szkript ezt hívja).
#
#  Parancsok:
#    python3 docker/kontener-adat.py --vizsgal <mappa>
#        megmondja, mi van a mappában, hány növény/napló/mérés
#    python3 docker/kontener-adat.py --egyesit <régi-mappa> <új-mappa>
#        a két mappából egyesít (az új nyer, de a hiányzó növények/mérések
#        átkerülnek) – akkor kell, ha a régi konténerben volt az adat
# ==============================================================
import argparse
import json
import os
import shutil
import sys


def betolt(mappa):
    ut = os.path.join(mappa, "florum-data.json")
    if not os.path.isfile(ut):
        return None
    try:
        with open(ut, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def osszegzes(d):
    if not d:
        return "nincs florum-data.json"
    return "növény: %d · napló: %d · hőmérséklet-mérés: %d · saját faj: %d" % (
        len(d.get("plants") or []), len(d.get("history") or []),
        len(d.get("tempLog") or []), len(d.get("customDb") or []))


def vizsgal(mappa):
    if not os.path.isdir(mappa):
        print("  ✗ nincs ilyen mappa: %s" % mappa)
        return 1
    d = betolt(mappa)
    print("  mappa: %s" % mappa)
    print("  %s" % osszegzes(d))
    if d is None:
        print("  (a mappában lévő fájlok: %s)" % (", ".join(sorted(os.listdir(mappa))[:8]) or "üres"))
        return 1
    return 0


def egyesit(regi, uj):
    """A régi mappa adatait hozzáolvasztja az újhoz (az új élvez elsőbbséget)."""
    dr, du = betolt(regi), betolt(uj)
    if dr is None:
        print("  ✗ a régi mappában nincs érvényes florum-data.json: %s" % regi)
        return 1
    if du is None:
        print("  · az új mappában még nincs adat → a régi lesz az új")
        du = {"plants": [], "history": [], "settings": {}, "meta": {}, "customDb": [], "tempLog": []}
    elotte = osszegzes(du)

    # növények: azonosító szerint egyesítés
    van = set(str(p.get("id")) for p in (du.get("plants") or []))
    for p in dr.get("plants") or []:
        if str(p.get("id")) not in van:
            du.setdefault("plants", []).append(p)

    # napló: (plantId, type, date) hármas alapján, hogy ne legyen duplikáció
    van = set()
    for e in du.get("history") or []:
        van.add((str(e.get("plantId")), str(e.get("type")), str(e.get("date"))))
    for e in dr.get("history") or []:
        kulcs = (str(e.get("plantId")), str(e.get("type")), str(e.get("date")))
        if kulcs not in van:
            du.setdefault("history", []).append(e)

    # hőmérséklet-mérések: azonosító szerint
    van = set(str(x.get("id")) for x in (du.get("tempLog") or []))
    for x in dr.get("tempLog") or []:
        if str(x.get("id")) not in van:
            du.setdefault("tempLog", []).append(x)

    # saját fajok: név szerint
    van = set(str(x.get("name", "")).lower() for x in (du.get("customDb") or []))
    for x in dr.get("customDb") or []:
        if str(x.get("name", "")).lower() not in van:
            du.setdefault("customDb", []).append(x)

    # biztonsági mentés az újról, aztán írás
    cel = os.path.join(uj, "florum-data.json")
    if os.path.isfile(cel):
        shutil.copy2(cel, cel + ".elotte.json")
    os.makedirs(uj, exist_ok=True)
    with open(cel, "w", encoding="utf-8") as fh:
        json.dump(du, fh, ensure_ascii=False, indent=2)

    # a többi fájl (fotók, mentések) – ami hiányzik, átmásoljuk
    for alkonyvtar in ("photos", "mentes"):
        forras = os.path.join(regi, alkonyvtar)
        if not os.path.isdir(forras):
            continue
        celmappa = os.path.join(uj, alkonyvtar)
        for gyoker, _, fajlok in os.walk(forras):
            rel = os.path.relpath(gyoker, forras)
            celgyoker = os.path.join(celmappa, rel) if rel != "." else celmappa
            os.makedirs(celgyoker, exist_ok=True)
            for f in fajlok:
                c = os.path.join(celgyoker, f)
                if not os.path.exists(c):
                    shutil.copy2(os.path.join(gyoker, f), c)

    print("  előtte: %s" % elotte)
    print("  utána:  %s" % osszegzes(du))
    print("  (a korábbi új fájl megmaradt: florum-data.json.elotte.json)")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Florum – konténer-adatok vizsgálata/egyesítése")
    ap.add_argument("--vizsgal", metavar="MAPPA")
    ap.add_argument("--egyesit", nargs=2, metavar=("RÉGI", "ÚJ"))
    a = ap.parse_args()
    if a.vizsgal:
        return vizsgal(a.vizsgal)
    if a.egyesit:
        return egyesit(a.egyesit[0], a.egyesit[1])
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
