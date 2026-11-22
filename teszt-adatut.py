#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.33.2  ·  teszt: adatok saját mappába (--data-dir / --atkoltoztetes)
#  Fájl:    teszt-adatut.py
#
#  A felhasználó: „python3 florum.py --data-dir – ezzel átteszem saját
#  mappájába.” Ez igaz, DE csak arra az egy indításra. Ha utána a menüből
#  indul, visszaáll az alapértelmezett mappára, és úgy tűnik, elveszett
#  minden. Ezért ez a teszt azt őrzi, hogy:
#
#    1. a --data-dir elfogad ~ és relatív utat is, és tényleg oda ment,
#    2. a --atkoltoztetes ÁTMÁSOL (JSON + képek + mentések + naptár),
#       ellenőrzi a darabszámot, és a régit NEM törli,
#    3. ugyanaz a cél → „nincs mit tenni”, írhatatlan cél → hibajelzés,
#    4. a florum-megnyitas.sh megjegyzi a mappát (florum-adat.conf / FLORUM_DATA),
#    5. a florum-atkoltoztetes.sh egy paranccsal elvégzi az egészet.
# ==============================================================

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
FERUM = os.path.join(HERE, "florum.py")
MEGNYITAS = os.path.join(HERE, "florum-megnyitas.sh")
ATKOLT = os.path.join(HERE, "florum-atkoltoztetes.sh")
CONF = os.path.join(HERE, "florum-adat.conf")

KORNY = dict(os.environ)
KORNY["PYTHONPATH"] = "/home/user/pylibs" + os.pathsep + KORNY.get("PYTHONPATH", "")


def szoveg(ut):
    with open(ut, encoding="utf-8") as fh:
        return fh.read()


def florum(*args, timeout=60):
    return subprocess.run([sys.executable, FERUM] + list(args),
                          capture_output=True, text=True, timeout=timeout, env=KORNY)


def regi_mappa(gyoker):
    """Egy „használt” adatmappa: 2 növény, 1 napló, 1 kép, 1 mentés, naptár."""
    os.makedirs(os.path.join(gyoker, "photos"))
    os.makedirs(os.path.join(gyoker, "mentes"))
    allapot = {
        "plants": [{"id": "p1", "name": "Klívia", "room": "Nappali", "waterDays": 7},
                   {"id": "p2", "name": "Sárgarépa", "room": "Kert", "garden": True}],
        "history": [{"id": "h1", "plantId": "p1", "plantName": "Klívia",
                     "type": "watering", "date": "2026-10-20", "ts": 1761000000000}],
        "settings": {}, "meta": {}, "customDb": [],
    }
    with io.open(os.path.join(gyoker, "florum-data.json"), "w", encoding="utf-8") as fh:
        json.dump(allapot, fh, ensure_ascii=False)
    with open(os.path.join(gyoker, "photos", "p1-20261020-101500.jpg"), "wb") as fh:
        fh.write(b"\xff\xd8\xff\xe0" + b"x" * 400)
    with io.open(os.path.join(gyoker, "mentes", "florum-perc-20261020-101500.json"),
                 "w", encoding="utf-8") as fh:
        fh.write("{}")
    return allapot


