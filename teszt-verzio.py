#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.33.2  ·  teszt: verzió-egyezés („felül új, lent régi”)
#  Fájl:    teszt-verzio.py
#
#  A hiba, amit ez a teszt őriz:
#     a felület fejlécében a FÁJL verziója van (statikus szöveg),
#     a lábléc viszont a FUTÓ szerver /api/info válaszából dolgozik.
#     Ha a háttérben még egy régi példány fut, a kettő eltér:
#     „felül 1.24, lent 1.22”.
#
#  Amit vizsgál:
#   1. file_version() / VERSION fájl / APP_VERSION összhangja
#   2. a HTML meta-verziója és a figyelmeztető sáv (checkVersion)
#   3. /api/info → fileVersion, versionMismatch
#   4. a futó példány felismerése (futo_peldany, futo_folyamatok)
#   5. a --verzio és a --leallit parancs
# ==============================================================

import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import florum      # noqa: E402

HTML = os.path.join(HERE, "florum.html")
# A tiszta forrás a florum mappa TESTVÉRE (a munkaterületen és a user gépén is).
# Korábban abszolút /home/user út volt – ez más gépen és próbamásolatban elbukott.
_SZULO = os.path.dirname(HERE)
FORRAS = os.path.join(_SZULO, "minden_html-original", "florum", "florum.html")
if not os.path.isfile(FORRAS):
    FORRAS = "/home/user/minden_html-original/florum/florum.html"


def szoveg(ut):
    with io.open(ut, encoding="utf-8") as fh:
        return fh.read()


class VerzioFajl(unittest.TestCase):
    """A VERSION fájl és a program verziója egyezzen."""

    def test_version_fajl_letezik(self):
        self.assertTrue(os.path.isfile(os.path.join(HERE, "VERSION")))

    def test_file_version_egyezik(self):
        self.assertTrue(florum.file_version())
        self.assertEqual(florum.file_version(), szoveg(os.path.join(HERE, "VERSION")).strip())

    def test_app_version_egyezik_a_fajllal(self):
        """A telepített kód és a VERSION ne csússzon el egymástól."""
        self.assertEqual(florum.APP_VERSION, florum.file_version())

    def test_verzio_formatum(self):
        self.assertRegex(florum.APP_VERSION, r"^\d+\.\d+\.\d+$")


class HtmlOldal(unittest.TestCase):
    """A felület maga is ismerje a saját verzióját."""

    @classmethod
    def setUpClass(cls):
        cls.html = szoveg(HTML)

    def test_meta_verzio(self):
        m = re.search(r'<meta name="florum-version" content="([^"]+)">', self.html)
        self.assertIsNotNone(m, "hiányzik a <meta name=florum-version>")
        self.assertEqual(m.group(1), florum.APP_VERSION)

    def test_fejlec_verzio(self):
        m = re.search(r"FLORUM ([0-9.]+)", self.html)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), florum.APP_VERSION)

    def test_checkversion_fuggveny(self):
        for kell in ("var FILE_VERSION", "function checkVersion(info)",
                     "info.appVersion", "=== String(FILE_VERSION)"):
            self.assertIn(kell, self.html, "hiányzik: " + kell)

    def test_egy_kattintasos_ujrainditas(self):
        """A figyelmeztető sávból egy kattintással újraindítható a régi példány."""
        self.assertIn("verRestart", self.html)
        self.assertIn("function restartServer()", self.html)
        self.assertIn("/api/restart", self.html)
        with io.open(os.path.join(HERE, "florum.py"), encoding="utf-8") as fh:
            forras = fh.read()
        self.assertIn('/api/restart', forras)
        self.assertIn("INVOCATION_ID", forras, "systemd alatt ne indítsa újra magát")

    def test_figyelmezteto_sav(self):
        self.assertIn("verBanner", self.html)
        self.assertIn("Két verzió fut egyszerre", self.html)
        self.assertIn("systemctl --user restart florum-szerver", self.html)
        self.assertIn("python3 florum.py --leallit", self.html)

    def test_lablec_mindket_verziot_mutatja(self):
        self.assertIn("' (fut) / '", self.html)
        self.assertIn("' (fájl)'", self.html)

    def test_checkversion_meghivva(self):
        """Az initStorage a /api/state válasza után azonnal ellenőriz."""
        m = re.search(r"store\.info = j\.info \|\| null;\s*\n\s*checkVersion\(j\.info\);", self.html)
        self.assertIsNotNone(m, "a checkVersion nincs bekötve az initStorage-ba")

    def test_forrasban_is(self):
        if not os.path.exists(FORRAS):
            self.skipTest("nincs minden_html-original ezen a gépen")
        s = szoveg(FORRAS)
        for kell in ('<meta name="florum-version"', "function checkVersion(info)", "verBanner"):
            self.assertIn(kell, s, "hiányzik a forrásból: " + kell)


