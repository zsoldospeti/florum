#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.3  ·  Event Calendar plasmoid – magyar felirat
#  Fájl:    kde-eventcalendar-magyar.sh
#  Futtatás:  bash kde-eventcalendar-magyar.sh
#
#  MIT CSINÁL?
#  Az Event Calendar widgethez (plasma_applet_org.kde.plasma.
#  eventcalendar) nincs magyar fordítás – ezt a hiányt tölti be ez a
#  csomag: a forditas/ mappában lévő hu.po / .mo 587 szöveget tartalmaz
#  (a hivatalos template.pot alapján, kézzel fordítva, 100%).
#
#  Telepítés helye (a KDE szabványos nyelvezeti mappája, ezért
#  rendszer-szintű telepítésnél is működik):
#      ~/.local/share/locale/hu/LC_MESSAGES/
#          plasma_applet_org.kde.plasma.eventcalendar.mo
#
#  Visszavonás: a .mo törlése + plasmashell újraindítás.
# ==============================================================
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MO_NEV="plasma_applet_org.kde.plasma.eventcalendar.mo"
MO="$DIR/forditas/$MO_NEV"
CEL="$HOME/.local/share/locale/hu/LC_MESSAGES"
PLASMOID_NEV="org.kde.plasma.eventcalendar"

echo
echo "  🌿 Event Calendar – magyar felirat"
echo "  ------------------------------------------------------------"

# ---- 1) ellenőrzés
if [ ! -f "$MO" ]; then
  echo "  ✗ nem találom: $MO"
  echo "    Készítsd el a forrásból:  python3 forditas/keszit.py"
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  SZAM="$(python3 - "$MO" <<'PY'
import sys, gettext, os, tempfile, shutil
mo = sys.argv[1]
d = tempfile.mkdtemp()
try:
    os.makedirs(os.path.join(d, "hu", "LC_MESSAGES"))
    shutil.copy(mo, os.path.join(d, "hu", "LC_MESSAGES",
        "plasma_applet_org.kde.plasma.eventcalendar.mo"))
    t = gettext.translation("plasma_applet_org.kde.plasma.eventcalendar",
                            localedir=d, languages=["hu"])
    print(len([1 for k in t._catalog if k]))
finally:
    shutil.rmtree(d, ignore_errors=True)
PY
)"
  echo "  ✓ fordítás rendben – ${SZAM:-?} szöveg a .mo fájlban"
fi

# ---- 2) telepítés
mkdir -p "$CEL" || { echo "  ✗ nem tudom létrehozni: $CEL"; exit 1; }
cp -f "$MO" "$CEL/$MO_NEV" && echo "  ✓ telepítve: $CEL/$MO_NEV"

# ha a plasmoid felhasználói telepítésű, a csomagba is belemásoljuk
for MAPPA in "$HOME/.local/share/plasma/plasmoids/$PLASMOID_NEV"; do
  if [ -d "$MAPPA/contents" ]; then
    mkdir -p "$MAPPA/contents/locale/hu/LC_MESSAGES" 2>/dev/null &&
      cp -f "$MO" "$MAPPA/contents/locale/hu/LC_MESSAGES/$MO_NEV" 2>/dev/null &&
      echo "  ✓ a plasmoid csomagjába is belemásolva"
  fi
done

# ---- 3) mit kell még tudni
echo
echo "  A widget a magyar szöveget a következő indításnál veszi át."
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active plasma-plasmashell.service >/dev/null 2>&1; then
  echo "  → plasmashell újraindítása (a panel 1-2 másodpercre eltűnhet)…"
  systemctl --user restart plasma-plasmashell.service 2>/dev/null || true
elif pgrep -x plasmashell >/dev/null 2>&1; then
  echo "  → plasmashell újraindítása…"
  pkill -x plasmashell; sleep 1; (nohup plasmashell >/dev/null 2>&1 &)
else
  echo "  ! a plasmashell nem fut – a következő bejelentkezéskor lép életbe"
fi

echo
echo "  ------------------------------------------------------------"
echo "  Amit magyarul látsz ezután: a widget teljes felülete –"
echo "  hónap/hét/nap/agenda nézet, beállítások, naptárkezelés,"
echo "  értesítések, időjárás, időzítő, importálás, keresés."
echo
echo "  A hónap- és napnevek a Plasma nyelvi beállítását követik:"
echo "    Rendszerbeállítások → Nyelv és régió → Régió: Magyarország"
echo
echo "  Visszavonás (eredeti angol felirat):"
echo "    rm \"$CEL/$MO_NEV\" && systemctl --user restart plasma-plasmashell"
echo
