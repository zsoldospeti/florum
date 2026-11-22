#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.22.0  ·  közös mentés-modul (mentes.py)
#  Szerep:  automatikus, előzményes mentés bármely app saját mappájába
#  Licenc:  szabadon használható, módosítható és terjeszthető
# ==============================================================
"""
Közös mentés-modul – „mentés mappa minden módosítás után, 30 nap után töröl".

Amit jobban csinál a naiv megoldásnál:

  1. NEM minden mentés egyformán öregszik. Négy szint van:
        perc-*     minden mentés (legutóbbi 20, azonos tartalmat kihagyja)
        napi-*     a nap ELSŐ mentése   – 30 napig
        havi-*     a hónap ELSŐ mentése – 12 hónapig
        kezi-*     kézi/pin – SOHA nem törlődik
     Így a 30 napos előzmény valóban 30 nap, nem „az utolsó aktív napom".
  2. Törlés csak a saját névmintára illeszkedő fájlokra (soha nem viszi el
     a felhasználó saját .json-jait), és csak a legfrissebb N megtartásával.
  3. Írás atomikus (tmp + fsync + os.replace), és a kész fájlt visszaolvassa
     (json.load) – sérült mentés nem szoríthatja ki a jót.
  4. Az azonos tartalmú mentést kihagyja (sha1), így nem keletkezik 200
     egyforma fájl egy szerkesztésből.
  5. A visszaállítás a legfrissebb ÉP fájlt választja, és a visszaállítás
     előtt maga is ment (nincs „visszaállítok és elvész a mostani állapot").

Használat:

    from mentes import Mentes
    m = Mentes("florum", "~/.local/share/florum/mentes")
    m.inditaskor()                       # régi mentések törlése (gyors)
    m.mentes(adat_dict)                  # minden módosítás után
    m.lista()                            # [(név, méret, idő, szint), …]
    m.visszaallit("napi-20261022-000000") # a legfrissebb ép állapot betöltése
    m.csomag()                           # zip az összes mentésből (bytes)

Parancssorból is használható:

    python3 mentes.py list    --mappa ~/.local/share/florum/mentes --elotag florum
    python3 mentes.py restore --mappa … --elotag florum --nev napi-20261022-…
    python3 mentes.py export  --mappa … --elotag florum --ki florum-mentes.zip
    python3 mentes.py prune   --mappa … --elotag florum
"""

import argparse
import datetime as _dt
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile

# ----------------------------- beállítások -----------------------------

PERC_DB = 20          # ennyi „minden mentés" típusú pillanatkép marad
NAPI_NAP = 30         # napi mentés ennyi napig
HAVI_HONAP = 12       # havi mentés ennyi hónapig
MIN_MEGTART = 10      # ha minden mást törölni kellene, ennyi akkor is marad

SZINTEK = ("perc", "napi", "havi", "kezi")

# csak ilyen fájlneveket törölhet / listázhat (a prefixet hozzáfűzzük)
NEV_MINTA = re.compile(r"^(?P<prefix>[a-z0-9_-]+)-(?P<szint>perc|napi|havi|kezi)-"
                       r"(?P<stamp>\d{8}-\d{6})(?P<suffix>[-a-z0-9]*)\.json$")


def _most() -> _dt.datetime:
    return _dt.datetime.now()


def _stamp(d: _dt.datetime) -> str:
    return d.strftime("%Y%m%d-%H%M%S")


