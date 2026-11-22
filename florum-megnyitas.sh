#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.2  ·  EGYETLEN indító (a panel-widgethez és a menühöz)
#  Fájl:    florum-megnyitas.sh
#
#  MIÉRT VAN EZ?
#    Eddig KÉT indító létezett:
#       florum.desktop      → python3 florum.py --app   (böngésző/Chromium)
#       florum-kde.desktop  → florum-kde (saját KDE-ablak)
#    Ha mindkettő kikerült a panelre, két Florum-ikon látszott. Ez a
#    szkript EGY belépési pont: eldönti, mit kell nyitni, és ha kell,
#    elindítja a háttérszervert is.
#
#  Használat:
#     bash florum-megnyitas.sh              # megnyitás (a legjobb móddal)
#     bash florum-megnyitas.sh --kde        # mindig a KDE-ablak
#     bash florum-megnyitas.sh --bongeszo   # mindig böngésző
#     bash florum-megnyitas.sh --csak-url   # csak kiírja a címet
#     bash florum-megnyitas.sh --dry-run    # nem csinál semmit, csak megmondja
#     bash florum-megnyitas.sh --allapot    # mi fut most?
#
#  Kilépési kód: 0 = rendben, 2 = nem sikerült megnyitni
# ==============================================================
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${FLORUM_PORT:-8777}"

# ---- hol vannak az adatok? --------------------------------------------------
# Sorrend: FLORUM_DATA környezeti változó → florum-adat.conf (a program mellett)
#          → a Florum alapértelmezése (~/.local/share/florum).
# Így a --data-dir nem csak EGY indításra érvényes: a megnyitó megjegyzi.
ADAT="${FLORUM_DATA:-}"
if [ -z "$ADAT" ] && [ -f "$HERE/florum-adat.conf" ]; then
  # a fájl egyetlen érdemi sora:  DATA_DIR=/valami/utvonal
  ADAT="$(sed -n 's/^[[:space:]]*DATA_DIR[[:space:]]*=[[:space:]]*//p' "$HERE/florum-adat.conf" | head -1)"
  ADAT="${ADAT%\"}"
  ADAT="${ADAT#\"}"
fi
ADAT_ARG=()
if [ -n "$ADAT" ]; then
  ADAT_ARG=(--data-dir "$ADAT")
fi
MOD="auto"
DRY=0
CSAK_URL=0
ALLAPOT=0

for arg in "$@"; do
  case "$arg" in
    --kde)        MOD="kde" ;;
    --bongeszo)   MOD="bongeszo" ;;
    --auto)       MOD="auto" ;;
    --csak-url)   CSAK_URL=1 ;;
    --dry-run|--dryrun) DRY=1 ;;
    --allapot)    ALLAPOT=1 ;;
    -h|--help)
      sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0 ;;
  esac
done

mond() { printf '%s\n' "$*"; }
dry()  { printf '  [dry] %s\n' "$*"; }
lepes(){ [ "$DRY" -eq 1 ] || printf '  · %s\n' "$*"; }

# ---------------------------------------------------------------- 1. szerver
szerver_el() {
  python3 - "$PORT" <<'PY' >/dev/null 2>&1
import json, sys, urllib.request
port = sys.argv[1]
try:
    with urllib.request.urlopen("http://127.0.0.1:%s/api/info" % port, timeout=1.5) as r:
        d = json.loads(r.read().decode("utf-8"))
    sys.exit(0 if d.get("app") == "Florum" else 1)
except Exception:
    sys.exit(1)
PY
}

szerver_indit() {
  lepes "a háttérszerver nem fut – indítom (port $PORT)"
  if [ "$DRY" -eq 1 ]; then
    dry "python3 florum.py --szerver --port $PORT --host 127.0.0.1 ${ADAT_ARG[*]}"
    return 0
  fi
  ( cd "$HERE" && setsid nohup python3 "$HERE/florum.py" --szerver --port "$PORT" --host 127.0.0.1 "${ADAT_ARG[@]}" \
      >/dev/null 2>&1 & ) || return 1
  for i in $(seq 1 20); do
    sleep 0.4
    szerver_el && { lepes "szerver elindult"; return 0; }
  done
  return 1
}

URL="http://127.0.0.1:$PORT/"

