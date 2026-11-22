#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Florum – külső naptár-források (Google Naptár, Outlook, Nextcloud, .ics fájl)
=============================================================================

A Florum a saját teendői mellé be tudja olvasni a **már meglévő** naptárait, és
ezeket ugyanabban a panel-widgetben mutatja. Nem kell hozzá OAuth, fiók,
Akonadi vagy PIM-plugin: elég a naptár **iCal (.ics) címe**.

Google Naptár → jobb oldalt a naptár mellett ⋮ → „Beállítások és megosztás” →
„A naptár integrálása” → **„Titkos cím iCal formátumban”** → ezt a linket kell
bemásolni. (Nem jelszó, csak olvasásra jó, bármikor visszavonható.)

Mit tud:
  * `http(s)://…ics` letöltése (időtúllépéssel) és **helyi gyorsítótárba** írása
    (`~/.local/share/florum/naptar-forrasok/<azonosító>.ics`) – ha a hálózat
    kiesik, a legutóbbi letöltésből dolgozik;
  * `file:///…ics` és sima helyi útvonal olvasása;
  * események kigyűjtése egy időszakra: egész napos és időpontos események,
    ismétlődések (NAPI/HETI/HAVI/ÉVI, INTERVAL, COUNT, UNTIL) és EXDATE;
  * ha van `icalendar` + `recurring_ical_events` modul, azt használja (pontosabb),
    különben a beépített, egyszerű feldolgozóra vált.

Használat parancssorból:
    python3 naptar_forras.py --url "https://calendar.google.com/…/basic.ics"
    python3 naptar_forras.py --lista
