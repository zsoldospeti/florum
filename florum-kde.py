#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.33.4  ·  KDE-ablak (PySide6 + QtWebEngine)
#  Fájl:    florum-kde.py
#
#  Mit tud?
#   • a Florum saját, Natív KDE-ablakban fut (nem böngésző-fül):
#     toolbár, KDE-s kinézet (org.kde.desktop stílus), ikon, cím
#   • a háttérszervert magától elindítja, ha még nem fut
#     (a 8777-es portot használja, mint a panel-widget)
#   • tálcára tehető: ott van a növények állapota + „mi a mai teendő”
#   • értesítés (QSystemTrayIcon.showMessage) esedékes teendőnél
#   • ha nincs Qt a gépen: NEM omlik össze – megmondja a
#     telepítési parancsot, és felajánlja a böngészős indítást
#
#  Használat:
#     python3 florum-kde.py                 # ablak + háttérszerver
#     python3 florum-kde.py --csak-ablak    # a már futó szerverhez csatlakozik
#     python3 florum-kde.py --teszt         # önellenőrzés Qt nélkül is
#     python3 florum-kde.py --bongeszo      # Qt nélkül: a böngészőben nyitja
# ==============================================================

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

APP_NAME = "Florum"
APP_VERSION = "1.33.4"
HERE = os.path.dirname(os.path.abspath(__file__))
QML_FILE = os.path.join(HERE, "florum-kde.qml")
ICON_FILE = os.path.join(HERE, "florum.svg")
DESKTOP_FILE = os.path.join(HERE, "florum-kde.desktop")
DEFAULT_PORT = 8777

# ezek a pacman-csomagok kellenek a KDE-ablakhoz (CachyOS / Arch)
PACMAN = ["pyside6", "qt6-webengine", "qt6-declarative"]
# ezek „jó, ha van” – a KDE-s kinéthez és a tálcához
PACMAN_AJANLOTT = ["qqc2-desktop-style", "kirigami"]


# ---------------------------------------------------------------- segédek
def szerver_url(port=DEFAULT_PORT, host="127.0.0.1"):
    return "http://%s:%d/" % (host, port)


def info(port=DEFAULT_PORT, timeout=1.5):
    """A futó Florum /api/info válasza, vagy None (ha nem fut)."""
    try:
        with urllib.request.urlopen(szerver_url(port) + "api/info", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def panel(port=DEFAULT_PORT, timeout=2.0):
    """A panel-widget adatai (mi a következő teendő) – tálca/értesítés."""
    try:
        with urllib.request.urlopen(szerver_url(port) + "api/panel.json", timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError):
        return None


def var_szerverre(port=DEFAULT_PORT, seconds=25):
    """Megvárja, míg a háttérszerver válaszol (indítás után)."""
    vege = time.time() + seconds
    while time.time() < vege:
        if info(port):
            return True
        time.sleep(0.35)
    return False


def talal_florum():
    """A florum.py helye (ugyanabban a mappában, vagy a PATH-on)."""
    helyi = os.path.join(HERE, "florum.py")
    if os.path.isfile(helyi):
        return helyi
    return shutil.which("florum.py") or ""


def hatso_indit(data_dir="", port=DEFAULT_PORT, var=10):
    """Elindítja a háttérszervert (florum.py --szerver), ha még nem fut."""
    if info(port):
        return None, "már fut"
    florum_py = talal_florum()
    if not florum_py:
        return None, "nem találom a florum.py-t"
    cmd = [sys.executable, florum_py, "--szerver", "--port", str(port)]
    if data_dir:
        cmd += ["--data-dir", data_dir]
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True, close_fds=True)
    except OSError as exc:
        return None, "nem indult el: %s" % exc
    return p, ("elindult (%d. folyamat)" % p.pid if var_szerverre(port, var)
                else "elindult, de nem válaszol")


def qt_van():
    """Telepítve van-e a PySide6 + a QtWebEngine?"""
    try:
        import PySide6                     # noqa: F401
        from PySide6 import QtWebEngineQuick  # noqa: F401
        return True
    except Exception:
        return False


def pacman_tipp():
    return "sudo pacman -S " + " ".join(PACMAN)


