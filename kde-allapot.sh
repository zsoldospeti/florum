#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.2  ·  KDE-állapot ellenőrzés (csak olvas, nem módosít)
#  Fájl:    kde-allapot.sh
#  Futtatás:  bash kde-allapot.sh
#  Mit néz meg?
#    * telepítve van-e a kdepim-addons / korganizer / libnotify,
#    * fut-e az Akonadi (a KDE naptár-adatbázis) és van-e benne naptár,
#    * be van-e kapcsolva a Digitális óra PIM pluginja (és hol a beállítás),
#    * látszik-e a Florum naptárfájlja és hány esemény van benne,
#    * működik-e az értesítés.
# ==============================================================
set -uo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${FLORUM_DATA:-$HOME/.local/share/florum}"
ICS="$DATA/florum.ics"
OK="  ✓"; NO="  ✗"; WARN="  !"

echo
echo "  🌿 Florum – KDE-állapot"
echo "  ------------------------------------------------------------"

# ---- 1) csomagok
echo
echo "  1) Csomagok"
if command -v pacman >/dev/null 2>&1; then
  for csomag in kdepim-addons korganizer akonadi libnotify plasma-workspace; do
    if pacman -Qq "$csomag" >/dev/null 2>&1; then
      printf "%s %-22s %s\n" "$OK" "$csomag" "$(pacman -Q "$csomag" 2>/dev/null | awk '{print $2}')"
    else
      printf "%s %-22s nincs telepítve\n" "$NO" "$csomag"
    fi
  done
  echo "     (a PIM pluginhoz kell: kdepim-addons; az értesítéshez: libnotify)"
else
  echo "$WARN nem pacman-alapú rendszer – a csomagokat kézzel ellenőrizd"
fi

# ---- 2) Akonadi
echo
echo "  2) Akonadi (a KDE naptár-háttér)"
if command -v akonadictl >/dev/null 2>&1; then
  allapot="$(akonadictl status 2>&1 | tr '\n' ' ')"
  echo "     $allapot"
  if printf '%s' "$allapot" | grep -qi "running"; then
    echo "$OK fut"
    if command -v akonadictl >/dev/null 2>&1; then
      eroforrasok="$(akonadictl fsck 2>/dev/null | head -3)"
      [ -n "$eroforrasok" ] && echo "     fsck: $eroforrasok"
    fi
  else
    echo "$NO nem fut – indítsd: akonadictl start (a KDE általában magától indítja)"
  fi
else
  echo "$NO nincs akonadictl – az Akonadi (kdepim-runtime) nincs telepítve"
  echo "     Ez esetben a Digitális óra PIM fülén nem is lesz mit választani."
fi

# iCal-erőforrás konfigurációk
mapfile -t res < <(ls "$HOME/.config"/akonadi_ical_resource_*.rc 2>/dev/null)
if [ "${#res[@]}" -gt 0 ]; then
  for f in "${res[@]}"; do
    utvonal="$(grep -m1 '^Path' "$f" 2>/dev/null | cut -d= -f2-)"
    printf "%s iCal-erőforrás: %s\n     útvonal: %s\n" "$OK" "$(basename "$f")" "${utvonal:-?}"
    case "$utvonal" in
      *florum.ics*) echo "     → erre mutat a Florum naptárfájlja (jó)" ;;
    esac
  done
else
  echo "$WARN nincs iCal-erőforrás (akonadi_ical_resource_*.rc)"
fi

# ---- 3) Digitális óra beállítása
echo
echo "  3) Digitális óra – naptár-pluginok"
PLASMARCS="$HOME/.config/plasmashellrc"
APPLETSRC="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
PIM_SOR="$(grep -h '^calendars=' "$PLASMARCS" 2>/dev/null | head -1 | cut -d= -f2-)"
PIM_NEM_UERES=0
[ -n "${PIM_SOR//,/}" ] && PIM_NEM_UERES=1
if [ "$PIM_NEM_UERES" = "1" ]; then
  echo "$WARN a PIM plugin be van állítva naptárakkal (ez fagyaszthat, ha sok az esemény):"
  echo "     calendars=$PIM_SOR"
  echo "     Kikapcsolás: bash kde-pim-kikapcsolas.sh"
elif grep -qs "PIMEventsPlugin" "$PLASMARCS" "$APPLETSRC" 2>/dev/null; then
  echo "$OK a PIM plugin be van állítva, de nincs kijelölt naptár (nem fagyaszthat)"
else
  echo "$OK nincs PIM plugin beállítás (a panel naptára nem olvas Akonadiból)"
fi
if grep -qs "enabledCalendarPlugins" "$APPLETSRC" 2>/dev/null; then
  echo "     applet-beállítás: $(grep -h "enabledCalendarPlugins" "$APPLETSRC" | head -1)"
fi

# ---- 4) Florum naptárfájl
echo
echo "  4) Florum naptárfájl"
if [ -f "$ICS" ]; then
  db="$(grep -c '^BEGIN:VEVENT' "$ICS" 2>/dev/null || echo 0)"
  echo "$OK $ICS"
  echo "     események: $db · utolsó írás: $(date -r "$ICS" '+%Y-%m-%d %H:%M' 2>/dev/null)"
  if [ "$db" -ge 120 ]; then
    echo "$WARN sok esemény – a KDE PIM plugin ilyenkor hajlamos fagyni."
    echo "     Csökkentsd a Beállításokban az előretekintést (30–60 nap), vagy maradjon a démon."
  fi
  if ! grep -q "^BEGIN:VCALENDAR" "$ICS"; then
    echo "$NO a fájl nem tűnik érvényes .ics-nek"
  fi
else
  echo "$WARN nincs $ICS – indítsd egyszer a Florumot: python3 florum.py --no-browser"
fi

# ---- 5) Értesítés
echo
echo "  5) Értesítés"
if command -v notify-send >/dev/null 2>&1; then
  echo "$OK notify-send megvan – próba: python3 emlekezteto.py --teszt"
else
  echo "$NO nincs notify-send – telepítés: sudo pacman -S libnotify"
fi
if command -v systemctl >/dev/null 2>&1; then
  if systemctl --user is-active florum-emlekezteto.service >/dev/null 2>&1; then
    echo "$OK a Florum emlékeztető démon fut (systemd --user)"
  else
    echo "$WARN a démon nem fut – bekapcsolás: systemctl --user enable --now florum-emlekezteto"
  fi
fi

# ---- 6) Mai teendők (ha van python)
echo
echo "  6) Mai teendők"
if command -v python3 >/dev/null 2>&1 && [ -f "$DIR/emlekezteto.py" ]; then
  python3 "$DIR/emlekezteto.py" --lista 2>/dev/null | sed 's/^/     /' || echo "$WARN nem sikerült kiolvasni"
else
  echo "$WARN nincs python3 vagy emlekezteto.py"
fi

echo
echo "  ------------------------------------------------------------"
echo "  Ha a PIM fül üres / a panel lefagy:"
echo "    1) bash kde-pim-kikapcsolas.sh      (a plugin kikapcsolása)"
echo "    2) python3 emlekezteto.py --daemon  (értesítés Akonadi nélkül)"
echo "    3) akonadi nélküli panel: Event Calendar plasmoid (.ics)"
echo