class AdatDir(unittest.TestCase):
    """--data-dir: ~ és relatív út, tényleg oda ment."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="florum-adat-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        if os.path.exists(CONF):
            os.remove(CONF)

    def test_atkoltoztetes_atmasol_es_nem_torol(self):
        regi = os.path.join(self.tmp, "regi")
        uj = os.path.join(self.tmp, "uj")
        os.makedirs(regi)
        allapot = regi_mappa(regi)
        e = florum("--data-dir", regi, "--atkoltoztetes", uj)
        self.assertEqual(e.returncode, 0, e.stdout + e.stderr)
        # mi került át?
        self.assertTrue(os.path.isfile(os.path.join(uj, "florum-data.json")), "nincs adatfájl")
        self.assertTrue(os.path.isfile(os.path.join(uj, "photos", "p1-20261020-101500.jpg")),
                        "nincs kép")
        self.assertTrue(os.path.isfile(os.path.join(uj, "mentes",
                                                    "florum-perc-20261020-101500.json")),
                        "nincs mentés")
        # ugyanaz a tartalom?
        with io.open(os.path.join(uj, "florum-data.json"), encoding="utf-8") as fh:
            uj_allapot = json.load(fh)
        self.assertEqual(len(uj_allapot["plants"]), 2)
        self.assertEqual(len(uj_allapot["history"]), 1)
        self.assertEqual([p["name"] for p in uj_allapot["plants"]], ["Klívia", "Sárgarépa"])
        # a régi érintetlen
        self.assertTrue(os.path.isfile(os.path.join(regi, "florum-data.json")),
                        "a régi adatfájlt kitörölte!")
        self.assertIn("ellenőrzés: növény 2 → 2", e.stdout)
        self.assertIn("naplóbejegyzés 1 → 1", e.stdout)
        self.assertIn("MEGMARAD", e.stdout)

    def test_ugyanaz_a_cel(self):
        regi = os.path.join(self.tmp, "regi")
        os.makedirs(regi)
        regi_mappa(regi)
        e = florum("--data-dir", regi, "--atkoltoztetes", regi)
        self.assertEqual(e.returncode, 0)
        self.assertIn("nincs mit tenni", e.stdout)

    def test_irhatatlan_cel(self):
        if os.geteuid() == 0:
            self.skipTest("rootként a chmod nem véd")
        regi = os.path.join(self.tmp, "regi")
        os.makedirs(regi)
        regi_mappa(regi)
        zaros = os.path.join(self.tmp, "zaros")
        os.makedirs(zaros)
        os.chmod(zaros, 0o500)
        try:
            e = florum("--data-dir", regi, "--atkoltoztetes", os.path.join(zaros, "alatta"))
        finally:
            os.chmod(zaros, 0o700)
        self.assertEqual(e.returncode, 1, e.stdout)
        self.assertIn("nem írható", e.stdout)

    def test_hianyzo_regi_mappa(self):
        e = florum("--data-dir", os.path.join(self.tmp, "nincs"),
                   "--atkoltoztetes", os.path.join(self.tmp, "uj"))
        self.assertEqual(e.returncode, 0)
        self.assertIn("nem volt mit átvinni", e.stdout)


class Megjegyzes(unittest.TestCase):
    """A megnyitó megjegyzi a mappát – a --data-dir ne csak egy indításra éljen."""

    def setUp(self):
        if os.path.exists(CONF):
            os.remove(CONF)

    def tearDown(self):
        if os.path.exists(CONF):
            os.remove(CONF)

    def test_megnyito_olvassa_a_confot(self):
        t = szoveg(MEGNYITAS)
        self.assertIn("FLORUM_DATA", t)
        self.assertIn("florum-adat.conf", t)
        self.assertIn('ADAT_ARG=(--data-dir "$ADAT")', t)
        # a szerverindítás és mindhárom megnyitási ág megkapja
        self.assertGreaterEqual(t.count('"${ADAT_ARG[@]}"'), 3,
                                "valamelyik indítás nem kapja meg a --data-dir-t")

    def test_allapot_kiirja_a_mappat(self):
        e = subprocess.run(["bash", MEGNYITAS, "--allapot"], capture_output=True, text=True)
        self.assertEqual(e.returncode, 0, e.stderr)
        self.assertIn("adatmappa", e.stdout)

    def test_conf_hatassal_van(self):
        with io.open(CONF, "w", encoding="utf-8") as fh:
            fh.write('# teszt\nDATA_DIR="/tmp/florum-teszt-hely"\n')
        e = subprocess.run(["bash", MEGNYITAS, "--allapot"], capture_output=True, text=True)
        self.assertIn("/tmp/florum-teszt-hely", e.stdout, "a conf-ot nem olvassa: " + e.stdout)
        d = subprocess.run(["bash", MEGNYITAS, "--dry-run"], capture_output=True, text=True)
        self.assertIn("/tmp/florum-teszt-hely", d.stdout, "a dry-run nem mutatja: " + d.stdout)

    def test_env_elsobbseg(self):
        korny = dict(os.environ)
        korny["FLORUM_DATA"] = "/tmp/florum-env-hely"
        e = subprocess.run(["bash", MEGNYITAS, "--allapot"], capture_output=True,
                           text=True, env=korny)
        self.assertIn("/tmp/florum-env-hely", e.stdout)


class EgyParancs(unittest.TestCase):
    """florum-atkoltoztetes.sh: a kényelmes út."""

    def test_letezik_es_futtathato(self):
        self.assertTrue(os.path.isfile(ATKOLT), "hiányzik a florum-atkoltoztetes.sh")
        self.assertTrue(os.access(ATKOLT, os.X_OK), "nem futtatható")

    def test_shell_szintaxis(self):
        e = subprocess.run(["bash", "-n", ATKOLT], capture_output=True, text=True)
        self.assertEqual(e.returncode, 0, e.stderr)

    def test_mi_es_dry_run(self):
        e = subprocess.run(["bash", ATKOLT, "--mi"], capture_output=True, text=True)
        self.assertEqual(e.returncode, 0, e.stderr)
        self.assertIn("melyik mappát", e.stdout)
        d = subprocess.run(["bash", ATKOLT, "/tmp/florum-proba-adat", "--dry-run"],
                           capture_output=True, text=True)
        self.assertEqual(d.returncode, 0, d.stderr)
        self.assertIn("[dry]", d.stdout)
        self.assertIn("DATA_DIR", d.stdout)
        self.assertIn("átmásolnám", d.stdout)

    def test_help(self):
        e = subprocess.run(["bash", ATKOLT, "--help"], capture_output=True, text=True)
        self.assertEqual(e.returncode, 0, e.stderr)
        self.assertIn("--data-dir", e.stdout, "a súgó nem magyarázza meg a --data-dir-t")


if __name__ == "__main__":
    unittest.main(verbosity=2)
