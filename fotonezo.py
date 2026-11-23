#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.33.4  ·  otthoni növénygondozó
#  Fájl:    fotonezo.py
#  Szerep:  a növényfotók megnyitása külső nézegetőben
#           (feh, böngésző, gwenview, loupe …) és a terminálban
#           (chafa, viu, timg, catimg, img2txt)
#  Licenc:  szabadon használható, módosítható és terjeszthető
# ==============================================================

"""
Mivel nézzük meg a fotókat?

A Florum maga is mutatja a képeket a böngészőben (nagy nézet: /foto), de
néha kényelmesebb egy igazi képmegnéző. Ez a modul ehhez keres programot:

  * grafikus:  feh, gwenview, loupe, eog, imv, nsxiv/sxiv, ristretto,
               végső esetben xdg-open (a rendszer alapértelmezett nézője –
               CachyOS-on ez általában a böngésző vagy a Gwenview)
  * terminálos: chafa, viu, timg, catimg, img2txt – ezek ANSI-blokkokkal
               „rajzolják” a képet a terminálba (SSH-n is működik)

Egyik sem kötelező: ha nincs telepítve, a Florum egyszerűen azt mondja meg,
mit érdemes telepíteni (sudo pacman -S feh chafa), és a böngészős nagy nézet
mindig működik.

Parancssor:
    python3 fotonezo.py --lista            # mi van telepítve?
    python3 fotonezo.py kep.jpg            # megnyitás alapértelmezettel
    python3 fotonezo.py kep.jpg --terminal # terminálba „rajzolva”
"""

import os
import shutil
import subprocess
import sys

# ---------------------------------------------------------------- ismert nézők
# (program, kapcsolók) – a sorrend egyben a keresés sorrendje is
GRAFIKUS = [
    ("feh",       ["--auto-zoom", "--scale-down", "--geometry", "1200x800"]),
    ("gwenview",  []),
    ("loupe",     []),          # GNOME 45+ képmegnéző
    ("eog",       []),
    ("imv",       []),
    ("nsxiv",     ["-f"]),
    ("sxiv",      ["-f"]),
    ("ristretto", []),
    ("xdg-open",  []),          # a rendszer alapértelmezett megnyitója
]

TERMINAL = [
    ("chafa",   ["--size", "80x40", "--format", "symbols"]),
    ("viu",     ["-w", "80", "-h", "40"]),
    ("timg",    ["-g", "80x40"]),
    ("catimg",  ["-w", "80"]),
    ("img2txt", ["-W", "80"]),
]

# Ezek a programok „tudják” a PNG/JPEG/WebP formátumokat; a böngésző is.
KITERJESZTESEK = (".jpg", ".jpeg", ".png", ".webp", ".gif")


# ---------------------------------------------------------------- segédek
def talal(nev):
    """A program útvonala, ha telepítve van – különben üres szöveg."""
    return shutil.which(nev) or ""


def elerheto(terminal=False):
    """A telepített nézők listája: [(név, útvonal, kapcsolók)]."""
    tabla = TERMINAL if terminal else GRAFIKUS
    return [(nev, talal(nev), kapcs) for nev, kapcs in tabla if talal(nev)]


def valaszto(terminal=False, kedvenc=""):
    """Melyik programmal nyissunk? (név, útvonal, kapcsolók) vagy (None, …)."""
    if kedvenc:
        ut = talal(kedvenc)
        if ut:
            for nev, kapcs in (TERMINAL if terminal else GRAFIKUS):
                if nev == kedvenc:
                    return nev, ut, kapcs
            return kedvenc, ut, []
    for nev, ut, kapcs in elerheto(terminal):
        return nev, ut, kapcs
    return None, None, []


def parancs(ut, terminal=False, kedvenc=""):
    """A futtatandó parancslista (üres lista, ha nincs néző)."""
    if not ut:
        return []
    nev, exe, kapcs = valaszto(terminal, kedvenc)
    if not exe:
        return []
    if nev == "xdg-open":
        return [exe, ut]                       # az xdg-open nem szereti a kapcsolókat
    return [exe] + list(kapcs) + [ut]


