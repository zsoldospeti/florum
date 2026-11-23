#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.4  ·  „Florum naptár” panel-widget telepítése
#  Fájl:    telepites-florum-panel.sh
#
#  A Florum saját Plasma 6 widgetjét telepíti a felhasználói
#  mappába. Ez a widget NEM függ az Event Calendar plasmoidtól,
#  az Akonaditól vagy a PIM-pluginoktól: a futó Florumtól kéri
#  el a teendőket (http://127.0.0.1:8777/api/panel.json).
#
#  Használat:
#     bash telepites-florum-panel.sh              # telepítés
#     bash telepites-florum-panel.sh --autostart  # + a Florum indítása bejelentkezéskor
#     bash telepites-florum-panel.sh --eltavolitas
#     bash telepites-florum-panel.sh --csak-mappa  # nem nyúl a panelhoz
#
#  A háttérszerver (systemd --user) kezelése külön:
#     bash florum-szolgaltatas.sh allapot|indit|naplo|kikapcsol
# ==============================================================
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SRC="$HERE/florum-panel"
DEST="${XDG_DATA_HOME:-$HOME/.local/share}/plasma/plasmoids/hu.florum.panel"
AUTOSTART="${XDG_CONFIG_HOME:-$HOME/.config}/autostart/florum.desktop"
UNIT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
UNIT="$UNIT_DIR/florum-szerver.service"
SZERVER_JSON="${XDG_DATA_HOME:-$HOME/.local/share}/florum/szerver.json"
ICON_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"

OK="  ✓"; ERR="  ✗"; INFO="  ·"

ELTAVOLITAS=0; AUTOSTARTOL=0; CSAK_MAPPA=0; ALLAPOT=0; NAPLO=0
for arg in "$@"; do
  case "$arg" in
    --eltavolitas) ELTAVOLITAS=1 ;;
    --autostart)   AUTOSTARTOL=1 ;;
    --csak-mappa)  CSAK_MAPPA=1 ;;
    --allapot)     ALLAPOT=1 ;;
    --naplo)       NAPLO=1 ;;
    -h|--help)     sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Ismeretlen kapcsoló: $arg"; exit 2 ;;
  esac
done

if [ "$NAPLO" = "1" ]; then
  echo
  echo "  🌿 Florum – háttérszerver naplója (utolsó 20 sor)"
  echo "  ------------------------------------------------------------"
  journalctl --user -u florum-szerver -n 20 --no-pager 2>/dev/null \
    || echo "$ERR nincs journalctl – próbáld: systemctl --user status florum-szerver"
  exit 0
fi

if [ "$ALLAPOT" = "1" ]; then
  echo
  echo "  🌿 Florum – szerver állapot"
  echo "  ------------------------------------------------------------"
  if command -v systemctl >/dev/null 2>&1; then
    if [ -f "$UNIT" ]; then
      if systemctl --user is-active florum-szerver >/dev/null 2>&1; then
        echo "$OK a florum-szerver szolgáltatás fut"
      else
        echo "$ERR a florum-szerver szolgáltatás telepítve van, de nem fut"
        echo "      indítás: systemctl --user start florum-szerver"
        echo "      vagy:    bash florum-szolgaltatas.sh indit"
      fi
    else
      echo "$ERR a szolgáltatás NINCS telepítve ($UNIT nem létezik)"
      echo "      ezért jön a „Unit florum-szerver.service not found” hiba"
      echo "      megoldás: bash florum-szolgaltatas.sh indit"
    fi
  fi
  if [ -f "$SZERVER_JSON" ]; then
    echo "$INFO leíró: $SZERVER_JSON"
    python3 - "$SZERVER_JSON" <<'PY' 2>/dev/null || cat "$SZERVER_JSON"
import json, sys, urllib.request
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("      verzió %s · port %s · mód %s · pid %s" % (d.get("version"), d.get("port"), d.get("mode"), d.get("pid")))
url = "http://127.0.0.1:%s/api/panel.json" % d.get("port")
try:
    valasz = json.load(urllib.request.urlopen(url, timeout=3))
    print("      ✓ válaszol: %d sor, %d lejárt" % (len(valasz.get("rows", [])), valasz.get("lateCount", 0)))
except Exception as exc:
    print("      ✗ nem válaszol (%s)" % exc)
PY
  else
    echo "$ERR nincs szerver-leíró ($SZERVER_JSON) – a Florum nem fut"
  fi

  # értesítés: melyik démon adja, mikor szólt utoljára
  ADAT="${XDG_DATA_HOME:-$HOME/.local/share}/florum"
  if command -v systemctl >/dev/null 2>&1 && systemctl --user is-enabled florum-emlekezteto.service >/dev/null 2>&1; then
    echo "$INFO a külön emlékeztető démon is fut – a háttérszerver mellett ez DUPLA értesítést ad"
    echo "      kikapcsolás: systemctl --user disable --now florum-emlekezteto.service"
  fi
  if [ -f "$ADAT/notify-state.json" ]; then
    python3 - "$ADAT/notify-state.json" <<'PY' 2>/dev/null
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
print("      utolsó értesítés: %s (%s teendő, %s)" % (d.get("lastDate"), d.get("lastCount"), d.get("lastRun", "?")))
PY
  fi
  if command -v notify-send >/dev/null 2>&1; then
    echo "$INFO notify-send megvan – az értesítés a Plasma saját rendszerében jelenik meg"
  else
    echo "$ERR nincs notify-send (sudo pacman -S libnotify) – a démon csak a naplóba ír"
  fi
  exit 0
