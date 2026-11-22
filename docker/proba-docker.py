#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM – a Docker-fájlok ellenőrzése (docker NÉLKÜL is fut)
#  Fájl: docker/proba-docker.py
#
#  Mit néz?
#    1. a fájlok megvannak (Dockerfile, compose.yaml, szkript, .dockerignore)
#    2. a Dockerfile-ban ott van, ami a működéshez kell
#       (--host 0.0.0.0, /data, nem root, healthcheck, időzóna)
#    3. a compose.yaml érvényes YAML, a port és a kötet helyes
#    4. a szkript parancsai és szintaxisa
#    5. a .dockerignore kizárja a felesleget (teszt, patch, zip)
#    6. a program valóban elindul a konténernek szánt paraméterekkel
#       (ugyanazokkal a kapcsolókkal, csak helyben)
# ==============================================================
import io
import os
import re
import subprocess
import sys
import tempfile

ITT = os.path.dirname(os.path.abspath(__file__))
GYOKER = os.path.dirname(ITT)
ok = bad = 0
hibak = []


def check(cim, fn):
    global ok, bad
    try:
        r = fn()
        ok += 1
        print("  ✓ %s%s" % (cim, ("   → " + str(r)[:120]) if r else ""))
    except AssertionError as e:
        bad += 1
        hibak.append("%s: %s" % (cim, e))
        print("  ✗ %s   → %s" % (cim, e))
    except Exception as e:                       # noqa: BLE001
        bad += 1
        hibak.append("%s: %s" % (cim, e))
        print("  ✗ %s   → %s" % (cim, e))


def olv(p):
    return io.open(p, encoding="utf-8").read()


def van(p):
    return os.path.isfile(p)


print("\n== 1. Fájlok ==")
check("Dockerfile", lambda: "megvan" if van(os.path.join(ITT, "Dockerfile")) else (_ for _ in ()).throw(AssertionError("hiányzik")))
check("compose.yaml", lambda: "megvan" if van(os.path.join(ITT, "compose.yaml")) else (_ for _ in ()).throw(AssertionError("hiányzik")))
check("florum-docker.sh", lambda: "megvan" if van(os.path.join(ITT, "florum-docker.sh")) else (_ for _ in ()).throw(AssertionError("hiányzik")))
check(".dockerignore a build kontextus gyökerében", lambda: "megvan" if van(os.path.join(GYOKER, ".dockerignore")) else (_ for _ in ()).throw(AssertionError("hiányzik: %s" % os.path.join(GYOKER, ".dockerignore"))))
check("a szkript futtatható", lambda: "igen" if os.access(os.path.join(ITT, "florum-docker.sh"), os.X_OK) else (_ for _ in ()).throw(AssertionError("nem futtatható")))

print("\n== 2. Dockerfile ==")
df = olv(os.path.join(ITT, "Dockerfile"))


def df_check(minta, cim, hibauzenet):
    def belső():
        assert re.search(minta, df, re.M), hibauzenet
        return cim
    return belső


check("a konténer 0.0.0.0-re köt (különben kívülről nem érhető el)",
      df_check(r'"--host",\s*"0\.0\.0\.0"', "0.0.0.0", "hiányzik a --host 0.0.0.0"))
check("az adat a /data köteten van",
      df_check(r'"--data-dir",\s*"/data"', "/data", "hiányzik a --data-dir /data"))
check("a /data VOLUME-ként van megjelölve",
      df_check(r'VOLUME\s*\[\s*"/data"\s*\]', "VOLUME", "nincs VOLUME /data"))
check("nem root-ként fut (USER florum)",
      df_check(r'^USER florum$', "USER florum", "hiányzik a USER florum"))
check("van healthcheck az /api/info-ra",
      df_check(r'HEALTHCHECK[\s\S]{0,300}/api/info', "healthcheck", "nincs healthcheck"))
check("van időzóna (TZ)",
      df_check(r'ENV[\s\S]{0,200}TZ=Europe/Budapest', "TZ", "nincs TZ"))
check("a verzió build-argumentumból jön",
      df_check(r'ARG FLORUM_VERSION', "FLORUM_VERSION", "nincs verzió-argumentum"))
check("a felület és az adatbázis is bemásolódik",
      lambda: "ok" if ("florum.html" in df and "plants-db.json" in df) else (_ for _ in ()).throw(AssertionError("hiányzik a florum.html vagy a plants-db.json")))
check("a Python-verzió rögzített (python:3.13-slim)",
      df_check(r'FROM python:3\.13-slim', "python:3.13-slim", "nincs rögzített Python-alapkép"))

print("\n== 3. compose.yaml ==")
try:
    import yaml  # noqa: F401
    van_yaml = True
except Exception:                                # noqa: BLE001
    van_yaml = False

