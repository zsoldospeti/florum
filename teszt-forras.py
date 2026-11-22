#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Florum – a külső naptár-források (Google Naptár, .ics) tesztjei.

Futtatás:
    python3 teszt-forras.py
"""

import datetime
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import naptar_forras as N  # noqa: E402
import florum               # noqa: E402

MINTA = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Google Inc//Google Calendar 70.9054//EN
CALSCALE:GREGORIAN
X-WR-CALNAME:munka
BEGIN:VEVENT
DTSTART;VALUE=DATE:20261026
DTEND;VALUE=DATE:20261027
SUMMARY:Szabi fel nap
LOCATION:Otthon
END:VEVENT
BEGIN:VEVENT
DTSTART:20261027T090000
DTEND:20261027T100000
SUMMARY:Heti megbeszeles
RRULE:FREQ=WEEKLY;INTERVAL=1;COUNT=8
LOCATION:Zoom
END:VEVENT
BEGIN:VEVENT
DTSTART:20261024T080000
DTEND:20261024T083000
SUMMARY:Reggeli futas
RRULE:FREQ=DAILY;INTERVAL=1;COUNT=5
EXDATE:20261026T080000
END:VEVENT
BEGIN:VEVENT
DTSTART:20261028T180000
DTEND:20261028T193000
SUMMARY:Fogorvos
END:VEVENT
END:VCALENDAR
"""

TOL = datetime.date(2026, 10, 24)
IG = datetime.date(2026, 11, 10)


class Olvasas(unittest.TestCase):

    def setUp(self):
        self.lista = N.esemenyek(MINTA, TOL, IG, naptar="munka")

    def test_egyszeru_esemeny(self):
        cimek = [e["cim"] for e in self.lista]
        self.assertIn("Fogorvos", cimek)

    def test_egesz_napos(self):
        szabi = [e for e in self.lista if e["cim"].startswith("Szabi")][0]
        self.assertTrue(szabi["egesz"])
        self.assertEqual(szabi["kezdet"], "2026-10-26")
        self.assertEqual(szabi["hely"], "Otthon")

    def test_heti_ismetlodes(self):
        heti = [e for e in self.lista if e["cim"].startswith("Heti")]
        # COUNT=8, de csak a 2026-11-10-ig eső rész kell
        self.assertEqual(len(heti), 3)
        self.assertEqual(heti[0]["kezdet"], "2026-10-27T09:00:00")

    def test_napi_ismetlodes_es_exdate(self):
        napi = [e["cim"] for e in self.lista if e["cim"].startswith("Reggeli")]
        self.assertEqual(len(napi), 4)      # 5 nap - 1 EXDATE

    def test_idorendben(self):
        kulcsok = [e["kezdet"] for e in self.lista]
        self.assertEqual(kulcsok, sorted(kulcsok))

    def test_json_sorosithato(self):
        szoveg = json.dumps(self.lista, ensure_ascii=False)
        self.assertIn("Fogorvos", szoveg)

    def test_ures_bemenet(self):
        self.assertEqual(N.esemenyek("", TOL, IG), [])
        self.assertEqual(N.esemenyek("BEGIN:VCALENDAR\nEND:VCALENDAR", TOL, IG), [])

    def test_ismetlodes_hatarok(self):
        """A COUNT és az UNTIL is érvényesül."""
        ics = MINTA.replace("COUNT=5", "UNTIL=20261027T235959Z")
        lista = N.esemenyek(ics, TOL, IG)
        napi = [e for e in lista if e["cim"].startswith("Reggeli")]
        self.assertEqual(len(napi), 3)   # 24., 25., 27. (a 26. EXDATE)

    def test_nem_erintett_idoszak(self):
        lista = N.esemenyek(MINTA, datetime.date(2027, 3, 1), datetime.date(2027, 3, 31))
        # a Fogorvos és a Szabi nem ismétlődik, a heti/napi pedig lejárt
        self.assertLessEqual(len(lista), 1)