fi

if [ "$ELTAVOLITAS" = "1" ]; then
  if command -v systemctl >/dev/null 2>&1 && [ -f "$UNIT" ]; then
    systemctl --user disable --now florum-szerver >/dev/null 2>&1 || true
    rm -f "$UNIT"
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    echo "$OK a háttérszerver szolgáltatás kikapcsolva"
  fi
  rm -f "$AUTOSTART"
  rm -f "$ICON_DIR/florum-symbolic.svg" "$ICON_DIR/florum.svg"
  if [ -d "$DEST" ]; then
    rm -rf "$DEST"
    echo "$OK a widget eltávolítva: $DEST"
  else
    echo "$INFO nem volt telepítve"
  fi
  echo "$INFO a panel újraindítása: systemctl --user restart plasma-plasmashell"
  exit 0
fi

echo
echo "  🌿 Florum – panel-widget telepítése"
echo "  ------------------------------------------------------------"

[ -d "$SRC" ] || { echo "$ERR hiányzik a florum-panel mappa ($SRC)"; exit 1; }
[ -f "$SRC/metadata.json" ] || { echo "$ERR hiányzik a metadata.json"; exit 1; }

# Plasma 6?
if command -v plasmashell >/dev/null 2>&1; then
  echo "$OK $(plasmashell --version 2>/dev/null | head -1)"
  case "$(plasmashell --version 2>/dev/null | grep -o '[0-9]*' | head -1)" in
    5) echo "$ERR ez a widget Plasma 6-ot kér (CachyOS-on ez az alap)"; exit 1 ;;
  esac
else
  echo "  ! nem találom a plasmashellt – a widget akkor is bemásolható"
fi

mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
mkdir -p "$DEST"
cp -r "$SRC/contents" "$DEST/"
cp "$SRC/metadata.json" "$DEST/"
echo "$OK widget bemásolva: $DEST"

# a régi QML-gyorsítótár törlése – különben a panel a régi (hibás) változatot futtatná
for CACHE in "$HOME/.cache/qmlcache" "$HOME/.cache/plasmashell/qmlcache"; do
  if [ -d "$CACHE" ]; then rm -rf "$CACHE"; echo "$OK QML-gyorsítótár törölve: $CACHE"; fi
done

# a monokróm ikon a téma számára is (a widgetek hozzáadása listához)
mkdir -p "$ICON_DIR"
cp "$SRC/contents/icons/florum-symbolic.svg" "$ICON_DIR/florum-symbolic.svg"
cp "$SRC/contents/icons/florum-sotet.svg" "$ICON_DIR/florum.svg"
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -q -t "$(dirname "$(dirname "$(dirname "$ICON_DIR")")")" 2>/dev/null || true
fi
echo "$OK monokróm ikon: $ICON_DIR/florum-symbolic.svg"

# ---- systemd --user egység beírása -----------------------------------------
#  EZ VOLT A HIBA OKA: a `systemctl --user start florum-szerver` csak akkor
#  működik, ha a .service fájl már benne van a ~/.config/systemd/user mappában.
#  Korábban ez csak `--autostart` mellett történt meg, ezért jött a
#  „Unit florum-szerver.service not found”. Most mindig beírjuk (bekapcsolni
#  viszont csak --autostart esetén kapcsoljuk be).
if command -v systemctl >/dev/null 2>&1 && [ -f "$HERE/florum-szerver.service" ]; then
  mkdir -p "$UNIT_DIR"
  sed "s#@DIR@#$HERE#g" "$HERE/florum-szerver.service" > "$UNIT"
  systemctl --user daemon-reload >/dev/null 2>&1 || true
  echo "$OK szolgáltatás beírva: $UNIT"
  if ! systemctl --user is-enabled florum-szerver >/dev/null 2>&1; then
    echo "$INFO indítás: systemctl --user start florum-szerver"
    echo "$INFO vagy:    bash florum-szolgaltatas.sh indit   (bekapcsolja bejelentkezéskor is)"
  fi
else
  echo "  ! nincs systemctl – a háttérszervert kézzel kell indítani"
fi

