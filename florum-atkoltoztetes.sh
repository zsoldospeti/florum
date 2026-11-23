#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.3  ·  az adatok átköltöztetése saját mappába
#  Fájl:    florum-atkoltoztetes.sh
#
#  MIÉRT KELL EZ, HA VAN --data-dir?
#    A `python3 florum.py --data-dir /saját/mappa` csak ARRA az egy
#    indításra érvényes. Ha utána a panelről vagy a menüből indítod,
#    a Florum visszaáll az alapértelmezett mappára, és úgy tűnik,
#    mintha elveszett volna minden növény.
#    Ez a szkript átmásolja az adatokat, és BEÍRJA a mappát a
#    florum-adat.conf-ba – onnantól minden indító (menü, panel,
#    frissítő, háttérszolgáltatás) azt használja.
#
#  Használat:
#     bash florum-atkoltoztetes.sh ~/Florum-adat
#     bash florum-atkoltoztetes.sh --cel /home/…/Florum-adat
#     bash florum-atkoltoztetes.sh ~/Florum-adat --dry-run
#     bash florum-atkoltoztetes.sh ~/Florum-adat --ne-inditsd
#     bash florum-atkoltoztetes.sh --vissza          # alapértelmezett mappára
#     bash florum-atkoltoztetes.sh --mi              # melyik mappát használja?
#
#  A régi mappát NEM törli (biztonsági másolat marad).
# ==============================================================
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF="$HERE/florum-adat.conf"
PY="${PYTHON:-python3}"
PORT="${FLORUM_PORT:-8777}"

CEL=""; DRY=0; INDITSD=1; VISSZA=0; MI=0
while [ $# -gt 0 ]; do
  case "$1" in
    --cel) shift; CEL="${1:-}" ;;
    --cel=*) CEL="${1#--cel=}" ;;
    --dry-run|--dryrun) DRY=1 ;;
    --ne-inditsd) INDITSD=0 ;;
    --vissza) VISSZA=1 ;;
    --mi) MI=1 ;;
    -h|--help) sed -n '2,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "  ✗ ismeretlen kapcsoló: $1"; exit 2 ;;
    *) CEL="$1" ;;
  esac
  shift
done

# ---- jelenlegi mappa (ugyanaz a sorrend, mint a megnyitóban)
jelenlegi() {
  local v="${FLORUM_DATA:-}"
  if [ -z "$v" ] && [ -f "$CONF" ]; then
    v="$(sed -n 's/^[[:space:]]*DATA_DIR[[:space:]]*=[[:space:]]*//p' "$CONF" | head -1)"
    v="${v%\"}"; v="${v#\"}"
  fi
  if [ -z "$v" ]; then v="$HOME/.local/share/florum"; fi
  printf '%s\n' "$v"
}

JELEN="$(jelenlegi)"

if [ "$MI" -eq 1 ]; then
  echo "  Florum – melyik mappát használja?"
  echo "    éppen ez:      $JELEN"
  [ -f "$CONF" ] && echo "    beállítva itt: $CONF"
  if [ -d "$JELEN" ]; then
    echo "    tartalom:"
    for f in florum-data.json florum.ics photos mentes; do
      if [ -e "$JELEN/$f" ]; then
        if [ -d "$JELEN/$f" ]; then
          echo "      ✓ $f/  ($(find "$JELEN/$f" -type f 2>/dev/null | wc -l) fájl)"
        else
          echo "      ✓ $f  ($(du -h "$JELEN/$f" 2>/dev/null | cut -f1))"
        fi
      fi
    done
  else
    echo "    (a mappa még nem létezik – az első mentéskor jön létre)"
  fi
  command -v curl >/dev/null 2>&1 && {
    valasz="$(curl -s --max-time 2 "http://127.0.0.1:$PORT/api/info" 2>/dev/null || true)"
    if [ -n "$valasz" ]; then
      echo "    futó példány:  $(printf '%s' "$valasz" | "$PY" -c 'import json,sys;d=json.load(sys.stdin);print(d.get("appVersion"),"→",d.get("dataDir"))' 2>/dev/null)"
    fi
  }
  exit 0
fi

# ---- vissza az alapértelmezettre
if [ "$VISSZA" -eq 1 ]; then
  echo "  Florum – vissza az alapértelmezett adatmappára"
  if [ "$DRY" -eq 1 ]; then
    echo "  [dry] törölném: $CONF"
    echo "  [dry] alapértelmezés: $HOME/.local/share/florum"
    exit 0
  fi
  rm -f "$CONF"
  echo "  ✓ a florum-adat.conf törölve – minden indító az alapértelmezettet használja"
  echo "     ($HOME/.local/share/florum)"
  if command -v systemctl >/dev/null 2>&1 && systemctl --user is-active florum-szerver >/dev/null 2>&1; then
    systemctl --user restart florum-szerver 2>/dev/null && echo "  ✓ háttérszerver újraindítva"
  fi
  exit 0
