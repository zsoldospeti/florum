#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Florum – Event Calendar widget diagnózis és javítás
===================================================

Azt vizsgálja, miért nem mutatja a widget a Florum teendőit:

  1. megvan-e a widget (és támogatja-e egyáltalán az .ics naptárakat),
  2. mit tartalmaz a widget naptár-beállítása (`icalCalendarList`),
  3. a mentett útvonalat elfogadja-e a widget szabálya
     (csak /home/<user>/.local/share/plasma_org.kde.plasma.eventcalendar/*.ics),
  4. a widget saját beolvasója (icsjson.py) hibátlanul listázza-e az eseményeket,
  5. megvannak-e a Python-függőségei (icalendar, recurring-ical-events).

Használat:
    python3 eventcalendar-diagnosztika.py              # csak vizsgálat
    python3 eventcalendar-diagnosztika.py --javitas    # beállítás rendbetétele
    python3 eventcalendar-diagnosztika.py --javitas --restart
"""

import argparse
import base64
import binascii
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

PLASMOID = "org.kde.plasma.eventcalendar"
MIRROR_NAME = "florum.ics"
DOMAIN = "plasma_applet_org.kde.plasma.eventcalendar"

CFG = os.path.join(os.path.expanduser("~"), ".config", "plasma-org.kde.plasma.desktop-appletsrc")
WIDGET_DIRS = [
    os.path.join(os.path.expanduser("~"), ".local", "share", "plasma", "plasmoids", PLASMOID),
    os.path.join("/usr/share/plasma/plasmoids", PLASMOID),
    os.path.join(os.path.expanduser("~"), ".local", "share", "plasma", "plasmoids", PLASMOID + "-ics"),
]
PY_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "plasma_org.kde.plasma.eventcalendar", "python")
MIRROR_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "plasma_org.kde.plasma.eventcalendar")

OK, ERR, WARN, INFO = "  ✓", "  ✗", "  !", "  ·"


# ---------------------------------------------------------------- segédek
def find_widget():
    """A telepített widget mappái (a felhasználói példány előre)."""
    out = []
    for d in WIDGET_DIRS:
        if os.path.isdir(os.path.join(d, "contents")):
            out.append(d)
    return out


def helper_script(widget_dir):
    p = os.path.join(widget_dir, "contents", "scripts", "icsjson.py")
    return p if os.path.exists(p) else None


def widget_version(widget_dir):
    p = os.path.join(widget_dir, "metadata.json")
    try:
        with open(p, encoding="utf-8") as fh:
            adat = json.load(fh)
        kp = adat.get("KPlugin") or {}
        return "%s %s" % (kp.get("Name") or "?", adat.get("KPlugin", {}).get("Version") or adat.get("Version") or "")
    except (OSError, ValueError):
        return "?"


def sections():
    """A .rc fájl [Containments][n][Applets][m][Configuration][Events] szakaszai."""
    try:
        with open(CFG, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return []
    out = []
    for m in re.finditer(r"(?m)^\[Containments\]\[\d+\]\[Applets\]\[\d+\]\[Configuration\]\[Events\]\s*$", text):
        start = m.start()
        nxt = text.find("\n[", m.end())
        block = text[m.end():] if nxt < 0 else text[m.end():nxt]
        out.append({"header": m.group(0).strip(), "start": start, "end": (len(text) if nxt < 0 else nxt), "body": block})
    return out


def applet_plugin(header):
    """Az adott applet plugin-neve (a [Containments][n][Applets][m] szakaszból)."""
    m = re.match(r"\[Containments\]\[(\d+)\]\[Applets\]\[(\d+)\]", header)
    if not m:
        return ""
    applet = "[Containments][%s][Applets][%s]" % (m.group(1), m.group(2))
    try:
        with open(CFG, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return ""
    i = text.find("\n" + applet + "\n")
    if i < 0:
        i = text.find(applet)
    if i < 0:
        return ""
    j = text.find("\n[", i + 1)
    blokk = text[i:(len(text) if j < 0 else j)]
    pm = re.search(r"(?m)^plugin=(.+)$", blokk)
    return pm.group(1).strip() if pm else ""


def decode_list(raw):
    raw = (raw or "").strip()
    if not raw:
        return []
    pad = "=" * (-len(raw) % 4)
    try:
        data = base64.b64decode(raw + pad, validate=False)
        val = json.loads(data.decode("utf-8", "replace"))
        return val if isinstance(val, list) else []
    except (binascii.Error, ValueError):
        return []


def encode_list(val):
    return base64.b64encode(json.dumps(val, ensure_ascii=False).encode("utf-8")).decode("ascii")


def value_of(body, key):
    m = re.search(r"(?m)^%s=(.*)$" % re.escape(key), body)
    return m.group(1) if m else ""


def user_home_ok():
    """A widget a /home/<login> utat várja (ConfigICal.qml)."""
    home = os.path.expanduser("~")
    login = os.environ.get("USER") or os.environ.get("LOGNAME") or os.path.basename(home)
    return home, "/home/" + login


# ---------------------------------------------------------------- vizsgálat
def check_python(script, url, days_back=30, days_forward=120):
    """A widget saját beolvasója, pontosan úgy, ahogy ő hívja (kitöltetlen dátumok!)."""
    ma = datetime.date.today()
    kezd = ma - datetime.timedelta(days=days_back)
    veg = ma + datetime.timedelta(days=days_forward)
    # az ICalManager.qml így építi: getFullYear() + '-' + (getMonth()+1) + '-' + getDate()
    parancs = [sys.executable or "python3", script, "--url", url, "query",
               "%d-%d-%d" % (kezd.year, kezd.month, kezd.day),
               "%d-%d-%d" % (veg.year, veg.month, veg.day)]
    try:
        r = subprocess.run(parancs, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "nem indult el: %s" % exc, parancs
    if r.returncode != 0:
        hiba = (r.stderr or r.stdout or "").strip().splitlines()
        return None, (hiba[-1] if hiba else "ismeretlen hiba"), parancs
    try:
        adat = json.loads(r.stdout)
        return len(adat.get("items") or []), "", parancs
    except ValueError:
        return None, "a kimenet nem JSON", parancs


def check_module(nev):
    r = subprocess.run([sys.executable or "python3", "-c", "import %s" % nev],
                       capture_output=True, text=True)
    return r.returncode == 0


# ---------------------------------------------------------------- panel-kezelés
PIM_PLUGIN_HINTS = (
    "/usr/lib/qt6/plugins/pimeventsplugin.so",
    "/usr/lib/qt6/plugins/plasma/calendar/pimeventsplugin.so",
    "/usr/lib64/qt6/plugins/pimeventsplugin.so",
)


def plasmashell_running():
    if not shutil.which("pgrep"):
        return False
    return subprocess.run(["pgrep", "-x", "plasmashell"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def stop_plasmashell():
    """A panelt LE KELL állítani a beállítás írása ELŐTT.

    A futó plasmashell a memóriájában tartja az applet-beállításokat, és
    kilépéskor visszaírja őket – vagyis a futás közben kézzel átírt
    appletsrc-et felülírná. Ez volt az egyik fő oka, hogy a javítás
    „nem használt”.
    """
    if not plasmashell_running():
        return True
    for cmd in (["systemctl", "--user", "stop", "plasma-plasmashell.service"],
                ["kquitapp6", "plasmashell"],
                ["pkill", "-x", "plasmashell"]):
        if not shutil.which(cmd[0]):
            continue
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        for _ in range(30):
            if not plasmashell_running():
                return True
            time.sleep(0.2)
    return not plasmashell_running()


def start_plasmashell():
    for cmd in (["systemctl", "--user", "start", "plasma-plasmashell.service"],
                ["kstart", "plasmashell"],
                ["plasmashell"]):
        if not shutil.which(cmd[0]):
            continue
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            continue
        for _ in range(25):
            if plasmashell_running():
                return True
            time.sleep(0.4)
    return plasmashell_running()


def pim_plugin_installed():
    if any(os.path.exists(p) for p in PIM_PLUGIN_HINTS):
        return True
    if shutil.which("pacman") and shutil.which("pacman"):
        r = subprocess.run(["pacman", "-Qq", "kdepim-addons"],
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return r.returncode == 0
    return False


def panel_widgets():
    """Minden panel-widget a beállításból: (plugin, szakasz fejléce)."""
    out = []
    for s in sections():
        out.append((applet_plugin(s["header"]), s["header"]))
    return out


def diagnose():
    print()
    print("  🌿 Event Calendar – diagnózis")
    print("  " + "-" * 60)

    problems = []
    home, vart_home = user_home_ok()

    # 1) widget
    print("\n  1) A widget")
    widgets = find_widget()
    if not widgets:
        print("%s nincs telepítve Event Calendar plasmoid (%s)" % (ERR, PLASMOID))
        problems.append("widget")
    script = None
    for w in widgets:
        h = helper_script(w)
        print("%s %s  (%s)%s" % (OK, w, widget_version(w), "" if h else "   ← NINCS .ics támogatás!"))
        if h and not script:
            script = h
    if widgets and not script:
        print("%s ez a widget-változat nem tud .ics fájlt olvasni – a divinae-féle"
              " változat kell (bash kde-eventcalendar-telepites.sh)" % ERR)
        problems.append("fork")
    if home != vart_home:
        print("%s a saját mappád (%s) nem a /home/%s – a widget beállítás-oldala ezt várja,"
              " a mentett útvonalat elutasíthatja" % (WARN, home, os.path.basename(home)))
        problems.append("home")

    # 2) a naptár-beállítás
    print("\n  2) A widget naptár-beállítása (%s)" % CFG)
    secs = [s for s in sections() if value_of(s["body"], "icalCalendarList") != ""]
    if not os.path.exists(CFG):
        print("%s nincs beállításfájl – a widget még nem futott ezzel a felhasználóval" % ERR)
        problems.append("nincs rc")
    elif not secs:
        print("%s nincs icalCalendarList bejegyzés – a widgetben nincs felvéve naptár" % ERR)
        problems.append("nincs bejegyzés")
    else:
        for s in secs:
            plugin = applet_plugin(s["header"])
            print("  · %s  (plugin: %s)" % (s["header"], plugin or "?"))
            if plugin and PLASMOID not in plugin:
                print("    (nem Event Calendar applet – kihagyva)")
                continue
            entries = decode_list(value_of(s["body"], "icalCalendarList"))
            if not entries:
                print("%s a naptárlista üres" % ERR)
                problems.append("üres lista")
                continue
            for e in entries:
                url = str(e.get("url") or "")
                nev = str(e.get("name") or "")
                show = e.get("show", True)
                print("    - név: %-14s show: %-5s url: %s" % (nev or "(nincs)", show, url or "(ÜRES)"))
                if not url.strip():
                    print("%s     üres az útvonal – a widget nem tud mit beolvasni" % ERR)
                    problems.append("üres url")
                    continue
                tiszt = url[7:] if url.startswith("file://") else url
                if not tiszt.startswith(vart_home + "/"):
                    print("%s     a widget csak ezt fogadja el: %s/*.ics" % (ERR, vart_home))
                    problems.append("rossz útvonal")
                elif not tiszt.lower().endswith(".ics"):
                    print("%s     nem .ics fájl" % ERR)
                    problems.append("nem ics")
                if not os.path.exists(tiszt):
                    print("%s     a fájl nem létezik: %s" % (ERR, tiszt))
                    problems.append("nincs fájl")
                else:
                    with open(tiszt, encoding="utf-8", errors="replace") as fh:
                        db = fh.read().count("BEGIN:VEVENT")
                    print("%s     a fájl megvan, %d esemény, %d byte" %
                          (OK, db, os.path.getsize(tiszt)))
                if show is False:
                    print("%s     a naptár KI van jelölve (show=false) – a widget nem tölti be" % ERR)
                    problems.append("show=false")
                if script and os.path.exists(tiszt):
                    db, hiba, parancs = check_python(script, url)
                    if db is None:
                        print("%s     a beolvasó hibát ad: %s" % (ERR, hiba))
                        print("        parancs: %s" % " ".join(parancs))
                        problems.append("beolvasó hiba")
                    else:
                        print("%s     a widget beolvasója %d eseményt lát" % (OK, db))
                        if db == 0:
                            print("%s     nulla esemény a következő 120 napra – a naptár üres lehet"
                                  % WARN)
                            problems.append("0 esemény")

    # 2b) a panel többi widgetje – melyik tud egyáltalán eseményt mutatni?
    print("\n  2b) A panel widgetjei")
    widgetek = panel_widgets()
    if not widgetek:
        print("%s nincs beolvasható applet-beállítás" % INFO)
    for plugin, fej in widgetek:
        jel = ""
        if plugin == PLASMOID:
            jel = "← Event Calendar"
        elif plugin == "org.kde.plasma.digitalclock":
            jel = "← Digitális óra (esemény csak a PIM Events Pluginnal, kdepim-addons)"
        elif plugin == "org.kde.plasma.calendar":
            jel = "← Naptár (esemény csak a PIM Events Pluginnal, kdepim-addons)"
        print("%s %-42s %s" % (INFO, plugin or "?", jel))
    pim = any(p in ("org.kde.plasma.digitalclock", "org.kde.plasma.calendar") for p, _ in widgetek)
    if pim:
        if pim_plugin_installed():
            print("%s PIM Events Plugin megvan (Digitális óra/Naptár widgethez)" % OK)
            print("%s     ha ott sem látszik semmi: Akonadi iCal-erőforrás kell a .ics-hez –" %
                  INFO)
            print("        ez a KDE ismert hibái miatt (bug 526769, 493415) gyakran nem működik")
        else:
            print("%s a Digitális óra/Naptár widgethez kell a PIM Events Plugin:" % WARN)
            print("        sudo pacman -S kdepim-addons")
    print("%s biztos megoldás, ha egyik sem működik: a Florum saját widgetje" % INFO)
    print("      bash telepites-florum-panel.sh")

    # 3) python-függőségek
    print("\n  3) Python-függőségek (a widget a rendszer python3-at hívja)")
    for mod in ("icalendar", "recurring_ical_events"):
        if check_module(mod):
            print("%s %s" % (OK, mod))
        else:
            print("%s %s hiányzik" % (ERR, mod))
            problems.append("modul: " + mod)
    if os.path.isdir(PY_DIR):
        print("%s a widget saját Python-mappája megvan: %s" % (INFO, PY_DIR))

    # 4) a másolat
    print("\n  4) A Florum naptár-másolata")
    mirror = os.path.join(MIRROR_DIR, MIRROR_NAME)
    if os.path.exists(mirror):
        print("%s %s" % (OK, mirror))
    else:
        print("%s nincs másolat: %s" % (ERR, mirror))
        print("        Hozd létre: python3 naptar_ics.py   (vagy indítsd a Florumot egyszer)")
        problems.append("nincs másolat")

    # 5) összegzés
    print("\n  " + "-" * 60)
    print("  Ha a widget továbbra sem mutat semmit, a Florum saját panel-widgetje")
    print("  minden ilyen függőség nélkül működik:")
    print("    bash telepites-florum-panel.sh")
    print()
    if not problems:
        print("  Minden rendben. Ha a widget mégsem mutat semmit:")
        print("    · jobb klikk → Configure Event Calendar → Calendars: a naptár be legyen ikszelve,")
        print("    · a nézet legyen Hónap vagy Agenda, és nézd meg a következő napokat,")
        print("    · indítsd újra a panelt: systemctl --user restart plasma-plasmashell")
    else:
        print("  Talált hibák: %s" % ", ".join(sorted(set(problems))))
        print("  Javítás: python3 eventcalendar-diagnosztika.py --javitas --restart")
        if "modul: icalendar" in problems or "modul: recurring_ical_events" in problems:
            print("  Hiányzó Python-modul: bash kde-eventcalendar-fuggoseg.sh")
    print()
    return 0 if not problems else 1


# ---------------------------------------------------------------- javítás
def repair(restart=False):
    print()
    print("  🔧 Event Calendar – a naptár-beállítás rendbetétele")
    print("  " + "-" * 60)
    mirror = os.path.join(MIRROR_DIR, MIRROR_NAME)
    if not os.path.exists(mirror):
        print("%s nincs %s – előbb: python3 naptar_ics.py" % (ERR, mirror))
        return 1
    if not os.path.exists(CFG):
        print("%s nincs %s" % (ERR, CFG))
        return 1

    with open(CFG, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    mentes = CFG + ".florum-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".bak"
    shutil.copy2(CFG, mentes)
    print("%s biztonsági mentés: %s" % (OK, mentes))

    cel = {
        "url": mirror,
        "name": "Florum",
        "backgroundColor": "#2fa86f",
        "show": True,
        "isReadOnly": True,
    }
    valtozott = 0
    for s in sections():
        plugin = applet_plugin(s["header"])
        if plugin and PLASMOID not in plugin:
            continue
        body = s["body"]
        lista = decode_list(value_of(body, "icalCalendarList"))
        uj = []
        volt = False
        for e in lista:
            url = str(e.get("url") or "")
            if url.endswith(MIRROR_NAME) or "plasma_org.kde.plasma.eventcalendar" in url:
                nev = str(e.get("name") or "").strip()
                uj.append(dict(cel, name="Florum" if nev in ("", "Label") else nev))
                volt = True
            else:
                uj.append(e)
        if not volt:
            uj.append(cel)
        sor = "icalCalendarList=" + encode_list(uj)
        if re.search(r"(?m)^icalCalendarList=.*$", body):
            uj_body = re.sub(r"(?m)^icalCalendarList=.*$", sor.replace("\\", "\\\\"), body)
        else:
            uj_body = body.rstrip("\n") + "\n" + sor + "\n"
        text = text[:s["start"]] + s["header"] + uj_body + text[s["end"]:]
        valtozott += 1
        print("%s %s → %d naptár, a Florumé: %s (show=true)" % (OK, s["header"], len(uj), mirror))

    if not valtozott:
        # nincs Events-szakasz: az Event Calendar applet szakasza alá beszúrjuk
        m = None
        for mm in re.finditer(r"(?m)^\[Containments\]\[\d+\]\[Applets\]\[\d+\]\s*$", text):
            blokk_end = text.find("\n[", mm.end())
            blokk = text[mm.end():] if blokk_end < 0 else text[mm.end():blokk_end]
            if re.search(r"(?m)^plugin=%s\s*$" % re.escape(PLASMOID), blokk):
                m = (mm, blokk_end)
        if not m:
            print("%s nem találom az Event Calendar appletet a beállításban –"
                  " előbb add hozzá a widgetet a panelhez" % ERR)
            return 1
        beszur = "\n[Containments]%s[Configuration][Events]\nicalCalendarList=%s\n" % (
            re.search(r"\[Containments\]\[(\d+)\]\[Applets\]\[(\d+)\]", text[m[0].start():m[0].end()]).group(1, 2)[0],
            encode_list([cel]))
        # pontos szakaszkulcs az applet-fejlécből
        fej = text[m[0].start():m[0].end()].strip()          # [Containments][1][Applets][5]
        resz = re.match(r"\[Containments\]\[(\d+)\]\[Applets\]\[(\d+)\]", fej)
        szakasz = "\n[Containments][%s][Applets][%s][Configuration][Events]\nicalCalendarList=%s\n" % (
            resz.group(1), resz.group(2), encode_list([cel]))
        text = text[:m[0].end()] + szakasz + text[m[0].end():]
        valtozott += 1
        print("%s új Events-szakasz készült a Florum naptárával" % OK)

    # FONTOS: a futó plasmashell a memóriájából írja vissza a beállítást,
    # ezért előbb le kell állítani – különben a javítás elveszne.
    leallitva = False
    if plasmashell_running():
        print("  → a panel leállítása (a futó plasmashell felülírná a beállítást)…")
        if stop_plasmashell():
            leallitva = True
            print("%s panel leállítva" % OK)
        else:
            print("%s a panelt nem sikerült leállítani – indítsd újra kézzel" % WARN)

    with open(CFG, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("%s beállítás kiírva" % OK)

    if restart or leallitva:
        print("  → plasmashell indítása…")
        if start_plasmashell():
            print("%s panel újraindítva – a widget most már a friss beállítást olvassa" % OK)
        else:
            print("%s a panel nem indult el magától: systemctl --user start plasma-plasmashell"
                  % WARN)
    else:
        print("  A widget a panel újraindítása után veszi át:"
              " systemctl --user restart plasma-plasmashell")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Event Calendar – diagnózis és javítás")
    ap.add_argument("--javitas", action="store_true", help="a naptár-beállítás rendbetétele")
    ap.add_argument("--restart", action="store_true", help="a panel újraindítása a javítás után")
    args = ap.parse_args(argv)
    if args.javitas:
        return repair(restart=args.restart)
    return diagnose()


if __name__ == "__main__":
    sys.exit(main())
