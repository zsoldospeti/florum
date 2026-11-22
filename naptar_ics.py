#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Florum – naptár-kapu (iCalendar / .ics a KDE panelhez)
======================================================

A KDE Plasma Digitális órája (Digital Clock) az **Akonadi**-naptárakból mutatja az
eseményeket, ha be van kapcsolva a „PIM Events Plugin” (kdepim-addons). Ez a modul
ezért szabványos **iCalendar** fájlt állít elő a Florum teendőiből:

  * minden esedékes öntözés / tápoldatozás / permetezés / átültetés egy-egy
    egész napos esemény (VEVENT, DTSTART;VALUE=DATE),
  * napi emlékeztető (VALARM) a beállított órában,
  * a lejárt teendő **a mai napra** kerül (hogy a panelen látszódjon),
  * az áthelyezett (szundi) teendő a felülírt napon jelenik meg,
  * a téli tápoldat-szünet és a téli 1,5×-ös öntözés ugyanúgy érvényesül, mint a felületen.

Fájlok:
  * `florum.py` ezt a modult használja: `GET /api/calendar.ics`, illetve minden
    mentés után kiírja a `florum.ics`-t az adatmappába,
  * önállóan is futtatható: `python3 naptar-ics.py --data ~/.local/share/florum`
    (a systemd időzítő ezt hívja, ha a Florum nem fut).