if [ "$ALLAPOT" -eq 1 ]; then
  mond "Florum – mi fut?"
  if szerver_el; then mond "  ✓ háttérszerver: fut ($URL)"; else mond "  ✗ háttérszerver: nem fut (port $PORT)"; fi
  for p in florum-kde.py florum.py; do
    if pgrep -f "$p" >/dev/null 2>&1; then mond "  ✓ folyamat: $p"; fi
  done
  if python3 -c "import PySide6" >/dev/null 2>&1; then
    mond "  ✓ PySide6 megvan (saját KDE-ablak lehetséges)"
  else
    mond "  · PySide6 nincs (a KDE-ablakhoz: sudo pacman -S pyside6 pyside6-webengine)"
  fi
  if [ -n "$ADAT" ]; then mond "  · adatmappa: $ADAT (beállítva)"; else mond "  · adatmappa: alapértelmezés (~/.local/share/florum)"; fi
  for eszkoz in kdotool wmctrl xdotool; do
    command -v "$eszkoz" >/dev/null 2>&1 && mond "  ✓ ablakkezelő segéd: $eszkoz"
  done
  exit 0
fi

if [ "$CSAK_URL" -eq 1 ]; then
  szerver_el || { [ "$DRY" -eq 1 ] && dry "szervert indítanék"; }
  mond "$URL"
  exit 0
fi

if [ "$DRY" -eq 1 ]; then
  mond "Florum – megnyitás (próba, nem változtat semmit)"
  if szerver_el; then dry "a háttérszerver fut ($URL) – nem indítok újat"; else dry "a háttérszerver nem fut → indítanék: florum.py --szerver --port $PORT"; fi
  if pgrep -f "florum-kde.py" >/dev/null 2>&1; then
    dry "a KDE-ablak már fut → előtérbe hoznám (kdotool/wmctrl/xdotool)"
  elif command -v python3 >/dev/null 2>&1 && python3 -c "import PySide6" >/dev/null 2>&1 && [ -f "$HERE/florum-kde.py" ]; then
    dry "KDE-ablakot nyitnék: python3 florum-kde.py"
  else
    dry "böngésző/Chromium app-módot nyitnék: python3 florum.py --app"
  fi
  case "$MOD" in
    kde)      dry "mód: --kde (mindig a KDE-ablak)" ;;
    bongeszo) dry "mód: --bongeszo (mindig a böngésző)" ;;
    *)        dry "mód: auto (a legjobb elérhető)" ;;
  esac
  if [ -n "$ADAT" ]; then dry "adatmappa: $ADAT"; else dry "adatmappa: alapértelmezés (~/.local/share/florum)"; fi
  exit 0
fi

szerver_el || szerver_indit || { mond "  ✗ A háttérszervert nem sikerült elindítani. Próbáld: python3 \"$HERE/florum.py\" --szerver"; exit 2; }

# ---------------------------------------------------------------- 2. ablak
# Előtérbe hozás, ha már nyitva van (a felhasználónak ne legyen 2 ablaka)
eloterbe() {
  if command -v kdotool >/dev/null 2>&1; then
    kdotool search --class florum-kde windowactivate >/dev/null 2>&1 && return 0
  fi
  if command -v wmctrl >/dev/null 2>&1; then
    wmctrl -a "Florum" >/dev/null 2>&1 && return 0
  fi
  if command -v xdotool >/dev/null 2>&1; then
    xdotool search --class florum-kde windowactivate >/dev/null 2>&1 && return 0
  fi
  return 1
}

van_kde_ablak() { pgrep -f "florum-kde.py" >/dev/null 2>&1; }
van_pyside()    { python3 -c "import PySide6" >/dev/null 2>&1; }

case "$MOD" in
  bongeszo)
    lepes "böngésző / Chromium app-mód"
    ( cd "$HERE" && setsid nohup python3 "$HERE/florum.py" --app "${ADAT_ARG[@]}" >/dev/null 2>&1 & )
    ;;
  kde)
    if van_kde_ablak && eloterbe; then lepes "a KDE-ablak előtérben"; exit 0; fi
    if van_pyside && [ -f "$HERE/florum-kde.py" ]; then
      lepes "KDE-ablak indítása"
      ( cd "$HERE" && setsid nohup python3 "$HERE/florum-kde.py" >/dev/null 2>&1 & )
    else
      lepes "PySide6 nincs – böngészőben nyitom"
      ( cd "$HERE" && setsid nohup python3 "$HERE/florum.py" --app "${ADAT_ARG[@]}" >/dev/null 2>&1 & )
    fi
    ;;
  *)
    if van_kde_ablak && eloterbe; then lepes "a KDE-ablak előtérben"; exit 0; fi
    if van_pyside && [ -f "$HERE/florum-kde.py" ]; then
      lepes "KDE-ablak indítása (a legjobb mód ezen a gépen)"
      ( cd "$HERE" && setsid nohup python3 "$HERE/florum-kde.py" >/dev/null 2>&1 & )
    else
      lepes "böngésző / Chromium app-mód"
      ( cd "$HERE" && setsid nohup python3 "$HERE/florum.py" --app "${ADAT_ARG[@]}" >/dev/null 2>&1 & )
    fi
    ;;
esac

exit 0
