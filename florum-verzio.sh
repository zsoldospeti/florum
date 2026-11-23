#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.3  ·  „Felül új, lent régi” – verzió-ellenőrzés
#  Fájl:  florum-verzio.sh
#
#  Megmutatja, MI FUT valójában:
#    · mi van a fájlokban (VERSION, florum.py, florum.html)
#    · milyen Florum-folyamatok élnek, mióta
#    · melyik port mit vall magáról (/api/info)
#  és megmondja, mit kell tenni.
#
#  Használat:
#      bash florum-verzio.sh            # csak megnéz
#      bash florum-verzio.sh --leallit  # a futó példány(ok) leállítása
#      bash florum-verzio.sh --ujraindit  # leállít + háttérben újraindít
# ==============================================================
set -u

ITT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOD="${1:-}"

zold=$'\033[32m'; piros=$'\033[31m'; sarga=$'\033[33m'; halv=$'\033[2m'; nincs=$'\033[0m'
if [ ! -t 1 ]; then zold=""; piros=""; sarga=""; halv=""; nincs=""; fi

fejlec(){ printf "\n%s\n" "=============================================================="; printf " %s\n" "$1"; printf "%s\n" "=============================================================="; }

# ---------- 1) mi van a fájlokban?
fejlec "1) A FÁJLOK verziója (amit felraktál)"

FAJL_VER="(nincs VERSION fájl)"
[ -f "$ITT/VERSION" ] && FAJL_VER="$(tr -d ' \n\r' < "$ITT/VERSION")"
PY_VER="$(grep -m1 '^APP_VERSION' "$ITT/florum.py" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/')"
HTML_VER="$(grep -m1 'name="florum-version"' "$ITT/florum.html" 2>/dev/null | sed 's/.*content="\([^"]*\)".*/\1/')"
DB_VER="$(python3 - "$ITT/plants-db.json" <<'PY' 2>/dev/null || true
import json,sys
try:
    d=json.load(open(sys.argv[1], encoding="utf-8"))
    print("%s (%d növény)" % (d.get("version","?"), len(d.get("plants",[]))))
except Exception:
    print("?")
PY
)"
printf "  VERSION fájl:        %s\n" "$FAJL_VER"
printf "  florum.py:           %s\n" "${PY_VER:-(nincs)}"
printf "  florum.html:         %s\n" "${HTML_VER:-(nincs meta)}"
printf "  plants-db.json:      %s\n" "${DB_VER:-?}"
printf "  mappa:               %s\n" "$ITT"

# ---------- 2) mi fut?
fejlec "2) MI FUT most a gépen"

FOLYAMATOK="$(ps -eo pid,lstart,args 2>/dev/null | grep '[f]lorum\.py' || true)"
if [ -z "$FOLYAMATOK" ]; then
  printf "  ${halv}nincs futó florum.py folyamat${nincs}\n"
else
  printf "%s\n" "$FOLYAMATOK" | while IFS= read -r sor; do
    printf "  %s\n" "$sor"
  done
fi

# rendszerd-szolgáltatás?
if systemctl --user is-active --quiet florum-szerver 2>/dev/null; then
  printf "  florum-szerver.service: ${zold}fut${nincs}\n"
elif systemctl --user status florum-szerver >/dev/null 2>&1; then
  printf "  florum-szerver.service: ${halv}nem fut${nincs}\n"
else
  printf "  florum-szerver.service: ${halv}nincs telepítve${nincs}\n"
fi

# ---------- 3) melyik port mit mond?
fejlec "3) MIT VALL MAGÁRÓL a futó példány (/api/info)"

PORTOK="8777 8778 8779 8780"   # duplikátumokat lásd lent
# ha van szerver.json, abból is
for j in "$HOME/.local/share/florum/szerver.json" "$ITT/szerver.json" /tmp/fotodemo/szerver.json; do
  [ -f "$j" ] || continue
  p="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('port',''))" "$j" 2>/dev/null || true)"
  [ -n "${p:-}" ] && PORTOK="$PORTOK $p"
done

# duplikátumok kiszűrése (a szerver.json ugyanazt a portot is hozhatja)
EGYEDI=""
for p in $PORTOK; do
  case " $EGYEDI " in *" $p "*) continue;; esac
  EGYEDI="$EGYEDI $p"
done
PORTOK="$EGYEDI"

FUTOTT_VER=""
for p in $PORTOK; do
  valasz="$(curl -s --max-time 2 "http://127.0.0.1:$p/api/info" 2>/dev/null || true)"
  if [ -z "$valasz" ]; then
    printf "  %-5s ${halv}nem válaszol${nincs}\n" "$p"
    continue
  fi
  ki="$(printf '%s' "$valasz" | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
