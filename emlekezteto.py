#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Florum – emlékeztető démon (KDE panel / asztali értesítés)
==========================================================

A `florum-data.json`-ból számolja ki a teendőket (ugyanaz a logika, mint a
`.`ics`-ben – `naptar_ics.py`), és `notify-send`-del (KDE Plasma
értesítésként) szól, ha ma van valami dolga. Nem igényel futó Florum-ot.

Használat:
    python3 emlekezteto.py                     # egy kör, kilép
    python3 emlekezteto.py --daemon            # folyamatosan (30 percenként)
    python3 emlekezteto.py --daemon --intervallum 15
    python3 emlekezteto.py --lista             # emberi szöveg a mai teendőkről
    python3 emlekezteto.py --json              # JSON a panel-szöveghez / feedhez
    python3 emlekezteto.py --ics               # .ics újragenerálása
    python3 emlekezteto.py --teszt             # próbaértesítés

Kimenetek:
  * `emlekezteto-allapot.json` – mi ment már ki ma (ne szóljon kétszer),
  * `esemenyek.jsonl` – eseménynapló (minden kimenő értesítés egy sor),
  * `florum.ics` – a naptár-fájl (ha `--ics` vagy `--daemon`).

Az értesítés a `notify-send -a Florum -i <ikon> -u <fontosság>` híváson megy ki,
így a KDE Plasma saját értesítési rendszerében, a panelen jelenik meg.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import naptar_ics  # noqa: E402  (a közös ütemezés-logika)

APP = "Florum"
ALLAPOT = "emlekezteto-allapot.json"
NAPLO = "esemenyek.jsonl"
ICS = "florum.ics"


# ---------------------------------------------------------------- segédek
try:
    import permetviz
except Exception:
    permetviz = None


def data_dir(path=""):
    return path or os.path.join(os.path.expanduser("~"), ".local", "share", "florum")


def state_path(folder):
    return os.path.join(folder, "florum-data.json")


def read_json(path, fallback=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return fallback


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def notify_send(title, body, urgency="normal", icon="florum"):
    """KDE/asztali értesítés; visszaadja, hogy sikerült-e."""
    for exe, args in (
        ("notify-send", ["-a", APP, "-i", icon, "-u", urgency, title, body]),
        ("kdialog", ["--title", title, "--passivepopup", body, "15"]),
        ("zenity", ["--notification", "--text", title + " " + body]),
    ):
        if shutil.which(exe):
            try:
                subprocess.run([exe] + args, check=False, timeout=15,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except (OSError, subprocess.SubprocessError):
                continue
    return False


# ---------------------------------------------------------------- mai teendők
def due_today(state, today=None, elore=0):
    """
    A mai (és opcionálisan a következő `elore` nap) teendők a közös ütemezésből.
    Visszaad: [{nap, kesik, cim, feladat, noveny, szoba, hely, kulcs}]
    """
    today = today or datetime.date.today()
    events = naptar_ics.collect(state, days=max(0, elore), today=today)
    out = []
    for ev in events:
        plant, task = ev["plant"], ev["task"]
        title = naptar_ics.plant_title(plant, ev["alias_first"])
        out.append({
            "nap": ev["date"].isoformat(),
            "ma": ev["date"] == today,
            "kesik": bool(ev.get("late_for")),
            "eredeti": ev["late_for"].isoformat() if ev.get("late_for") else "",
            "feladat": task["label"],
            "kulcs": task["key"],
            "ikon": task["icon"],
            "noveny": title,
            "hivatalos": plant.get("name") or "",
            "szoba": plant.get("room") or "",
            "cim": "%s %s – %s" % (task["icon"], task["label"], title),
            # permetezésnél: „esővízzel, reggel” – a szöveg végére kerül
            "viz": (permetviz.hint(plant) if (permetviz and task["key"] == "misting") else ""),
        })
    return out


def summary_lines(items):
    lines = []
    for it in items:
        sor = it["cim"]
        if it["szoba"]:
            sor += " (%s)" % it["szoba"]
        if it["kesik"]:
            sor += " – lejárt: %s" % it["eredeti"]
        elif not it["ma"]:
            sor += " – %s" % it["nap"]
        if it.get("viz"):
            sor += " · " + it["viz"]
        lines.append(sor)
    return lines


def panel_text(items, maxt=5):
    """Rövid, egysoros szöveg a panelhez / tooltiphez."""
    if not items:
        return "Ma nincs teendő 🌿"
    ma = [i for i in items if i["ma"]]
    head = ", ".join("%s %s" % (i["noveny"], i["feladat"].lower()) for i in ma[:maxt])
    marad = len(ma) - maxt
    if marad > 0:
        head += " és %d további" % marad
    return ("Ma: " + head) if ma else "Ma nincs teendő 🌿"


# ---------------------------------------------------------------- fő kör
def run_once(folder, elore=0, csendes=False, teszt=False, ics=True, alarm=8, days=90,
             mirror=True):
    """Egy értesítési kör. Visszaad: (küldött-e, szöveg, darabszám)."""
    today = datetime.date.today()
    state = read_json(state_path(folder), {}) or {}
    if ics:
        try:
            naptar_ics.write_ics(os.path.join(folder, ICS), state, days=days, alarm_hour=alarm,
                                 today=today, mirror=mirror)
        except OSError as exc:
            if not csendes:
                print("Nem sikerült kiírni a naptárt: %s" % exc, file=sys.stderr)

    items = due_today(state, today=today, elore=elore)
    ma = [i for i in items if i["ma"]]
    if not ma:
        return False, "Ma nincs teendő.", 0

    # napi egyszeri emlékeztető: a nap + a teendők lenyomata
    allapot_path = os.path.join(folder, ALLAPOT)
    allapot = read_json(allapot_path, {}) or {}
    kulcs = today.isoformat() + "|" + "|".join(sorted("%s:%s" % (i["noveny"], i["kulcs"]) for i in ma))
    if allapot.get("kulcs") == kulcs and not teszt:
        if not csendes:
            print("Már szóltunk ma (%d teendő)." % len(ma))
        return False, panel_text(items), len(ma)

    cim = "%d teendő ma" % len(ma) if len(ma) > 1 else "1 teendő ma"
    sorok = summary_lines(ma)
    body = "\n".join(sorok[:8])
    if len(sorok) > 8:
        body += "\n… és %d további" % (len(sorok) - 8)
    kesik = any(i["kesik"] for i in ma)
    ok = notify_send("%s – %s" % (APP, cim), body,
                     urgency="critical" if kesik else "normal",
                     icon="florum" if shutil.which("florum") else "dialog-information")

    if not csendes:
        print(("%s – %s\n%s" % (APP, cim, body)) if not ok else ("Elküldve: %s" % cim))
        if not ok:
            print("(nincs notify-send / kdialog / zenity – a szöveg a fenti)", file=sys.stderr)

    # napló
    try:
        with open(os.path.join(folder, NAPLO), "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "idopont": datetime.datetime.now().isoformat(timespec="seconds"),
                "cim": cim, "darab": len(ma), "kesik": kesik,
                "teendok": [{"nap": i["nap"], "feladat": i["feladat"], "noveny": i["noveny"],
                             "szoba": i["szoba"], "kesik": i["kesik"]} for i in ma],
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass

    write_json(allapot_path, {"kulcs": kulcs, "nap": today.isoformat(), "darab": len(ma),
                              "idopont": datetime.datetime.now().isoformat(timespec="seconds")})
    return True, panel_text(items), len(ma)


def daemon(folder, intervallum=1800, elore=0, csendes=False, alarm=8, days=90):
    print("%s emlékeztető – %s percenként, adat: %s" % (APP, max(1, intervallum // 60), folder))
    while True:
        try:
            run_once(folder, elore=elore, csendes=csendes, alarm=alarm, days=days)
        except Exception as exc:                      # a démon ne álljon le egy hibától
            print("Hiba a körben: %s" % exc, file=sys.stderr)
        time.sleep(max(60, intervallum))


# ---------------------------------------------------------------- CLI
def main(argv=None):
    p = argparse.ArgumentParser(description="Florum emlékeztető (KDE panel / notify-send)")
    p.add_argument("--data", default="", help="adatmappa (alap: ~/.local/share/florum)")
    p.add_argument("--daemon", action="store_true", help="folyamatos futás")
    p.add_argument("--intervallum", type=int, default=1800, help="másodperc a körök között (alap: 1800)")
    p.add_argument("--elore", type=int, default=0, help="a következő N napot is jelezze (alap: 0 = csak ma)")
    p.add_argument("--alarm", type=int, default=8, help="emlékeztető órája az .ics-ben (alap: 8)")
    p.add_argument("--days", type=int, default=90, help="hány napra készüljön az .ics (alap: 90)")
    p.add_argument("--lista", action="store_true", help="a mai teendők szövegesen")
    p.add_argument("--json", action="store_true", help="a mai teendők JSON-ban")
    p.add_argument("--panel", action="store_true", help="egysoros összefoglaló a panelhez")
    p.add_argument("--ics", action="store_true", help="csak az .ics újragenerálása")
    p.add_argument("--teszt", action="store_true", help="próbaértesítés (a napi zárolás megkerülésével)")
    p.add_argument("--csendes", action="store_true", help="ne írjon a kimenetre")
    p.add_argument("--no-mirror", action="store_true",
                   help="ne készüljön másolat az Event Calendar adatmappájába")
    args = p.parse_args(argv)

    folder = data_dir(args.data)
    if not os.path.isdir(folder):
        os.makedirs(folder, exist_ok=True)

    if args.ics:
        state = read_json(state_path(folder), {}) or {}
        count = naptar_ics.write_ics(os.path.join(folder, ICS), state, days=args.days,
                                     alarm_hour=args.alarm, mirror=not args.no_mirror)
        print("másolat a widgetnek → %s" % naptar_ics.mirror_path())
        print("%d esemény → %s" % (count, os.path.join(folder, ICS)))
        return 0

    if args.lista or args.json or args.panel:
        state = read_json(state_path(folder), {}) or {}
        items = due_today(state, elore=args.elore)
        if args.json:
            print(json.dumps({"ok": True, "darab": len(items), "panel": panel_text(items),
                              "teendok": items}, ensure_ascii=False, indent=1))
        elif args.panel:
            print(panel_text(items))
        else:
            if not items:
                print("Ma nincs teendő 🌿")
            else:
                print("Mai teendők (%d):" % len(items))
                for sor in summary_lines(items):
                    print("  • " + sor)
        return 0

    if args.teszt:
        ok = notify_send("%s – próbaértesítés" % APP,
                         "Ha ezt látod a KDE panelen, működik az emlékeztető. 🌿",
                         icon="dialog-information")
        print("Elküldve." if ok else "Nincs notify-send / kdialog / zenity a gépen.")
        return 0 if ok else 1

    if args.daemon:
        try:
            daemon(folder, intervallum=args.intervallum, elore=args.elore,
                   csendes=args.csendes, alarm=args.alarm, days=args.days)
        except KeyboardInterrupt:
            print("\nLeállítva.")
        return 0

    run_once(folder, elore=args.elore, csendes=args.csendes, alarm=args.alarm,
             days=args.days, mirror=not args.no_mirror)
    return 0


if __name__ == "__main__":
    sys.exit(main())