class Cache(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.fajl = os.path.join(self.d, "naptar.ics")
        with io.open(self.fajl, "w", encoding="utf-8") as fh:
            fh.write(MINTA)

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_helyi_fajl(self):
        szoveg, honnan, hiba = N.beolvas(self.fajl, self.d)
        self.assertEqual(honnan, "fájl")
        self.assertEqual(hiba, "")
        self.assertIn("Fogorvos", szoveg)

    def test_file_techorvonal(self):
        szoveg, honnan, _ = N.beolvas("file://" + self.fajl, self.d)
        self.assertEqual(honnan, "fájl")
        self.assertIn("X-WR-CALNAME", szoveg)

    def test_nem_letezo_fajl(self):
        szoveg, honnan, hiba = N.beolvas(os.path.join(self.d, "nincs.ics"), self.d)
        self.assertEqual(szoveg, "")
        self.assertTrue(hiba)

    def test_ures_cim(self):
        szoveg, honnan, hiba = N.beolvas("", self.d)
        self.assertEqual((szoveg, honnan), ("", ""))
        self.assertTrue(hiba)

    def test_rossz_protokol(self):
        _, _, hiba = N.beolvas("ftp://pelda.hu/n.ics", self.d)
        self.assertIn("http", hiba)

    def test_halozati_hiba_gyorsitotar(self):
        """Ha a letöltés nem megy, a mentett példányt használjuk."""
        url = "http://127.0.0.1:9/nem-letezik.ics"
        gyors = os.path.join(N.forras_dir(self.d), N.forras_azonosito(url) + ".ics")
        os.makedirs(os.path.dirname(gyors), exist_ok=True)
        with io.open(gyors, "w", encoding="utf-8") as fh:
            fh.write(MINTA)
        szoveg, honnan, hiba = N.beolvas(url, self.d, timeout=1, max_age=0)
        self.assertEqual(honnan, "gyorsítótár")
        self.assertIn("Fogorvos", szoveg)

    def test_gyujt_allapot(self):
        forrasok = [{"nev": "munka", "url": self.fajl},
                    {"nev": "kikapcsolt", "url": self.fajl, "enabled": False},
                    {"nev": "üres", "url": ""}]
        lista, allapot = N.gyujt(forrasok, self.d, days=17, ma=TOL)
        self.assertEqual(len(allapot), 1)          # csak a bekapcsolt, címmel rendelkező
        self.assertEqual(allapot[0]["nev"], "munka")
        self.assertEqual(allapot[0]["honnan"], "fájl")
        self.assertGreater(len(lista), 3)


class PanelSorok(unittest.TestCase):

    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.fajl = os.path.join(self.d, "naptar.ics")
        with io.open(self.fajl, "w", encoding="utf-8") as fh:
            fh.write(MINTA)
        self.allapot = {
            "plants": [{"id": "p1", "name": "Aloe", "waterDays": 14, "fertDays": 30,
                        "mistDays": 45, "repotMonths": 24,
                        "lastWatered": "2026-10-20", "lastFertilized": "2026-10-01",
                        "lastMisted": "2026-10-01", "lastRepotted": "2025-09-01"}],
            "history": [],
            "settings": {"calSources": [{"nev": "Google – munka", "url": self.fajl}]},
            "meta": {},
        }

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_esemeny_sorok(self):
        sorok, allapot = florum.naptar_rows(self.allapot, self.d, days=17,
                                              today=datetime.date(2026, 10, 26))
        self.assertGreater(len(sorok), 3)
        sor = sorok[0]
        self.assertEqual(sor["kind"], "event")
        self.assertEqual(sor["icon"], "📅")
        self.assertEqual(sor["task"], "event")
        self.assertIn("Google", sor["label"])
        self.assertFalse(sor["late"])          # naptári esemény nem „lejárt”
        self.assertEqual(allapot[0]["nev"], "Google – munka")

    def test_nincs_forras(self):
        sorok, allapot = florum.naptar_rows({"settings": {}}, self.d)
        self.assertEqual((sorok, allapot), ([], []))

    def test_hibas_forras_nem_allit_meg(self):
        self.allapot["settings"]["calSources"] = [
            {"nev": "rossz", "url": os.path.join(self.d, "nincs.ics")},
            {"nev": "jó", "url": self.fajl},
        ]
        sorok, allapot = florum.naptar_rows(self.allapot, self.d, days=17,
                                              today=datetime.date(2026, 10, 26))
        self.assertEqual(len(allapot), 2)
        self.assertTrue(allapot[0]["hiba"])
        self.assertGreater(len(sorok), 0)

    def test_panel_osszefesules(self):
        """A teendők és az események dátum szerint keverednek."""
        adat = florum.panel_data(self.allapot, days=17)
        esemenyek, _ = florum.naptar_rows(self.allapot, self.d, days=17,
                                              today=datetime.date(2026, 10, 26))
        egyutt = adat["rows"] + esemenyek
        egyutt.sort(key=lambda r: (str(r.get("due") or "")[:10]))
        napok = [str(r["due"])[:10] for r in egyutt]
        self.assertEqual(napok, sorted(napok))


class Segedek(unittest.TestCase):

    def test_forras_azonosito_stabil(self):
        url = "https://calendar.google.com/calendar/ical/x/basic.ics"
        self.assertEqual(N.forras_azonosito(url), N.forras_azonosito(url))
        self.assertEqual(len(N.forras_azonosito(url)), 16)

    def test_naptar_nev(self):
        self.assertEqual(florum._naptar_nev(MINTA), "munka")

    def test_is_web(self):
        self.assertTrue(N.is_web("https://a.hu/b.ics"))
        self.assertTrue(N.is_web("http://a.hu/b.ics"))
        self.assertFalse(N.is_web("/tmp/b.ics"))
        self.assertFalse(N.is_web("ftp://a.hu/b.ics"))

    def test_hataridok(self):
        """A hónap végi lépés nem csúszik el (jan. 31. → febr. 28.)."""
        d1 = datetime.date(2027, 1, 31)
        self.assertEqual(N._honap(d1, 1), datetime.date(2027, 2, 28))
        self.assertEqual(N._honap(d1, 2), datetime.date(2027, 3, 31))
        self.assertEqual(N._honap(datetime.date(2028, 2, 29), 12), datetime.date(2029, 2, 28))


class NaptarIdoszak(unittest.TestCase):
    """A naptárnézet a LÁTHATÓ időszakot kéri (/api/calendars?from&days).

    A hónap-rács első napja a múlt hónapba eshet, ezért nem a mai naptól
    indulunk – enélkül a korábbi napok eseményei elvesznének.
    """

    def test_alap(self):
        tol, napok = florum.naptar_idoszak("/api/calendars")
        self.assertEqual(napok, 14)
        self.assertEqual(tol, datetime.date.today())

    def test_from_es_days(self):
        tol, napok = florum.naptar_idoszak("/api/calendars?from=2026-09-28&days=35")
        self.assertEqual(tol, datetime.date(2026, 9, 28))
        self.assertEqual(napok, 35)

    def test_hatarertekek(self):
        self.assertEqual(florum.naptar_idoszak("/api/calendars?days=9999")[1], 400)
        self.assertEqual(florum.naptar_idoszak("/api/calendars?days=0")[1], 1)
        self.assertEqual(florum.naptar_idoszak("/api/calendars?days=-5")[1], 1)

    def test_hibas_ertek(self):
        tol, napok = florum.naptar_idoszak("/api/calendars?from=hülye&days=abc")
        self.assertEqual(napok, 14)
        self.assertEqual(tol, datetime.date.today())

    def test_urlkodolt_from(self):
        tol, _ = florum.naptar_idoszak("/api/calendars?from=2026-10-01%20&days=7")
        self.assertEqual(tol, datetime.date(2026, 10, 1))

    def test_mult_esemeny_is_bejon(self):
        """Ha a kezdő nap a múltban van, a korábbi események is megjönnek."""
        mappa = tempfile.mkdtemp(prefix="florum-forras-")
        try:
            ut = os.path.join(mappa, "n.ics")
            with io.open(ut, "w", encoding="utf-8", newline="") as fh:
                fh.write(MINTA.replace("\n", "\r\n"))
            forrasok = [{"nev": "munka", "url": ut, "enabled": True}]
            # 2026-10-20-tól 30 nap: a 10-24-i és 10-26-i esemény is benne van
            lista, allapot = N.gyujt(forrasok, mappa, days=30,
                                     ma=datetime.date(2026, 10, 20))
            napok = sorted({e["kezdet"][:10] for e in lista})
            self.assertIn("2026-10-24", napok)
            self.assertIn("2026-10-26", napok)
            # a mai naptól indulva a 10-20-i múlt már kimaradhat
            lista2, _ = N.gyujt(forrasok, mappa, days=30,
                                ma=datetime.date(2026, 10, 27))
            self.assertNotIn("2026-10-24", sorted({e["kezdet"][:10] for e in lista2}))
        finally:
            shutil.rmtree(mappa, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
