#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.2  ·  kiadás: verzióváltás, szűrés, GitHubra feltöltés
#  Fájl:    florum-kiadas.sh
#
#  MIÉRT VAN EZ?
#    A verzió számos helyen szerepel (VERSION, HTML meta, README,
#    OLVASSEL, compose, py fájlok, .desktop…). Kézi cserénél
#    mindig marad el egy hely – aztán „felül új, lent régi”.
#    Ez a szkript EGYBŐL, ellenőrzötten cseréli mindenhol.
#
#  HASZNÁLAT
#      bash florum-kiadas.sh                      # mi a verzió most
#      bash florum-kiadas.sh --uj 1.33.3          # verzióváltás mindenhol
#      bash florum-kiadas.sh --uj 1.33.3 --csomag # + tiszta zip újragenerálása
#      bash florum-kiadas.sh --git-elokeszites     # git repó + első commit
#      bash florum-kiadas.sh --allapot             # mi van a repóban
#      bash florum-kiadas.sh --feltoltes           # git push a GitHubra
#
#  A feltöltéshez egyszer be kell állítani a repót:
#      git remote add origin git@github.com:FELHASZNALONEV/florum.git
#  (a --git-elokeszites ezt megmutatja, de nem találja ki a nevet)
# ==============================================================
set -u

ITT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ITT"

