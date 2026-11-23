#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.13.0  ·  otthoni növénygondozó
#  Fájl:    florum.py
#  Szerep:  asztali indító: helyi szerver, fájlmentés, fotók, értesítések
#  Licenc:  szabadon használható, módosítható és terjeszthető
# ==============================================================

"""
Florum – otthoni növénygondozó (asztali indító + helyi adattár)
==============================================================

Ez a szkript indítja az appot, és **fájlba menti** az adatokat – nem a böngésző
tárhelyére. A mentés helye:

    ~/.local/share/florum/florum-data.json       (növények, napló, beállítások)
    ~/.local/share/florum/florum-data.bak.json   (előző állapot biztonsági másolata)
    ~/.local/share/florum/plants-db.json         (frissített növény-adatbázis, ha van)

A `--data-dir` kapcsolóval más mappát is megadhatsz (pl. pendrive-ra).

Csak a Python 3 szabványos könyvtárát használja – semmit nem kell telepíteni.

Használat:
    python3 florum.py              # elindul, megnyitja a böngészőt
    python3 florum.py --app        # Chrome/Chromium app-módban (keret nélküli ablak)
    python3 florum.py --data-dir ~/Dokumentumok/florum
    python3 florum.py --port 8765  # fix port
    python3 florum.py --no-browser # csak a szervert indítja
"""

import argparse
import base64
import datetime
import json
import os
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler

# Közös, előzményes mentés-modul (ugyanabban a mappában: mentes.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from mentes import Mentes
    from mentes import PERC_DB as PERC_DB_MENTES, NAPI_NAP as NAPI_NAP_MENTES, \
        HAVI_HONAP as HAVI_HONAP_MENTES
except Exception:                       # ha a fájl hiányzik, az app akkor is elindul
    Mentes = None
    PERC_DB_MENTES, NAPI_NAP_MENTES, HAVI_HONAP_MENTES = 20, 30, 12

# Külső naptár-források (Google Naptár, .ics linkek) – a saját teendők mellé
try:
    import naptar_forras
except Exception:                       # a Florum modul nélkül is induljon
    naptar_forras = None

# Fotónézegetők (feh, böngésző, chafa …) – a fotók megnyitása a Florumon kívül
try:
    import fotonezo
except Exception:
    fotonezo = None

# Új növény adatlapjának kiolvasása linkről / beillesztett szövegből
try:
    import novenykereso
except Exception:
    novenykereso = None

# Permetezés vize (növényenként) – közös tábla a felülettel és a naptárral
try:
    import permetviz
except Exception:                       # ha a fájl hiányzik, az app akkor is elindul
    permetviz = None

# Naptár-export (iCalendar) a KDE panel Digitális órájához
try:
    import naptar_ics
except Exception:                       # ha a fájl hiányzik, az app akkor is elindul
    naptar_ics = None

APP_NAME = "Florum"
APP_VERSION = "1.33.4"
MAIN_FILE = "florum.html"
DB_FILE = "plants-db.json"
DATA_FILE = "florum-data.json"
BACKUP_FILE = "florum-data.bak.json"
USER_DB_FILE = "plants-db.json"
PHOTO_DIR = "photos"
SNAPSHOT_DIR = "mentes"
try:
    from mentes import PERC_DB as PERC_DB_MENTES, NAPI_NAP as NAPI_NAP_MENTES, \
        HAVI_HONAP as HAVI_HONAP_MENTES
except Exception:
    PERC_DB_MENTES, NAPI_NAP_MENTES, HAVI_HONAP_MENTES = 20, 30, 12
NOTIFY_STATE = "notify-state.json"
ICS_FILE = "florum.ics"          # a KDE panel órájának (Akonadi iCal-erőforrás)
ICS_DAYS = 90                    # hány napra előre
ICS_ALARM = 8                    # emlékeztető órája a naptárban
MAX_BODY = 25 * 1024 * 1024  # 25 MB

CHROMIUM_BROWSERS = [
    "chromium", "chromium-browser", "google-chrome-stable", "google-chrome",
    "brave", "brave-browser", "microsoft-edge-stable", "microsoft-edge",
    "vivaldi-stable", "vivaldi", "ungoogled-chromium",
]