"""

import argparse
import datetime
import hashlib
import json
import os
import sys

try:
    import permetviz
except Exception:                       # önállóan is működjön
    permetviz = None

APP = "Florum"
PRODID = "-//Florum//Novenygondozo//HU"
UID_DOMAIN = "florum.local"
TZ = "Europe/Budapest"

# A felület TASK_DEFS-e: kulcs, felirat, mező, utolsó alkalom, hónapos-e, ikon
TASKS = [
    {"key": "watering",    "label": "Öntözés",    "field": "waterDays",   "last": "lastWatered",    "months": False, "icon": "💧"},
    {"key": "fertilizing", "label": "Tápoldat",   "field": "fertDays",    "last": "lastFertilized", "months": False, "icon": "🌿"},
    {"key": "misting",     "label": "Permetezés", "field": "mistDays",    "last": "lastMisted",     "months": False, "icon": "💦"},
    {"key": "repotting",   "label": "Átültetés",  "field": "repotMonths", "last": "lastRepotted",   "months": True,  "icon": "🪴"},
]

WINTER_SEASON = (10, 11, 12, 1, 2)      # a felület szerint: októbertől februárig

# Az Event Calendar plasmoid (Plasma 6) biztonsági okból CSAK a saját
# adatmappájában lévő .ics fájlt hajlandó beolvasni:
#   ~/.local/share/plasma_org.kde.plasma.eventcalendar
# (a szkriptje: package/contents/scripts/icsjson.py → parse_calendar_url(),
#  LOCAL_ICS_DIR; minden más helyre „Local calendar file path is invalid”.)
# Ezért ide tükröt írunk – így a widget is látja a teendőket.
MIRROR_DIR = os.path.join(os.path.expanduser("~"), ".local", "share",
                          "plasma_org.kde.plasma.eventcalendar")
MIRROR_NAME = "florum.ics"


def mirror_path():
    """A widget által is olvasható másolat útvonala."""
    return os.path.join(MIRROR_DIR, MIRROR_NAME)


# ---------------------------------------------------------------- segédek
def parse_iso(text):
    try:
        return datetime.date.fromisoformat(str(text)[:10])
    except (ValueError, TypeError):
        return None


def add_days(d, n):
    return d + datetime.timedelta(days=int(n))


def add_months(d, months):
    total = d.month - 1 + int(months)
    year = d.year + total // 12
    month = total % 12 + 1
    napok = [31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
    return datetime.date(year, month, min(d.day, napok))


def is_winter_date(d):
    return d.month in WINTER_SEASON


def winter_enabled(settings, today):
    mode = str((settings or {}).get("winterMode") or "auto")
    if mode == "on":
        return True
    if mode == "off":
        return False
    return is_winter_date(today)



# ---------------------------------------------------------------- szezon
HONAPOK = ["január", "február", "március", "április", "május", "június", "július",
           "augusztus", "szeptember", "október", "november", "december"]

FERT_NEV = {
    "tapoldat": "tápoldat", "kaktusz": "kaktusz tápoldat",
    "viragzo": "virágzó tápoldat", "level": "levéltápoldat",
    "granulatum": "szemcsés műtrágya", "komposzt": "komposzt",
    "istallo": "istállótrágya", "semmi": "nincs",
}


def _honap(iso):
    try:
        return int(str(iso)[5:7])
    except (TypeError, ValueError):
        return 0


def honapban(month, from_month, to_month):
    """Hónap-ablak, átfordulással is (pl. 11→2)."""
    try:
        a, b = int(from_month), int(to_month)
    except (TypeError, ValueError):
        return True
    if not month:
        return True
    if a <= b:
        return a <= month <= b
    return month >= a or month <= b


def in_season(plant, iso=None):
    """Kerti növénynél a szezonon kívül nincs teendő (télen pihen)."""
    if not plant.get("garden"):
        return True
    m = _honap(iso) if iso else 0
    if not m:
        return True
    return honapban(m, plant.get("seasonFrom") or 4, plant.get("seasonTo") or 10)


def fert_ablak(plant):
    return (plant.get("fertFrom") or 3, plant.get("fertTo") or 9)


def fert_szoveg(plant):
    """„tápoldat · 2 ml / 1 l víz · N-P-K 7-3-5 · március–szeptember”"""
    if str(plant.get("fertKind") or "") == "semmi":
        return "nem tápoldatozom"
    reszek = []
    nev = FERT_NEV.get(str(plant.get("fertKind") or "tapoldat"), "tápoldat")
    reszek.append(nev)
    if plant.get("fertDose"):
        reszek.append(str(plant["fertDose"]))
    if plant.get("fertNpk"):
        reszek.append(str(plant["fertNpk"]))
    a, b = fert_ablak(plant)
    reszek.append("%s–%s" % (HONAPOK[a - 1], HONAPOK[b - 1]))
    return " · ".join(reszek)


def nap_engedve(plant, task, iso):
    """Szabad-e ezen a napon ezt a teendőt kitűzni (szezon + tápoldat-ablak)?"""
    if not in_season(plant, iso):
        return False
    if task.get("key") == "fertilizing":
        if str(plant.get("fertKind") or "") == "semmi":
            return False
        a, b = fert_ablak(plant)
        return honapban(_honap(iso), a, b)
    return True


def task_label(plant, task):
    """Kerten „Trágyázás”, szobában „Tápoldatozás”."""
    if task.get("key") == "fertilizing":
        kind = str(plant.get("fertKind") or "")
        if plant.get("garden") or kind in ("komposzt", "istallo"):
            return "Trágyázás"
        return "Tápoldatozás"
    return task.get("label", "")

def interval_at(plant, task, iso, wint):
    """Ugyanaz, mint a felületen az intervalAtDate()."""
    try:
        base = int(plant.get(task["field"]) or 0)
    except (TypeError, ValueError):
        base = 0
    if base <= 0:
        return 0
    # végleges kikapcsolás: „nem tápoldatozom”
    if task["key"] == "fertilizing" and str(plant.get("fertKind") or "") == "semmi":
        return 0
    if task["key"] == "watering" and plant.get("winterSlowdown", True) and wint and is_winter_date(iso):
        try:
            w = int(plant.get("waterWinter") or 0)
        except (TypeError, ValueError):
            w = 0
        if w > 0:
            return w
        return int(base * 1.5 + 0.5)          # Math.round(base * 1.5)
    return base


def plant_title(plant, alias_first=True):
    """A megjelenített név: saját név, ha van (a beállítás szerint)."""
    alias = str(plant.get("alias") or "").strip()
    name = str(plant.get("name") or "Növény").strip()
    if not alias:
        return name
    return alias if alias_first else name


def plant_alt(plant, alias_first=True):
    alias = str(plant.get("alias") or "").strip()
    name = str(plant.get("name") or "").strip()
    if not alias:
        return ""
    return name if alias_first else alias


# ---------------------------------------------------------------- ütemezés
def occurrences(plant, task, from_date, to_date, wint, today):
    """
    Egy növény + teendő esedékességei a [from_date, to_date] időszakban.
    A felület taskOccurrences()-ének a párja, azzal a különbséggel, hogy a
    legkorábbi nyitott (lejárt) esedékességet a mai napra hozza.
    """
    try:
        if int(plant.get(task["field"]) or 0) <= 0:
            return []
    except (TypeError, ValueError):
        return []

    # aki nem szereti a permetezést, annak nincs permetezés-eseménye
    if task["key"] == "misting" and permetviz and not permetviz.szereti(plant):
        return []

    anchor = parse_iso(plant.get(task["last"])) or parse_iso(plant.get("createdAt")) or today
    # Az `idx` az esedékesség sorszáma az utolsó alkalomtól számolva. Ez az
    # azonosító (UID) alapja: így a naptárbejegyzés UID-je NEM változik meg
    # akkor, amikor a dátum elmozdul (szundi, elvégzés) – a KDE Akonadi
    # ugyanis a cserélődő UID-ket tömeges törlésnek látja, és ettől a
    # plasmashell lefagyhat (KDE bug 526769 / 493415).
    out, cursor, guard = [], anchor, 0
    while guard < 500:
        guard += 1
        iv = interval_at(plant, task, cursor, wint)
        if not iv:
            break
        nxt = add_months(cursor, iv) if task["months"] else add_days(cursor, iv)
        if nxt <= cursor:
            break
        cursor = nxt

        # kerti növény: szezonon kívül (télen) nincs teendő – a szezon
        # első napján (pl. április 1.) folytatjuk
        if not in_season(plant, cursor):
            try:
                kezd = int(plant.get("seasonFrom") or 4)
            except (TypeError, ValueError):
                kezd = 4
            kov = datetime.date(cursor.year, kezd, 1)
            if kov <= cursor:
                kov = datetime.date(cursor.year + 1, kezd, 1)
            cursor = kov
            if cursor > to_date:
                break
            out.append({"due": cursor, "orig": cursor, "idx": len(out) + 1})
            continue

        # tápoldatozás: csak a beállított hónap-ablakban (alap: március–szeptember).
        # A tiltott időszakot átugorjuk, és az ablak első napján folytatjuk –
        # így a téli szünet után (pl. március 1.) jelenik meg az új esedékesség.
        if task["key"] == "fertilizing":
            a, b = fert_ablak(plant)
            if not honapban(cursor.month, a, b):
                kov = datetime.date(cursor.year, a, 1)
                if kov <= cursor:
                    kov = datetime.date(cursor.year + 1, a, 1)
                cursor = kov
                if cursor > to_date:
                    break
                out.append({"due": cursor, "orig": cursor, "idx": len(out) + 1})
                continue

        if cursor > to_date:
            break
        out.append({"due": cursor, "orig": cursor, "idx": len(out) + 1})
    if not out:
        return []

    # áthelyezés (a felület p.snooze mezője): a teendő a kiválasztott napra
    # kerül, a korábbi (elmaradt) esedékességek pedig törlődnek – a felület is
    # így viselkedik, amikor a naptárban elhúzod a teendőt.
    snooze = parse_iso((plant.get("snooze") or {}).get(task["key"]))
    if snooze and snooze >= today:
        out = [o for o in out if o["due"] >= today]
        if out:
            out[0]["due"] = snooze
            out[0]["snoozed"] = True
            out.sort(key=lambda o: o["due"])
        else:
            out = [{"due": snooze, "orig": snooze, "snoozed": True, "idx": 1}]

    # a lejárt teendő: csak a LEGUTOLSÓ elmaradt esedékesség jelenik meg a mai
    # napon (a korábbiak már történelem) – így egy növény + teendő párosból nem
    # lesz egyszerre tucatnyi mai esemény.
    mult = [o for o in out if o["due"] < today]
    if mult:
        utolso = mult[-1]
        utolso["late_for"] = utolso["due"]
        utolso["due"] = today
        out = [utolso] + [o for o in out if o["due"] >= today and o is not utolso]
    for occ in out:
        occ.setdefault("late_for", None)
    # a mai napra áthelyezett (lejárt) esemény se essen tiltott időszakra:
    # októberben nincs tápoldat, kerten szezonon kívül semmi
    out = [o for o in out if nap_engedve(plant, task, o["due"].isoformat())]
    return [o for o in out if from_date <= o["due"] <= to_date]


def collect(state, days=90, today=None):
    """Az összes esemény: [{date, plant, task, late_for, orig}, …] dátum szerint."""
    today = today or datetime.date.today()
    settings = state.get("settings") or {}
    wint = winter_enabled(settings, today)
    alias_first = settings.get("aliasFirst", True) is not False
    to_date = add_days(today, days)
    events = []
    for plant in state.get("plants") or []:
        for task in TASKS:
            for occ in occurrences(plant, task, today, to_date, wint, today):
                events.append({
                    "date": occ["due"],
                    "idx": occ.get("idx", 1),
                    "plant": plant,
                    "task": task,
                    "late_for": occ.get("late_for"),
                    "alias_first": alias_first,
                })
    events.sort(key=lambda e: (e["date"], e["task"]["key"], plant_title(e["plant"], e["alias_first"])))
    return events


# ---------------------------------------------------------------- iCalendar
def ics_escape(text):
    s = str(text or "")
    s = s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    return s.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def ics_fold(line):
    """RFC 5545: 75 oktétumonként tördelés, UTF-8-tudatosan (karakterenként mérve)."""
    if len(line.encode("utf-8")) <= 75:
        return line
    sorok, aktualis, hossz, elso = [], [], 0, True
    for ch in line:
        n = len(ch.encode("utf-8"))
        korlat = 75 if elso else 74
        if hossz + n > korlat:
            sorok.append("".join(aktualis))
            aktualis, hossz, elso = [], 0, False
        aktualis.append(ch)
        hossz += n
    if aktualis:
        sorok.append("".join(aktualis))
    return "\r\n ".join(sorok)


def vevent(ev, alarm_hour=8, stamp=None):
    plant, task = ev["plant"], ev["task"]
    day = ev["date"]
    title = plant_title(plant, ev["alias_first"])
    alt = plant_alt(plant, ev["alias_first"])
    pid = str(plant.get("id") or plant.get("name") or "noveny")
    # Szándékosan NEM tartalmaz dátumot és nevet: a UID akkor is ugyanaz marad,
    # ha a teendőt elvégzed, eltolod vagy átnevezed a növényt.
    uid_src = "%s|%s|%d" % (pid, task["key"], int(ev.get("idx") or 1))
    uid = "florum-" + hashlib.sha1(uid_src.encode("utf-8")).hexdigest()[:18] + "@" + UID_DOMAIN

    felirat = task_label(plant, task)
    summary = "%s %s – %s" % (task["icon"], felirat, title)
    viz = permetviz.rovid(plant) if (permetviz and task["key"] == "misting") else ""
    if viz:
        summary += " (%s)" % viz
    if ev.get("late_for"):
        summary += " (lejárt)"

    bits = []
    if alt:
        bits.append("Hivatalos név: " + alt)
    if plant.get("species"):
        bits.append("Faj: " + str(plant["species"]))
    if plant.get("room"):
        bits.append("Hely: " + str(plant["room"]))
    if ev.get("late_for"):
        bits.append("Eredeti esedékesség: " + ev["late_for"].isoformat() + " – ez már lejárt.")
    try:
        iv = interval_at(plant, task, day, True)
    except Exception:
        iv = 0
    if iv:
        bits.append("Ütem: %d %s" % (iv, "hónap" if task["months"] else "nap"))
    if permetviz and task["key"] == "misting":
        mondat = permetviz.mondat(plant)
        if mondat:
            bits.append(mondat)
    if plant.get("notes"):
        bits.append("Jegyzet: " + str(plant["notes"])[:300])
    links = [l for l in (plant.get("links") or []) if isinstance(l, dict) and l.get("url")]
    for l in links[:3]:
        bits.append("Link: " + (str(l.get("cim") or "") + " – " if l.get("cim") else "") + str(l["url"]))
    bits.append("Florum – növénygondozó")

    stamp = stamp or datetime.datetime.now(datetime.timezone.utc)
    lines = [
        "BEGIN:VEVENT",
        "UID:" + uid,
        "DTSTAMP:" + stamp.strftime("%Y%m%dT%H%M%SZ"),
        "DTSTART;VALUE=DATE:" + day.strftime("%Y%m%d"),
        "DTEND;VALUE=DATE:" + add_days(day, 1).strftime("%Y%m%d"),
        "SUMMARY:" + ics_escape(summary),
        "DESCRIPTION:" + ics_escape("\n".join(bits)),
        "CATEGORIES:" + ics_escape("Florum," + felirat),
        "TRANSP:TRANSPARENT",
        "STATUS:CONFIRMED",
        "PRIORITY:6" if not ev.get("late_for") else "PRIORITY:3",
        "X-FLORUM-TASK:" + task["key"],
        "X-FLORUM-PLANT:" + ics_escape(plant.get("name") or ""),
    ]
    if plant.get("room"):
        lines.append("LOCATION:" + ics_escape(plant["room"]))
    if links:
        try:
            lines.append("URL:" + str(links[0]["url"]))
        except Exception:
            pass
    if alarm_hour is not None and 0 <= int(alarm_hour) <= 23:
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:" + ics_escape("Florum: " + felirat + " – " + title),
            "TRIGGER;RELATED=START:PT%dH" % int(alarm_hour),
            "END:VALARM",
        ]
    lines.append("END:VEVENT")
    return lines


def build_ics(state, days=90, alarm_hour=8, today=None, calname=None, stamp=None):
    """A teljes .ics szöveg (CRLF sorvégekkel)."""
    today = today or datetime.date.today()
    stamp = stamp or datetime.datetime.now(datetime.timezone.utc)
    events = collect(state, days=days, today=today)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:" + PRODID,
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:" + ics_escape(calname or "Florum teendők"),
        "X-WR-CALDESC:" + ics_escape("Florum növénygondozó – öntözés, tápoldat, permetezés, átültetés"),
        "X-WR-TIMEZONE:" + TZ,
        "REFRESH-INTERVAL;VALUE=DURATION:PT1H",
        "X-PUBLISHED-TTL:PT1H",
    ]
    for ev in events:
        lines += vevent(ev, alarm_hour=alarm_hour, stamp=stamp)
    lines.append("END:VCALENDAR")
    return "\r\n".join(ics_fold(l) for l in lines) + "\r\n", len(events)


def _write_atomic(path, text):
    folder = os.path.dirname(os.path.abspath(path))
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def write_ics(path, state, days=90, alarm_hour=8, today=None, mirror=True):
    """A naptárfájl kiírása. `mirror=True` esetén az Event Calendar
    plasmoid adatmappájába is készül egy másolat (a widget csak onnan olvas)."""
    text, count = build_ics(state, days=days, alarm_hour=alarm_hour, today=today)
    _write_atomic(path, text)
    if mirror:
        try:
            _write_atomic(mirror_path(), text)
        except OSError:
            pass          # ha nem írható, a fő fájl akkor is elkészült
    return count


# ---------------------------------------------------------------- CLI
def main(argv=None):
    p = argparse.ArgumentParser(description="Florum → iCalendar (.ics) a KDE panelhez")
    p.add_argument("--data", default="", help="adatmappa (alapból: ~/.local/share/florum)")
    p.add_argument("--state", default="", help="közvetlenül a florum-data.json útvonala")
    p.add_argument("--out", default="", help="hova írja a .ics-t (alapból: <adatmappa>/florum.ics)")
    p.add_argument("--days", type=int, default=90, help="hány napra előre (alap: 90)")
    p.add_argument("--alarm", type=int, default=8, help="emlékeztető órája 0–23 (alap: 8)")
    p.add_argument("--print", action="store_true", help="a kimenetet írja a képernyőre")
    p.add_argument("--no-mirror", action="store_true",
                   help="ne készüljön másolat az Event Calendar plasmoid adatmappájába")
    args = p.parse_args(argv)

    data_dir = args.data or os.path.join(os.path.expanduser("~"), ".local", "share", "florum")
    state_path = args.state or os.path.join(data_dir, "florum-data.json")
    out_path = args.out or os.path.join(data_dir, "florum.ics")

    try:
        with open(state_path, encoding="utf-8") as fh:
            state = json.load(fh)
    except (OSError, ValueError):
        state = {"plants": [], "history": [], "settings": {}}

    if args.print:
        text, count = build_ics(state, days=args.days, alarm_hour=args.alarm)
        sys.stdout.write(text)
        return 0

    count = write_ics(out_path, state, days=args.days, alarm_hour=args.alarm,
                      mirror=not args.no_mirror)
    print("%d esemény → %s" % (count, out_path))
    if not args.no_mirror:
        print("másolat a widgetnek → %s" % mirror_path())
    return 0


if __name__ == "__main__":
    sys.exit(main())