fi

if [ -z "$CEL" ]; then
  echo "  Használat:  bash florum-atkoltoztetes.sh ~/Florum-adat"
  echo "  (a mappa jön létre; a régi adatok átmásolódnak, semmi nem törlődik)"
  exit 2
fi

# ---- a cél kiszámítása
CEL="${CEL/#\~/$HOME}"
case "$CEL" in
  /*) : ;;
  *) CEL="$PWD/$CEL" ;;
esac
CEL="$(cd "$(dirname "$CEL")" 2>/dev/null && pwd || echo "$(dirname "$CEL")")/$(basename "$CEL")"

echo
echo "  🌿 Florum – adatok átköltöztetése"
echo "  ------------------------------------------------------------"
echo "    honnan:  $JELEN"
echo "    ide:     $CEL"
echo

if [ "$CEL" = "$JELEN" ]; then
  echo "  A kettő ugyanaz – nincs mit átköltöztetni."
  exit 0
fi

if [ "$DRY" -eq 1 ]; then
  echo "  [dry] létrehoznám: $CEL"
  echo "  [dry] átmásolnám:  florum-data.json, .bak, photos/, mentes/, florum.ics, notify-state.json"
  echo "  [dry] beírnám ide:  $CONF  →  DATA_DIR=\"$CEL\""
  echo "  [dry] újraindítanám a háttérszervert a(z) $PORT porton, ezzel a mappával"
  exit 0
fi

# ---- 1) futó példány leállítása
if [ "$INDITSD" -eq 1 ]; then
  if command -v curl >/dev/null 2>&1 && curl -s --max-time 2 "http://127.0.0.1:$PORT/api/info" >/dev/null 2>&1; then
    echo "  · a futó példány leállítása…"
    "$PY" "$HERE/florum.py" --leallit --port "$PORT" >/dev/null 2>&1 || true
    sleep 1
  fi
fi

# ---- 2) másolás (a florum.py végzi, ellenőrzéssel)
echo "  · másolás…"
if ! "$PY" "$HERE/florum.py" --data-dir "$JELEN" --atkoltoztetes "$CEL"; then
  echo "  ✗ Az átköltöztetés nem sikerült – a régi mappa érintetlen."
  exit 1
fi

# ---- 3) a mappa megjegyzése
cat > "$CONF" <<CONF
# Florum – hol vannak az adatok (ezt a florum-atkoltoztetes.sh írta)
# A florum-megnyitas.sh, a florum-frissites.sh és a szolgáltatás ezt használja.
DATA_DIR="$CEL"
CONF
echo
echo "  ✓ beállítva: $CONF"
echo "     DATA_DIR=\"$CEL\""

# ---- 4) háttérszerver újraindítása az új mappával
if [ "$INDITSD" -eq 1 ]; then
  if command -v systemctl >/dev/null 2>&1 && systemctl --user is-enabled florum-szerver >/dev/null 2>&1; then
    systemctl --user restart florum-szerver 2>/dev/null && echo "  ✓ háttérszerver (systemd) újraindítva"
  else
    echo "  · háttérszerver indítása az új mappával…"
    ( cd "$HERE" && setsid nohup "$PY" "$HERE/florum.py" --szerver --port "$PORT" \
        --host 127.0.0.1 --data-dir "$CEL" >/dev/null 2>&1 & )
    for i in $(seq 1 20); do
      sleep 0.4
      if command -v curl >/dev/null 2>&1 && curl -s --max-time 1 "http://127.0.0.1:$PORT/api/info" >/dev/null 2>&1; then
        echo "  ✓ háttérszerver elindult (port $PORT)"
        break
      fi
    done
  fi
  # ellenőrzés: tényleg az új mappát használja?
  if command -v curl >/dev/null 2>&1; then
    fut="$(curl -s --max-time 3 "http://127.0.0.1:$PORT/api/info" 2>/dev/null || true)"
    if [ -n "$fut" ]; then
      printf '%s' "$fut" | "$PY" -c '
import json, sys
d = json.load(sys.stdin)
cel = sys.argv[1]
print("  ellenőrzés: a futó Florum adatmappája: " + str(d.get("dataDir")))
if str(d.get("dataDir")) != cel:
    print("  ⚠ FIGYELEM: a futó példány még a régi mappát használja!")
    sys.exit(1)
print("  ✓ a futó példány már az új mappát használja")
' "$CEL" || true
    fi
  fi
fi

echo
echo "  Kész. A régi mappa megmaradt: $JELEN"
echo "  Ha biztosan minden átjött, később törölheted – előbb nézd meg a Naplót a felületen."
echo
echo "  Mostantól:  bash florum-megnyitas.sh    (ez már az új mappát használja)"
echo "  Ellenőrzés: bash florum-atkoltoztetes.sh --mi"
echo