# ---------------------------------------------------------------- segédek
def app_dir() -> str:
    """A florum.html mappája."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def default_data_dir() -> str:
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "florum")


def atomic_write(path: str, text: str):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    if os.path.exists(path):
        try:
            shutil.copy2(path, path.replace(".json", ".bak.json"))
        except OSError:
            pass
    os.replace(tmp, path)


def empty_state():
    return {"plants": [], "history": [], "settings": {}, "meta": {}, "customDb": [], "tempLog": []}


def read_json(path, fallback=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return fallback


def parse_iso(text):
    try:
        return datetime.date.fromisoformat(str(text)[:10])
    except (ValueError, TypeError):
        return None


def add_months(d: datetime.date, months: int) -> datetime.date:
    total = d.month - 1 + months
    year = d.year + total // 12
    month = total % 12 + 1
    day = min(d.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                      31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime.date(year, month, day)


TASKS = [
    {"key": "watering", "label": "Öntözés", "field": "waterDays", "last": "lastWatered", "months": False},
    {"key": "fertilizing", "label": "Tápoldat", "field": "fertDays", "last": "lastFertilized", "months": False},
    {"key": "misting", "label": "Permetezés", "field": "mistDays", "last": "lastMisted", "months": False},
    {"key": "repotting", "label": "Átültetés", "field": "repotMonths", "last": "lastRepotted", "months": True},
]


# A téli időszak egységesen október 1. – február vége (a felülettel és a
# naptár-íróval egyezően): a naptár, a KDE-panel és a Python-oldali
# emlékeztető ugyanazt a határt használja.
WINTER_MONTHS = (10, 11, 12, 1, 2)


def is_winter(d: datetime.date) -> bool:
    return d.month in WINTER_MONTHS


def _honap_ablak(month, from_month, to_month):
    try:
        a, b = int(from_month), int(to_month)
    except (TypeError, ValueError):
        return True
    if not month:
        return True
    if a <= b:
        return a <= month <= b
    return month >= a or month <= b


def _szezonban(plant, day):
    """Kerti növénynél a szezonon kívül nincs teendő (télen pihen)."""
    if not plant.get("garden"):
        return True
    return _honap_ablak(day.month, plant.get("seasonFrom") or 4, plant.get("seasonTo") or 10)


def _fert_szoveg(plant):
    """A panel/értesítés rövid tápoldat-sora (adag + összetétel)."""
    nevek = {"tapoldat": "tápoldat", "kaktusz": "kaktusz tápoldat",
             "viragzo": "virágzó tápoldat", "level": "levéltápoldat",
             "granulatum": "szemcsés", "komposzt": "komposzt",
             "istallo": "istállótrágya"}
    kind = str(plant.get("fertKind") or "tapoldat")
    if kind == "semmi":
        return ""
    reszek = [nevek.get(kind, "tápoldat")]
    if plant.get("fertDose"):
        reszek.append(str(plant["fertDose"]))
    return " · ".join(reszek)


def _task_label(plant, task):
    if task.get("key") == "fertilizing":
        kind = str(plant.get("fertKind") or "")
        if plant.get("garden") or kind in ("komposzt", "istallo"):
            return "Trágyázás"
        return "Tápoldatozás"
    return task.get("label", "")


def compute_due(state, day=None):
    """Visszaadja a lejárt / mai / közeli teendőket (a felület logikája szerint)."""
    day = day or datetime.date.today()
    settings = state.get("settings") or {}
    winter_on = settings.get("winterSlowdown", True)
    horizon = int(settings.get("horizon") or 7)
    out = []
    for plant in state.get("plants") or []:
        snoozes = plant.get("snooze") or {}
        for task in TASKS:
            try:
                interval = int(plant.get(task["field"]) or 0)
            except (TypeError, ValueError):
                interval = 0
            if interval <= 0:
                continue
            # kerti növény: szezonon kívül (télen) nincs teendő
            if not _szezonban(plant, day):
                continue
            # tápoldatozás: csak a megadott hónapokban, „semmi” esetén soha
            if task["key"] == "fertilizing":
                if str(plant.get("fertKind") or "") == "semmi":
                    continue
                if not _honap_ablak(day.month, plant.get("fertFrom") or 3,
                                    plant.get("fertTo") or 9):
                    continue
            # aki nem szereti a permetezést (pihés/gyapjas levél), annak nincs
            # permetezés-teendője sem – se a listán, se a panelen, se a naptárban
            if task["key"] == "misting" and permetviz and not permetviz.szereti(plant):
                continue
            if task["key"] == "watering" and plant.get("winterSlowdown", True) and winter_on and is_winter(day):
                w = int(plant.get("waterWinter") or 0)
                interval = w if w > 0 else int(round(interval * 1.5))
            last = parse_iso(plant.get(task["last"]))
            if not last:
                continue
            due = add_months(last, interval) if task["months"] else last + datetime.timedelta(days=interval)
            sn = parse_iso(snoozes.get(task["key"]))
            if sn and due <= sn:
                due = sn
            days_left = (due - day).days
            out.append({
                "plant": plant.get("name", "?"),
                "room": plant.get("room", ""),
                "task": task["key"],
                "label": _task_label(plant, task),
                "due": due.isoformat(),
                "daysLeft": days_left,
                "late": days_left < 0,
                "today": days_left == 0,
                "soon": 0 < days_left <= horizon,
                # csak a permetezésnél van értelme: „esővízzel, reggel”
                "hint": (permetviz.hint(plant) if (permetviz and task["key"] == "misting") else ""),
                "mistWater": (permetviz.ertek(plant) if permetviz else ""),
            })
    return out


TASK_ICONS = {"watering": "💧", "fertilizing": "🌿", "misting": "💦", "repotting": "🪴"}


def panel_data(state, days=14, limit=12):
    """A KDE-panel widgethez (florum-panel) szánt, kicsi és gyors JSON.

    Csak a közeljövő (alap: 14 nap) teendőit adja vissza, a lejártak elöl,
    hogy a panelen egy pillantással látszódjon, mi esedékes.
    """
    due = compute_due(state)
    due.sort(key=lambda t: (t["due"], t["plant"], t["task"]))
    kozel = [t for t in due if t["daysLeft"] <= days]
    sorok = []
    for t in kozel[:limit]:
        sorok.append({
            "plant": t["plant"],
            "room": t.get("room", ""),
            "task": t["task"],
            "label": t["label"],
            "icon": TASK_ICONS.get(t["task"], "•"),
            "due": t["due"],
            "daysLeft": t["daysLeft"],
            "late": bool(t["late"]),
            "today": bool(t["today"]),
            "hint": t.get("hint", ""),
        })
    return {
        "ok": True,
        "app": APP_NAME,
        "version": APP_VERSION,
        "generated": datetime.datetime.now().replace(microsecond=0).isoformat(),
        "lateCount": len([t for t in due if t["late"]]),
        "todayCount": len([t for t in due if t["today"]]),
        "weekCount": len([t for t in due if t["daysLeft"] <= 7]),
        "rows": sorok,
    }


def _modul_van(nev):
    try:
        __import__(nev)
        return True
    except Exception:
        return False


def _naptar_nev(szoveg):
    """A naptár neve az .ics fejlécéből (X-WR-CALNAME)."""
    import re as _re
    m = _re.search(r"(?im)^X-WR-CALNAME:(.+)$", str(szoveg or ""))
    return m.group(1).strip() if m else ""


def _keres_parok(path):
    """GET-paraméterek egyszerű szótára (a self.path-ból)."""
    if "?" not in path:
        return {}
    out = {}
    for par in path.split("?", 1)[1].split("&"):
        if not par:
            continue
        k, _, v = par.partition("=")
        out[urllib.parse.unquote(k)] = urllib.parse.unquote(v)
    return out


def naptar_idoszak(path, alap_days=14, max_days=400):
    """A /api/calendars `from` és `days` paramétere → (kezdő dátum, napok).

    A naptárnézet nem a mai naptól indul: a hónap-rács első napja lehet a
    múlt hónapban, ezért kérhető kezdődátum. Hibás értéknél a mai nap.
    """
    par = _keres_parok(path)
    ma = datetime.date.today()
    tol = ma
    nyers = str(par.get("from") or "").strip()[:10]
    if nyers:
        try:
            tol = datetime.date.fromisoformat(nyers)
        except ValueError:
            tol = ma
    try:
        napok = int(par.get("days") or alap_days)
    except (TypeError, ValueError):
        napok = alap_days
    napok = max(1, min(int(max_days), napok))
    return tol, napok


def naptar_rows(state, data_dir, days=14, today=None):
    """A külső naptár-források (pl. Google Naptár) eseményei panel-sorként."""
    if naptar_forras is None:
        return [], []
    forrasok = (state.get("settings") or {}).get("calSources") or []
    if not forrasok:
        return [], []
    today = today or datetime.date.today()
    try:
        lista, allapot = naptar_forras.gyujt(forrasok, data_dir, days=days, ma=today)
    except Exception as exc:
        return [], [{"nev": "?", "hiba": str(exc), "darab": 0}]
    sorok = []
    for e in lista:
        kezdet = str(e.get("kezdet") or "")
        nap = kezdet[:10]
        if not nap:
            continue
        try:
            d = datetime.date.fromisoformat(nap)
        except ValueError:
            continue
        het = (d - today).days
        ido = kezdet[11:16] if len(kezdet) > 10 and not e.get("egesz") else ""
        sorok.append({
            "kind": "event",
            "plant": e.get("cim") or "(névtelen esemény)",   # a widget a „plant” mezőt címmé alakítja
            "room": e.get("hely") or "",
            "task": "event",
            "label": (e.get("naptar") or "Naptár") + (" " + ido if ido else ""),
            "icon": "📅",
            "due": kezdet,
            "daysLeft": het,
            "late": False,          # egy naptári esemény nem „lejárt”
            "today": het == 0,
        })
    return sorok, allapot


def foto_lista(state, data_dir=""):
    """A növények összes fotója egy listában (a naptárnézet/HTML is ezt használja).

    Visszaad: [{plantId, plant, alias, idx, total, file, url, taken, bytes, dataUrl}]
    A `url` mindig működik: fájl esetén /photos/…, data URL esetén /photo/…
    """
    out = []
    for plant in state.get("plants") or []:
        fotok = plant.get("photos") or []
        if not isinstance(fotok, list):
            continue
        pid = str(plant.get("id") or "")
        for idx, ph in enumerate(fotok):
            if not isinstance(ph, dict):
                continue
            fajl = str(ph.get("file") or "")
            ut = ""
            if fajl:
                ut = os.path.join(data_dir, fajl.replace("/", os.sep)) if data_dir else fajl
            if not fajl and not ph.get("dataUrl"):
                continue
            out.append({
                "plantId": pid,
                "plant": plant.get("name") or "Növény",
                "alias": plant.get("alias") or "",
                "idx": idx,
                "total": len(fotok),
                "file": fajl,
                "url": ("/" + fajl) if fajl else "/photo/%s/%d" % (pid, idx),
                "taken": str(ph.get("taken") or ""),
                "bytes": os.path.getsize(ut) if ut and os.path.isfile(ut) else 0,
                "dataUrl": bool(ph.get("dataUrl")),
            })
    # legfrissebb elöl
    out.sort(key=lambda f: (f["taken"] or "", f["plant"]), reverse=True)
    return out


def foto_fajl(plant, idx, data_dir):
    """A fotó tényleges fájlútvonala (data URL esetén ideiglenes fájlba írva).

    Visszaad: (útvonal, hiba). A hívó törölheti, ha `ideiglenes` is igaz.
    """
    fotok = plant.get("photos") or []
    if not isinstance(idx, int) or idx < 0 or idx >= len(fotok):
        return "", "nincs ilyen fotó"
    ph = fotok[idx] if isinstance(fotok[idx], dict) else {}
    fajl = str(ph.get("file") or "")
    if fajl:
        ut = os.path.join(data_dir, fajl.replace("/", os.sep))
        if os.path.isfile(ut):
            return ut, ""
        return "", "a fotófájl hiányzik: %s" % fajl
    durl = str(ph.get("dataUrl") or "")
    if not durl or "," not in durl:
        return "", "a fotó adatai hiányosak"
    head, b64 = durl.split(",", 1)
    kiterj = ".png" if "png" in head else ".webp" if "webp" in head else ".jpg"
    try:
        raw = base64.b64decode(b64, validate=False)
    except Exception:
        return "", "a kép dekódolása nem sikerült"
    tmp = os.path.join(tempfile.gettempdir(), "florum-foto-%s-%d%s"
                       % ("".join(ch for ch in str(plant.get("id") or "n") if ch.isalnum())[:24] or "n",
                          idx, kiterj))
    try:
        with open(tmp, "wb") as fh:
            fh.write(raw)
    except OSError as exc:
        return "", "nem sikerült kiírni: %s" % exc
    return tmp, ""


def foto_bytes(plant, idx, data_dir):
    """A fotó bájtjai + MIME-típus (a böngészős nézethez)."""
    ut, hiba = foto_fajl(plant, idx, data_dir)
    if hiba:
        return b"", "application/octet-stream", hiba
    kiterj = os.path.splitext(ut)[1].lower()
    ctype = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(kiterj, "image/jpeg")
    try:
        with open(ut, "rb") as fh:
            return fh.read(), ctype, ""
    except OSError as exc:
        return b"", ctype, str(exc)


# ================================================================
#  Böngészős nagy nézet: /foto  (a fotók a Florumon kívül, teljes képernyőn)
# ================================================================
FOTO_OLDAL = """<!DOCTYPE html>
<html lang="hu" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Florum – fotók</title>
<style>
  :root{--bg:#0b1210;--panel:#111b17;--line:#22322b;--ink:#e9f1eb;--muted:#93a89c;
        --green:#3f9b6b;--blue:#8fb0f5}
  *{box-sizing:border-box}
  html,body{margin:0;padding:0;background:var(--bg);color:var(--ink);
    font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
  header{display:flex;align-items:center;gap:12px;padding:14px 20px;border-bottom:1px solid var(--line);
    background:var(--panel);position:sticky;top:0;z-index:5}
  header h1{font-size:16px;margin:0;font-weight:650}
  header .sub{color:var(--muted);font-size:13px}
  header .grow{flex:1}
  .btn{border:1px solid var(--line);background:#16241e;color:var(--ink);font:inherit;font-size:13px;
    padding:7px 12px;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-flex;
    align-items:center;gap:6px}
  .btn:hover{border-color:var(--green)}
  .btn.primary{background:var(--green);border-color:transparent;color:#08120d;font-weight:700}
  main{padding:18px 20px 60px}
  .grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}
  figure{margin:0;background:var(--panel);border:1px solid var(--line);border-radius:14px;
    overflow:hidden;cursor:zoom-in;transition:.15s}
  figure:hover{transform:translateY(-2px);border-color:var(--green)}
  figure img{width:100%;height:170px;object-fit:cover;display:block;background:#0a0f0d}
  figcaption{padding:9px 11px;font-size:13px;display:flex;justify-content:space-between;gap:8px}
  figcaption .d{color:var(--muted);white-space:nowrap}
  .empty{padding:60px 20px;text-align:center;color:var(--muted)}
  .empty b{color:var(--ink);display:block;font-size:17px;margin-bottom:6px}
  /* nagy nézet */
  #lb{position:fixed;inset:0;background:rgba(4,8,6,.96);display:none;z-index:50;
    flex-direction:column;align-items:center;justify-content:center;padding:20px}
  #lb.open{display:flex}
  #lb img{max-width:min(96vw,1600px);max-height:78vh;object-fit:contain;border-radius:10px;
    box-shadow:0 20px 60px -20px #000}
  #lb .bar{display:flex;align-items:center;gap:10px;margin-top:14px;flex-wrap:wrap;justify-content:center}
  #lb .cap{color:var(--muted);font-size:13.5px}
  #lb .close{position:absolute;top:14px;right:16px;font-size:22px;line-height:1;
    background:none;border:0;color:var(--muted);cursor:pointer}
  #lb .close:hover{color:var(--ink)}
  #lb .nav{position:absolute;top:50%;transform:translateY(-50%);font-size:34px;background:none;
    border:0;color:var(--muted);cursor:pointer;padding:8px 14px}
  #lb .nav:hover{color:var(--ink)}
  #lb .prev{left:6px} #lb .next{right:6px}
  .hint{color:var(--muted);font-size:12.5px;margin-top:10px;text-align:center}
  #msg{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:#16241e;
    border:1px solid var(--line);color:var(--ink);padding:9px 14px;border-radius:10px;font-size:13px;
    opacity:0;transition:.2s;pointer-events:none;max-width:90vw}
  #msg.show{opacity:1}
</style>
</head>
<body>
<header>
  <span style="font-size:19px">🌿</span>
  <div><h1>Florum – fotók</h1><div class="sub" id="sub"></div></div>
  <div class="sub" id="extinfo"></div>
  <span class="grow"></span>
  <a class="btn" href="/">← Vissza a Florumhoz</a>