except Exception:
    print('(nem Florum válasz)'); raise SystemExit
print('verzió %s · adat: %s · növény: %s' % (d.get('appVersion','?'), d.get('dataDir','?'), d.get('dbCount','?')))
print('VER:' + str(d.get('appVersion','')))
" 2>/dev/null || echo '(olvashatatlan válasz)')"
  sor_ver="$(printf '%s\n' "$ki" | sed -n 's/^VER://p')"
  sor_ki="$(printf '%s\n' "$ki" | sed '/^VER:/d')"
  [ -n "$sor_ver" ] && FUTOTT_VER="$sor_ver"
  printf "  %-5s %s\n" "$p" "$sor_ki"
done

# ---------- 4) ítélet
fejlec "4) ÍTÉLET"

if [ -z "$FUTOTT_VER" ]; then
  printf "  ${zold}Nem fut helyben Florum-szerver.${nincs}\n"
  printf "  Ha a böngészőben mégis látszik, akkor a lapot fájlból nyitottad meg\n"
  printf "  (file://…) – ott a lábléc a MENTETT adatokból vette a számot.\n"
  printf "  Indítás:  python3 florum.py\n"
else
  printf "  Fájlokon:   %s\n" "$FAJL_VER"
  printf "  Fut:        %s\n" "$FUTOTT_VER"
  if [ "$FUTOTT_VER" = "$FAJL_VER" ]; then
    printf "  ${zold}✔ Egyeznek – nincs gond.${nincs}\n"
  else
    printf "  ${piros}✗ ELTÉRÉS: a futó példány a RÉGI.${nincs}\n"
    printf "    A Python a kódot indításkor a memóriába tölti, ezért a\n"
    printf "    frissített fájl csak ÚJraindítás után lép életbe.\n\n"
    printf "    ${sarga}Megoldás (1 parancs):${nincs}\n"
    printf "      python3 florum.py --leallit\n"
    printf "      python3 florum.py --szerver\n\n"
    printf "    vagy szolgáltatásként:\n"
    printf "      systemctl --user restart florum-szerver\n\n"
    printf "    vagy ezzel a szkripttel:\n"
    printf "      bash florum-verzio.sh --ujraindit\n"
  fi
fi

# ---------- 5) leállítás / újraindítás
case "$MOD" in
  --leallit|--ujraindit)
    fejlec "5) Leállítás"
    megolt=0
    for pid in $(ps -eo pid,args 2>/dev/null | awk '/[f]lorum\.py/{print $1}'); do
      kill "$pid" 2>/dev/null && { printf "  · leállítva: PID %s\n" "$pid"; megolt=$((megolt+1)); }
    done
    sleep 1
    for pid in $(ps -eo pid,args 2>/dev/null | awk '/[f]lorum\.py/{print $1}'); do
      kill -9 "$pid" 2>/dev/null && printf "  · erővel leállítva: PID %s\n" "$pid"
    done
    systemctl --user stop florum-szerver >/dev/null 2>&1 && printf "  · florum-szerver.service leállítva\n"
    [ "$megolt" -eq 0 ] && printf "  ${halv}nem futott semmi${nincs}\n"
    if [ "$MOD" = "--ujraindit" ]; then
      fejlec "6) Újraindítás"
      if systemctl --user status florum-szerver >/dev/null 2>&1; then
        systemctl --user start florum-szerver && printf "  ${zold}✔ florum-szerver.service elindítva${nincs}\n"
      fi
      cd "$ITT" || exit 1
      setsid nohup python3 "$ITT/florum.py" --szerver --notify </dev/null >"${TMPDIR:-/tmp}/florum-szerver.log" 2>&1 &
      sleep 3
      for p in 8777 8778 8779 8780; do
        v="$(curl -s --max-time 2 "http://127.0.0.1:$p/api/info" 2>/dev/null | python3 -c "
import json,sys
try: print(json.load(sys.stdin).get('appVersion',''))
except Exception: print('')" 2>/dev/null || true)"
        [ -n "$v" ] && { printf "  ${zold}✔ fut a %s-es porton: %s${nincs}\n" "$p" "$v"; break; }
      done
      printf "  A böngészőben: Ctrl+Shift+R (a régi lap eldobása).\n"
      printf "  Napló: %s/florum-szerver.log\n" "${TMPDIR:-/tmp}"
    fi
    ;;
esac

printf "\n"
