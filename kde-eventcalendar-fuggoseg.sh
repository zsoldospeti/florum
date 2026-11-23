#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.4  ·  az Event Calendar Python-függőségei
#  Fájl:    kde-eventcalendar-fuggoseg.sh
#  Futtatás:  bash kde-eventcalendar-fuggoseg.sh
#
#  MIÉRT?
#  A widget az .ics fájlt a saját Python-segédjével olvassa
#  (contents/scripts/icsjson.py), ehhez kell az `icalendar` és a
#  `recurring-ical-events` modul. Ha ezek hiányoznak (vagy más
#  Python-verzióhoz települtek), a widget csendben nem mutat
#  semmit, illetve ezt írja: „Reading .ics files needs the Python
#  icalendar module”.
#
#  Ez a szkript a WIDGET SAJÁT mappájába telepít, amit az
#  icsjson.py mindig elsőként tesz a keresési útvonalba:
#      ~/.local/share/plasma_org.kde.plasma.eventcalendar/python
# ==============================================================
set -uo pipefail

CEL="${FLORUM_WIDGET_PY:-$HOME/.local/share/plasma_org.kde.plasma.eventcalendar/python}"
mkdir -p "$CEL" || { echo "  ✗ nem tudom létrehozni: $CEL"; exit 1; }

echo
echo "  🌿 Event Calendar – Python-függőségek"
echo "  ------------------------------------------------------------"
echo "  Célmappa: $CEL"

# 1) rendszer-szintű csomag (Arch/CachyOS)
if command -v pacman >/dev/null 2>&1; then
  for cs in python-icalendar python-recurring-ical-events; do
    if pacman -Qq "$cs" >/dev/null 2>&1; then
      echo "  ✓ $cs telepítve (rendszer-szinten)"
    else
      echo "  · $cs nincs rendszer-szinten (nem baj, a widget saját mappájába is telepíthető)"
    fi
  done
fi

# 2) telepítés a widget saját mappájába
echo "  → pip telepítés a widget saját mappájába…"
if python3 -m pip install --target="$CEL" --upgrade --quiet \
      "icalendar>=6.1,<8" "recurring-ical-events>=3.8,<4"; then
  echo "  ✓ modulok a helyükön"
else
  echo "  ! a pip nem sikerült – próbáld:"
  echo "      python3 -m pip install --user icalendar recurring-ical-events"
  echo "      sudo pacman -S python-icalendar python-recurring-ical-events"
fi

# 3) ellenőrzés pontosan úgy, ahogy a widget importál
echo "  → ellenőrzés…"
python3 - "$CEL" <<'PY'
import os, sys
cel = sys.argv[1]
sys.path.insert(0, cel)
try:
    import icalendar
    print("  ✓ icalendar %s" % getattr(icalendar, "__version__", "?"))
except Exception as exc:
    print("  ✗ icalendar: %s" % exc)
    sys.exit(1)
try:
    import recurring_ical_events
    print("  ✓ recurring-ical-events")
except Exception as exc:
    print("  ! recurring-ical-events: %s (az ismétlődő eseményekhez kell)" % exc)
PY

# 4) a Florum naptárának ellenőrzése a widget segédjével
HELPER=""
for d in "$HOME/.local/share/plasma/plasmoids/org.kde.plasma.eventcalendar" \
         /usr/share/plasma/plasmoids/org.kde.plasma.eventcalendar; do
  [ -f "$d/contents/scripts/icsjson.py" ] && HELPER="$d/contents/scripts/icsjson.py" && break
done
ICS="$HOME/.local/share/plasma_org.kde.plasma.eventcalendar/florum.ics"
if [ -n "$HELPER" ] && [ -f "$ICS" ]; then
  MA=$(date +%Y-%m-%d); VEG=$(date -d "+120 days" +%Y-%m-%d 2>/dev/null || date +%Y-%m-%d)
  DB=$(python3 "$HELPER" --url "$ICS" query "$MA" "$VEG" 2>/dev/null | grep -c '"summary"')
  echo "  ✓ a widget beolvasója ${DB:-0} eseményt lát a következő 120 napra"
  [ "${DB:-0}" = "0" ] && echo "    ! nulla esemény – nézd meg: python3 eventcalendar-diagnosztika.py"
fi

echo
echo "  Kész. Ha a panelon még mindig nincs esemény:"
echo "    systemctl --user restart plasma-plasmashell"
echo "    python3 eventcalendar-diagnosztika.py"
echo