</header>
<main><div class="grid" id="grid"></div><div class="empty" id="empty" hidden>
  <b>Még nincs feltöltött fotó</b>
  A Florumban a növény kártyáján a 📷 gombbal tölthetsz fel képeket – utána itt is látod őket.
</div></main>
<div id="lb">
  <button class="close" id="lbClose" title="Bezárás (Esc)">✕</button>
  <button class="nav prev" id="lbPrev" title="Előző (←)">‹</button>
  <img id="lbImg" alt="">
  <button class="nav next" id="lbNext" title="Következő (→)">›</button>
  <div class="bar">
    <span class="cap" id="lbCap"></span>
    <a class="btn" id="lbOpen" href="#" target="_blank" rel="noopener">Eredeti kép</a>
    <a class="btn" id="lbDown" href="#" download>Letöltés</a>
    <button class="btn" id="lbExt">Megnyitás feh-ben / nézegetőben</button>
  </div>
  <div class="hint">← → lapozás · Esc bezárás · a „feh” gomb a gépedre telepített képmegnézőt indítja</div>
</div>
<div id="msg"></div>
<script>
const FOTOK = __FOTOK__;
const EXT = __EXT__;               // van-e telepített külső nézegető a szerveren
let i = 0;
const grid = document.getElementById('grid');
const empty = document.getElementById('empty');
document.getElementById('sub').textContent =
  FOTOK.length ? (FOTOK.length + ' kép · ' + new Set(FOTOK.map(f => f.plantId)).size + ' növény') :
  'nincs kép';
if (!FOTOK.length) { empty.hidden = false; }
function cim(f){ return (f.alias || f.plant) + (f.alias && f.alias !== f.plant ? ' (' + f.plant + ')' : ''); }
function datum(s){ return s ? s.slice(0, 10).replace(/-/g, '. ') + '.' : ''; }
function mb(n){ return n ? (n / 1024 / 1024).toFixed(1) + ' MB' : ''; }
grid.innerHTML = FOTOK.map((f, n) =>
  '<figure data-n="' + n + '">' +
    '<img src="' + f.url + '" alt="" loading="lazy">' +
    '<figcaption><span>' + cim(f) + '</span><span class="d">' + datum(f.taken) + '</span></figcaption>' +
  '</figure>').join('');
grid.addEventListener('click', ev => {
  const fig = ev.target.closest('figure');
  if (fig) nyit(+fig.dataset.n);
});
const lb = document.getElementById('lb'), lbImg = document.getElementById('lbImg'),
      lbCap = document.getElementById('lbCap'), lbOpen = document.getElementById('lbOpen'),
      lbDown = document.getElementById('lbDown');
function nyit(n){
  if (!FOTOK.length) return;
  i = (n + FOTOK.length) % FOTOK.length;
  const f = FOTOK[i];
  lbImg.src = f.url;
  lbOpen.href = f.url;
  lbDown.href = f.url;
  lbDown.setAttribute('download', (cim(f) + '-' + (f.taken || '')).replace(/[^A-Za-z0-9_.-]+/g, '_') + '.jpg');
  lbCap.textContent = cim(f) + ' · ' + datum(f.taken) + ' · ' + (i + 1) + '/' + FOTOK.length
                      + (f.bytes ? ' · ' + mb(f.bytes) : '');
  lb.classList.add('open');
}
function zar(){ lb.classList.remove('open'); lbImg.src = ''; }
document.getElementById('lbClose').onclick = zar;
document.getElementById('lbPrev').onclick = () => nyit(i - 1);
document.getElementById('lbNext').onclick = () => nyit(i + 1);
lb.addEventListener('click', ev => { if (ev.target === lb) zar(); });
document.addEventListener('keydown', ev => {
  if (!lb.classList.contains('open')) return;
  if (ev.key === 'Escape') zar();
  else if (ev.key === 'ArrowLeft') { ev.preventDefault(); nyit(i - 1); }
  else if (ev.key === 'ArrowRight') { ev.preventDefault(); nyit(i + 1); }
});
function uzenet(t){ const m = document.getElementById('msg'); m.textContent = t;
  m.classList.add('show'); clearTimeout(uzenet._t);
  uzenet._t = setTimeout(() => m.classList.remove('show'), 3200); }
const extBtn = document.getElementById('lbExt');
document.getElementById('extinfo').textContent = EXT.ok
  ? ('Külső nézegető: ' + EXT.viewer)
  : ('Külső nézegető: nincs – ' + (EXT.tipp || ''));