def bongeszos_inditas(data_dir="", port=DEFAULT_PORT, indits=True):
    """Qt nélkül: a Florum a böngészőben nyílik meg (ez mindig működik)."""
    if indits and not info(port):
        _, allapot = hatso_indit(data_dir, port, var=6)
        print("  háttérszerver: %s" % allapot)
    url = szerver_url(port)
    print("  Böngésző: %s" % url)
    opener = shutil.which("xdg-open")
    if opener and indits:
        try:
            subprocess.Popen([opener, url], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True)
        except OSError:
            pass
    return 0


# ---------------------------------------------------------------- önteszt
def ontelleszt(verbose=True):
    """Qt NÉLKÜL is futó önellenőrzés: megvannak-e a fájlok, helyes-e a QML?"""
    hibak, ok = [], []

    def ell(kell, szoveg):
        if kell:
            ok.append(szoveg)
        else:
            hibak.append(szoveg)

    for ut, nev in ((QML_FILE, "florum-kde.qml"), (ICON_FILE, "florum.svg"),
                    (DESKTOP_FILE, "florum-kde.desktop")):
        ell(os.path.isfile(ut), "megvan: %s" % nev)
    if os.path.isfile(QML_FILE):
        with open(QML_FILE, encoding="utf-8") as fh:
            qml = fh.read()
        for kell in ("import QtQuick", "import QtQuick.Controls", "import QtWebEngine",
                     "WebEngineView", "backendUrl", "ApplicationWindow",
                     "ToolButton", "onNewWindowRequested"):
            ell(kell in qml, "QML tartalmazza: %s" % kell)
        ell(qml.count("{") == qml.count("}"), "a QML kapcsos zárójelei párosak")
    if os.path.isfile(DESKTOP_FILE):
        with open(DESKTOP_FILE, encoding="utf-8") as fh:
            d = fh.read()
        for kell in ("[Desktop Entry]", "Name=", "Exec=", "Icon=", "Categories=", "Type=Application"):
            ell(kell in d, "desktop fájl: %s" % kell)
    # a Python-forrás szintaxisa
    try:
        import ast
        with open(os.path.abspath(__file__), encoding="utf-8") as fh:
            ast.parse(fh.read())
        ell(True, "a Python-forrás szintaxisa rendben")
    except SyntaxError as exc:
        ell(False, "Python szintaxis-hiba: %s" % exc)
    # Qt jelenléte (ez NEM hiba, csak információ)
    van = qt_van()
    ok.append("Qt elérhető: %s" % ("igen" if van else "nem – " + pacman_tipp()))
    if verbose:
        print("Florum – KDE-ablak önellenőrzés")
        for s in ok:
            print("  ✓ " + s)
        for s in hibak:
            print("  ✗ " + s)
        print("\n  %d rendben, %d hiba" % (len(ok), len(hibak)))
    return 0 if not hibak else 1


