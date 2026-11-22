#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.2  ·  otthoni növénygondozó
#  Fájl:    install.sh
#  Szerep:  menüparancs telepítése (CachyOS / Arch / Linux asztal)
#  Licenc:  szabadon használható, módosítható és terjeszthető
# ==============================================================

# Florum – telepítő menüparancs CachyOS / Arch / bármilyen Linux asztalra.
# Nem telepít semmit, csak regisztrálja az appot a programmenüben.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/scalable/apps"

command -v python3 >/dev/null 2>&1 || { echo "Hiányzik a python3. Telepítés: sudo pacman -S python"; exit 1; }

mkdir -p "$APPS" "$ICONS"
cp "$DIR/florum.svg" "$ICONS/florum.svg"
chmod +x "$DIR/florum.py"

cat > "$APPS/florum.desktop" <<EOF
[Desktop Entry]
Type=Application
Version=1.0
Name=Florum
Name[hu]=Florum növénygondozó
GenericName=Plant Care Tracker
GenericName[hu]=Növénygondozó
Comment=Otthoni növények locsolása, tápoldatozása, átültetése
Comment[hu]=Otthoni növények locsolása, tápoldatozása, átültetése
Exec=bash "$DIR/florum-megnyitas.sh"
Icon=florum
Terminal=false
Categories=Utility;Education;
Keywords=plant;növény;watering;öntözés;garden;kert;
StartupWMClass=Florum
EOF

chmod +x "$APPS/florum.desktop"

# ---- EGY Florum legyen a menüben és a panelen -----------------------------
# Korábban két bejegyzés készült (florum.desktop és florum-kde.desktop),
# ezért lehetett két Florum-ikon a panelen. A régit félretesszük.
for regi in "$APPS/florum-kde.desktop"; do
  if [ -f "$regi" ]; then
    mv -f "$regi" "$regi.regi" 2>/dev/null || rm -f "$regi"
    echo "  ✓ félretettem a régi második menübejegyzést: $regi (→ .regi)"
  fi
done

# ikon-gyorsítótár frissítése, ha van hozzá eszköz
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true

# ---- emlékeztető démon (systemd --user) + KDE naptár -----------------------
UNITS="$HOME/.config/systemd/user"
mkdir -p "$UNITS"
cat > "$UNITS/florum-emlekezteto.service" <<EOF
[Unit]
Description=Florum – növénygondozó emlékeztető (naptár + asztali értesítés)
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 "$DIR/emlekezteto.py" --daemon --intervallum 1800
Restart=always
RestartSec=60
Nice=10

[Install]
WantedBy=default.target
EOF
if command -v systemctl >/dev/null 2>&1; then
  systemctl --user daemon-reload >/dev/null 2>&1 || true
  # FONTOS: a florum-szerver (panel-widgethez) ugyanazt az értesítést is ellátja,
  # ezért ha az fut, NEM indítjuk a külön emlékeztető démont (dupla értesítés).
  if systemctl --user is-enabled florum-szerver >/dev/null 2>&1; then
    echo "  ℹ A háttérszerver (florum-szerver) már fut – az emlékeztetőt is ez adja."
    echo "    A külön emlékeztető démont nem indítottam (dupla értesítés lenne)."
  else
    systemctl --user enable --now florum-emlekezteto.service >/dev/null 2>&1 || true
  fi
fi

# naptárfájl előkészítése (a KDE panel Digitális órájához)
if [ -f "$DIR/naptar_ics.py" ]; then
  python3 "$DIR/naptar_ics.py" >/dev/null 2>&1 || true
fi

# a KDE naptár-plugin (opcionális, csak ha van pacman és a felhasználó kéri)
if command -v pacman >/dev/null 2>&1 && ! pacman -Qq kdepim-addons >/dev/null 2>&1; then
  echo "  ℹ A KDE panel órájához kell a naptár-plugin:  sudo pacman -S kdepim-addons"
fi

echo
echo "  🌿 Kész! A Florum megjelent a programmenüben (Növénygondozó / Florum)."
echo "     Emlékeztető démon:  systemctl --user status florum-emlekezteto"
echo "     (vagy a háttérszerver:  systemctl --user status florum-szerver)"
echo "     Naptár a panelhez:  $HOME/.local/share/florum/florum.ics"
echo "     Panel-widget:      bash \"$DIR/telepites-florum-panel.sh\""
echo "     EGYETLEN indító:   bash \"$DIR/florum-megnyitas.sh\"  (ebben van a régi kettő)"
echo "     Ha nem látod azonnal: jelentkezz ki és vissza, vagy futtasd: kbuildsycoca6 / xdg-desktop-menu forceupdate"
echo "     Indítás terminálból: python3 \"$DIR/florum.py\" --app"
echo