class MunkateruletPeldanyok(unittest.TestCase):
    """A munkaterület MINDEN florum.html példánya egy verziót mutasson.

    A hiba, amit ez a teszt őriz (1.33.2):
        a build két lépésből áll – `build-plant-db.py --html` a tiszta forrásba ír,
        `kinezet-egyesites.sh` abból állítja elő a futó fájlt ÉS az egyesített
        példányt. Ha a második kimarad, a felület a régit mutatja, és semmi nem
        szól. A felhasználó ilyenkor azt hiszi, hogy „nem frissül a munkaterület”.
    """

    EGYESITETT = os.path.join(os.path.dirname(HERE), "minden_html-egyesitett",
                              "florum", "florum.html")
    if not os.path.isfile(EGYESITETT):
        EGYESITETT = "/home/user/minden_html-egyesitett/florum/florum.html"
    # A legfontosabb új funkciók – verziótól függetlenül. Ha valamelyik
    # hiányzik az egyesített példányból, az lemaradt. Új nagy funkciónál
    # ide egy sor kerül (nem kell verzióhoz kötni).
    JELLEMZOK = ["tempChartHTML", "data-tempwin", "chart-svg", "chart-sum"]

    @classmethod
    def setUpClass(cls):
        cls.fajlok = [HTML, FORRAS, cls.EGYESITETT]
        cls.megvannak = [f for f in cls.fajlok if os.path.isfile(f)]
        cls.verziok = {}
        for f in cls.megvannak:
            m = re.search(r'<meta name="florum-version" content="([^"]+)">', szoveg(f))
            cls.verziok[f] = m.group(1) if m else None

    def test_minden_peldany_ugyanazt_a_verziot_mondja(self):
        """Ne legyen „felül új, lent régi” a fájlok között sem."""
        elteres = {f: v for f, v in self.verziok.items() if v != florum.APP_VERSION}
        self.assertEqual(elteres, {},
                         "elmaradt példány (futtasd: bash kinezet-egyesites.sh): " +
                         ", ".join("%s → %s" % (os.path.relpath(f, "/home/user"), v)
                                   for f, v in elteres.items()))

    def test_forras_es_futo_fajl_egyezik(self):
        """A futó fájl a forrásból készüljön (a téma-blokk a különbség)."""
        if not os.path.isfile(FORRAS):
            self.skipTest("nincs minden_html-original ezen a gépen")
        forras = szoveg(FORRAS)
        futo = szoveg(HTML)
        # a forrás minden <script> blokkja benne legyen a futó fájlban
        blokkok = [b for b in re.findall(r"<script>(.*?)</script>", forras, re.S) if len(b) > 2000]
        self.assertTrue(blokkok, "nincs nagy script-blokk a forrásban")
        for b in blokkok:
            self.assertIn(b[:400], futo,
                          "a futó florum.html lemaradt a forrástól "
                          "(futtasd: bash kinezet-egyesites.sh)")

    def test_egyesitett_peldany_nem_maradt_el(self):
        """Az egyesített példány is kapja meg az új funkciókat."""
        if not os.path.isfile(self.EGYESITETT):
            self.skipTest("nincs minden_html-egyesitett ezen a gépen")
        s = szoveg(self.EGYESITETT)
        hianyzo = [j for j in self.JELLEMZOK if j not in s]
        self.assertEqual(hianyzo, [],
                         "a minden_html-egyesitett/florum/florum.html lemaradt – "
                         "futtasd: bash kinezet-egyesites.sh")

    def test_csak_a_legfrissebb_zip_van_meg(self):
        """A munkaterületen ne maradjon régi csomag (félrevezeti a letöltőt)."""
        mappak = [os.path.dirname(HERE), HERE]
        regi, friss_van = [], False
        friss = "florum-%s-tiszta.zip" % florum.APP_VERSION
        for mappa in mappak:
            if not os.path.isdir(mappa):
                continue
            for nev in os.listdir(mappa):
                m = re.fullmatch(r"florum-(\d+\.\d+\.\d+)-tiszta\.zip", nev)
                if not m:
                    continue
                if m.group(1) == florum.APP_VERSION or nev == friss:
                    friss_van = True
                else:
                    regi.append(os.path.join(mappa, nev))
        if regi:
            self.fail("régi csomag maradt: %s – töröld, csak a %s maradjon "
                      "(különben a letöltő a régit kapja)"
                      % (", ".join(regi), friss))
        if not friss_van:
            self.skipTest("a friss csomagot a kiadás készíti el: bash florum-kiadas.sh --csomag")