zold()  { printf '\033[32m%s\033[0m\n' "$*"; }
sarga() { printf '\033[33m%s\033[0m\n' "$*"; }
piros() { printf '\033[31m%s\033[0m\n' "$*"; }
cim()   { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()    { printf '  \033[32m✔\033[0m %s\n' "$*"; }
hiba()  { printf '  \033[31m✘\033[0m %s\n' "$*"; }

jelenlegi() { [ -f VERSION ] && tr -d '[:space:]' < VERSION || echo "?"; }

# ---- a verziót tartalmazó fájlok (a _patch* és teszt-* kimarad) -------------
VERZIOS_FAJLOK=(
  VERSION
  florum.html
  plants-db.json
  florum-kiadas.sh
  README.md
  OLVASSEL.txt
  florum.py
  novenykereso.py
  fotonezo.py
  build-plant-db.py
  _csomag_tiszta.py
  install.sh
  florum-verzio.sh
  florum-frissites.sh
  florum-szolgaltatas.sh
  florum-atkoltoztetes.sh
  florum-megnyitas.sh
  florum-kde.py
  florum-kde.qml
  florum.desktop
  florum-kde.desktop
  florum-szerver.service
  florum-emlekezteto.service
  florum-panel/metadata.json
  telepites-florum-panel.sh
  telepites-florum-kde.sh
  kde-allapot.sh
  kde-eventcalendar-telepites.sh
  kde-eventcalendar-magyar.sh
  kde-eventcalendar-fuggoseg.sh
  kde-pim-kikapcsolas.sh
  docker/Dockerfile
  docker/compose.yaml
)

# ---- verzióváltás mindenhol ------------------------------------------------
verzio_csere() {
  local uj="$1" regi fajl db=0
  if ! printf '%s' "$uj" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+$'; then
    hiba "rossz verzióformátum: $uj (helyes: 1.33.3)"; return 1
  fi
  regi="$(jelenlegi)"

  # Ha a VERSION és a HTML meta eltér (kézi szerkesztés, félbemaradt build),
  # a cserét MINDKÉT régi számra el kell végezni – különben 0 fájl cserélődik.
  local jeloltek=("$regi")
  if [ -f florum.html ]; then
    local html_regi
    html_regi="$(grep -o '<meta name="florum-version" content="[^"]*"' florum.html \
                | head -1 | sed 's/.*content="//; s/"$//')"
    if [ -n "$html_regi" ] && [ "$html_regi" != "$regi" ]; then
      sarga "  ⚠ a VERSION ($regi) és a florum.html ($html_regi) eltér – mindkettőt cserélem"
      jeloltek+=("$html_regi")
    fi
  fi
  if [ "$regi" = "$uj" ] && [ ${#jeloltek[@]} -eq 1 ]; then
    sarga "már ez a verzió: $uj – nincs mit cserélni"; return 0
  fi
  cim "Verzióváltás: ${jeloltek[*]} → $uj"
  for fajl in "${VERZIOS_FAJLOK[@]}"; do
    [ -f "$fajl" ] || continue
    if grep -qF -e "$regi" "$fajl" || { [ ${#jeloltek[@]} -gt 1 ] && grep -qF -e "${jeloltek[1]}" "$fajl"; }; then
      local xbit=0; [ -x "$fajl" ] && xbit=1
      local r
      for r in "${jeloltek[@]}"; do
        sed -i "s/$(printf '%s' "$r" | sed 's/\./\\./g')/$uj/g" "$fajl"
      done
      # a sed -i új fájlt ír, ezért ELVESZI a futtatható jogot – visszaadjuk
      [ "$xbit" -eq 1 ] && chmod +x "$fajl"
      printf '  · %s\n' "$fajl"
      db=$((db + 1))
    fi
  done
  printf '%s\n' "$uj" > VERSION
  # biztonsági háló: minden szkript maradjon futtatható
  for fajl in *.sh *.py docker/*.sh docker/*.py; do [ -f "$fajl" ] && chmod +x "$fajl"; done

  # ---- a két külső példány (forrás + egyesített) -------------------------
  # Ha ezek maradnak a régiben, a következő build VISSZAÍRJA a régi verziót:
  # a build a ../minden_html-original/florum/florum.html-ből dolgozik.
  local kulso valt
  for kulso in "../minden_html-original/florum/florum.html" \
                "../minden_html-egyesitett/florum/florum.html"; do
    [ -f "$kulso" ] || continue
    valt=0
    for r in "${jeloltek[@]}"; do
      if grep -qF "$r" "$kulso"; then
        sed -i "s/$(printf '%s' "$r" | sed 's/\./\\./g')/$uj/g" "$kulso"
        valt=1
      fi
    done
    if [ "$valt" -eq 1 ]; then printf '  · %s\n' "$kulso"; db=$((db + 1)); fi
  done
  ok "$db fájl frissítve, VERSION = $uj"

  # ---- ellenőrzés: maradt-e régi verzió bárhol?
  local maradek
  maradek="$(grep -rlF -e "$regi" ${jeloltek[1]:+-e "${jeloltek[1]}"} . 2>/dev/null | grep -vE '^\./(_patch|_|teszt-|\.git/)|^\./[^/]*-elonezet\.html$' || true)"
  if [ -n "$maradek" ]; then
    sarga "  ⚠ ezekben még ott a régi szám (kézzel nézd át):"
    printf '    %s\n' $maradek
  else
    ok "nem maradt régi verziószám a programban"
  fi


  sarga "  Következő lépés (egy parancs):"
  cat <<EOF
      bash florum-kiadas.sh --epit --csomag     # build + egyesítés + teszt + zip
EOF
}

# ---- csomag ---------------------------------------------------------------
# ---- teljes újraépítés: forrás → futó fájl → egyesített → teszt ----------
epit() {
  cim "Újraépítés (forrás → futó fájl → egyesített példány)"
  local forras="../minden_html-original/florum/florum.html"
  if [ -f "$forras" ]; then
    python3 build-plant-db.py --html "$forras" 2>&1 | tail -1
    ok "adatbázis beágyazva a forrásba"
  else
    sarga "  nincs $forras – a beágyazás kimarad"
  fi
  bash kinezet-egyesites.sh 2>&1 | tail -3
  # a build után a külső példányok verziója újra egyezzen
  if [ -f teszt-verzio.py ]; then
    if python3 teszt-verzio.py >/tmp/florum-verzio.log 2>&1; then
      ok "verzió-teszt: $(grep -oE 'Ran [0-9]+ tests' /tmp/florum-verzio.log | head -1) rendben"
    else
      hiba "verzió-teszt elbukott:"; grep -E "^(FAIL|AssertionError)" /tmp/florum-verzio.log | head -5 | sed 's/^/    /'
      return 1
    fi
  fi
}

csomag() {
  cim "Tiszta csomag"
  python3 _csomag_tiszta.py | tail -2
}

# ---- git: repó és állapot -------------------------------------------------
git_van() { command -v git >/dev/null 2>&1; }

git_elokeszites() {
  git_van || { hiba "nincs git – sudo pacman -S git"; return 1; }
  cim "Git repó előkészítése"
  if [ ! -d .git ]; then
    git init -q
    git branch -M main 2>/dev/null || true
    ok "git repó létrehozva (main ág)"
  else
    ok "már git repó"
  fi
  git add -A
  local n
  n="$(git diff --cached --name-only | wc -l)"
  ok "$n fájl előkészítve (a .gitignore kiszűri az adatot, zipet, előnézetet)"
  if ! git diff --cached --quiet; then
    git -c user.name="${GIT_AUTHOR_NAME:-Florum}" \
        -c user.email="${GIT_AUTHOR_EMAIL:-florum@localhost}" \
        commit -q -m "Florum $(jelenlegi) – hőmérséklet-grafikon, docker, GitHub-kiadás"
    ok "első commit kész: Florum $(jelenlegi)"
  fi
  cat <<EOF

  A GitHubon (böngészőben) hozz létre egy ÜRES repót, majd:

      git remote add origin git@github.com:FELHASZNALONEV/florum.git
      git push -u origin main

  SSH helyett HTTPS is jó (ekkor tokennel):
      git remote add origin https://github.com/FELHASZNALONEV/florum.git

  A repó neve legyen például: florum
  NEM kell README-t sem inicializálni (a fájlok már itt vannak).

EOF
}

git_allapot() {
  git_van || { hiba "nincs git"; return 1; }
  [ -d .git ] || { sarga "még nincs git repó – futtasd: bash florum-kiadas.sh --git-elokeszites"; return 0; }
  cim "Repó állapota"
  printf '  ág:        %s\n' "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  printf '  verzió:    %s\n' "$(jelenlegi)"
  printf '  commitok:  %s\n' "$(git rev-list --count HEAD 2>/dev/null || echo 0)"
  printf '  remote:    %s\n' "$(git remote get-url origin 2>/dev/null || echo 'nincs beállítva')"
  local valtozatlan
  valtozatlan="$(git status --porcelain | wc -l)"
  if [ "$valtozatlan" -eq 0 ]; then
    ok "minden mentve (nincs függő változás)"
  else
    sarga "  $valtozatlan fájl változott, még nincs commitolva:"
    git status --short | head -20 | sed 's/^/    /'
  fi
  # biztonsági ellenőrzés: nem került-e be adat
  local baj
  baj="$(git ls-files | grep -E 'florum-data\.json|^photos/|^mentes/|\.zip$|^\.env$' || true)"
  if [ -n "$baj" ]; then
    piros "  FIGYELEM: adat vagy zip van a repóban:"; printf '    %s\n' $baj
    echo "    javítás: git rm --cached <fájl>   (a .gitignore már tiltja)"
  else
    ok "a repóban nincs adat, fotó, zip és titok"
  fi
}

# ---- feltöltés ------------------------------------------------------------
feltoltes() {
  git_van || { hiba "nincs git"; return 1; }
  [ -d .git ] || { hiba "még nincs git repó – bash florum-kiadas.sh --git-elokeszites"; return 1; }
  if ! git remote get-url origin >/dev/null 2>&1; then
    hiba "nincs beállítva a GitHub repó (origin)"
    echo "    git remote add origin git@github.com:FELHASZNALONEV/florum.git"
    return 1
  fi
  cim "Feltöltés a GitHubra"

  # 1. biztonsági kapu: teszteljünk, mielőtt felmegy
  if [ -f teszt-verzio.py ]; then
    if python3 teszt-verzio.py >/tmp/florum-verzio.log 2>&1; then
      ok "verzió-teszt rendben ($(grep -oE 'Ran [0-9]+ tests' /tmp/florum-verzio.log | head -1))"
    else
      hiba "a verzió-teszt elbukott – előbb javítsd (lásd /tmp/florum-verzio.log)"
      grep -E "^(FAIL|AssertionError)" /tmp/florum-verzio.log | head -5 | sed 's/^/    /'
      return 1
    fi
  fi

  # 2. adat-védelem
  local baj
  baj="$(git ls-files | grep -E 'florum-data\.json|^photos/|^mentes/|\.zip$|^\.env$' || true)"
  if [ -n "$baj" ]; then
    hiba "adat/zip van a repóban – nem töltöm fel:"; printf '    %s\n' $baj; return 1
  fi

  # 3. commit, ha van változás
  if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git status --porcelain)" ]; then
    git add -A
    git -c user.name="${GIT_AUTHOR_NAME:-Florum}" \
        -c user.email="${GIT_AUTHOR_EMAIL:-florum@localhost}" \
        commit -q -m "Florum $(jelenlegi) – frissítés"
    ok "commit: Florum $(jelenlegi) – frissítés"
  else
    ok "nincs új változás, csak push"
  fi

  # 4. push
  git push -u origin HEAD 2>&1 | sed 's/^/  /'
  local s=${PIPESTATUS[0]}
  if [ "$s" -eq 0 ]; then
    ok "fent van a GitHubon: $(git remote get-url origin) ($(jelenlegi))"
    echo
    sarga "  Arcane / másik gép frissítése:"
    echo "      git pull && bash florum-kiadas.sh --csomag   # vagy docker/florum-docker.sh frissit"
  else
    hiba "a push nem sikerült (jogosultság? SSH-kulcs? – lásd a fenti sort)"
    return 1
  fi
}

# ---- main -----------------------------------------------------------------
case "${1:-}" in
  --uj)
      [ $# -ge 2 ] || { echo "használat: bash florum-kiadas.sh --uj 1.33.3 [--csomag]"; exit 1; }
      verzio_csere "$2" || exit 1
      for kapcs in "${@:3}"; do
        case "$kapcs" in
          --epit)   epit   || exit 1 ;;
          --csomag) csomag ;;
        esac
      done
      ;;
  --epit)            epit ;;
  --csomag)          csomag ;;
  --git-elokeszites) git_elokeszites ;;
  --allapot)         git_allapot ;;
  --feltoltes|--push) feltoltes ;;
  ""|--segitseg|-h|--help)
      cim "Florum kiadás-segéd"
      echo "  verzió: $(jelenlegi)"
      cat <<EOF

  bash florum-kiadas.sh --uj 1.33.3            verzióváltás mindenhol
  bash florum-kiadas.sh --uj 1.33.3 --epit --csomag   + build + zip
  bash florum-kiadas.sh --git-elokeszites      git repó + első commit
  bash florum-kiadas.sh --allapot              mi van a repóban
  bash florum-kiadas.sh --feltoltes            feltöltés (teszt + adat-ellenőrzés után)

  Részletes leírás: README 24. fejezet
EOF
      ;;
  *) hiba "ismeretlen kapcsoló: $1"; exit 1 ;;
esac