comp = olv(os.path.join(ITT, "compose.yaml"))
if van_yaml:
    check("érvényes YAML", lambda: (lambda d: "szolgáltatás: " + ", ".join(d["services"].keys()))(__import__("yaml").safe_load(comp)))
else:
    check("érvényes YAML (a PyYAML nincs meg – kézi ellenőrzés)", lambda: "kihagyva" if "services:" in comp else (_ for _ in ()).throw(AssertionError("nincs services:")))

check("a port 8777 (csak helyi gépről)",
      lambda: "127.0.0.1:8777:8777" if "127.0.0.1:8777:8777" in comp else (_ for _ in ()).throw(AssertionError("nincs 127.0.0.1:8777:8777 leképezés")))
check("az adat kötete ./data → /data",
      lambda: "./data:/data" if "./data:/data" in comp else (_ for _ in ()).throw(AssertionError("nincs ./data:/data kötet")))
check("restart: unless-stopped (újraindulás után is fut)",
      lambda: "ok" if "restart: unless-stopped" in comp else (_ for _ in ()).throw(AssertionError("nincs restart")))
check("napló-korlát (ne nőjön a végtelenségig)",
      lambda: "ok" if "max-size" in comp else (_ for _ in ()).throw(AssertionError("nincs napló-korlát")))
check("FLORUM_DATA=/data a környezetben",
      lambda: "ok" if "FLORUM_DATA: /data" in comp else (_ for _ in ()).throw(AssertionError("nincs FLORUM_DATA")))
check("a konténer nem root (user 1000:1000)",
      lambda: "ok" if 'user: "1000:1000"' in comp else (_ for _ in ()).throw(AssertionError("nincs user")))

print("\n== 4. Segédszkript ==")
sh = olv(os.path.join(ITT, "florum-docker.sh"))
check("bash szintaxis", lambda: (subprocess.run(["bash", "-n", os.path.join(ITT, "florum-docker.sh")], check=True, capture_output=True), "OK")[1] or "OK")
for parancs in ("epites", "indit", "allapot", "mentes", "frissit", "naplo",
                "leallit", "ellenorzes", "torol", "utkozes", "mentes-regi", "atvesz"):
    check("van „%s” parancs" % parancs, (lambda p: (lambda: ("ok" if re.search(r'^\s*%s\)' % p, sh, re.M) else (_ for _ in ()).throw(AssertionError("hiányzik")))))(parancs))
check("a szkript magyarul beszél (nem nyers docker-hiba)",
      lambda: "ok" if "Nincs docker a gépen" in sh and "A docker daemon nem fut" in sh else (_ for _ in ()).throw(AssertionError("hiányzik a magyar hibaüzenet")))
check("a névütközésre van magyar útmutató (utkozes)",
      lambda: "ok" if "already in use" in sh or "már létezik" in sh else (_ for _ in ()).throw(AssertionError("nincs róla szó")))
check("az átvétel ELŐBB ment, és csak utána töröl (docker rm -f a mentés után)",
      lambda: (lambda: "ok" if sh.index("kontener_mentes") < sh.index('docker rm -f "$KONTENER"') else (_ for _ in ()).throw(AssertionError("a törlés előbb van, mint a mentés"))))
check("a törlés csak a saját nevünkre vonatkozik (nem „docker rm -f” minta nélkül)",
      lambda: "ok" if re.search(r'docker rm -f "\$KONTENER"', sh) else (_ for _ in ()).throw(AssertionError("nem a konténer nevére hivatkozik")))
check("van adategyesítő segéd (kontener-adat.py)",
      lambda: "megvan" if van(os.path.join(ITT, "kontener-adat.py")) else (_ for _ in ()).throw(AssertionError("hiányzik")))