if [ "$AUTOSTARTOL" = "1" ]; then
  if command -v systemctl >/dev/null 2>&1; then
    [ -f "$UNIT" ] || { mkdir -p "$UNIT_DIR"; sed "s#@DIR@#$HERE#g" "$HERE/florum-szerver.service" > "$UNIT"; systemctl --user daemon-reload >/dev/null 2>&1 || true; }
    if systemctl --user enable --now florum-szerver >/dev/null 2>&1; then
      echo "$OK háttérszerver bekapcsolva: systemctl --user status florum-szerver"
      # a külön emlékeztető démon ugyanezt tenné – együtt DUPLA értesítés jönne
      if systemctl --user is-enabled florum-emlekezteto.service >/dev/null 2>&1; then
        systemctl --user disable --now florum-emlekezteto.service >/dev/null 2>&1 || true
        echo "$OK a külön emlékeztető démont kikapcsoltam (a háttérszerver ezt is ellátja)"
      fi
      sleep 1
      if [ -f "$SZERVER_JSON" ]; then
        PORT="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1],encoding='utf-8'))['port'])" "$SZERVER_JSON" 2>/dev/null || echo "?")"
        echo "$OK a szerver fut, port: $PORT"
      fi
      AUTOSTARTOL=0
    else
      echo "$ERR a systemd egység nem indult el – tartalék: bejelentkezéskori indítás"
    fi
  fi
fi

if [ "$AUTOSTARTOL" = "1" ]; then
  mkdir -p "$(dirname "$AUTOSTART")"
  cat > "$AUTOSTART" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Florum
Name[hu]=Florum növénygondozó
Comment=A panel-widget adatait ez a háttérben futó program adja
Exec=python3 "$HERE/florum.py" --szerver --notify
Icon=$HERE/florum.svg
Terminal=false
X-GNOME-Autostart-enabled=true
Categories=Utility;
DESKTOP
  echo "$OK bejelentkezéskori indítás bekapcsolva (háttérszerver): $AUTOSTART"
else
  if [ -f "$SZERVER_JSON" ]; then
    echo "$INFO a Florum szerver már fut (lásd: bash $0 --allapot)"
  else
    echo "$INFO a widget akkor mutat adatot, ha a Florum fut:"
    echo "      python3 $HERE/florum.py --szerver --notify"
    echo "      (állandó háttérszerverhez: bash $0 --autostart)"
  fi
fi

if [ "$CSAK_MAPPA" = "0" ]; then
  echo "$INFO panel újraindítása…"
  if command -v systemctl >/dev/null 2>&1; then
    systemctl --user restart plasma-plasmashell.service 2>/dev/null || true
  else
    pkill -x plasmashell 2>/dev/null || true
    (command -v plasmashell >/dev/null 2>&1 && plasmashell >/dev/null 2>&1 &) || true
  fi
fi


# ---- EGY Florum a panelen ---------------------------------------------------
# Ha a menüben két bejegyzés van (florum.desktop és florum-kde.desktop), a
# felhasználó könnyen mindkettőt kiteszi a panelre → két ikon. A régit itt is
# félretesszük, és megmutatjuk, mit kell tenni.
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
if [ -f "$APPS_DIR/florum-kde.desktop" ] && [ ! -f "$APPS_DIR/florum-kde.desktop.regi" ]; then
  mv -f "$APPS_DIR/florum-kde.desktop" "$APPS_DIR/florum-kde.desktop.regi" 2>/dev/null || true
  echo "$OK a régi második menübejegyzés félretéve (florum-kde.desktop.regi)"
fi

cat <<'HELP'

  ------------------------------------------------------------
  HOZZÁADÁS A PANELHEZ
    1) jobb klikk a panelen → „Panel beállítása…” (vagy „Szerkesztés”)
    2) „Widgetek hozzáadása…” → keresés: Florum
    3) „Florum naptár” → húzd a panelre

  A panelen EGY Florum-ikon látszik, mellette a mai + lejárt
  teendők száma. Kattintásra kinyílik a lista, és a listában ott a
  „Florum megnyitása” gomb – ez indítja a KDE-ablakot (vagy a
  böngészőt), illetve ha kell, a háttérszervert is.

  Ha KÉT Florum-ikon van a panelen, az a régi telepítés maradéka:
  a widget mellé korábban külön programindító is kikerült. Ilyenkor
    · jobb klikk a FÖLÖSLEGES ikonon → „Eltávolítás a panelről”
      (a widgetet hagyd meg – az mutatja a számot),
    · és a menüben már csak egy Florum van (a régit félretettem).
  Beállítás: a widget beállításaiban „Kattintásra a Florum nyíljon
  meg” – ekkor kattintásra rögtön az ablak jön, nem a lista.

  Ha nem jelenik meg:
    · bash florum-szolgaltatas.sh allapot         (telepítve van? fut?)
    · bash florum-szolgaltatas.sh indit           (beírja ÉS elindítja)
    · bash telepites-florum-panel.sh --allapot    (fut-e a szerver?)
    · bash telepites-florum-panel.sh --autostart  (háttérszerver bekapcsolása)
    · curl -s http://127.0.0.1:8777/api/panel.json
    · Plasma 6 kell hozzá (CachyOS-on alap)

  A Florum a 8777-es porton figyel; ha az foglalt, 8778, 8779… – a
  widget magától végigpróbálja ezeket.
HELP