def megnyit(ut, terminal=False, kedvenc="", proba=False):
    """Megnyitja a képet. Visszaad: dict(ok, nev, parancs, hiba, tipp)."""
    if not ut or not os.path.isfile(ut):
        return {"ok": False, "nev": "", "parancs": [], "hiba": "nincs ilyen fájl: %s" % (ut or "?"),
                "tipp": ""}
    if os.path.splitext(ut)[1].lower() not in KITERJESZTESEK:
        return {"ok": False, "nev": "", "parancs": [], "hiba": "ez nem képfájl: %s" % os.path.basename(ut),
                "tipp": ""}
    cmd = parancs(ut, terminal, kedvenc)
    nev = valaszto(terminal, kedvenc)[0]
    if not cmd:
        return {
            "ok": False, "nev": "", "parancs": [],
            "hiba": "nincs telepített %s nézegető" % ("terminálos" if terminal else "grafikus"),
            "tipp": ("sudo pacman -S " + ("chafa" if terminal else "feh")) +
                    " – vagy nyisd meg böngészőben: /foto",
        }
    if proba:
        return {"ok": True, "nev": nev, "parancs": cmd, "hiba": "", "tipp": ""}
    try:
        # külön folyamatcsoport: a néző akkor is él, ha a Florum kilép
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         stdin=subprocess.DEVNULL, start_new_session=True, close_fds=True)
    except (OSError, ValueError) as exc:
        return {"ok": False, "nev": nev, "parancs": cmd,
                "hiba": "nem indult el (%s): %s" % (nev, exc),
                "tipp": "próbáld: sudo pacman -S feh"}
    return {"ok": True, "nev": nev, "parancs": cmd, "hiba": "", "tipp": ""}


def terminal_kep(ut, kedvenc="", timeout=20):
    """A kép ANSI-szöveggé alakítva (chafa/viu/…). Visszaad: (szöveg, hiba)."""
    if not ut or not os.path.isfile(ut):
        return "", "nincs ilyen fájl"
    nev, exe, kapcs = valaszto(True, kedvenc)
    if not exe:
        return "", "nincs terminálos nézegető (sudo pacman -S chafa)"
    try:
        r = subprocess.run([exe] + list(kapcs) + [ut], capture_output=True,
                           timeout=timeout, text=True)
    except (OSError, subprocess.SubprocessError) as exc:
        return "", "%s: %s" % (nev, exc)
    if r.returncode != 0:
        return "", "%s hiba: %s" % (nev, (r.stderr or "").strip()[:200])
    return r.stdout, ""


def osszefoglalo():
    """A telepített nézők gépi ÉS embernek való formában.

    Visszaad: {grafikus: [név…], terminal: [név…], tipp: "…", sorok: ["Grafikus: …"]}
    A `sorok` a terminálba írható változat, a listák a JSON-hoz (/api/info).
    """
    g = [n for n, _, _ in elerheto(False)]
    t = [n for n, _, _ in elerheto(True)]
    sorok = ["Grafikus: " + (", ".join(g) if g else "nincs – sudo pacman -S feh"),
             "Terminálos: " + (", ".join(t) if t else "nincs – sudo pacman -S chafa")]
    tipp = ""
    if not g:
        tipp = "sudo pacman -S feh"
    elif not t:
        tipp = "sudo pacman -S chafa   (a terminálban is látszó képhez)"
    return {"grafikus": g, "terminal": t, "tipp": tipp, "sorok": sorok}


# ---------------------------------------------------------------- CLI
def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--lista" in argv or not argv:
        print("Florum – fotónézegetők:")
        for sor in osszefoglalo()["sorok"]:
            print("  " + sor)
        print("\n  Böngészős nagy nézet: http://127.0.0.1:8777/foto")
        return 0
    terminal = "--terminal" in argv or "-t" in argv
    kedvenc = ""
    for i, arg in enumerate(argv):
        if arg == "--nezo" and i + 1 < len(argv):
            kedvenc = argv[i + 1]
        elif arg.startswith("--nezo="):
            kedvenc = arg.split("=", 1)[1]
    utak = [a for a in argv if not a.startswith("-")]
    if not utak:
        if terminal:
            van = elerheto(True)
            print("Terminálos nézegetők: " + (", ".join(n for n, _, _ in van)
                                              if van else "nincs – sudo pacman -S chafa"))
            return 0
        print("Adj meg egy képfájlt (vagy: --lista).")
        return 2
    hibak = 0
    for ut in utak:
        if terminal:
            szoveg, hiba = terminal_kep(ut, kedvenc)
            if hiba:
                print("✗ %s – %s" % (ut, hiba))
                hibak += 1
            else:
                print(szoveg)
        else:
            r = megnyit(ut, kedvenc=kedvenc)
            if r["ok"]:
                print("✓ %s → %s" % (ut, r["nev"]))
            else:
                print("✗ %s – %s" % (ut, r["hiba"]))
                if r["tipp"]:
                    print("   " + r["tipp"])
                hibak += 1
    return 1 if hibak else 0


if __name__ == "__main__":
    sys.exit(main())