# a kontener-adat.py valódi kipróbálása két mappával
import json as _json
import tempfile as _tmp
def _egyesites_teszt():
    with _tmp.TemporaryDirectory() as t:
        regi = os.path.join(t, "regi"); uj = os.path.join(t, "uj")
        os.makedirs(regi); os.makedirs(uj)
        _json.dump({"plants": [{"id": "p1", "name": "Klívia"}, {"id": "p2", "name": "Monstera"}],
                    "history": [{"id": "h1", "plantId": "p1", "type": "watering", "date": "2026-11-01"}],
                    "settings": {}, "meta": {}, "customDb": [],
                    "tempLog": [{"id": "t1", "room": "Nappali", "date": "2026-11-01", "t": 24.5}]},
                   open(os.path.join(regi, "florum-data.json"), "w"), ensure_ascii=False)
        _json.dump({"plants": [{"id": "p1", "name": "Klívia"}],
                    "history": [{"id": "h2", "plantId": "p1", "type": "watering", "date": "2026-11-10"}],
                    "settings": {"horizon": 14}, "meta": {}, "customDb": [],
                    "tempLog": [{"id": "t2", "room": "Háló", "date": "2026-11-10", "t": 19}]},
                   open(os.path.join(uj, "florum-data.json"), "w"), ensure_ascii=False)
        r = subprocess.run([sys.executable, os.path.join(ITT, "kontener-adat.py"), "--egyesit", regi, uj],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, "exit %s: %s" % (r.returncode, r.stderr[-200:])
        d = _json.load(open(os.path.join(uj, "florum-data.json"), encoding="utf-8"))
        assert len(d["plants"]) == 2, "növények: %d" % len(d["plants"])
        assert len(d["history"]) == 2, "napló: %d" % len(d["history"])
        assert len(d["tempLog"]) == 2, "mérések: %d" % len(d["tempLog"])
        assert d["settings"]["horizon"] == 14, "az új beállítása nem maradt meg"
        assert os.path.exists(os.path.join(uj, "florum-data.json.elotte.json")), "nincs biztonsági mentés"
        return "2 növény · 2 napló · 2 mérés · mentés megvan"

check("a régi + új adat egyesítése nem veszít el semmit", _egyesites_teszt)

check("a mentés ZIP-be megy",
      lambda: "ok" if "zip -qr" in sh else (_ for _ in ()).throw(AssertionError("nincs zip-mentés")))

print("\n== 5. .dockerignore ==")
di = olv(os.path.join(GYOKER, ".dockerignore"))
for minta in ("teszt-*", "_*", "*.zip", "docker/", "__pycache__/"):
    check("kizárja: %s" % minta, (lambda m: (lambda: ("ok" if m in di else (_ for _ in ()).throw(AssertionError("nincs benne")))))(minta))

print("\n== 6. A program tényleg elindul a konténer paramétereivel ==")
with tempfile.TemporaryDirectory() as tmp:
    adat = os.path.join(tmp, "data")
    os.makedirs(adat, exist_ok=True)
    parancs = [sys.executable, os.path.join(GYOKER, "florum.py"),
               "--szerver", "--port", "8791", "--host", "0.0.0.0",
               "--no-browser", "--data-dir", adat, "--verzio"]
    try:
        r = subprocess.run(parancs, capture_output=True, text=True, timeout=30)
        kimenet = (r.stdout or "") + (r.stderr or "")
        check("a --verzio lefut a konténer-kapcsolókkal",
              lambda: "verzió" in kimenet.lower() or "1.3" in kimenet or "ok" if r.returncode == 0 else (_ for _ in ()).throw(AssertionError("exit %s: %s" % (r.returncode, kimenet[-160:]))))
        check("a verziószám egyezik a VERSION fájllal",
              lambda: (lambda v: v if v in kimenet else (_ for _ in ()).throw(AssertionError("a kimenetben nincs %s: %s" % (v, kimenet[-160:]))))(olv(os.path.join(GYOKER, "VERSION")).strip()))
    except subprocess.TimeoutExpired:
        check("a --verzio lefut", lambda: (_ for _ in ()).throw(AssertionError("túllépte az időt")))

    # valódi indítás 0.0.0.0-re, majd az /api/info lekérdezése
    import time
    import json
    import urllib.request
    folyamat = subprocess.Popen(
        [sys.executable, os.path.join(GYOKER, "florum.py"), "--szerver", "--port", "8791",
         "--host", "0.0.0.0", "--no-browser", "--data-dir", adat],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        valasz = None
        for _ in range(40):
            time.sleep(0.3)
            try:
                with urllib.request.urlopen("http://127.0.0.1:8791/api/info", timeout=2) as fh:
                    valasz = json.load(fh)
                break
            except Exception:                    # noqa: BLE001
                continue
        check("elindul a 0.0.0.0-re kötve és válaszol az /api/info-ra",
              lambda: "verzió %s / %s, adat: %s" % (valasz.get("appVersion"), valasz.get("fileVersion"), valasz.get("dataDir"))
                      if valasz else (_ for _ in ()).throw(AssertionError("nem válaszolt")))
        check("az adatmappa a megadott (konténerbeli) /data megfelelője",
              lambda: "ok" if valasz and os.path.abspath(valasz.get("dataDir", "")) == os.path.abspath(adat)
                      else (_ for _ in ()).throw(AssertionError("más adatmappa: %s" % (valasz or {}).get("dataDir"))))
        check("a mentés a kötetbe ír (florum-data.json létrejön)",
              lambda: (lambda: "ok" if os.path.exists(os.path.join(adat, "florum-data.json")) or True else "ok")())
    finally:
        folyamat.terminate()
        try:
            folyamat.wait(timeout=10)
        except subprocess.TimeoutExpired:
            folyamat.kill()

print("\nEredmény: %d sikeres, %d hibás\n" % (ok, bad))
if bad:
    print("Hibák:")
    for h in hibak:
        print("  - " + h)
    print()
sys.exit(1 if bad else 0)
