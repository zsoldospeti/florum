#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.4  ·  háttérszerver mint systemd --user szolgáltatás
#  Fájl:    florum-szolgaltatas.sh
#
#  Ezzel a NEM kell tudnod, telepítve van-e a szolgáltatás:
#  minden parancs előbb ellenőrzi, és ha kell, be is írja.
#
#  Használat:
#     bash florum-szolgaltatas.sh allapot      # mi a helyzet?
#     bash florum-szolgaltatas.sh telepit      # egység beírása (nem indít)
#     bash florum-szolgaltatas.sh indit        # telepít + indít + bekapcsol
#     bash florum-szolgaltatas.sh ujraindit
#     bash florum-szolgaltatas.sh leallit
#     bash florum-szolgaltatas.sh kikapcsol    # leállít + kiveszi az autostartból
#     bash florum-szolgaltatas.sh naplo
#     bash florum-szolgaltatas.sh eltavolit    # egység törlése
#
#  Miért kell ez?  A `systemctl --user start florum-szerver` csak akkor
#  működik, ha a .service fájl már benne van a ~/.config/systemd/user
#  mappában. Ez a szkript ezt magától elvégzi.
# ==============================================================
set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT="$UNIT_DIR/florum-szerver.service"
SABLON="$HERE/florum-szerver.service"
SZERVER_JSON="${XDG_DATA_HOME:-$HOME/.local/share}/florum/szerver.json"

OK="  ✓"; ERR="  ✗"; INFO="  ·"

if ! command -v systemctl >/dev/null 2>&1; then
  echo "$ERR ezen a rendszeren nincs systemctl – indítsd kézzel:"
  echo "      python3 \"$HERE/florum.py\" --szerver --notify"
  exit 1
fi

telepit() {
  if [ ! -f "$SABLON" ]; then
    echo "$ERR hiányzik a sablon: $SABLON"
    exit 1
  fi
  if [ -f "$UNIT" ] && ! grep -q "^WorkingDirectory=$HERE\$" "$UNIT" 2>/dev/null; then
    echo "$INFO a régi egység más mappára mutatott – felülírom"
  fi
  mkdir -p "$UNIT_DIR"
  sed "s#@DIR@#$HERE#g" "$SABLON" > "$UNIT"
  systemctl --user daemon-reload >/dev/null 2>&1 || true
  echo "$OK szolgáltatás beírva: $UNIT"
  echo "$INFO indítás most:      bash $0 indit"
  echo "$INFO vagy magától:      systemctl --user start florum-szerver"
}

telepitve() { [ -f "$UNIT" ]; }

# ---- parancsok -------------------------------------------------------------
PARANC="${1:-allapot}"

case "$PARANC" in
  telepit)
    telepit
    ;;

  indit)
    telepitve || telepit
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    if systemctl --user enable --now florum-szerver >/dev/null 2>&1; then
      echo "$OK a háttérszerver fut és bejelentkezéskor is elindul"
    elif systemctl --user start florum-szerver 2>/dev/null; then
      echo "$OK a háttérszerver elindult (de nincs bekapcsolva: systemctl --user enable florum-szerver)"
    else
      echo "$ERR nem indult el. Napló:"
      journalctl --user -u florum-szerver -n 15 --no-pager 2>/dev/null || true
      echo "$INFO tartalék (systemd nélkül):"
      echo "      nohup python3 \"$HERE/florum.py\" --szerver --notify >/dev/null 2>&1 &"
      exit 1
    fi
    sleep 1
    if [ -f "$SZERVER_JSON" ]; then
      PORT="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))['port'])" "$SZERVER_JSON" 2>/dev/null || echo '?')"
      echo "$OK válaszol: http://127.0.0.1:$PORT/api/panel.json"
    else
      echo "$INFO még nincs szerver-leíró – 2-3 másodperc, és megjelenik"
    fi
    ;;

  ujraindit)
    telepitve || telepit
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    systemctl --user restart florum-szerver && echo "$OK újraindítva"
    ;;

  leallit)
    telepitve || { echo "$ERR nincs telepítve (bash $0 telepit)"; exit 1; }
    systemctl --user stop florum-szerver && echo "$OK leállítva"
    ;;

  kikapcsol)
    if telepitve; then
      systemctl --user disable --now florum-szerver >/dev/null 2>&1 || true
      echo "$OK kikapcsolva (a bejelentkezéskor sem indul)"
    else
      echo "$INFO nem volt telepítve"
    fi
    ;;

  eltavolit)
    if telepitve; then
      systemctl --user disable --now florum-szerver >/dev/null 2>&1 || true
      rm -f "$UNIT"
      systemctl --user daemon-reload >/dev/null 2>&1 || true
      echo "$OK szolgáltatás eltávolítva"
    else
      echo "$INFO nem volt telepítve"
    fi
    ;;

  naplo)
    telepitve || { echo "$ERR nincs telepítve (bash $0 telepit)"; exit 1; }
    echo "  🌿 Florum – háttérszerver naplója (utolsó 20 sor)"
    echo "  ------------------------------------------------------------"
    journalctl --user -u florum-szerver -n 20 --no-pager
    exit 0
    ;;

  allapot|status)
    echo
    echo "  🌿 Florum – háttérszerver állapota"
    echo "  ------------------------------------------------------------"
    if telepitve; then
      echo "$OK szolgáltatás telepítve: $UNIT"
      if systemctl --user is-active florum-szerver >/dev/null 2>&1; then
        echo "$OK fut"
      else
        echo "$ERR nem fut – indítás: bash $0 indit"
      fi
      if systemctl --user is-enabled florum-szerver >/dev/null 2>&1; then
        echo "$OK bekapcsolva (bejelentkezéskor magától indul)"
      else
        echo "$INFO nincs bekapcsolva – bejelentkezéskor nem indul magától"
      fi
    else
      echo "$ERR a szolgáltatás NINCS telepítve ($UNIT nem létezik)"
      echo "      Ezért jön a „Unit florum-szerver.service not found” hiba."
      echo "      Javítás:  bash $0 indit        (beírja és elindítja)"
      echo "      vagy:     bash $0 telepit      (csak beírja)"
    fi
    echo
    if [ -f "$SZERVER_JSON" ]; then
      echo "$INFO leíró: $SZERVER_JSON"
      python3 - "$SZERVER_JSON" <<'PY' 2>/dev/null || true
import json, sys, urllib.request
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("      verzió %s · port %s · mód %s · pid %s" % (d.get("version"), d.get("port"), d.get("mode"), d.get("pid")))
try:
    v = json.load(urllib.request.urlopen("http://127.0.0.1:%s/api/panel.json" % d.get("port"), timeout=3))
    print("      ✓ válaszol: %d sor, %d lejárt" % (len(v.get("rows", [])), v.get("lateCount", 0)))
except Exception as exc:
    print("      ✗ nem válaszol (%s)" % exc)
PY
    else
      echo "$INFO nincs szerver-leíró – a Florum épp nem fut (ez önmagában nem hiba)"
    fi
    if systemctl --user is-enabled florum-emlekezteto.service >/dev/null 2>&1; then
      echo "$INFO a külön emlékeztető démon is be van kapcsolva – ez DUPLA értesítést ad"
      echo "      kikapcsolás: systemctl --user disable --now florum-emlekezteto.service"
    fi
    ;;

  -h|--help|segitseg)
    sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
    ;;

  *)
    echo "$ERR ismeretlen parancs: $PARANC"
    echo "      választható: allapot | telepit | indit | ujraindit | leallit | kikapcsol | naplo | eltavolit"
    exit 2
    ;;
esac
