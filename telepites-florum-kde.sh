#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.3  ·  a KDE-ablak telepítése
#  Fájl:    telepites-florum-kde.sh
#
#  Mit tesz?
#    1. ellenőrzi, hogy megvannak-e a szükséges csomagok
#       (pyside6, qt6-webengine, qt6-declarative)
#    2. a florum-kde parancsot a ~/.local/bin-be teszi
#    3. a menübe (KDE alkalmazásindító) bejegyzést készít
#    4. az ikont a hicolor ikontémába másolja
#
#  Használat:
#      bash telepites-florum-kde.sh            # telepítés
#      bash telepites-florum-kde.sh allapot    # mi van meg?
#      bash telepites-florum-kde.sh eltavolit  # eltávolítás
# ==============================================================
set -u

ITT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
IKONOK="$HOME/.local/share/icons/hicolor"

zold()  { printf '\033[32m%s\033[0m\n' "$*"; }
sarga() { printf '\033[33m%s\033[0m\n' "$*"; }
piros() { printf '\033[31m%s\033[0m\n' "$*"; }
cim()   { printf '\n\033[1m%s\033[0m\n' "$*"; }

csomag_van() { pacman -Qq "$1" >/dev/null 2>&1; }

csomagok() {
  cim "1) Szükséges csomagok"
  local hianyzo=()
  for p in pyside6 qt6-webengine qt6-declarative; do
    if csomag_van "$p"; then
      zold "  ✓ $p"
    else
      piros "  ✗ $p  (hiányzik)"
      hianyzo+=("$p")
    fi
  done
  for p in qqc2-desktop-style kirigami; do
    if csomag_van "$p"; then zold "  ✓ $p  (a KDE-s kinézethez)";
    else sarga "  · $p  (nem kötelező, de szebb tőle)"; fi
  done
  if [ ${#hianyzo[@]} -gt 0 ]; then
    cim "Telepítés (CachyOS / Arch):"
    echo "  sudo pacman -S ${hianyzo[*]}"
    echo
    sarga "  Ez nem a te hibád: ezek a csomagok alapból nincsenek a gépen."
    return 1
  fi
  return 0
}

telepit() {
  cim "2) Parancs és menübejegyzés"
  mkdir -p "$BIN" "$APPS" "$IKONOK/scalable/apps"
  cat > "$BIN/florum-kde" <<WRAPPER
#!/usr/bin/env bash
# Florum KDE-ablak – indító (a telepítő készítette)
exec python3 "$ITT/florum-kde.py" "\$@"
WRAPPER
  chmod +x "$BIN/florum-kde"
  zold "  ✓ $BIN/florum-kde"

  # NEM készítünk külön menübejegyzést: a Florum EGYSZER szerepel a menüben
  # és a panelen (florum.desktop → florum-megnyitas.sh választ KDE-ablakot
  # vagy böngészőt). A régi, második bejegyzést félretesszük.
  if [ -f "$APPS/florum-kde.desktop" ]; then
    mv -f "$APPS/florum-kde.desktop" "$APPS/florum-kde.desktop.regi" 2>/dev/null || true
    zold "  ✓ a régi második menübejegyzés félretéve (florum-kde.desktop.regi)"
  fi
  zold "  ✓ egyetlen menübejegyzés: florum.desktop (bash florum-megnyitas.sh)"

  if [ -f "$ITT/florum.svg" ]; then
    cp -f "$ITT/florum.svg" "$IKONOK/scalable/apps/florum.svg"
    zold "  ✓ $IKONOK/scalable/apps/florum.svg"
    ( gtk-update-icon-cache -q -t -f "$IKONOK" 2>/dev/null || true )
  fi
  ( update-desktop-database "$APPS" 2>/dev/null || true )

  case ":$PATH:" in
    *":$BIN:"*) : ;;
    *) sarga "  ! A $BIN nincs a PATH-ban – tedd be a ~/.bashrc / ~/.zshrc végére:"
       echo '     export PATH="$HOME/.local/bin:$PATH"' ;;
  esac

  cim "Kész – indítás"
  echo "  • a menüből:  „Florum – növénygondozó”"
  echo "  • terminálból: florum-kde"
  echo "  • önellenőrzés: python3 \"$ITT/florum-kde.py\" --teszt"
  echo
  sarga "  Első indításnál a KDE rákérdezhet – engedélyezd, hogy saját ablakban fusson."
}

allapot() {
  cim "Florum KDE-ablak – állapot"
  csomagok || true
  echo
  [ -x "$BIN/florum-kde" ] && zold "  ✓ parancs: $BIN/florum-kde" || sarga "  · parancs nincs telepítve"
  [ -f "$APPS/florum-kde.desktop" ] && zold "  ✓ menübejegyzés megvan" || sarga "  · menübejegyzés nincs"
  [ -f "$IKONOK/scalable/apps/florum.svg" ] && zold "  ✓ ikon megvan" || sarga "  · ikon nincs"
  echo
  echo "  Önellenőrzés: python3 \"$ITT/florum-kde.py\" --teszt"
}

eltavolit() {
  cim "Eltávolítás"
  rm -f "$BIN/florum-kde" "$APPS/florum-kde.desktop" "$IKONOK/scalable/apps/florum.svg"
  ( update-desktop-database "$APPS" 2>/dev/null || true )
  zold "  ✓ kész (az adatok a ~/.local/share/florum mappában megmaradtak)"
}

case "${1:-telepit}" in
  telepit)   csomagok && telepit ;;
  allapot)   allapot ;;
  eltavolit) eltavolit ;;
  *) echo "Használat: bash telepites-florum-kde.sh [telepit|allapot|eltavolit]"; exit 2 ;;
esac