def sha1_of(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


class Mentes:
    """Előzményes, önmagát takarító mentés egy app saját mappájába."""

    def __init__(self, elotag: str, mappa: str, naplo=None):
        self.elotag = re.sub(r"[^a-z0-9_-]+", "-", elotag.lower()).strip("-") or "app"
        self.mappa = os.path.abspath(os.path.expanduser(mappa))
        self.naplo = naplo or (lambda uzenet: None)
        os.makedirs(self.mappa, exist_ok=True)

    # ---------------------------- segédek ----------------------------

    def _ut(self, nev: str) -> str:
        return os.path.join(self.mappa, nev)

    def _uj_nev(self, szint: str, d: _dt.datetime, suffix: str = "") -> str:
        """Szabad fájlnév. Ha ugyanabban a másodpercben már mentettünk, sorszámot kap,
        hogy két gyors mentés ne írja felül egymást."""
        alap = "%s-%s-%s%s" % (self.elotag, szint, _stamp(d), suffix)
        nev = alap + ".json"
        i = 2
        while os.path.exists(self._ut(nev)):
            nev = "%s-%d.json" % (alap, i)
            i += 1
        return nev

    def _parse(self, nev: str):
        m = NEV_MINTA.match(nev)
        if not m or m.group("prefix") != self.elotag:
            return None
        try:
            stamp = _dt.datetime.strptime(m.group("stamp"), "%Y%m%d-%H%M%S")
        except ValueError:
            return None
        return {"nev": nev, "szint": m.group("szint"), "ido": stamp, "ut": self._ut(nev)}

    def _sajat_fajlok(self):
        out = []
        for ut in glob.glob(os.path.join(self.mappa, "%s-*.json" % self.elotag)):
            info = self._parse(os.path.basename(ut))
            if info and os.path.isfile(ut):
                try:
                    info["meret"] = os.path.getsize(ut)
                except OSError:
                    info["meret"] = 0
                out.append(info)
        out.sort(key=lambda x: x["ido"], reverse=True)
        return out

    # ---------------------------- írás ----------------------------

    def mentes(self, adat, szint: str = None, suffix: str = "", kenyszer: bool = False):
        """Pillanatkép készítése.

        Egy hívás több szintet is képezhet (ez a lényeg):
          - mindig:            „perc"  (a legutóbbi PERC_DB marad)
          - a nap első mentése: „napi"  (NAPI_NAP napig)
          - a hónap első mentése: „havi" (HAVI_HONAP hónapig)
        A „kezi" szintet csak kifejezetten kérve készíti, és soha nem törlődik.

        Visszaadja a legjelentősebb létrejött fájl nevét, vagy None-t,
        ha nem volt változás (azonos tartalom).
        """
        d = _most()
        szoveg = json.dumps(adat, ensure_ascii=False, indent=1, sort_keys=True)
        json.loads(szoveg)                       # amit nem lehet visszaolvasni, nem kerül ki
        uj_hash = sha1_of(szoveg)

        meglevo = self._sajat_fajlok()

        # azonos tartalom? (bármely szinten) -> nincs mit menteni
        if not kenyszer:
            for info in meglevo:
                try:
                    with open(info["ut"], encoding="utf-8") as fh:
                        if sha1_of(json.dumps(json.load(fh), ensure_ascii=False,
                                              indent=1, sort_keys=True)) == uj_hash:
                            return None
                except (OSError, ValueError):
                    continue

        # mely szintekre készüljön fájl?
        if szint == "kezi":
            szintek = ["kezi"]
        else:
            szintek = ["perc"]
            if not any(i["szint"] == "napi" and i["ido"].date() == d.date() for i in meglevo):
                szintek.append("napi")
            if not any(i["szint"] == "havi" and (i["ido"].year, i["ido"].month) == (d.year, d.month)
                       for i in meglevo):
                szintek.append("havi")

        letrejott = []
        for sz in szintek:
            nev = self._uj_nev(sz, d, suffix)
            ut = self._ut(nev)
            tmp = ut + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as fh:
                    fh.write(szoveg)
                    fh.flush()
                    os.fsync(fh.fileno())
                with open(tmp, encoding="utf-8") as fh:
                    json.load(fh)                # visszaolvasás: sérült fájl nem maradhat
                os.replace(tmp, ut)
                letrejott.append(nev)
            except (OSError, ValueError) as exc:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                self.naplo("mentés hiba (%s): %s" % (sz, exc))

        if not letrejott:
            return None

        # a legutolsó jó állapot mindig külön, fix néven is elérhető
        try:
            with open(os.path.join(self.mappa, "%s-legutolso.json" % self.elotag), "w", encoding="utf-8") as fh:
                fh.write(szoveg)
        except OSError:
            pass

        self.naplo("mentve: %s" % ", ".join(letrejott))
        self.takaritas()
        for sz in ("napi", "havi", "percek", "kezi"):
            for nev in letrejott:
                if "-%s-" % sz in nev:
                    return nev
        return letrejott[0]

    # ---------------------------- takarítás ----------------------------

    def takaritas(self, most: _dt.datetime = None):
        """A megőrzési szabály érvényesítése. Csak saját nevű fájlokat töröl."""
        most = most or _most()
        fajlok = self._sajat_fajlok()
        torlendo = set()

        # 1) perc-szintű: a legfrissebb PERC_DB marad
        percek = [f for f in fajlok if f["szint"] == "perc"]
        for f in percek[PERC_DB:]:
            torlendo.add(f["nev"])

        # 2) napi: NAPI_NAP napnál régebbiek
        hatar_nap = most - _dt.timedelta(days=NAPI_NAP)
        for f in fajlok:
            if f["szint"] == "napi" and f["ido"] < hatar_nap:
                torlendo.add(f["nev"])

        # 3) havi: HAVI_HONAP hónapnál régebbiek
        hatar_havi = most - _dt.timedelta(days=HAVI_HONAP * 31)
        for f in fajlok:
            if f["szint"] == "havi" and f["ido"] < hatar_havi:
                torlendo.add(f["nev"])

        # 4) a „kezi" soha nem törlődik; a legfrissebb MIN_MEGTART akkor is marad
        kezi = {f["nev"] for f in fajlok if f["szint"] == "kezi"}
        vedett = set(kezi)
        for f in fajlok:
            if len(vedett) >= MIN_MEGTART:
                break
            vedett.add(f["nev"])
        hatarolt = torlendo - vedett

        for nev in hatarolt:
            try:
                os.unlink(self._ut(nev))
                self.naplo("törölve (lejárt): %s" % nev)
            except OSError:
                pass
        return len(hatarolt)

    def inditaskor(self):
        """Indításkor egyszer: takarítás (mentés közben nem futtatunk törlést)."""
        return self.takaritas()

    # ---------------------------- lista / visszaállítás ----------------------------

    def lista(self):
        out = []
        for f in self._sajat_fajlok():
            out.append({
                "nev": f["nev"], "szint": f["szint"],
                "ido": f["ido"].strftime("%Y-%m-%d %H:%M:%S"),
                "meret": f["meret"],
            })
        return out

    def _legfrissebb_ep(self, nev: str = None):
        if nev:
            info = self._parse(nev)
            if not info or not os.path.isfile(info["ut"]):
                raise FileNotFoundError("nincs ilyen mentés: %s" % nev)
            jeloltek = [info]
        else:
            jeloltek = self._sajat_fajlok()
        for info in jeloltek:
            try:
                with open(info["ut"], encoding="utf-8") as fh:
                    return info, json.load(fh)
            except (OSError, ValueError):
                continue
        raise FileNotFoundError("nincs olvasható mentés")

    def visszaallit(self, nev: str = None, jelenlegi=None, biztonsagi: bool = True):
        """Visszaállít egy mentésből.

        Ha megadod a jelenlegi állapotot (`jelenlegi=…`), előbb azt menti el
        „kezi" szinten – így a visszaállítás visszafordítható.
        """
        info, adat = self._legfrissebb_ep(nev)
        if biztonsagi and jelenlegi is not None:
            self.mentes(jelenlegi, szint="kezi", suffix="-visszaallitas-elott", kenyszer=True)
        self.naplo("visszaállítva: %s (%s)" % (info["nev"], info["ido"]))
        return adat, info

    # ---------------------------- csomag ----------------------------

    def csomag(self, fajl=None):
        """Az összes mentés egy zipben (memóriában vagy fájlba)."""
        import io
        puffer = io.BytesIO() if fajl is None else None
        cel = puffer or fajl
        with zipfile.ZipFile(cel, "w", zipfile.ZIP_DEFLATED) as z:
            for f in self._sajat_fajlok():
                z.write(f["ut"], arcname=os.path.join("mentes", f["nev"]))
            jegyzet = (
                "Florum – mentés csomag\n"
                "app: %s\nkészült: %s\nmentések: %d\n\n"
                "Visszaállítás: a kívánt .json fájlt tedd az app adatmappájába\n"
                "(pl. ~/.local/share/%s/florum-data.json), vagy használd a\n"
                "Beállítások → Mentések → Visszaállítás gombot.\n"
            ) % (self.elotag, _most().strftime("%Y-%m-%d %H:%M"), len(self._sajat_fajlok()), self.elotag)
            z.writestr("mentes/OLVASSEL.txt", jegyzet)
        if puffer is not None:
            return puffer.getvalue()
        return fajl


# ------------------------------- CLI -------------------------------

def _cli(argv):
    ap = argparse.ArgumentParser(description="Közös mentés-modul (Florum)")
    ap.add_argument("muvelet", choices=["list", "restore", "export", "prune", "snap"])
    ap.add_argument("--mappa", required=True)
    ap.add_argument("--elotag", required=True)
    ap.add_argument("--nev", default="")
    ap.add_argument("--ki", default="")
    ap.add_argument("--adat", default="", help="snap: ebből a JSON-fájlból készít mentést")
    args = ap.parse_args(argv)

    m = Mentes(args.elotag, args.mappa, naplo=lambda u: print("  " + u))

    if args.muvelet == "list":
        for s in m.lista():
            print("%-34s %-5s %8d B  %s" % (s["nev"], s["szint"], s["meret"], s["ido"]))
        return 0
    if args.muvelet == "prune":
        print("törölve: %d fájl" % m.takaritas())
        return 0
    if args.muvelet == "restore":
        adat, info = m.visszaallit(args.nev or None)
        print(json.dumps(adat, ensure_ascii=False, indent=1)[:400])
        print("… visszaállítva: %s" % info["nev"])
        return 0
    if args.muvelet == "export":
        ki = args.ki or "%s-mentes.zip" % args.elotag
        m.csomag(ki)
        print("csomag: %s (%.1f kB)" % (ki, os.path.getsize(ki) / 1024.0))
        return 0
    if args.muvelet == "snap":
        if not args.adat or not os.path.isfile(args.adat):
            print("hiányzó --adat fájl")
            return 2
        with open(args.adat, encoding="utf-8") as fh:
            nev = m.mentes(json.load(fh))
        print("mentés: %s" % (nev or "nincs változás"))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
