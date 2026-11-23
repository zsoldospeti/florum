#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.4  ·  frissítés után: „még mindig a régi verzió”
#  Fájl:    florum-frissites.sh
#
#  MIT TESZ?
#    1. megmutatja, mi fut most (verzió, folyamat, port)
#    2. leállítja a futó Florumot (a régi kód a memóriában marad,
#       amíg a folyamat él – ezért látszik „felül új, lent régi”)
#    3. újraindítja: systemd --user szolgáltatásként, ha van ilyen,
#       különben háttérben (florum.py --szerver)
#    4. ellenőrzi, hogy a FUTÓ verzió már a fájlé-e
#
#  Használat:
#      bash florum-frissites.sh
#      bash florum-frissites.sh --csak-nez        # csak megmutatja, nem indít
# ==============================================================
set -u

ITT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT="${FLORUM_PORT:-8777}"
DATA="${FLORUM_DATA:-$HOME/.local/share/florum}"
PY=python3

zold()  { printf '\033[32m%s\033[0m\n' "$*"; }
sarga() { printf '\033[33m%s\033[0m\n' "$*"; }
piros() { printf '\033[31m%s\033[0m\n' "$*"; }
cim()   { printf '\n\033[1m%s\033[0m\n' "$*"; }

fajl_verzio() { [ -f "$ITT/VERSION" ] && cat "$ITT/VERSION" || echo "?"; }
futo_verzio() {
  curl -s --max-time 3 "http://127.0.0.1:$PORT/api/info" 2>/dev/null \
    | $PY -c 'import json,sys
try:
    print(json.load(sys.stdin).get("appVersion","?"))
except Exception:
    print("nincs")'
}

CSAK_NEZ=0
[ "${1:-}" = "--csak-nez" ] && CSAK_NEZ=1

cim "1) Mi fut most?"
FAJL="$(fajl_verzio)"
FUTO="$(futo_verzio)"
echo "   a fájl verziója:   $FAJL"
echo "   a futó szerver:    $FUTO   (port: $PORT)"
if [ "$FUTO" = "nincs" ]; then
  sarga "   · most nem fut szerver – a 3. lépés elindítja"
elif [ "$FUTO" = "$FAJL" ]; then
  zold "   ✓ egyeznek – nincs tennivaló"
else
  sarga "   ⚠ eltérnek – a régi példány még fut a memóriában"
fi

if [ "$CSAK_NEZ" = "1" ]; then
  exit 0
fi

cim "2) A futó példány(ok) leállítása"
if $PY "$ITT/florum.py" --leallit --port "$PORT" --data-dir "$DATA"; then
  :
else
  sarga "   (a leállítás nem sikerült – talán nincs is mit)"
fi
sleep 1

cim "3) Újraindítás"
if command -v systemctl >/dev/null 2>&1 \
   && systemctl --user list-unit-files 2>/dev/null | grep -q '^florum-szerver\.service'; then
  zold "   szolgáltatásként (systemd --user)"
  systemctl --user restart florum-szerver
  sleep 2
  systemctl --user --no-pager status florum-szerver | sed -n '1,6p'
else
  sarga "   nincs systemd egység – háttérben indítom"
  # teljesen leválasztva: a terminál azonnal visszakapja a vezérlést
  cd "$ITT" || exit 1
  setsid $PY florum.py --szerver --port "$PORT" --data-dir "$DATA" --notify \
      </dev/null >/dev/null 2>&1 &
  disown 2>/dev/null || true
  cd - >/dev/null 2>&1 || true
  for i in $(seq 1 30); do
    sleep 0.4
    [ "$(futo_verzio)" != "nincs" ] && break
  done
fi

cim "4) Ellenőrzés"
UJ="$(futo_verzio)"
echo "   a futó szerver most: $UJ"
if [ "$UJ" = "$FAJL" ]; then
  zold "   ✓ rendben – ugyanaz a verzió fut, mint ami a gépen van"
  echo
  echo "   A böngészőben nyomj egy erős újratöltést:  Ctrl+Shift+R"
  echo "   (a régi lap a memóriában tartja a régi felületet)"
else
  piros "   ✗ a futó verzió ($UJ) még mindig nem a fájlé ($FAJL)"
  echo "   Nézd meg kézzel:  ps -eo pid,cmd | grep florum.py"
  echo "   és:               python3 \"$ITT/florum.py\" --verzio"
  exit 1
fi
