#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.4  ·  Event Calendar plasmoid telepítése (Plasma 6)
#  Fájl:    kde-eventcalendar-telepites.sh
#  Futtatás:  bash kde-eventcalendar-telepites.sh
#
#  MIÉRT?
#  A beépített Digitális óra csak az Akonadin keresztül tud
#  eseményeket (PIM Events Plugin) – ez pedig nagy naptárnál
#  lefagy (KDE bug 526769 / 493415 / 523046).
#  Az Event Calendar plasmoid közvetlenül olvassa az .ics FÁJLT,
#  tehát:
#     * nem kell hozzá Akonadi, sem kdepim-addons,
#     * nem fagy le a panel,
#  és a Florum ugyanazt a florum.ics fájlt írja, amit ez olvas.
#
#  Telepítés után: jobb klikk az új widgetre → Configure Event
#  Calendar → Calendars → Add → ICS file → a Florum naptárfájlja.
# ==============================================================
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${FLORUM_DATA:-$HOME/.local/share/florum}"
ICS="$DATA/florum.ics"
# Az Event Calendar CSAK a saját adatmappájából olvas .ics-t – a Florum oda
# ír másolatot (lásd naptar_ics.py → mirror_path()).
WIDGET_ICS="$HOME/.local/share/plasma_org.kde.plasma.eventcalendar/florum.ics"
CSOMAG="plasma6-applets-eventcalendar"

echo
echo "  🌿 Florum – Event Calendar plasmoid (Akonadi nélkül)"
echo "  ------------------------------------------------------------"

# ---- 1) Python-függőségek (az .ics beolvasásához)
echo
echo "  1) Python-függőségek (icalendar, recurring-ical-events)"
PYBIN="python3"
if "$PYBIN" -c "import icalendar" >/dev/null 2>&1; then
  echo "  ✓ icalendar már megvan"
else
  echo "  → telepítés pip-pel (felhasználói módban)…"
  "$PYBIN" -m pip install --user --quiet "icalendar>=6.1,<8" "recurring-ical-events>=3.8,<4" \
    || echo "  ! a pip nem sikerült – telepítsd kézzel: sudo pacman -S python-icalendar python-recurring-ical-events"
fi

# ---- 2) plasmoid telepítése
echo
echo "  2) A plasmoid telepítése ($CSOMAG)"
if command -v pacman >/dev/null 2>&1 && pacman -Qq "$CSOMAG" >/dev/null 2>&1; then
  echo "  ✓ már telepítve van"
elif command -v yay >/dev/null 2>&1; then
  echo "  → yay -S $CSOMAG"
  yay -S --needed --noconfirm "$CSOMAG" || echo "  ! nem sikerült – lásd a kézi utat lentebb"
elif command -v paru >/dev/null 2>&1; then
  echo "  → paru -S $CSOMAG"
  paru -S --needed --noconfirm "$CSOMAG" || echo "  ! nem sikerült – lásd a kézi utat lentebb"
else
  echo "  ! nincs AUR-segéd (yay/paru). Kézi út:"
  echo "      https://github.com/divinae/plasma-applet-eventcalendar/releases"
  echo "      kpackagetool6 -t Plasma/Applet -i eventcalendar-*.plasmoid"
fi

# ---- 3) naptárfájl előkészítése
echo
echo "  3) A Florum naptárfájlja"
mkdir -p "$(dirname "$WIDGET_ICS")" 2>/dev/null
if [ -f "$ICS" ]; then
  cp -f "$ICS" "$WIDGET_ICS" 2>/dev/null && echo "  ✓ $WIDGET_ICS (a widget ezt olvassa)"
  echo "    forrás: $ICS ($(grep -c '^BEGIN:VEVENT' "$ICS" 2>/dev/null || echo 0) esemény)"
else
  if [ -f "$DIR/naptar_ics.py" ]; then
    python3 "$DIR/naptar_ics.py" >/dev/null 2>&1 && echo "  ✓ elkészült: $ICS"
  else
    echo "  ! nincs $ICS – indítsd egyszer a Florumot (python3 florum.py --no-browser)"
  fi
fi

# ---- 4) útmutató
cat <<EOF

  ------------------------------------------------------------
  4) Beállítás a plasmoidon
     • Jobb klikk a panelen → Add Widgets… → Event Calendar
     • Jobb klikk az új widgetre → Configure Event Calendar…
     • Calendars → Add → ICS file:
           $WIDGET_ICS
     • (opcionális) Views: Month / Agenda, a popup mérete
     • (opcionális) Weather: a városod – Open-Meteo, kulcs nélkül

  FONTOS: a widget csak a saját adatmappájában lévő .ics-t fogadja el
  (más helyen: „Local calendar file path is invalid”). A Florum ezért
  minden mentésnél ide is ír egy másolatot:
    $WIDGET_ICS

  A Florum minden mentésnél újraírja ezt a fájlt, a widget pedig
  magától újraolvassa – így a teendők a panelen is látszanak,
  Akonadi és kdepim-addons nélkül.

  FIGYELEM: ha az Event Calendar és a beépített óra PIM pluginja
  EGYSZERRE fut, a régi fagyás visszatérhet. A beépített óra
  PIM-jét előbb kapcsold ki:  bash kde-pim-kikapcsolas.sh
  ------------------------------------------------------------
EOF