if (!EXT.ok) { extBtn.title = EXT.tipp || 'nincs külső nézegető'; }
extBtn.onclick = () => {
  const f = FOTOK[i];
  fetch('/api/open', { method:'POST', headers:{ 'Content-Type':'application/json' },
    body: JSON.stringify({ plantId: f.plantId, idx: f.idx }) })
    .then(r => r.json())
    .then(j => uzenet(j.ok ? ('Megnyitva: ' + j.viewer) : ('Nem sikerült: ' + (j.error || '?') +
             (j.tipp ? ' – ' + j.tipp : ''))))
    .catch(e => uzenet('Hiba: ' + e.message));
};
</script>
</body>
</html>
"""


def foto_oldal_html(state, data_dir):
    """A /foto oldal HTML-je (a fotólista beágyazva, hogy ne kelljen külön kérés)."""
    lista = json.dumps(foto_lista(state, data_dir), ensure_ascii=False)
    nev = ""
    if fotonezo is not None:
        par = [n for n, _, _ in fotonezo.elerheto(False)]
        nev = {"ok": bool(par), "viewer": (par[0] if par else ""),
               "tipp": "" if par else "sudo pacman -S feh"}
    else:
        nev = {"ok": False, "viewer": "", "tipp": "hiányzik a fotonezo.py"}
    return (FOTO_OLDAL.replace("__FOTOK__", lista)
                     .replace("__EXT__", json.dumps(nev, ensure_ascii=False)))


def normalize_state(raw):
    if not isinstance(raw, dict):
        return empty_state()
    return {
        "plants": raw.get("plants") if isinstance(raw.get("plants"), list) else [],
        "history": raw.get("history") if isinstance(raw.get("history"), list) else [],
        "settings": raw.get("settings") if isinstance(raw.get("settings"), dict) else {},
        "meta": raw.get("meta") if isinstance(raw.get("meta"), dict) else {},
        # sajat, a feluleten felvett fajok – ezek a letoltott/beepitett adatbazis fole kerulnek
        "customDb": raw.get("customDb") if isinstance(raw.get("customDb"), list) else [],
        # helyisegenkenti homerseklet-meresek (a felulet ezt kuldi)
        "tempLog": raw.get("tempLog") if isinstance(raw.get("tempLog"), list) else [],
    }


# ---------------------------------------------------------------- rendszer-integráció
def _shell_quote(szoveg):
    """Egy parancs-argumentum biztonságos idézése (sh)."""
    return "'" + str(szoveg).replace("'", "'\\''") + "'"


def notify_send(title, body):
    """Asztali értesítés (notify-send / kdialog / zenity)."""
    for exe, args in (
        ("notify-send", ["-a", APP_NAME, title, body]),
        ("kdialog", ["--title", title, "--passivepopup", body, "12"]),
        ("zenity", ["--notification", "--text", title + " " + body]),
    ):
        path = shutil.which(exe)
        if not path:
            continue
        try:
            subprocess.Popen([path] + args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except OSError:
            continue
    return False


def notify_available():
    return any(shutil.which(n) for n in ("notify-send", "kdialog", "zenity"))


def build_notify_text(state):
    due = compute_due(state)
    todo = [t for t in due if t["late"] or t["today"]]
    if not todo:
        return None, 0
    by_task = {}
    for t in todo:
        by_task.setdefault(t["label"], []).append(t["plant"])
    parts = []
    for label, names in by_task.items():
        uniq = []
        for n in names:
            if n not in uniq:
                uniq.append(n)
        shown = ", ".join(uniq[:4]) + ("…" if len(uniq) > 4 else "")
        parts.append("%s: %s" % (label, shown))
    late = len([t for t in due if t["late"]])
    head = "Ma %d teendő" % len(todo)
    if late:
        head += " (%d lejárt)" % late
    return head + " – " + "; ".join(parts), len(todo)


def autostart_path():
    cfg = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(cfg, "autostart", "florum.desktop")


def autostart_enabled():
    return os.path.exists(autostart_path())


def set_autostart(enable, script_path):
    path = autostart_path()
    if not enable:
        if os.path.exists(path):
            os.remove(path)
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    icon = os.path.join(os.path.dirname(os.path.abspath(script_path)), "florum.svg")
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        "Name=Florum",
        "Name[hu]=Florum növénygondozó",
        "Comment=Otthoni növények locsolása, tápoldatozása, átültetése",
        'Exec=python3 "%s" --app --notify' % os.path.abspath(script_path),
        "Icon=%s" % (icon if os.path.exists(icon) else "florum"),
        "Terminal=false",
        "X-GNOME-Autostart-enabled=true",
        "Categories=Utility;",
        "",
    ]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return True


# ---------------------------------------------------------------- szerver
class Handler(SimpleHTTPRequestHandler):
    """Statikus fájlok + apró JSON API a saját gépen."""

    data_dir = ""
    bundled_db_path = ""
    server_version = "Florum/" + APP_VERSION

    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

    # ---- segédek
    def _json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # a panel-widget (QML XMLHttpRequest) más eredetről kérdez – engedjük
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except ValueError:
            return None

    def _state_paths(self):
        return (
            os.path.join(self.data_dir, DATA_FILE),
            os.path.join(self.data_dir, BACKUP_FILE),
        )

    _mentes_obj = None

    def _mentes(self):
        """A közös mentés-modul példánya (előzményes pillanatképek)."""
        if Mentes is None:
            return None
        if self._mentes_obj is None:
            type(self)._mentes_obj = Mentes("florum", os.path.join(self.data_dir, SNAPSHOT_DIR))
        return self._mentes_obj

    ics_days = ICS_DAYS
    ics_alarm = ICS_ALARM

    def _ics_path(self):
        return os.path.join(self.data_dir, ICS_FILE)

    def _ics_opts(self, state=None):
        """A naptár beállításai: a felületen megadott érték, különben a parancssori."""
        days = int(getattr(self, "ics_days", ICS_DAYS))
        alarm = int(getattr(self, "ics_alarm", ICS_ALARM))
        settings = (state or {}).get("settings") or {}
        try:
            if settings.get("icsDays"):
                days = max(1, min(730, int(settings["icsDays"])))
        except (TypeError, ValueError):
            pass
        try:
            if settings.get("icsAlarm") not in (None, ""):
                alarm = max(0, min(23, int(settings["icsAlarm"])))
        except (TypeError, ValueError):
            pass
        return days, alarm

    def _write_ics(self, state):
        """A florum.ics újraírása (a KDE panel ezt olvassa). Hiba esetén csendben továbblép."""
        if naptar_ics is None:
            return 0
        days, alarm = self._ics_opts(state)
        # az Event Calendar plasmoid csak a saját adatmappájában lévő .ics-t
        # hajlandó beolvasni → oda is írunk másolatot (Beállításokban kikapcsolható)
        mirror = (state or {}).get("settings", {}).get("icsEventCal", True) is not False
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            return naptar_ics.write_ics(self._ics_path(), state, days=days, alarm_hour=alarm,
                                        mirror=mirror)
        except Exception:
            return 0

    def _ics_mirror_info(self):
        if naptar_ics is None:
            return {"icsMirror": "", "icsMirrorExists": False}
        p = naptar_ics.mirror_path()
        return {"icsMirror": p, "icsMirrorExists": os.path.exists(p)}

    def _user_db_path(self):
        return os.path.join(self.data_dir, USER_DB_FILE)

    def _active_db(self):
        user = read_json(self._user_db_path())
        if isinstance(user, dict) and isinstance(user.get("plants"), list) and user["plants"]:
            user.setdefault("origin", "letöltött")
            return user
        bundled = read_json(self.bundled_db_path, {})
        if isinstance(bundled, dict) and isinstance(bundled.get("plants"), list):
            bundled.setdefault("origin", "beépített")
            return bundled
        return {"plants": [], "version": "0", "count": 0, "origin": "nincs"}

    def _info(self):
        data_path, _ = self._state_paths()
        db = self._active_db()
        return {
            "app": APP_NAME,
            "appVersion": APP_VERSION,
            "fileVersion": file_version(),
            "versionMismatch": bool(file_version()) and file_version() != APP_VERSION,
            "dataDir": self.data_dir,
            "dataFile": data_path,
            "dataExists": os.path.exists(data_path),
            "dbFile": self._user_db_path() if db.get("origin") == "letöltött" else self.bundled_db_path,
            "dbVersion": db.get("version", "?"),
            "dbCount": len(db.get("plants", [])),
            "dbOrigin": db.get("origin", "?"),
            "dbUpdated": db.get("updated", ""),
            "photosDir": os.path.join(self.data_dir, PHOTO_DIR),
            "photosCount": len(foto_lista(
                normalize_state(read_json(data_path, {})), self.data_dir)),
            "photoPage": "/foto",
            "plantFetch": novenykereso is not None,
            "viewers": (fotonezo.osszefoglalo() if fotonezo is not None
                        else {"grafikus": [], "terminal": [], "tipp": "hiányzik a fotonezo.py"}),
            "notifyAvailable": notify_available(),
            "autostartEnabled": autostart_enabled(),
            "autostartFile": autostart_path(),
            "notifyFile": os.path.join(self.data_dir, NOTIFY_STATE),
            "icsFile": self._ics_path(),
            "icsExists": os.path.exists(self._ics_path()),
            "icsUrl": "/api/calendar.ics",
            "port": self.server.server_address[1] if getattr(self, "server", None) else 0,
            "szerverFile": os.path.join(self.data_dir, SZERVER_FILE),
            "icsDays": self._ics_opts(normalize_state(read_json(data_path, {})))[0],
            "icsAlarm": self._ics_opts(normalize_state(read_json(data_path, {})))[1],
            **self._ics_mirror_info(),
            "snapshotDir": os.path.join(self.data_dir, SNAPSHOT_DIR),
            "snapshotCount": len(self._mentes().lista()) if self._mentes() else 0,
        }

    # ---- GET
    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/snapshots":
            mt = self._mentes()
            if mt is None:
                self._json({"ok": False, "error": "A mentés-modul nem érhető el (mentes.py)."}, 501)
                return
            self._json({
                "ok": True,
                "dir": mt.mappa,
                "count": len(mt.lista()),
                "snapshots": mt.lista(),
                "policy": {"perc": PERC_DB_MENTES, "napi": NAPI_NAP_MENTES, "havi": HAVI_HONAP_MENTES},
            })
            return

        if path == "/api/snapshots/export":
            mt = self._mentes()
            if mt is None:
                self._json({"ok": False, "error": "nincs mentés-modul"}, 501)
                return
            blob = mt.csomag()
            name = "florum-mentes-%s.zip" % time.strftime("%Y%m%d-%H%M")
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="%s"' % name)
            self.send_header("Content-Length", str(len(blob)))
            self.end_headers()
            self.wfile.write(blob)
            return

        if path == "/api/state":
            data_path, backup_path = self._state_paths()
            raw = read_json(data_path)
            corrupted = False
            if raw is None and os.path.exists(data_path):
                corrupted = True
                raw = read_json(backup_path)
            state = normalize_state(raw)
            self._json({
                "ok": True,
                "state": state,
                "corrupted": corrupted,
                "info": self._info(),
            })
            return

        if path == "/api/db":
            self._json(self._active_db())
            return

        if path == "/api/info":
            self._json(self._info())
            return

        if path in ("/api/calendar.ics", "/florum.ics", "/api/calendar"):
            state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            if naptar_ics is None:
                self._json({"ok": False, "error": "A naptar_ics.py modul nem érhető el."}, 501)
                return
            ics_days, ics_alarm = self._ics_opts(state)
            text, count = naptar_ics.build_ics(state, days=ics_days, alarm_hour=ics_alarm)
            if path == "/api/calendar":
                self._json({"ok": True, "events": count, "file": self._ics_path(),
                            "download": "/api/calendar.ics"})
                return
            data = text.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.send_header("Content-Disposition", 'inline; filename="florum.ics"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        if path.startswith("/photos/"):
            return self._serve_photo(path[len("/photos/"):])

        # ---- böngészős nagy nézet: /foto (opcionálisan ?noveny=<id>)
        if path in ("/foto", "/foto/", "/galeria", "/galeria/"):
            state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            if "noveny=" in self.path:
                only = urllib.parse.unquote(self.path.split("noveny=", 1)[1].split("&")[0])
                if only:
                    state = dict(state)
                    state["plants"] = [p for p in (state.get("plants") or [])
                                       if str(p.get("id")) == only]
            oldal = foto_oldal_html(state, self.data_dir).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(oldal)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(oldal)
            return

        # ---- egy fotó bájtjai: /photo/<növény-azonosító>/<sorszám>
        if path.startswith("/photo/"):
            darab = path[len("/photo/"):].strip("/").split("/")
            if len(darab) != 2:
                self.send_error(404)
                return
            state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            plant = None
            for p in state.get("plants") or []:
                if str(p.get("id")) == darab[0]:
                    plant = p
                    break
            if plant is None:
                self.send_error(404)
                return
            try:
                idx = int(darab[1])
            except ValueError:
                self.send_error(404)
                return
            nyers, ctype, hiba = foto_bytes(plant, idx, self.data_dir)
            if hiba:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(nyers)))
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()
            self.wfile.write(nyers)
            return

        if path == "/api/photos":
            state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            lista = foto_lista(state, self.data_dir)
            nezok = {"ok": False, "viewer": "", "terminal": ""}
            if fotonezo is not None:
                g = fotonezo.elerheto(False)
                t = fotonezo.elerheto(True)
                nezok = {"ok": bool(g), "viewer": (g[0][0] if g else ""),
                         "terminal": (t[0][0] if t else ""),
                         "grafikuok": [n for n, _, _ in g],
                         "terminalok": [n for n, _, _ in t]}
            self._json({"ok": True, "count": len(lista), "photos": lista, "viewers": nezok})
            return

        if path == "/api/megnyitas":
            # A KDE panel-widget ezen keresztül nyitja meg a Florumot.
            # (A /api/open a FOTÓK megnyitására szolgál – ez más.)
            # Csak a helyi gépről fogadjuk el, mert a szerver 0.0.0.0-ra is köthet.
            kliens = str((self.client_address or ("",))[0])
            if kliens not in ("127.0.0.1", "::1", "::ffff:127.0.0.1", "localhost"):
                self._json({"ok": False, "error": "csak helyi gépből nyitható meg"}, 403)
                return
            par = _keres_parok(self.path)
            mod = str(par.get("mod") or "").strip().lower()
            if mod not in ("kde", "bongeszo", "auto"):
                mod = "auto"
            szkript = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "florum-megnyitas.sh")
            if not os.path.exists(szkript):
                self._json({"ok": False, "error": "hiányzik a florum-megnyitas.sh"}, 501)
                return
            if os.environ.get("FLORUM_OPEN_DRYRUN") == "1":
                self._json({"ok": True, "dryRun": True, "script": szkript, "mod": mod})
                return
            try:
                parancs = ["bash", szkript]
                if mod == "kde":
                    parancs.append("--kde")
                elif mod == "bongeszo":
                    parancs.append("--bongeszo")
                subprocess.Popen(parancs, cwd=os.path.dirname(szkript),
                                 stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL,
                                 start_new_session=True)
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
                return
            print("  🖥  panel: Florum megnyitása kérve (mód: %s)" % mod)
            self._json({"ok": True, "script": szkript, "mod": mod})
            return

        if path in ("/api/panel.json", "/api/panel"):
            state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            days = 14
            try:
                days = max(1, min(90, int((state.get("settings") or {}).get("panelDays") or 14)))
            except (TypeError, ValueError):
                days = 14
            adat = panel_data(state, days=days)
            esemenyek, forras_allapot = naptar_rows(state, self.data_dir, days=days)
            if esemenyek:
                # a naptár-események a saját teendők után, a beállított sorlimiten belül
                # dátum szerint összefésülve (a lejárt teendők maradnak elöl)
                egyutt = adat["rows"] + esemenyek
                egyutt.sort(key=lambda r: (0 if r.get("late") else 1,
                                           str(r.get("due") or "")[:10],
                                           0 if r.get("kind") != "event" else 1))
                adat["rows"] = egyutt
                adat["eventCount"] = len(esemenyek)
                adat["calendars"] = forras_allapot
            self._json(adat)
            return

        if path == "/api/calendars":
            state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            forrasok = (state.get("settings") or {}).get("calSources") or []
            if naptar_forras is None:
                self._json({"ok": False, "error": "a naptar_forras.py modul nem érhető el"}, 501)
                return
            tol, napok = naptar_idoszak(self.path)
            try:
                lista, allapot = naptar_forras.gyujt(forrasok, self.data_dir,
                                                     days=napok, ma=tol)
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
                return
            self._json({"ok": True, "sources": forrasok, "status": allapot,
                        "events": lista, "count": len(lista),
                        "from": tol.isoformat(), "days": napok,
                        "module": {"icalendar": _modul_van("icalendar"),
                                   "recurring_ical_events": _modul_van("recurring_ical_events")}})
            return

        if path == "/api/calendars/test":
            kerdes = self.path.split("?", 1)[1] if "?" in self.path else ""
            url = ""
            for pár in kerdes.split("&"):
                if pár.startswith("url="):
                    url = urllib.parse.unquote(pár[4:])
            if naptar_forras is None:
                self._json({"ok": False, "error": "modul hiányzik"}, 501)
                return
            szoveg, honnan, hiba = naptar_forras.beolvas(url, self.data_dir, max_age=0)
            ma = datetime.date.today()
            lista = naptar_forras.esemenyek(szoveg, ma, ma + datetime.timedelta(days=30),
                                            naptar="próba")
            self._json({"ok": not hiba and bool(szoveg), "honnan": honnan, "error": hiba,
                        "count": len(lista),
                        "first": lista[0]["cim"] if lista else "",
                        "naptarnev": _naptar_nev(szoveg)})
            return

        if path == "/api/due":
            state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            text, count = build_notify_text(state)
            self._json({"ok": True, "due": compute_due(state), "summary": text, "count": count})
            return

        if path in ("/", ""):
            self.path = "/" + MAIN_FILE

        return super().do_GET()

    def _serve_photo(self, name):
        safe = os.path.basename(name or "")
        if not safe or safe.startswith("."):
            self.send_error(404)
            return
        full = os.path.join(self.data_dir, PHOTO_DIR, safe)
        if not os.path.isfile(full):
            self.send_error(404)
            return
        ext = os.path.splitext(safe)[1].lower()
        ctype = {".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/jpeg")
        try:
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError:
            self.send_error(500)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    # ---- POST
    def do_POST(self):
        path = self.path.split("?")[0]
        body = self._read_body()

        if path == "/api/state":
            if body is None:
                self._json({"ok": False, "error": "Hibás kérés"}, 400)
                return
            state = normalize_state(body)
            if isinstance(body.get("meta"), dict):
                state["meta"] = body["meta"]
            try:
                os.makedirs(self.data_dir, exist_ok=True)
                data_path, _ = self._state_paths()
                atomic_write(data_path, json.dumps(state, ensure_ascii=False, indent=1))
                mt = self._mentes()
                if mt is not None:
                    mt.mentes(state)      # előzmény: perc / napi / havi szintek
                self._write_ics(state)    # naptár a KDE panelhez
            except OSError as exc:
                self._json({"ok": False, "error": "Írási hiba: %s" % exc}, 500)
                return
            self._json({"ok": True, "savedAt": state["meta"].get("savedAt"), "info": self._info()})
            return

        if path == "/api/restart":
            # Csak akkor indítjuk újra magunkat, ha NEM szolgáltatásként futunk
            # (systemd alatt a systemctl a helyes út – ott ne csináljunk versenyt).
            if os.environ.get("INVOCATION_ID") or os.environ.get("FLORUM_SZOLGALTATAS"):
                self._json({"ok": False, "mode": "systemd",
                            "error": "Szolgáltatásként fut – használd: systemctl --user restart florum-szerver"},
                           409)
                return
            parancs = [sys.executable, os.path.abspath(__file__)] + sys.argv[1:]
            if "--szerver" not in parancs:
                parancs.append("--szerver")
            try:
                # kis késleltetés: előbb szabaduljon fel a port, aztán induljon az új
                kagylo = "sleep 1; exec " + " ".join(_shell_quote(x) for x in parancs)
                subprocess.Popen(["/bin/sh", "-c", kagylo],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 start_new_session=True, cwd=os.getcwd())
            except Exception as exc:                     # noqa: BLE001
                self._json({"ok": False, "error": "Nem sikerült újraindítani: %s" % exc}, 500)
                return
            self._json({"ok": True, "indul": parancs[-4:], "verzio": APP_VERSION,
                        "uzenet": "A régi példány leáll, az új indul."})
            threading.Timer(0.8, lambda: os._exit(0)).start()
            return

        if path == "/api/calendars":
            if body is None or not isinstance(body.get("sources"), list):
                self._json({"ok": False, "error": "Hibás kérés"}, 400)
                return
            forrasok = []
            for f in body["sources"][:20]:
                if not isinstance(f, dict):
                    continue
                url = str(f.get("url") or "").strip()[:2000]
                if not url:
                    continue
                forrasok.append({
                    "id": str(f.get("id") or (naptar_forras.forras_azonosito(url)
                                              if naptar_forras else url[:16])),
                    "nev": str(f.get("nev") or f.get("name") or "Naptár")[:60],
                    "url": url,
                    "szin": str(f.get("szin") or "")[:20],
                    "enabled": f.get("enabled") is not False,
                })
            try:
                data_path, _ = self._state_paths()
                state = normalize_state(read_json(data_path, {}))
                state.setdefault("settings", {})["calSources"] = forrasok
                atomic_write(data_path, json.dumps(state, ensure_ascii=False, indent=1))
            except OSError as exc:
                self._json({"ok": False, "error": "Írási hiba: %s" % exc}, 500)
                return
            self._json({"ok": True, "sources": forrasok})
            return

        if path == "/api/snapshots/create":
            mt = self._mentes()
            if mt is None:
                self._json({"ok": False, "error": "nincs mentés-modul"}, 501)
                return
            data_path, _ = self._state_paths()
            cur = read_json(data_path, {})
            nev = mt.mentes(cur, szint="kezi", suffix="-kezi", kenyszer=True)
            self._json({"ok": bool(nev), "file": nev, "count": len(mt.lista())})
            return

        if path == "/api/snapshots/restore":
            mt = self._mentes()
            if mt is None:
                self._json({"ok": False, "error": "nincs mentés-modul"}, 501)
                return
            nev = str((body or {}).get("file", "")).strip()
            data_path, _ = self._state_paths()
            jelenlegi = read_json(data_path, {})
            try:
                adat, info = mt.visszaallit(nev or None, jelenlegi=jelenlegi)
            except FileNotFoundError as exc:
                self._json({"ok": False, "error": str(exc)}, 404)
                return
            except OSError as exc:
                self._json({"ok": False, "error": "olvasási hiba: %s" % exc}, 500)
                return
            state = normalize_state(adat)
            atomic_write(data_path, json.dumps(state, ensure_ascii=False, indent=1))
            self._write_ics(state)
            self._json({"ok": True, "restored": info["nev"], "at": info["ido"].strftime("%Y-%m-%d %H:%M"),
                        "state": state, "info": self._info()})
            return

        if path == "/api/db/update":
            # 1) URL-ről letöltés, 2) vagy közvetlenül kapott JSON
            payload = None
            source = "?"
            if isinstance(body, dict) and body.get("url"):
                url = str(body["url"]).strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    self._json({"ok": False, "error": "Csak http(s) cím használható."}, 400)
                    return
                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "Florum/" + APP_VERSION})
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        payload = json.loads(resp.read(MAX_BODY).decode("utf-8"))
                    source = url
                except (urllib.error.URLError, ValueError, OSError) as exc:
                    self._json({"ok": False, "error": "A letöltés nem sikerült: %s" % exc}, 502)
                    return
            elif isinstance(body, dict) and isinstance(body.get("plants"), list):
                payload = body
                source = "feltöltött fájl"
            else:
                self._json({"ok": False, "error": "Hiányzó url vagy plants lista."}, 400)
                return

            if not isinstance(payload, dict) or not isinstance(payload.get("plants"), list) or not payload["plants"]:
                self._json({"ok": False, "error": "A fájl nem érvényes növény-adatbázis (nincs benne plants lista)."}, 400)
                return
            cleaned = []
            for item in payload["plants"]:
                if not isinstance(item, dict) or not item.get("name"):
                    continue
                item.setdefault("latin", "")
                item.setdefault("aliases", [])
                item.setdefault("diseases", [])
                item.setdefault("pests", [])
                item.setdefault("tips", [])
                item.setdefault("light", "")
                for key in ("water", "waterWinter", "fert", "mist", "repot"):
                    try:
                        item[key] = int(item.get(key) or 0)
                    except (TypeError, ValueError):
                        item[key] = 0
                if not item.get("id"):
                    item["id"] = "%s-%d" % (str(item["name"]).lower().replace(" ", "-"), len(cleaned))
                cleaned.append(item)
            if not cleaned:
                self._json({"ok": False, "error": "Egyetlen érvényes növény sincs a fájlban."}, 400)
                return

            payload["plants"] = cleaned
            payload["count"] = len(cleaned)
            payload["origin"] = "letöltött"
            payload.setdefault("version", "egyedi")
            payload["downloadedFrom"] = source
            payload["downloadedAt"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
            try:
                os.makedirs(self.data_dir, exist_ok=True)
                atomic_write(self._user_db_path(), json.dumps(payload, ensure_ascii=False, indent=1))
            except OSError as exc:
                self._json({"ok": False, "error": "Írási hiba: %s" % exc}, 500)
                return
            self._json({"ok": True, "count": len(cleaned), "version": payload.get("version"), "source": source})
            return

        if path == "/api/photo":
            if not isinstance(body, dict) or not body.get("dataUrl"):
                self._json({"ok": False, "error": "Hiányzó kép."}, 400)
                return
            data_url = str(body["dataUrl"])
            if "," not in data_url:
                self._json({"ok": False, "error": "Érvénytelen képformátum."}, 400)
                return
            head, b64 = data_url.split(",", 1)
            ext = ".png" if "png" in head else ".webp" if "webp" in head else ".jpg"
            try:
                raw = base64.b64decode(b64, validate=False)
            except Exception:
                self._json({"ok": False, "error": "A kép dekódolása nem sikerült."}, 400)
                return
            if len(raw) > 12 * 1024 * 1024:
                self._json({"ok": False, "error": "A kép túl nagy (max 12 MB)."}, 400)
                return
            plant_id = "".join(ch for ch in str(body.get("plantId") or "noveny") if ch.isalnum() or ch in "-_")[:60]
            os.makedirs(os.path.join(self.data_dir, PHOTO_DIR), exist_ok=True)
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            name = "%s-%s%s" % (plant_id or "noveny", stamp, ext)
            try:
                with open(os.path.join(self.data_dir, PHOTO_DIR, name), "wb") as fh:
                    fh.write(raw)
            except OSError as exc:
                self._json({"ok": False, "error": "Írási hiba: %s" % exc}, 500)
                return
            self._json({"ok": True, "file": "photos/" + name, "bytes": len(raw),
                        "taken": datetime.date.today().isoformat()})
            return

        if path == "/api/plant/fetch":
            if novenykereso is None:
                self._json({"ok": False, "error": "hiányzik a novenykereso.py modul"}, 501)
                return
            if not isinstance(body, dict):
                self._json({"ok": False, "error": "Hibás kérés"}, 400)
                return
            nev = str(body.get("name") or "").strip()
            szoveg = str(body.get("text") or "").strip()
            url = str(body.get("url") or "").strip()
            if not szoveg and not url:
                self._json({"ok": False,
                            "error": "Adj meg egy linket, vagy illeszd be a cikk szövegét."}, 400)
                return
            if szoveg:
                entry = novenykereso.szovegbol(szoveg, nev=nev, forras="beillesztett szöveg")
                print("  🔎 adatlap kiolvasva beillesztett szövegből: %s" % entry["name"])
                self._json({"ok": True, "entry": entry, "source": "szöveg",
                            "note": entry.get("megjegyzes", "")})
                return
            entry, hiba = novenykereso.urlbol(url, nev)
            if hiba:
                print("  🔎 nem sikerült kiolvasni: %s" % url)
                self._json({"ok": False, "error": hiba, "needText": True,
                            "source": "link"}, 200)
                return
            print("  🔎 adatlap kiolvasva: %s → %s" % (url, entry["name"]))
            self._json({"ok": True, "entry": entry, "source": "link",
                        "note": entry.get("megjegyzes", "")})
            return

        if path == "/api/open":
            if fotonezo is None:
                self._json({"ok": False, "error": "hiányzik a fotonezo.py modul"}, 501)
                return
            if not isinstance(body, dict):
                self._json({"ok": False, "error": "Hibás kérés"}, 400)
                return
            # kétféle kérés: {file:"photos/x.jpg"} vagy {plantId, idx}
            ut, hiba = "", ""
            if body.get("file"):
                safe = os.path.basename(str(body["file"]))
                ut = os.path.join(self.data_dir, PHOTO_DIR, safe)
                if not os.path.isfile(ut):
                    ut, hiba = "", "nincs ilyen fotó: %s" % safe
            elif body.get("plantId") is not None:
                state = normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
                plant = None
                for p in state.get("plants") or []:
                    if str(p.get("id")) == str(body.get("plantId")):
                        plant = p
                        break
                if plant is None:
                    hiba = "nincs ilyen növény"
                else:
                    try:
                        idx = int(body.get("idx", 0))
                    except (TypeError, ValueError):
                        idx = 0
                    ut, hiba = foto_fajl(plant, idx, self.data_dir)
            else:
                hiba = "hiányzik a fotó azonosítója"
            if hiba:
                self._json({"ok": False, "error": hiba}, 404)
                return
            terminal = bool(body.get("terminal"))
            r = fotonezo.megnyit(ut, terminal=terminal, kedvenc=str(body.get("viewer") or ""))
            valasz = {"ok": r["ok"], "viewer": r["nev"], "file": os.path.basename(ut),
                      "error": r["hiba"], "tipp": r["tipp"]}
            if r["ok"]:
                print("  📷 fotó megnyitva (%s): %s" % (r["nev"], os.path.basename(ut)))
            self._json(valasz, 200 if r["ok"] else 503)
            return

        if path == "/api/photo/delete":
            if not isinstance(body, dict) or not body.get("file"):
                self._json({"ok": False, "error": "Hiányzó fájlnév."}, 400)
                return
            safe = os.path.basename(str(body["file"]))
            full = os.path.join(self.data_dir, PHOTO_DIR, safe)
            try:
                if os.path.isfile(full):
                    os.remove(full)
            except OSError as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
                return
            self._json({"ok": True})
            return

        if path == "/api/notify/test":
            text, count = build_notify_text(
                normalize_state(read_json(os.path.join(self.data_dir, DATA_FILE), {}))
            )
            title = APP_NAME + " – próbaértesítés"
            body_txt = text or "Minden rendben, ma nincs esedékes teendő."
            sent = notify_send(title, body_txt)
            self._json({"ok": sent, "sent": sent, "message": body_txt,
                        "available": notify_available()})
            return

        if path == "/api/autostart":
            enable = bool(body.get("enabled")) if isinstance(body, dict) else False
            try:
                state = set_autostart(enable, os.path.join(app_dir(), "florum.py"))
            except OSError as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
                return
            self._json({"ok": True, "enabled": state, "file": autostart_path()})
            return

        if path == "/api/db/reset":
            try:
                if os.path.exists(self._user_db_path()):
                    os.remove(self._user_db_path())
            except OSError as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
                return
            self._json({"ok": True, "info": self._info()})
            return

        if path == "/api/open-dir":
            try:
                subprocess.Popen(["xdg-open", self.data_dir],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._json({"ok": True, "dir": self.data_dir})
            except OSError as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
            return

        if path == "/api/quit":
            self._json({"ok": True})
            threading.Timer(0.3, lambda: os._exit(0)).start()
            return

        self._json({"ok": False, "error": "Ismeretlen végpont"}, 404)

    # ---- egyéb
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def log_message(self, fmt, *args):
        pass


def notify_worker(data_dir, stop_event):
    """Percekén ellenőrzi: eljött-e az értesítés ideje, és van-e teendő."""
    while not stop_event.is_set():
        try:
            state = normalize_state(read_json(os.path.join(data_dir, DATA_FILE), {}))
            settings = state.get("settings") or {}
            cfg = settings.get("notify") or {}
            if cfg.get("enabled"):
                target = str(cfg.get("time") or "08:00")
                now = datetime.datetime.now()
                today = now.date().isoformat()
                marker = read_json(os.path.join(data_dir, NOTIFY_STATE), {}) or {}
                if now.strftime("%H:%M") >= target and marker.get("lastDate") != today:
                    text, count = build_notify_text(state)
                    if text:
                        notify_send(APP_NAME + " - növénygondozó", text)
                    marker = {"lastDate": today, "lastCount": count or 0,
                              "lastRun": now.isoformat(timespec="seconds")}
                    try:
                        with open(os.path.join(data_dir, NOTIFY_STATE), "w", encoding="utf-8") as fh:
                            json.dump(marker, fh, ensure_ascii=False)
                    except OSError:
                        pass
        except Exception:
            pass
        stop_event.wait(45)


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


DEFAULT_PORT = 8777
PORT_RANGE = 10          # 8777 … 8786 – ha a 8777 foglalt, a widget is ezeket próbálja
SZERVER_FILE = "szerver.json"


VERSION_FILE = "VERSION"
HERE_DIR = os.path.dirname(os.path.abspath(__file__))


def file_version():
    """A gépen lévő VERSION fájl tartalma (a „fájl verziója”).

    Ez akkor térhet el az APP_VERSION-től, ha a programot frissítettük,
    de a háttérben még a RÉGI példány fut (a folyamat a memóriában
    tartja a kódot) – ilyenkor „felül új, lent régi” verzió látszik.
    """
    for ut in (os.path.join(HERE_DIR, VERSION_FILE),
               os.path.join(os.getcwd(), VERSION_FILE)):
        try:
            with open(ut, encoding="utf-8") as fh:
                v = fh.read().strip()
            if v:
                return v
        except OSError:
            continue
    return ""


def futo_peldany(port: int, host="127.0.0.1", timeout=1.5):
    """Válaszol-e már egy Florum a megadott porton? → /api/info szótára vagy None."""
    cim = "http://%s:%d/api/info" % ("127.0.0.1" if host in ("0.0.0.0", "") else host, port)
    try:
        with urllib.request.urlopen(cim, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def futo_folyamatok():
    """A futó florum.py folyamatok: [(pid, verzió?, cmdline)].

    A /proc-ot olvassuk (Linux) – így akkor is megtaláljuk a régi példányt,
    ha a szerver.json már elveszett.
    """
    talalt = []
    try:
        pidek = [d for d in os.listdir("/proc") if d.isdigit()]
    except OSError:
        return talalt
    sajat = os.getpid()
    for pid in pidek:
        if int(pid) == sajat:
            continue
        try:
            with open("/proc/%s/cmdline" % pid, "rb") as fh:
                cmd = [x.decode("utf-8", "replace") for x in fh.read().split(b"\x00") if x]
        except OSError:
            continue
        if not cmd:
            continue
        # csak a VALÓDI Florum-példány: python interpreter + florum.py szkript
        szkript = [x for x in cmd if os.path.basename(x) == "florum.py"]
        if not szkript:
            continue
        elso = os.path.basename(cmd[0])
        if not (elso.startswith("python") or elso == "florum.py"):
            continue                     # bash/sh parancssorból – nem a miénk
        talalt.append((int(pid), " ".join(cmd)))
    return talalt


def leallit_futo(data_dir="", port=DEFAULT_PORT, csend=False):
    """Leállítja a futó Florum-példányokat. Visszaad: (leállított pidek, üzenetek)."""
    leallitott, uzenetek = [], []

    # 1) a szerver.json-ban megadott pid (ha még él)
    adat = read_szerver_info(data_dir) if data_dir else None
    if adat and adat.get("pid") and adat.get("version") != APP_VERSION:
        uzenetek.append("a %s porton egy %s verziójú példány fut (pid %s)"
                        % (adat.get("port"), adat.get("version"), adat.get("pid")))

    # 2) minden florum.py folyamat (a --szerver és az asztali is)
    jeloltek = futo_folyamatok()
    for pid, cmd in jeloltek:
        try:
            os.kill(pid, signal.SIGTERM)
            leallitott.append(pid)
            if not csend:
                print("  ■ leállítva: pid %d – %s" % (pid, cmd[:110]))
        except OSError as exc:
            uzenetek.append("a %d. folyamatot nem sikerült leállítani: %s" % (pid, exc))
    if not jeloltek:
        uzenetek.append("nem fut Florum-folyamat")
    return leallitott, uzenetek


def port_free(port: int, host="127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((host if host not in ("", "0.0.0.0") else "0.0.0.0", port))
        except OSError:
            return False
    return True


def free_port(preferred: int = 0) -> int:
    """Előbb a kért (alap: 8777) portot adja, ha az foglalt, a következő szabadot.

    A panel-widget és a beállítások ezt a számot keresik – ezért nem lehet
    véletlenszerű: a 8777 a „Florum portja”.
    """
    if preferred and port_free(preferred):
        return preferred
    for i in range(1, PORT_RANGE):
        if port_free(preferred + i):
            return preferred + i
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def write_szerver_info(data_dir, port, host, url, mod):
    """A futó szerver leírója – ebből tudja bármi (diagnózis, panel), hol van."""
    ut = os.path.join(data_dir, SZERVER_FILE)
    adat = {
        "app": APP_NAME,
        "version": APP_VERSION,
        "port": port,
        "host": host,
        "url": url,
        "mode": mod,
        "pid": os.getpid(),
        "started": datetime.datetime.now().replace(microsecond=0).isoformat(),
    }
    try:
        with open(ut, "w", encoding="utf-8") as fh:
            json.dump(adat, fh, ensure_ascii=False, indent=1)
    except OSError:
        pass
    return ut


def read_szerver_info(data_dir):
    """A futó szerver leírója, ha él; egyébként None."""
    ut = os.path.join(data_dir, SZERVER_FILE)
    try:
        with open(ut, encoding="utf-8") as fh:
            adat = json.load(fh)
    except (OSError, ValueError):
        return None
    port = adat.get("port")
    if not isinstance(port, int) or not port_free(port):
        return None          # elavult leíró (a szerver már nem fut)
    return adat


def remove_szerver_info(data_dir):
    try:
        os.remove(os.path.join(data_dir, SZERVER_FILE))
    except OSError:
        pass


def find_browser():
    for name in CHROMIUM_BROWSERS:
        path = shutil.which(name)
        if path:
            return path
    return None


def open_browser(url: str, app_mode: bool, profile_dir: str):
    if app_mode:
        browser = find_browser()
        if browser:
            try:
                subprocess.Popen(
                    [
                        browser,
                        "--app=" + url,
                        "--user-data-dir=" + profile_dir,
                        "--class=" + APP_NAME,
                        "--window-size=1180,900",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
            except OSError:
                pass
        print("  (nem találtam Chromium-alapú böngészőt – a rendszer alap böngészőjét nyitom meg)")
    webbrowser.open(url, new=1)


def mentes_inditaskor(data_dir: str):
    """Indításkor egyszer lefuttatja a lejárt mentések törlését."""
    if Mentes is None:
        return
    try:
        Mentes("florum", os.path.join(data_dir, SNAPSHOT_DIR)).inditaskor()
    except OSError:
        pass


def foto_parancs(data_dir, keres="", terminal=False, nezo=""):
    """`--foto` kapcsoló: lista, vagy a találó növények fotóinak megnyitása."""
    ut = os.path.join(data_dir, DATA_FILE)
    if not os.path.isfile(ut):
        print("Nincs adatfájl ebben a mappában: %s" % data_dir)
        print("  (add meg a mappát: --data-dir /útvonal)")
        return 1
    state = normalize_state(read_json(ut, {}))
    lista = foto_lista(state, data_dir)
    if keres:
        q = keres.strip().lower()
        lista = [f for f in lista
                 if q in (f["plant"] or "").lower() or q in (f["alias"] or "").lower()
                 or q == f["plantId"].lower()]
    if not lista:
        print("Nincs fotó%s." % (" ehhez: %s" % keres if keres else ""))
        print("  A Florumban a növény kártyáján a 📷 gombbal tölthetsz fel képeket.")
        return 1
    if not keres and not terminal:
        # lista
        print("\n  🌿 Florum – fotók (%d)\n" % len(lista))
        for n, f in enumerate(lista, 1):
            cim = f["alias"] or f["plant"]
            if f["alias"] and f["alias"] != f["plant"]:
                cim += " (" + f["plant"] + ")"
            if len(cim) > 36:
                cim = cim[:35] + "…"
            if not f["bytes"]:
                meret = "adat"
            elif f["bytes"] < 1024 * 1024:
                meret = "%d kB" % max(1, round(f["bytes"] / 1024.0))
            else:
                meret = "%.1f MB" % (f["bytes"] / 1024.0 / 1024.0)
            print("  %2d. %-36s %s  %7s  %s" % (
                n, cim, (f["taken"] or "?")[:10], meret,
                f["file"] or ("/photo/%s/%d" % (f["plantId"], f["idx"]))))
        print("\n  Megnyitás:  python3 florum.py --foto \"NÖVÉNY NÉV\"")
        print("  Terminál:   python3 florum.py --foto \"NÖVÉNY\" --terminal")
        print("  Böngésző:   http://127.0.0.1:8777/foto\n")
        return 0
    if fotonezo is None:
        print("Hiányzik a fotonezo.py modul.")
        return 1
    if terminal and not fotonezo.elerheto(True):
        print("Nincs terminálos nézegető. Telepítés:  sudo pacman -S chafa")
        print("  (vagy böngészőben: http://127.0.0.1:8777/foto)")
        return 1
    hibak = 0
    for f in lista:
        ut, hiba = foto_fajl(
            [p for p in state.get("plants") or [] if str(p.get("id")) == f["plantId"]][0],
            f["idx"], data_dir)
        if hiba:
            print("✗ %s: %s" % (f["plant"], hiba))
            hibak += 1
            continue
        if terminal:
            szoveg, hiba = fotonezo.terminal_kep(ut, nezo)
            if hiba:
                print("✗ %s: %s" % (f["plant"], hiba))
                hibak += 1
            else:
                print(szoveg)
        else:
            r = fotonezo.megnyit(ut, kedvenc=nezo)
            if r["ok"]:
                print("✓ %s (%s) → %s" % (f["plant"], f["taken"] or "?", r["nev"]))
            else:
                print("✗ %s: %s" % (f["plant"], r["hiba"]))
                if r["tipp"]:
                    print("   " + r["tipp"])
                hibak += 1
    return 1 if hibak else 0


def main(argv=None):
    """Belépési pont. `argv` nélkül a sys.argv-t használja (teszthez átadható)."""
    parser = argparse.ArgumentParser(description="Florum növénygondozó – asztali indító")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help="port (alapértelmezés: %d; 0 = véletlen)" % DEFAULT_PORT)
    parser.add_argument("--host", default="127.0.0.1", help="figyelési cím (alapértelmezés: 127.0.0.1)")
    parser.add_argument("--data-dir", default="", help="saját adatmappa (alapértelmezés: ~/.local/share/florum)")
    parser.add_argument("--app", action="store_true", help="Chromium app-mód, keret nélküli ablak")
    parser.add_argument("--no-browser", action="store_true", help="ne nyisson böngészőt")
    parser.add_argument("--notify", action="store_true",
                        help="háttér-emlékeztetők (asztali értesítés) bekapcsolása")
    parser.add_argument("--szerver", action="store_true",
                        help="fejetlen szerver mód: nincs ablak, csak az adat a panelnek")
    parser.add_argument("--ics-days", type=int, default=ICS_DAYS,
                        help="hány napra készüljön a naptár (.ics), alap: 90")
    parser.add_argument("--ics-alarm", type=int, default=ICS_ALARM,
                        help="emlékeztető órája a naptárban (0-23), alap: 8")
    parser.add_argument("--no-ics", action="store_true",
                        help="ne írja ki a florum.ics naptárfájlt")
    parser.add_argument("--ne-indits", action="store_true",
                        help="ne indítsa el a háttérszervert (csak csatlakozzon)")
    parser.add_argument("--leallit", action="store_true",
                        help="a futó Florum-példány(ok) leállítása (pl. frissítés után)")
    parser.add_argument("--atkoltoztetes", default="", metavar="CÉL",
                        help="az adatok (növények, napló, képek, mentések) átmásolása egy "
                             "másik mappába; a program a régit NEM törli")
    parser.add_argument("--kert", action="store_true",
                        help="kerti növények ellenőrzése: melyik növény miért nincs a Kert fülön")
    parser.add_argument("--verzio", action="store_true",
                        help="verziók kiírása (program + fájl + futó szerver)")
    parser.add_argument("--foto", nargs="?", const="", default=None, metavar="NÉV",
                        help="fotók listázása/megnyitése (NÉV nélkül: lista; "
                             "pl. --foto \"Füge\" megnyitja a növény képeit)")
    parser.add_argument("--terminal", action="store_true",
                        help="a --foto a terminálban rajzolja ki a képet (chafa/viu)")
    parser.add_argument("--nezo", default="", metavar="PROGRAM",
                        help="melyik nézővel nyissa (feh, chafa, gwenview …)")
    args = parser.parse_args(argv)

    directory = app_dir()
    if not os.path.exists(os.path.join(directory, MAIN_FILE)):
        print("Hiba: nem találom a %s fájlt itt: %s" % (MAIN_FILE, directory))
        input("Nyomj Entert a kilépéshez…")
        return 1

    data_dir = os.path.abspath(os.path.expanduser(args.data_dir)) if args.data_dir else default_data_dir()
    try:
        os.makedirs(data_dir, exist_ok=True)
        probe = os.path.join(data_dir, ".write-test")
        with open(probe, "w", encoding="utf-8") as fh:
            fh.write("ok")
        os.remove(probe)
    except OSError as exc:
        print("Hiba: az adatmappa nem írható (%s): %s" % (data_dir, exc))
        return 1

    Handler.data_dir = data_dir
    Handler.bundled_db_path = os.path.join(directory, DB_FILE)
    Handler.ics_days = max(1, min(730, int(args.ics_days)))
    Handler.ics_alarm = max(0, min(23, int(args.ics_alarm)))
    mentes_inditaskor(data_dir)      # lejárt mentések törlése indításkor

    if not args.no_ics and naptar_ics is not None:
        try:
            _kezdo = normalize_state(read_json(os.path.join(data_dir, DATA_FILE), {}))
            naptar_ics.write_ics(os.path.join(data_dir, ICS_FILE), _kezdo,
                                 days=Handler.ics_days, alarm_hour=Handler.ics_alarm)
        except Exception as exc:
            print("  (a naptárfájl most nem készült el: %s)" % exc)

    # ---- --atkoltoztetes: adatok átvitele saját mappába
    if args.atkoltoztetes:
        cel = os.path.abspath(os.path.expanduser(args.atkoltoztetes))
        if cel == data_dir:
            print("  A cél ugyanaz, mint a jelenlegi adatmappa – nincs mit tenni.")
            return 0
        print("  Florum – adatok átköltöztetése")
        print("  honnan: %s" % data_dir)
        print("  ide:    %s" % cel)
        if not os.path.isdir(data_dir):
            print("\n  A jelenlegi adatmappa nem létezik – nincs mit átvinni.")
            print("  Egyszerűen indítsd így:  python3 florum.py --data-dir %s" % cel)
            return 0
        try:
            os.makedirs(cel, exist_ok=True)
            with open(os.path.join(cel, ".irhato"), "w", encoding="utf-8") as fh:
                fh.write("ok")
            os.remove(os.path.join(cel, ".irhato"))
        except OSError as exc:
            print("\n  ✗ A célmappa nem írható: %s" % exc)
            return 1

        # mit viszünk: az adatfájlok, a képek, a mentések, az értesítés-állapot
        # (a florum.ics nem kell: a program indításkor úgyis újraírja az új mappában)
        mit = [DATA_FILE, BACKUP_FILE, NOTIFY_STATE]
        mappak = [PHOTO_DIR, SNAPSHOT_DIR]
        atvitt, kihagyott, hibak = [], [], []
        for nev in mit:
            for forras in (os.path.join(data_dir, nev),
                           os.path.join(data_dir, nev.replace(".json", ".bak.json"))
                           if nev == DATA_FILE else ""):
                if not forras or not os.path.isfile(forras):
                    continue
                cel_ut = os.path.join(cel, os.path.basename(forras))
                try:
                    if os.path.abspath(forras) == os.path.abspath(cel_ut):
                        continue
                    shutil.copy2(forras, cel_ut)
                    atvitt.append((os.path.basename(forras), os.path.getsize(cel_ut)))
                except OSError as exc:
                    hibak.append("%s: %s" % (os.path.basename(forras), exc))
        for mappa in mappak:
            forras_mappa = os.path.join(data_dir, mappa)
            if not os.path.isdir(forras_mappa):
                continue
            cel_mappa = os.path.join(cel, mappa)
            darab, meret = 0, 0
            for gyoker, _mappak, fajlok in os.walk(forras_mappa):
                for fajl in fajlok:
                    ut = os.path.join(gyoker, fajl)
                    rel = os.path.relpath(ut, forras_mappa)
                    cel_ut = os.path.join(cel_mappa, rel)
                    try:
                        os.makedirs(os.path.dirname(cel_ut), exist_ok=True)
                        if os.path.abspath(ut) == os.path.abspath(cel_ut):
                            continue
                        shutil.copy2(ut, cel_ut)
                        darab += 1
                        meret += os.path.getsize(cel_ut)
                    except OSError as exc:
                        hibak.append("%s/%s: %s" % (mappa, rel, exc))
            if darab:
                atvitt.append(("%s/ (%d fájl)" % (mappa, darab), meret))

        print()
        if atvitt:
            for nev, meret in atvitt:
                print("  ✓ %-34s %8.1f kB" % (nev, meret / 1024.0))
        else:
            print("  · nem volt mit átvinni – a régi mappában még nincs adat.")
            print("    Egyszerűen indítsd így:  python3 florum.py --data-dir %s" % cel)
        for h in hibak:
            print("  ✗ %s" % h)
        for k in kihagyott:
            print("  · kihagyva: %s" % k)

        # ellenőrzés: a növények száma egyezik-e
        regi_allapot = normalize_state(read_json(os.path.join(data_dir, DATA_FILE), {}))
        uj_allapot = normalize_state(read_json(os.path.join(cel, DATA_FILE), {}))
        rn, un = len(regi_allapot.get("plants") or []), len(uj_allapot.get("plants") or [])
        rh, uh = len(regi_allapot.get("history") or []), len(uj_allapot.get("history") or [])
        print()
        print("  ellenőrzés: növény %d → %d · naplóbejegyzés %d → %d" % (rn, un, rh, uh))
        if (rn, rh) != (un, uh):
            print("  ✗ Az átvitel nem teljes – a régi mappa érintetlen, semmi nem veszett el.")
            return 1

        print("""
  Kész. A régi mappa MEGMARAD (biztonsági másolat), semmit nem töröltem.

  Mostantól MINDIG ezzel a mappával indítsd:

      python3 florum.py --data-dir %s

  Hogy ne kelljen mindig beírni, két lehetőség:

   1) a megnyitó megjegyzi (ajánlott):
        bash florum-atkoltoztetes.sh %s
      (ez ugyanezt teszi, és beírja a florum-adat.conf-ba, amit a
       florum-megnyitas.sh, a frissítő és a szolgáltatás is használ)

   2) kézzel, állandóra:
        export FLORUM_DATA=%s        # a ~/.bashrc végére
        systemctl --user stop florum-szerver
        systemctl --user edit florum-szerver     # ExecStart=… --data-dir %s

  Ha a régi mappát meg akarod tartani biztonsági másolatként, ne töröld.
  Ha biztosan jó, később bátran törölheted: %s