"""

import datetime
import hashlib
import json
import os
import re
import urllib.error
import urllib.request

APP = "Florum"
FORRAS_DIR = "naptar-forrasok"
CACHE_FILE = "forras-allapot.json"
MAX_BYTES = 10 * 1024 * 1024        # 10 MiB, ugyanaz a korlát, mint az icsjson.py-nál
USER_AGENT = "Florum/1.22 (+iCal olvasó)"


# --------------------------------------------------------------------- segédek
def forras_azonosito(url):
    """Rövid, stabil azonosító a gyorsítótár-fájlhoz."""
    return hashlib.sha1(str(url).encode("utf-8")).hexdigest()[:16]


def forras_dir(data_dir):
    return os.path.join(data_dir, FORRAS_DIR)


def is_web(url):
    return bool(re.match(r"^https?://\S+$", str(url or ""), re.I))


def is_fajl(url):
    u = str(url or "").strip()
    return u.startswith("file://") or (u and not is_web(u) and os.path.exists(os.path.expanduser(u)))


def fajl_utvonal(url):
    u = str(url or "").strip()
    if u.lower().startswith("file://"):
        return os.path.expanduser(u[7:])
    return os.path.expanduser(u)


# --------------------------------------------------------------- letöltés / cache
def _cache_ut(data_dir, url):
    return os.path.join(forras_dir(data_dir), forras_azonosito(url) + ".ics")


def beolvas(url, data_dir="", timeout=12, max_age=1800):
    """A forrás tartalma: (szöveg, honnan, hibaüzenet).

    `honnan`: "hálózat" / "gyorsítótár" / "fájl".  Ha a hálózat nem elérhető,
    a gyorsítótárból dolgozik (max_age másodpercnél fiatalabbat használ előbb).
    """
    url = str(url or "").strip()
    if not url:
        return "", "", "üres cím"

    if is_fajl(url):
        ut = fajl_utvonal(url)
        try:
            with open(ut, "rb") as fh:
                adat = fh.read(MAX_BYTES + 1)
        except OSError as exc:
            return "", "", "a fájl nem olvasható: %s" % exc
        return adat[:MAX_BYTES].decode("utf-8", "replace"), "fájl", ""

    if not is_web(url):
        return "", "", "csak http(s):// vagy helyi fájl lehet"

    gyors = _cache_ut(data_dir, url) if data_dir else ""
    friss = False
    if gyors and os.path.exists(gyors):
        friss = (datetime.datetime.now().timestamp() - os.path.getmtime(gyors)) < max_age

    if friss and max_age > 0:
        try:
            with open(gyors, encoding="utf-8", errors="replace") as fh:
                return fh.read(), "gyorsítótár", ""
        except OSError:
            pass

    ker = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                               "Accept": "text/calendar, text/plain, */*"})
    try:
        with urllib.request.urlopen(ker, timeout=timeout) as valasz:
            adat = valasz.read(MAX_BYTES + 1)
        if len(adat) > MAX_BYTES:
            return "", "", "a naptár túl nagy (> 10 MiB)"
        szoveg = adat.decode("utf-8", "replace")
        if gyors:
            try:
                os.makedirs(os.path.dirname(gyors), exist_ok=True)
                with open(gyors, "w", encoding="utf-8", newline="") as fh:
                    fh.write(szoveg)
            except OSError:
                pass
        return szoveg, "hálózat", ""
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
        if gyors and os.path.exists(gyors):
            try:
                with open(gyors, encoding="utf-8", errors="replace") as fh:
                    return fh.read(), "gyorsítótár", "letöltés nem sikerült (%s) – a mentett példány" % exc
            except OSError:
                pass
        return "", "", "letöltés nem sikerült: %s" % exc


# ------------------------------------------------------------------ iCal olvasás
def _kibont(szoveg):
    """A 75 oktétumos tördelés (fold) visszabontása."""
    sorok = []
    for sor in str(szoveg).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if sor.startswith((" ", "\t")) and sorok:
            sorok[-1] += sor[1:]
        else:
            sorok.append(sor)
    return sorok


def _ertek(sor):
    """'DTSTART;VALUE=DATE:20261024' → ('DTSTART', {'VALUE': 'DATE'}, '20261024')"""
    if ":" not in sor:
        return None
    fej, _, ertek = sor.partition(":")
    reszek = fej.split(";")
    nev = reszek[0].upper()
    par = {}
    for r in reszek[1:]:
        if "=" in r:
            k, _, v = r.partition("=")
            par[k.upper()] = v.strip('"').upper()
    return nev, par, ertek


def _datum(ertek, par):
    """iCal dátum → date vagy datetime (időzóna nélkül, helyi idő szerint)."""
    ertek = ertek.strip()
    if par.get("VALUE") == "DATE" or re.match(r"^\d{8}$", ertek):
        try:
            return datetime.date(int(ertek[0:4]), int(ertek[4:6]), int(ertek[6:8]))
        except ValueError:
            return None
    m = re.match(r"^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})?(Z)?$", ertek)
    if not m:
        return None
    try:
        dt = datetime.datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)),
                               int(m.group(4)), int(m.group(5)), int(m.group(6) or 0))
    except ValueError:
        return None
    if m.group(7):                      # UTC → helyi idő
        dt = dt.replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)
    return dt


def _rruleszabaly(ertek):
    """RRULE → dict (FREQ, INTERVAL, COUNT, UNTIL, BYDAY)."""
    out = {}
    for resz in str(ertek).split(";"):
        if "=" not in resz:
            continue
        k, _, v = resz.partition("=")
        out[k.strip().upper()] = v.strip().upper()
    return out


def _egyszeru_esemenyek(szoveg):
    """Beépített feldolgozó: VEVENT-ek (ismétlődés nélkül) + RRULE-kiterjesztés."""
    esemenyek = []
    jelenlegi = None
    for sor in _kibont(szoveg):
        f = _ertek(sor)
        if f is None:
            continue
        nev, par, ertek = f
        if nev == "BEGIN" and ertek.strip().upper() == "VEVENT":
            jelenlegi = {"exdate": [], "rdate": [], "vege": None}
            continue
        if nev == "END" and ertek.strip().upper() == "VEVENT":
            if jelenlegi and jelenlegi.get("kezdet"):
                jelenlegi["kezdet"] = _datum(jelenlegi["kezdet"], jelenlegi.get("kezdet_par") or {})
                if jelenlegi.get("vege_ertek"):
                    jelenlegi["vege"] = _datum(jelenlegi["vege_ertek"], jelenlegi.get("vege_par") or {})
                if jelenlegi["kezdet"]:
                    esemenyek.append(jelenlegi)
            jelenlegi = None
            continue
        if jelenlegi is None:
            continue
        if nev == "SUMMARY":
            jelenlegi["cim"] = ertek.replace("\\,", ",").replace("\\;", ";").strip()
        elif nev == "DTSTART":
            jelenlegi["kezdet"], jelenlegi["kezdet_par"] = ertek, par
        elif nev == "DTEND":
            jelenlegi["vege_ertek"], jelenlegi["vege_par"] = ertek, par
        elif nev == "RRULE":
            jelenlegi["rrule"] = _rruleszabaly(ertek)
        elif nev == "EXDATE":
            for egy in ertek.split(","):
                d = _datum(egy, par)
                if d:
                    jelenlegi["exdate"].append(_napkulcs(d))
        elif nev == "RDATE":
            for egy in ertek.split(","):
                d = _datum(egy, par)
                if d:
                    jelenlegi["rdate"].append(d)
        elif nev == "LOCATION":
            jelenlegi["hely"] = ertek.replace("\\,", ",").strip()
    return esemenyek


def _napkulcs(d):
    if isinstance(d, datetime.datetime):
        return d.date().isoformat()
    return d.isoformat()


def _ismetlesek(esemeny, tol, ig):
    """Egy esemény előfordulásai [tol, ig] között: [(kezdet, vége, egész_napos)]."""
    kezdet = esemeny["kezdet"]
    vege = esemeny.get("vege")
    egesz = _egesz_napos(kezdet)
    hossz = None
    if isinstance(kezdet, datetime.datetime) and isinstance(vege, datetime.datetime):
        hossz = vege - kezdet
    elif egesz and isinstance(vege, datetime.date):
        hossz = datetime.timedelta(days=max(1, (vege - kezdet).days))
    if hossz is None:
        hossz = datetime.timedelta(days=1) if _egesz_napos(egesz) else datetime.timedelta(hours=1)

    rrule = esemeny.get("rrule") or {}
    ki = []
    if not rrule:
        if _benne(kezdet, tol, ig):
            ki.append((kezdet, kezdet + hossz, _egesz_napos(egesz)))
    else:
        freq = rrule.get("FREQ", "")
        try:
            intervallum = max(1, int(rrule.get("INTERVAL", "1")))
        except ValueError:
            intervallum = 1
        darab = rrule.get("COUNT")
        try:
            darab = int(darab) if darab else None
        except ValueError:
            darab = None
        until = _datum(rrule.get("UNTIL", ""), {}) if rrule.get("UNTIL") else None
        aktualis = kezdet
        lepes = 0
        while lepes < 3000:
            lepes += 1
            if darab is not None and lepes > darab:
                break
            if isinstance(until, datetime.datetime) and isinstance(aktualis, datetime.datetime) \
                    and aktualis > until:
                break
            if isinstance(until, datetime.date) and _napkulcs(aktualis) > _napkulcs(until):
                break
            if _napkulcs(aktualis) > ig.isoformat():
                break
            if _napkulcs(aktualis) not in esemeny.get("exdate", []) and _benne(aktualis, tol, ig):
                ki.append((aktualis, aktualis + hossz, _egesz_napos(egesz)))
            kov = _lep(aktualis, freq, intervallum)
            if kov is None or kov == aktualis:
                break
            aktualis = kov
    for extra in esemeny.get("rdate", []):
        if _benne(extra, tol, ig):
            ki.append((extra, extra + hossz, _egesz_napos(egesz)))
    return ki





def _lep(d, freq, n):
    if freq == "DAILY":
        return d + datetime.timedelta(days=n)
    if freq == "WEEKLY":
        return d + datetime.timedelta(days=7 * n)
    if freq == "MONTHLY":
        return _honap(d, n)
    if freq == "YEARLY":
        return _honap(d, 12 * n)
    return None


def _honap(d, n):
    """Hónapokkal lépés (a hónap végén maradva, pl. jan. 31. → febr. 28.)."""
    y, m = d.year, d.month - 1 + n
    y += m // 12
    m = m % 12 + 1
    napok = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    nap = min(d.day, napok[m - 1])
    try:
        if isinstance(d, datetime.datetime):
            return d.replace(year=y, month=m, day=nap)
        return datetime.date(y, m, nap)
    except ValueError:
        return None


def _egesz_napos(ert):
    """Egész napos esemény-e (dátum, nem időpont)."""
    return isinstance(ert, datetime.date) and not isinstance(ert, datetime.datetime)


def _benne(d, tol, ig):
    kulcs = _napkulcs(d)
    return tol.isoformat() <= kulcs <= ig.isoformat()


# ------------------------------------------------------------------ gyűjtés
def esemenyek(szoveg, tol, ig, naptar="", szin=""):
    """Események listája az időszakra: {cim, kezdet, vege, egesz, hely, naptar, szin}."""
    if not szoveg:
        return []
    try:                                            # pontosabb, ha van
        import icalendar                            # noqa: F401
        import recurring_ical_events
        naptar_obj = icalendar.Calendar.from_ical(szoveg)
        nyers = recurring_ical_events.of(naptar_obj).between(
            datetime.datetime.combine(tol, datetime.time.min),
            datetime.datetime.combine(ig, datetime.time.max))
        ki = []
        for e in nyers:
            kezdet = e.get("DTSTART").dt if e.get("DTSTART") else None
            if kezdet is None:
                continue
            vege = e.get("DTEND").dt if e.get("DTEND") else kezdet
            egesz = _egesz_napos(kezdet)
            # a recurring_ical_events néha éjfélre teszi az egész napos eseményt
            if (not egesz and isinstance(kezdet, datetime.datetime)
                    and kezdet.time() == datetime.time(0, 0)
                    and isinstance(vege, datetime.datetime)
                    and vege.time() == datetime.time(0, 0)):
                egesz = True
                kezdet, vege = kezdet.date(), vege.date()
            ki.append({
                "cim": str(e.get("SUMMARY", "")).strip() or "(névtelen esemény)",
                "kezdet": kezdet.isoformat(),
                "vege": vege.isoformat(),
                "egesz": _egesz_napos(kezdet),
                "hely": str(e.get("LOCATION", "")).strip(),
                "naptar": naptar,
                "szin": szin,
            })
        return sorted(ki, key=lambda x: str(x["kezdet"]))
    except Exception:
        pass

    ki = []
    for e in _egyszeru_esemenyek(szoveg):
        for kezdet, vege, egesz in _ismetlesek(e, tol, ig):
            ki.append({
                "cim": e.get("cim") or "(névtelen esemény)",
                "kezdet": kezdet.isoformat(),
                "vege": vege.isoformat(),
                "egesz": _egesz_napos(kezdet),
                "hely": e.get("hely", ""),
                "naptar": naptar,
                "szin": szin,
            })
    ki.sort(key=lambda x: str(x["kezdet"]))
    return ki


def gyujt(forrasok, data_dir, days=14, ma=None, max_age=1800):
    """Minden bekapcsolt forrás eseményei + forrás-onkénti állapot.

    Visszaad: (esemenyek, allapotok)
      allapotok: [{id, nev, url, hibak, honnan, darab}]
    """
    ma = ma or datetime.date.today()
    # `ma` egyben a kezdő nap is lehet (a naptárnézet a látható rács
    # első napját küldi, ami a múlt hónapba eshet) – ezért nem a mai nap.
    ig = ma + datetime.timedelta(days=max(1, days))
    osszes, allapotok = [], []
    for f in forrasok or []:
        if not isinstance(f, dict) or f.get("enabled") is False:
            continue
        url = str(f.get("url") or "").strip()
        nev = str(f.get("nev") or f.get("name") or "Naptár").strip()
        if not url:
            continue
        szoveg, honnan, hiba = beolvas(url, data_dir, max_age=max_age)
        lista = esemenyek(szoveg, ma, ig, naptar=nev, szin=str(f.get("szin") or ""))
        osszes.extend(lista)
        allapotok.append({
            "id": f.get("id") or forras_azonosito(url),
            "nev": nev,
            "url": url,
            "honnan": honnan,
            "hiba": hiba,
            "darab": len(lista),
        })
    osszes.sort(key=lambda x: str(x["kezdet"]))
    return osszes, allapotok


# ------------------------------------------------------------------ parancssor
def main(argv=None):
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Florum – külső naptár-források (.ics)")
    ap.add_argument("--url", help="a naptár iCal címe (http(s):// vagy fájl)")
    ap.add_argument("--lista", action="store_true", help="a beállított források kipróbálása")
    ap.add_argument("--nap", type=int, default=14, help="hány napra (alap: 14)")
    ap.add_argument("--data-dir", default="", help="adatmappa")
    args = ap.parse_args(argv)

    data_dir = os.path.abspath(os.path.expanduser(args.data_dir)) if args.data_dir else \
        os.path.join(os.path.expanduser("~"), ".local", "share", "florum")

    if args.url:
        forrasok = [{"nev": "próba", "url": args.url}]
    elif args.lista:
        try:
            with open(os.path.join(data_dir, "florum-data.json"), encoding="utf-8") as fh:
                allapot = json.load(fh)
            forrasok = ((allapot.get("settings") or {}).get("calSources") or [])
        except (OSError, ValueError):
            forrasok = []
        if not forrasok:
            print("Nincs beállított naptár-forrás (Beállítások → Naptár-források).")
            return 0
    else:
        ap.print_help()
        return 0

    esemenyek_lista, allapotok = gyujt(forrasok, data_dir, days=args.nap)
    for a in allapotok:
        print("%s %-22s %-10s %3d esemény %s" % ("✓" if not a["hiba"] else "!",
                                                 a["nev"], a["honnan"], a["darab"],
                                                 a["hiba"] or ""))
    print()
    for e in esemenyek_lista[:40]:
        print("  %s  %s%s" % (str(e["kezdet"])[:16], e["cim"],
                              ("  (" + e["naptar"] + ")") if e.get("naptar") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