# ---------------------------------------------------------------- Qt-indítás
def qt_inditas(args):
    from PySide6.QtCore import QTimer, QUrl, Qt
    from PySide6.QtGui import QAction, QIcon
    from PySide6.QtWebEngineQuick import QtWebEngineQuick
    from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
    from PySide6.QtQml import QQmlApplicationEngine

    QtWebEngineQuick.initialize()
    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME + " – növénygondozó")
    app.setApplicationVersion(APP_VERSION)
    app.setDesktopFileName("florum-kde")
    app.setWindowIcon(QIcon(ICON_FILE))

    # KDE-s kinézet, ha a qqc2-desktop-style telepítve van
    stilus = os.environ.get("QT_QUICK_CONTROLS_STYLE", "")
    if not stilus:
        try:
            from PySide6.QtQuickControls2 import QQuickStyle
            QQuickStyle.setStyle("org.kde.desktop")
        except Exception:
            pass

    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    ctx.setContextProperty("backendUrl", szerver_url(args.port))
    ctx.setContextProperty("appVersion", APP_VERSION)
    ctx.setContextProperty("dataDir", args.data_dir or os.path.expanduser("~/.local/share/florum"))
    ctx.setContextProperty("iconPath", "file://" + ICON_FILE)
    engine.load(QUrl.fromLocalFile(QML_FILE))
    if not engine.rootObjects():
        print("A QML nem töltődött be. Ellenőrizd: %s" % QML_FILE)
        print("  Tipp: %s" % pacman_tipp())
        return 1

    # ---- tálcaikon + menü
    ablak = engine.rootObjects()[0]
    tray = None
    if QSystemTrayIcon.isSystemTrayAvailable() and not args.nincs_talca:
        tray = QSystemTrayIcon(QIcon(ICON_FILE), app)
        tray.setToolTip("%s %s" % (APP_NAME, APP_VERSION))
        from PySide6.QtGui import QDesktopServices

        def mutat():
            ablak.show()
            ablak.raise_()
            ablak.requestActivate()

        menu = QMenu()
        menu.addAction("Megnyitás", mutat)
        menu.addAction("Fotók (nagy nézet)",
                       lambda: QDesktopServices.openUrl(QUrl(szerver_url(args.port) + "foto")))
        menu.addAction("Naptár (.ics)", lambda: QDesktopServices.openUrl(
            QUrl(szerver_url(args.port) + "api/calendar.ics")))
        menu.addSeparator()
        menu.addAction("Kilépés", app.quit)
        tray.setContextMenu(menu)
        tray.show()

    # ---- esedékes teendő → tálca-értesítés (5 percenként)
    emlekezteto = {"utolso": ""}

    def ellenorzes():
        if not tray or args.nincs_ertesites:
            return
        adat = panel(args.port)
        if not adat:
            return
        sorok = adat.get("rows") or []
        keses = int(adat.get("lateCount") or 0)
        if keses:
            t = [s for s in sorok if s.get("late")][0] if sorok else {}
            sor = "%d lejárt teendő · %s: %s (%s)" % (
                keses, t.get("plant", "Növény"), t.get("label", "teendő"), t.get("due", ""))
        elif int(adat.get("todayCount") or 0):
            t = [s for s in sorok if s.get("today")][0] if sorok else {}
            sor = "Ma: %s – %s" % (t.get("plant", "Növény"), t.get("label", "teendő"))
        else:
            return
        if sor != emlekezteto["utolso"]:
            emlekezteto["utolso"] = sor
            tray.showMessage(APP_NAME, sor, QSystemTrayIcon.MessageIcon.Information, 9000)

    idozito = QTimer(app)
    idozito.timeout.connect(ellenorzes)
    idozito.start(args.ellenorzes_perc * 60 * 1000)
    QTimer.singleShot(4000, ellenorzes)

    print("  🌿 %s %s – KDE-ablak" % (APP_NAME, APP_VERSION))
    print("  Szerver:  %s" % szerver_url(args.port))
    print("  Adatok:   %s" % (args.data_dir or os.path.expanduser("~/.local/share/florum")))
    return app.exec()


# ---------------------------------------------------------------- main
def main(argv=None):
    p = argparse.ArgumentParser(
        description="Florum növénygondozó – natív KDE-ablak (PySide6 + QtWebEngine)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT,
                   help="a háttérszerver portja (alapértelmezés: %d)" % DEFAULT_PORT)
    p.add_argument("--data-dir", default="", help="az adatok mappája")
    p.add_argument("--ne-indits", action="store_true",
                   help="ne indítsa el a háttérszervert (csak csatlakozzon)")
    p.add_argument("--csak-ablak", action="store_true",
                   help="ne indítsa el a szervert, csak csatlakozzon a futóhoz")
    p.add_argument("--bongeszo", action="store_true",
                   help="Qt nélkül: a böngészőben nyissa meg (mindig működik)")
    p.add_argument("--nincs-talca", action="store_true", help="ne tegyen ikont a tálcára")
    p.add_argument("--nincs-ertesites", action="store_true", help="ne szóljon a teendőkről")
    p.add_argument("--ellenorzes-perc", type=int, default=5,
                   help="milyen sűrűn nézze a teendőket (perc)")
    p.add_argument("--teszt", action="store_true", help="önellenőrzés (Qt nélkül is fut)")
    args = p.parse_args(argv)

    if args.teszt:
        return ontelleszt()

    if args.bongeszo or not qt_van():
        print("  A KDE-ablakhoz Qt6 kell:  %s" % pacman_tipp())
        print("  (a böngészős indítás most is működik)")
        return bongeszos_inditas(args.data_dir, args.port,
                                 indits=not (args.ne_indits or args.csak_ablak))

    if not args.csak_ablak:
        _, allapot = hatso_indit(args.data_dir, args.port)
        print("  háttérszerver: %s" % allapot)
        if not var_szerverre(args.port, 15):
            print("  A háttérszerver nem válaszol a %d-es porton." % args.port)
            print("  Próbáld: python3 florum.py --szerver --port %d" % args.port)
            return 1
    return qt_inditas(args)


if __name__ == "__main__":
    sys.exit(main())