class KiadasGit(unittest.TestCase):
    """A GitHub-kiadás eszközei – hogy ne csendben romoljanak el.

    A hiba, amit ez őriz:
        a kiadás két lépésből áll (verzió + push). Ha a verzióváltó szkript
        kimarad a csomagból, vagy a .gitignore nem zárja ki az adatot,
        a felhasználó vagy a régi verziót tölti fel, vagy felmegy a naplója.
    """

    @classmethod
    def setUpClass(cls):
        cls.kiadas = os.path.join(HERE, "florum-kiadas.sh")
        cls.gitignore = os.path.join(HERE, ".gitignore")

    def test_kiadas_szkript_letezik_es_futtathato(self):
        self.assertTrue(os.path.isfile(self.kiadas), "hiányzik a florum-kiadas.sh")
        self.assertTrue(os.access(self.kiadas, os.X_OK),
                        "a florum-kiadas.sh nem futtatható (chmod +x)")

    def test_kiadas_szintaxis(self):
        r = subprocess.run(["bash", "-n", self.kiadas], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, "bash szintaxis-hiba: " + r.stderr)

    def test_kiadas_ismeri_a_parancsokat(self):
        r = subprocess.run(["bash", self.kiadas, "--segitseg"],
                           capture_output=True, text=True, cwd=HERE)
        self.assertEqual(r.returncode, 0)
        for kapcsolo in ("--uj", "--epit", "--csomag", "--git-elokeszites",
                         "--allapot", "--feltoltes"):
            self.assertIn(kapcsolo, r.stdout, "hiányzik a súgóból: " + kapcsolo)
        self.assertIn(florum.APP_VERSION, r.stdout)

    def test_kiadas_atirja_a_verziot_mindenhol(self):
        """A verzióváltó a három florum.html példányt is kezelje."""
        with io.open(self.kiadas, encoding="utf-8") as fh:
            sh = fh.read()
        self.assertIn("minden_html-original", sh,
                      "a forrás-példány verziója nem frissül → a build visszaírja a régit")
        self.assertIn("minden_html-egyesitett", sh)
        self.assertIn("chmod +x", sh, "a sed -i elveszi a futtatható jogot")

    def test_gitignore_kizarja_az_adatot(self):
        self.assertTrue(os.path.isfile(self.gitignore), "hiányzik a .gitignore")
        with io.open(self.gitignore, encoding="utf-8") as fh:
            gi = fh.read()
        for kell in ("florum-data.json", "photos/", "mentes/", "docker/data/",
                     "*.zip", "__pycache__/", ".env"):
            self.assertIn(kell, gi, "a .gitignore nem zárja ki: " + kell)

    def test_gitignore_valoban_mukodik(self):
        """Ha van git: a tényleges kizárás is stimmeljen (nem csak a szöveg)."""
        if not shutil.which("git"):
            self.skipTest("nincs git ezen a gépen")
        with tempfile.TemporaryDirectory(prefix="florum-git-") as d:
            shutil.copy2(self.gitignore, os.path.join(d, ".gitignore"))
            # tipikus adatfájlok, amiknek KI kell esniük
                # és egy programfájl, aminek BENT kell maradnia
            for nev in ("florum-data.json", "florum.ics", "notify-state.json",
                        "florum-1.0.0-tiszta.zip", "naplo-elonezet.html", "florum.html"):
                io.open(os.path.join(d, nev), "w", encoding="utf-8").write("x")
            os.makedirs(os.path.join(d, "photos"))
            os.makedirs(os.path.join(d, "docker", "data"))
            io.open(os.path.join(d, "photos", "a.jpg"), "w").write("x")
            io.open(os.path.join(d, "docker", "data", "florum-data.json"), "w").write("x")
            r = subprocess.run(["git", "init", "-q", d], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            r = subprocess.run(["git", "-C", d, "status", "--porcelain", "--untracked-files=all"],
                               capture_output=True, text=True)
            lathato = r.stdout
            self.assertIn("florum.html", lathato, "a programfájl nem kerülne be a repóba")
            for nev in ("florum-data.json", "photos/a.jpg", "docker/data/florum-data.json",
                        ".zip", "elonezet"):
                self.assertNotIn(nev, lathato,
                                 "a .gitignore nem zárja ki: %s (adat kerülne fel!)" % nev)


class ApiInfo(unittest.TestCase):
    """/api/info adja a fájl verzióját is, ne csak a futóét."""

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix="florum-verzio-")
        florum.Handler.data_dir = cls.dir
        florum.Handler.bundled_db_path = os.path.join(HERE, florum.DB_FILE)
        florum.Handler.ics_days = 90
        florum.Handler.ics_alarm = 8

        def make_handler(*a, **kw):
            return florum.Handler(*a, directory=HERE, **kw)

        cls.szerver = florum.Server(("127.0.0.1", 0), make_handler)
        cls.port = cls.szerver.server_address[1]
        threading.Thread(target=cls.szerver.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.szerver.shutdown()
        cls.szerver.server_close()
        shutil.rmtree(cls.dir, ignore_errors=True)

    def info(self):
        cim = "http://127.0.0.1:%d/api/info" % self.port
        with urllib.request.urlopen(cim, timeout=10) as r:
            return json.loads(r.read().decode())

    def test_fileversion_es_mismatch(self):
        j = self.info()
        self.assertIn("fileVersion", j)
        self.assertIn("versionMismatch", j)
        self.assertEqual(j["fileVersion"], florum.file_version())
        self.assertEqual(j["versionMismatch"], False)      # most egyeznek

    def test_app_version(self):
        self.assertEqual(self.info()["appVersion"], florum.APP_VERSION)


class FolyamatFelismeres(unittest.TestCase):
    """A futó példány megtalálása – és a téves találatok kizárása."""

    def test_nem_fut_semmi(self):
        self.assertIsNone(florum.futo_peldany(port=1, timeout=0.4))

    def test_shell_nem_peldany(self):
        """Egy `bash -c „… florum.py …”` NEM Florum-példány (ne öljük meg)."""
        p = subprocess.Popen(["bash", "-c", "echo /tmp/florum.py >/dev/null; sleep 5"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            time.sleep(0.4)
            pidek = [pid for pid, _ in florum.futo_folyamatok()]
            self.assertNotIn(p.pid, pidek)
        finally:
            p.terminate()
            p.wait(timeout=10)

    def test_valodi_szerver_felismerese(self):
        """Egy igazi `florum.py --szerver` példányt megtalál, és le is állítja."""
        d = tempfile.mkdtemp(prefix="florum-futo-")
        port = 8912
        p = subprocess.Popen([sys.executable, os.path.join(HERE, "florum.py"), "--szerver",
                              "--port", str(port), "--data-dir", d, "--no-ics"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            adat, vege = None, time.time() + 20
            while time.time() < vege and adat is None:
                adat = florum.futo_peldany(port, timeout=0.5)
                if adat is None:
                    time.sleep(0.3)
            self.assertIsNotNone(adat, "a szerver nem indult el a %d-es porton" % port)
            self.assertEqual(adat["appVersion"], florum.APP_VERSION)
            pidek = [pid for pid, cmd in florum.futo_folyamatok() if str(port) in cmd]
            self.assertIn(p.pid, pidek)
            # leállítás (a --leallit logikájával, de csak erre a folyamatra)
            os.kill(p.pid, signal.SIGTERM)
            p.wait(timeout=15)
        finally:
            if p.poll() is None:
                p.kill()
            shutil.rmtree(d, ignore_errors=True)


class Parancssor(unittest.TestCase):
    """--verzio és --leallit."""

    def futtat(self, *kapcsolok):
        return subprocess.run([sys.executable, os.path.join(HERE, "florum.py")] +
                              list(kapcsolok), capture_output=True, text=True, timeout=120)

    def test_verzio_kimenet(self):
        r = self.futtat("--verzio", "--port", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("ez a program:", r.stdout)
        self.assertIn("VERSION fájl:", r.stdout)
        self.assertIn(florum.APP_VERSION, r.stdout)
        self.assertIn("futó szerver:      nincs", r.stdout)

    def test_leallit_nincs_mit(self):
        """Ha nem fut semmi: barátságos üzenet, 0-val kilép (nem hiba)."""
        from unittest import mock
        with mock.patch.object(florum, "futo_folyamatok", return_value=[]):
            pidek, uzenetek = florum.leallit_futo("", 1, csend=True)
        self.assertEqual(pidek, [])
        self.assertIn("nem fut Florum-folyamat", " ".join(uzenetek))

    def test_leallit_parancs_kimenet(self):
        from unittest import mock
        import unittest.mock as um
        with um.patch.object(sys, "argv", ["florum.py"]):
            pass
        # közvetlenül a main()-t hívjuk, üres folyamatlistával
        from unittest import mock as m
        with m.patch.object(florum, "futo_folyamatok", return_value=[]):
            kod = florum.main(["--leallit", "--port", "1"])
        self.assertEqual(kod, 0)

    def test_inditasi_figyelmeztetes_a_forrasban(self):
        forras = szoveg(os.path.join(HERE, "florum.py"))
        self.assertIn("MÁR FUT egy Florum", forras)
        self.assertIn("a memóriában", forras)
        self.assertIn("--leallit", forras)
        self.assertIn("systemctl --user restart florum-szerver", forras)

    def test_ne_indits_kapcsolo(self):
        forras = szoveg(os.path.join(HERE, "florum.py"))
        self.assertIn('"--ne-indits"', forras)


class FrissitesSzkript(unittest.TestCase):
    """A florum-frissites.sh – egy paranccsal rendbe teszi a verziókat."""

    @classmethod
    def setUpClass(cls):
        cls.ut = os.path.join(HERE, "florum-frissites.sh")
        cls.sh = szoveg(cls.ut)

    def test_letezik_es_futtathato(self):
        self.assertTrue(os.path.isfile(self.ut))
        self.assertTrue(os.access(self.ut, os.X_OK))

    def test_shell_szintaxis(self):
        r = subprocess.run(["bash", "-n", self.ut], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_lepesek_megvannak(self):
        for kell in ("--leallit", "systemctl --user restart florum-szerver",
                     "florum.py --szerver", "Ctrl+Shift+R", "--csak-nez",
                     "futo_verzio", "fajl_verzio"):
            self.assertIn(kell, self.sh, "hiányzik: " + kell)

    def test_csak_nez_mod_nem_indit(self):
        """A --csak-nez csak olvas: nem indít és nem állít le semmit."""
        r = subprocess.run(["bash", self.ut, "--csak-nez"], capture_output=True,
                           text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("a fájl verziója:", r.stdout)
        self.assertIn("a futó szerver:", r.stdout)
        self.assertNotIn("Újraindítás", r.stdout)

    def test_nem_hagyja_fugni_a_terminált(self):
        """A háttérindítás le legyen választva (setsid + disown)."""
        self.assertIn("setsid", self.sh)
        self.assertIn("disown", self.sh)
        self.assertIn("</dev/null >/dev/null 2>&1", self.sh)


if __name__ == "__main__":
    unittest.main(verbosity=2)