""" % (cel, cel, cel, cel, data_dir))
        return 0

    # ---- --kert: miért nincs (vagy van) növény a Kert fülön?
    if args.kert:
        allapot = normalize_state(read_json(os.path.join(data_dir, DATA_FILE), {}))
        növények = allapot.get("plants") or []
        print("  Florum – kerti növények ellenőrzése")
        print("  adatfájl: %s" % os.path.join(data_dir, DATA_FILE))
        if not növények:
            print("\n  Nincs egyetlen növény sem az adatfájlban.")
            print("  Indítsd el a Florumot (python3 florum.py), és vedd fel a növényt.")
            return 0
        print("  összes növény: %d\n" % len(növények))
        kerti = 0
        for p_ in növények:
            nev = str(p_.get("name") or "(névtelen)")
            hely = str(p_.get("room") or "")
            jelolo = bool(p_.get("garden"))
            hely_kert = any(k in hely.lower() for k in ("kert", "üvegház", "uveghaz"))
            if jelolo or hely_kert:
                kerti += 1
                print("  ✓ %-22s hely: %-14s kerti: IGEN%s" %
                      (nev, hely or "—",
                       "  · szezon %s–%s" % (p_.get("seasonFrom") or 4, p_.get("seasonTo") or 10)))
            else:
                print("  ✗ %-22s hely: %-14s kerti: nem   ← ezért nincs a Kert fülön" %
                      (nev, hely or "—"))
        print("\n  kerti növény: %d / %d" % (kerti, len(növények)))
        if kerti == 0:
            print("\n  Mit tegyél?  A felületen: Növények fül → ceruza (szerkesztés) →")
            print("  „Hely” = Kert  →  Mentés.  A növény attól kezdve a Kert fülön van.")
            print("  Vagy a Kert fül alján: „Áthelyezés a kertbe” → kattints a növényre.")
        return 0

    # ---- --verzio: mi fut, és mi van a gépen?
    if args.verzio:
        fajl = file_version()
        print("  Florum – verziók")
        print("    ez a program:      %s" % APP_VERSION)
        print("    VERSION fájl:      %s" % (fajl or "(nincs)"))
        mar = futo_peldany(args.port, args.host)
        if mar:
            print("    futó szerver:      %s  (%d-es port, %s)"
                  % (mar.get("appVersion", "?"), args.port, mar.get("dataDir", "?")))
            if str(mar.get("appVersion")) != APP_VERSION:
                print("    ⚠ ELTÉRÉS – a régi példány még fut!  →  python3 florum.py --leallit")
        else:
            print("    futó szerver:      nincs (%d-es port)" % args.port)
        if len(futo_folyamatok()) > 1:
            print("    futó folyamatok:")
            for pid, cmd in futo_folyamatok():
                print("      %6d  %s" % (pid, cmd[:100]))
        if fajl and fajl != APP_VERSION:
            print("    ⚠ a VERSION fájl (%s) és a program (%s) eltér" % (fajl, APP_VERSION))
        return 0

    # ---- --leallit: a futó példányok leállítása
    if args.leallit:
        print("  Florum – futó példányok leállítása")
        pidek, uzenetek = leallit_futo(data_dir, args.port)
        for u in uzenetek:
            print("  · " + u)
        if pidek:
            print("  Kész: %d folyamat leállítva. Indíthatod újra: python3 florum.py --szerver"
                  % len(pidek))
        else:
            print("  Nem fut semmi – nincs mit leállítani.")
        return 0

    # ---- --foto: a fotók listázása / megnyitása (a szerver nélkül is működik)
    if args.foto is not None:
        return foto_parancs(data_dir, args.foto, args.terminal, args.nezo)

    if args.szerver:
        args.no_browser = True

    # ---- fut-e már valaki a kért porton? (a „felül új, lent régi” tipikus oka)
    if args.port and not args.ne_indits:
        mar = futo_peldany(args.port, args.host)
        if mar:
            regi_ver = str(mar.get("appVersion") or "?")
            print()
            print("  ⚠  A %d-es porton MÁR FUT egy Florum – verzió: %s" % (args.port, regi_ver))
            if regi_ver != APP_VERSION:
                print("     Ez a program most %s – a régi példány a memóriában" % APP_VERSION)
                print("     tartja a régi kódot, ezért mutat vegyes verziót.")
                print("     Megoldás:")
                print("       python3 florum.py --leallit")
                print("       (vagy: systemctl --user restart florum-szerver)")
            else:
                print("     Ugyanez a verzió fut – valószínűleg a böngészőablak már nyitva van.")
            print()

    port = free_port(args.port) if args.port else free_port(0)

    def make_handler(*a, **kw):
        return Handler(*a, directory=directory, **kw)

    try:
        httpd = Server((args.host, port), make_handler)
    except OSError as exc:
        print("Nem sikerült elindítani a szervert a(z) %s:%s címen: %s" % (args.host, port, exc))
        return 1

    host_for_url = "127.0.0.1" if args.host in ("0.0.0.0", "") else args.host
    url = "http://%s:%d/" % (host_for_url, port)
    profile_dir = os.path.join(data_dir, "browser-profile")

    print()
    print("  🌿  %s %s – növénygondozó" % (APP_NAME, APP_VERSION))
    print("  " + "-" * 52)
    print("  Fut itt:      %s" % url)
    print("  Adatok itt:   %s" % os.path.join(data_dir, DATA_FILE))
    print("  Adatbázis:    %s" % os.path.join(directory, DB_FILE))
    print("  Naptár:       %s" % (os.path.join(data_dir, ICS_FILE) if not args.no_ics
                                   else "(kikapcsolva)"))
    print("  Mód:          %s" % ("szerver (háttér)" if args.szerver else "asztali"))
    print("  Leállítás:    Ctrl+C")
    print()
    write_szerver_info(data_dir, port, args.host, url,
                       "szerver" if args.szerver else "asztali")

    if args.notify:
        stop_event = threading.Event()
        threading.Thread(target=notify_worker, args=(data_dir, stop_event), daemon=True).start()
        print("  Értesítés:    bekapcsolva (a felületen beállított időpontban)"
              if notify_available() else "  Értesítés:    nincs notify-send/kdialog a rendszeren")

    if not args.no_browser:
        threading.Timer(0.45, lambda: open_browser(url, args.app, profile_dir)).start()

    # SIGHUP (pl. terminál bezárása) ne állítsa le a háttérszervert
    try:
        signal.signal(signal.SIGHUP, signal.SIG_IGN)
    except (AttributeError, OSError, ValueError):
        pass

    # SIGTERM (systemd stop) esetén is takarítsunk: töröljük a leírót
    def _leallitas(*_):
        raise KeyboardInterrupt
    for jel in ("SIGTERM", "SIGINT"):
        try:
            signal.signal(getattr(signal, jel), _leallitas)
        except (AttributeError, OSError, ValueError):
            pass

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Viszlát! 🌱")
    finally:
        httpd.server_close()
        remove_szerver_info(data_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
