#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.3  ·  a Digitális óra PIM pluginjának kikapcsolása
#  Fájl:    kde-pim-kikapcsolas.sh
#  Futtatás:  bash kde-pim-kikapcsolas.sh
#
#  MIÉRT KELL?
#  A KDE Digitális óra naptár-pluginnál ismert hiba (bugs.kde.org
#  526769, 493415, 523046): ha egy Akonadi-naptár sok eseményt
#  tartalmaz, vagy egyszerre sok minden változik, a plasmashell
#  (a panel) lefagy. A KDE-fórumon ismert kerülőút: a naptár-
#  kijelölést ÚGY kell módosítani, hogy közben a plasmashell NEM fut
#  – így a plugin indításkor csak hozzáad, nem töröl.
#
#  Ez a szkript:
#    1) biztonsági mentést készít a beállításfájlokról (~/florum-kde-backup-*),
#    2) leállítja a plasmashelt,
#    3) kiveszi a PIM plugin beállítását a konfigurációból,
#    4) újraindítja a plasmashelt.
#
#  Visszakapcsolás: a mentett fájlokat másold vissza (az útvonalat
#  a szkript kiírja a végén).
# ==============================================================
set -uo pipefail

RCS=("$HOME/.config/plasmashellrc" "$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc")
MAPPA="$HOME/florum-kde-backup-$(date +%Y%m%d-%H%M%S)"

echo
echo "  🌿 Florum – KDE PIM plugin kikapcsolása"
echo "  ------------------------------------------------------------"
echo

if [ "${1:-}" != "--csak-nezet" ]; then
  mkdir -p "$MAPPA" 2>/dev/null
  for f in "${RCS[@]}"; do
    if [ -f "$f" ]; then
      cp -a "$f" "$MAPPA/" 2>/dev/null && echo "  ✓ mentve: $f"
    fi
  done
  echo "  Biztonsági mentés: $MAPPA"
  echo
fi

# ---- 1) plasmashell leállítása (a fagyás elkerülésének kulcslépése)
if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active plasma-plasmashell.service >/dev/null 2>&1; then
  echo "  → plasma-plasmashell leállítása…"
  systemctl --user stop plasma-plasmashell.service
  ALUDT=1
elif pgrep -x plasmashell >/dev/null 2>&1; then
  echo "  → plasmashell leállítása (kill)…"
  pkill -x plasmashell
  ALUDT=1
else
  echo "  ! a plasmashell nem fut (nem baj)"
  ALUDT=0
fi
[ "${ALUDT:-0}" = "1" ] && sleep 2

# ---- 2) a PIM beállítás kivétele
if command -v kwriteconfig6 >/dev/null 2>&1; then
  for f in "${RCS[@]}"; do
    [ -f "$f" ] || continue
    # a PIM csoport kiürítése (a plugin így nem indul el)
    kwriteconfig6 --file "$f" --group PIMEventsPlugin --key calendars "" 2>/dev/null
  done
  echo "  ✓ PIMEventsPlugin → calendars üres"
else
  # kézi tartalék: a [PIMEventsPlugin] szakasz "calendars=" sorát ürítjük
  for f in "${RCS[@]}"; do
    [ -f "$f" ] || continue
    python3 - "$f" <<'PY' 2>/dev/null || sed -i 's/^calendars=.*/calendars=/' "$f"
import io, sys, re
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
s = re.sub(r"(?m)^calendars=.*$", "calendars=", s)
io.open(p, "w", encoding="utf-8").write(s)
PY
  done
  echo "  ✓ calendars= ürítve (kézi mód)"
fi

# az applet-oldali engedélyezett pluginok listájából is kivesszük a PIM-et
APPLETS="$HOME/.config/plasma-org.kde.plasma.desktop-appletsrc"
if [ -f "$APPLETS" ] && command -v python3 >/dev/null 2>&1; then
  python3 - "$APPLETS" <<'PY'
import io, re, sys
p = sys.argv[1]
s = io.open(p, encoding="utf-8").read()
uj = re.sub(r"(?m)^(enabledCalendarPlugins=.*?)pimeventsplugin,?", r"\1", s)
uj = re.sub(r"(?m)^(enabledCalendarPlugins=.*?),pimeventsplugin", r"\1", uj)
if uj != s:
    io.open(p, "w", encoding="utf-8").write(uj)
    print("  ✓ enabledCalendarPlugins: pimeventsplugin kivéve")
else:
    print("  · az applet-beállításban nem szerepelt a plugin")
PY
fi

# ---- 3) plasmashell visszaindítása
if [ "${ALUDT:-0}" = "1" ]; then
  echo "  → plasmashell újraindítása…"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user start plasma-plasmashell.service 2>/dev/null \
      || (nohup plasmashell >/dev/null 2>&1 &)
  else
    (nohup plasmashell >/dev/null 2>&1 &)
  fi
  sleep 1
fi

echo
echo "  ------------------------------------------------------------"
echo "  Kész. A Digitális óra most nem olvas Akonadiból, tehát nem fog"
echo "  lefagyasztani. A Florum teendői két másik úton továbbra is"
echo "  elérhetők:"
echo
echo "    python3 emlekezteto.py --daemon     # asztali értesítés (Akonadi nélkül)"
echo "    systemctl --user enable --now florum-emlekezteto"
echo
echo "  Visszakapcsolás (ha később mégis kell a panel-naptár):"
echo "    cp $MAPPA/* ~/.config/ && systemctl --user restart plasma-plasmashell"
echo
