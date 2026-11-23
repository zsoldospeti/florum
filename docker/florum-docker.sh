#!/usr/bin/env bash
# ==============================================================
#  FLORUM – Docker segédszkript
#  Fájl: docker/florum-docker.sh
#
#  Egy paranccsal: építés, indítás, adatmentés, frissítés, leállítás.
#  Arcane mellett is használható (a compose.yaml ugyanaz).
#
#    bash docker/florum-docker.sh epites        # kép építése
#    bash docker/florum-docker.sh indit         # indítás (háttérben)
#    bash docker/florum-docker.sh allapot       # fut-e, melyik porton, hol az adat
#    bash docker/florum-docker.sh mentes        # adatok ZIP-be (a kötetből)
#    bash docker/florum-docker.sh frissit       # kép újraépítés + csere (adat megmarad)
#    bash docker/florum-docker.sh naplo         # élő napló (Ctrl+C kilép)
#    bash docker/florum-docker.sh leallit       # leállítás (az adat megmarad)
#    bash docker/florum-docker.sh torol         # leállítás + kép törlése (az adat NEM)
#    bash docker/florum-docker.sh ellenorzes    # a futó példány /api/info-ja
#    bash docker/florum-docker.sh utkozes       # „name is already in use” – mi a teendő
#    bash docker/florum-docker.sh atvesz        # a régi konténer ADATAINAK átmentése + csere
# ==============================================================
set -u

ITT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GYOKER="$(cd "$ITT/.." && pwd)"
KONTENER="florum"
KEP="florum:$(cat "$GYOKER/VERSION" 2>/dev/null || echo latest)"
PORT="${FLORUM_PORT:-8777}"

piros()  { printf '\033[31m%s\033[0m\n' "$*"; }
zold()   { printf '\033[32m%s\033[0m\n' "$*"; }
sarga()  { printf '\033[33m%s\033[0m\n' "$*"; }
cim()    { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }

docker_van() {
  if ! command -v docker >/dev/null 2>&1; then
    piros "Nincs docker a gépen."
    echo "  CachyOS / Arch:  sudo pacman -S docker docker-compose"
    echo "  Utána:           sudo systemctl enable --now docker.service"
    echo "  (user csoportba: sudo usermod -aG docker $USER  → jelentkezz ki/be)"
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    piros "A docker daemon nem fut, vagy nincs jogosultságod."
    echo "  sudo systemctl start docker.service"
    echo "  vagy: sudo usermod -aG docker $USER  (utána új bejelentkezés)"
    exit 1
  fi
}

# compose parancs felismerése (v2 plugin vagy külön bináris)
compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  elif command -v docker-compose >/dev/null 2>&1; then
    docker-compose "$@"
  else
    piros "Nincs docker compose. Telepítés: sudo pacman -S docker-compose"
    exit 1
  fi
}

# ---------------------------------------------------------------------------
#  Névütközés: „Conflict. The container name \"/florum\" is already in use”
# ---------------------------------------------------------------------------
#  Ok: a konténer nem a compose-tól származik (docker run-nal indítottad,
#  vagy egy korábbi compose-projekt más mappából), ezért a compose nem
#  érzi a magáénak – de a nevet nem tudja újrahasználni.
#
#  FONTOS: a törlés CSAK AKKOR biztonságos, ha az adat köteten van.
#  Ezt itt ellenőrizzük, és ha nem, előbb kimásoljuk a konténerből.

kontener_letezik() { docker ps -a --format '{{.Names}}' | grep -qx "$KONTENER"; }

# hova csatolja a régi konténer az adatot? (van-e egyáltalán kötete)
kontener_kotet() {
  docker inspect "$KONTENER" \
    --format '{{range .Mounts}}{{.Type}}|{{.Source}}|{{.Destination}}{{"\n"}}{{end}}' 2>/dev/null
}

# az adatot a konténerből a gazdagépre másolja (akkor is, ha nincs kötet)
kontener_mentes() {
  local cel="${1:-$GYOKER/docker/regi-kontener-mentes-$(date +%Y%m%d-%H%M)}"
  mkdir -p "$cel" || return 1
  echo "  · adatok kimásolása a konténerből ide: $cel"
  docker cp "$KONTENER:/data/." "$cel/" >/dev/null 2>&1 \
    || docker cp "$KONTENER:/root/.local/share/florum/." "$cel/" >/dev/null 2>&1 \
    || docker cp "$KONTENER:/app/data/." "$cel/" >/dev/null 2>&1 \
    || { sarga "  (nem találtam /data mappát a konténerben – lehet, hogy köteten van)"; }
  local db
  db="$(find "$cel" -name 'florum-data.json' -print -quit 2>/dev/null)"
  if [ -n "$db" ]; then
    zold "  ✓ megvan: ${db#$GYOKER/}"
    python3 - "$db" <<'PYEOF' 2>/dev/null || true
import json, sys
try:
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    print("    növény: %d · napló: %d · hőmérséklet-mérés: %d" % (
        len(d.get("plants") or []), len(d.get("history") or []), len(d.get("tempLog") or [])))
except Exception as e:
    print("    (a fájlt nem tudtam értelmezni: %s)" % e)
PYEOF
  else
    sarga "  ! nem találtam florum-data.json-t a konténerben"
    echo "    Ha a felület működött, az adat MÁSHOL van. Nézd meg:"
    echo "      docker inspect $KONTENER --format '{{json .Mounts}}'"
  fi
  echo "$cel"
}

utkozes_sugo() {
  cim "Névütközés: a(z) „$KONTENER” konténer már létezik"
  kontener_letezik || { zold "Most épp nincs ilyen konténer – újrapróbálhatod: bash docker/florum-docker.sh indit"; return 0; }
  docker ps -a --filter "name=^${KONTENER}$" \
    --format '  állapot: {{.Status}}
  kép:    {{.Image}}
  létre:  {{.CreatedAt}}'
  echo
  echo "  Csatolt mappák (itt van az adat, ha van):"
  kontener_kotet | sed 's/^/    /'
  echo
  echo "  Teendő (a sorrend fontos!):"
  echo "    1) bash docker/florum-docker.sh atvesz     # adatmentés + csere (ez a jó)"
  echo "   vagy kézzel:"
  echo "    1) bash docker/florum-docker.sh mentes-regi"
  echo "    2) docker rm -f $KONTENER        ← CSAK az 1) után!"
  echo "    3) bash docker/florum-docker.sh indit"
}

eset="${1:-allapot}"

case "$eset" in

  epites)
    docker_van
    cim "Kép építése: $KEP"
    docker build -f "$ITT/Dockerfile" -t "$KEP" \
      --build-arg "FLORUM_VERSION=$(cat "$GYOKER/VERSION" 2>/dev/null || echo 0)" "$GYOKER" || exit 1
    zold "Kész: $KEP"
    docker image ls | grep -E "^florum" || true
    ;;

  indit)
    docker_van
    mkdir -p "$GYOKER/docker/data"
    # a konténer nem root (uid 1000) – a mappának írhatónak kell lennie
    chmod 775 "$GYOKER/docker/data" 2>/dev/null || true
    cim "Indítás (compose)"
    ( cd "$GYOKER/docker" && compose up -d --build ) || exit 1
    sleep 3
    "$0" allapot
    ;;

  allapot)
    docker_van
    cim "Florum konténer"
    if docker ps --format '{{.Names}}' | grep -qx "$KONTENER"; then
      zold "fut"
      docker ps --filter "name=^${KONTENER}$" \
        --format '  név: {{.Names}}\n  kép: {{.Image}}\n  állapot: {{.Status}}\n  port: {{.Ports}}'
      echo "  felület:  http://127.0.0.1:${PORT}/"
    else
      sarga "nem fut"
      docker ps -a --filter "name=^${KONTENER}$" --format '  (van ilyen konténer, állapot: {{.Status}})' || true
    fi
    cim "Adatok helye (gazdagép)"
    if [ -d "$GYOKER/docker/data" ]; then
      printf '  %s\n' "$GYOKER/docker/data"
      ls -1 "$GYOKER/docker/data" 2>/dev/null | sed 's/^/    /' | head -12
      du -sh "$GYOKER/docker/data" 2>/dev/null | sed 's/^/  méret: /'
    else
      sarga "  még nincs (az első indítás hozza létre)"
    fi
    ;;

  utkozes)
    docker_van
    utkozes_sugo
    ;;

  mentes-regi)
    docker_van
    cim "A régi konténer adatainak mentése"
    if ! kontener_letezik; then
      sarga "Nincs „$KONTENER” konténer – nincs mit menteni."
      exit 0
    fi
    kontener_mentes
    ;;

  atvesz)
    docker_van
    cim "Átvétel: a régi konténer adatai → kötet → új konténer"
    if ! kontener_letezik; then
      sarga "Nincs „$KONTENER” konténer – egyszerűen indítom az újat."
      "$0" indit
      exit $?
    fi

    # 1) hol van az adat?
    kotetek="$(kontener_kotet)"
    echo "  · a régi konténer csatolásai:"
    [ -n "$kotetek" ] && echo "$kotetek" | sed 's/^/      /' || echo "      (nincs – az adat a konténeren belül van!)"

    cel="$GYOKER/docker/data"
    mkdir -p "$cel"
    adat_mappa=""
    # ha van gazdagép-mappa, ami /data-ra van csatolva, azt használjuk
    while IFS='|' read -r tipus forras celpont; do
      [ -z "$tipus" ] && continue
      if [ "$celpont" = "/data" ] && [ "$tipus" = "bind" ]; then adat_mappa="$forras"; fi
    done <<< "$kotetek"

    if [ -n "$adat_mappa" ]; then
      zold "  ✓ az adat már köteten van: $adat_mappa"
      echo "    (ezt nem mozgatom – a régi konténer törlése után is megmarad)"
      if [ "$(cd "$adat_mappa" 2>/dev/null && pwd)" != "$(cd "$cel" && pwd)" ]; then
        sarga "    FIGYELEM: a compose a ./docker/data mappát használja, nem ezt."
        echo "      Ha azt akarod, hogy ott legyen, másold át:"
        echo "        cp -a \"$adat_mappa/.\" \"$cel/\""
      fi
    else
      echo "  · nincs /data kötés → kimásolom az adatot a konténerből"
      kontener_mentes "$cel" >/dev/null || true
      if [ -f "$cel/florum-data.json" ]; then
        zold "  ✓ adat átvéve ide: ${cel#$GYOKER/}"
      else
        piros "  ✗ Nem találtam adatot a konténerben."
        echo "    Állj meg, és nézd meg kézzel:"
        echo "      docker exec -it $KONTENER sh -lc 'ls -la /data 2>/dev/null; ls -la ~/.local/share/florum 2>/dev/null'"
        echo "    Ha ott van a florum-data.json, másold ki:"
        echo "      docker cp $KONTENER:<az a mappa>/. \"$cel/\""
        exit 1
      fi
    fi

    # ha az új mappában MÁR van adat (pl. az új konténer közben elindult üresen),
    # a kettőt egyesítjük – így nem veszik el egyik sem
    legfrissebb="$(ls -1dt "$GYOKER"/docker/regi-kontener-mentes-* 2>/dev/null | head -1)"
    if [ -n "$legfrissebb" ] && [ -f "$cel/florum-data.json" ] && [ "$legfrissebb" != "$cel" ]; then
      echo "  · az új mappában már van adat → egyesítés a mentéssel"
      python3 "$ITT/kontener-adat.py" --egyesit "$legfrissebb" "$cel" | sed 's/^/    /'
    fi

    chmod 775 "$cel" 2>/dev/null || true
    chown 1000:1000 "$cel"/* 2>/dev/null || true

    # 2) régi konténer törlése (az adat már biztonságban)
    cim "A régi konténer törlése"
    docker rm -f "$KONTENER" >/dev/null 2>&1 && zold "  ✓ törölve" || sarga "  (nem sikerült – lehet, hogy már nincs)"

    # 3) új indítás
    cim "Az új verzió indítása"
    ( cd "$GYOKER/docker" && compose up -d --build ) || exit 1
    sleep 3
    "$0" ellenorzes
    echo
    zold "Kész. Az adat: ${cel#$GYOKER/}"
    echo "  Ha a felület üres lenne, a mentés itt van: ls -1 $GYOKER/docker/regi-kontener-mentes-*"
    ;;

  ellenorzes)
    cim "A futó példány válasza (/api/info)"
    if curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/api/info" 2>/dev/null | python3 -m json.tool 2>/dev/null | head -20; then
      :
    else
      piros "Nem válaszol a http://127.0.0.1:${PORT}/api/info"
      echo "  Indítsd: bash docker/florum-docker.sh indit"
      echo "  Vagy nézd a naplót: bash docker/florum-docker.sh naplo"
    fi
    ;;

  naplo)
    docker_van
    docker logs -f --tail 80 "$KONTENER"
    ;;

  mentes)
    docker_van
    cim "Adatok mentése ZIP-be"
    if [ ! -d "$GYOKER/docker/data" ]; then
      piros "Nincs mit menteni: $GYOKER/docker/data nem létezik."
      exit 1
    fi
    cel="$HOME/florum-docker-mentes-$(date +%Y%m%d-%H%M).zip"
    ( cd "$GYOKER/docker" && zip -qr "$cel" data ) || exit 1
    zold "Kész: $cel ($(du -h "$cel" | cut -f1))"
    echo "  Visszaállítás: unzip -o \"$cel\" -d \"$GYOKER/docker\"  (a konténer álljon le közben)"
    ;;

  frissit)
    docker_van
    cim "Frissítés (az adat megmarad)"
    # 1) új kód (ha git repó és van remote)
    if [ -d "$GYOKER/.git" ]; then
      local elotte; elotte="$(cat "$GYOKER/VERSION" 2>/dev/null || echo '?')"
      echo "  · git pull"
      if git -C "$GYOKER" pull --ff-only 2>&1 | sed 's/^/    /'; then :; else
        sarga "  a git pull nem sikerült (kézi módosítás? nincs remote?) – a mostani fájlokkal folytatom"
      fi
      local utana; utana="$(cat "$GYOKER/VERSION" 2>/dev/null || echo '?')"
      if [ "$elotte" != "$utana" ]; then zold "  verzió: $elotte → $utana"; fi
    fi
    # 2) új kép (a helyes build-kontextussal, lásd: compose-frissit)
    echo "  · új kép építése"
    "$0" epites || exit 1
    echo "  · konténer cseréje"
    ( cd "$GYOKER/docker" && compose up -d --build ) || exit 1
    sleep 3
    "$0" ellenorzes
    zold "A régi kép megmaradt visszaállításhoz: docker image ls | grep florum"
    ;;

  compose-frissit)
    # ==================================================================
    #  Arcane / Git Sync KONFIGURÁCIÓS fájl – külön mappába
    #
    #  MIÉRT KELL EZ?
    #    A docker/compose.yaml `build.context: ..` – azaz a build a repó
    #    gyökerét várja EGY szinttel feljebb. Arcane viszont csak a compose
    #    fájlt (vagy a saját mappáját) másolja a projekt-mappájába, a
    #    szülőmappa nem a repó gyökere lesz → a build elhasal
    #    („failed to read dockerfile: open Dockerfile: no such file”).
    #    Ezt a fájlt kifejezetten Arcane-hez készítjük: image: + ./data kötet,
    #    build NÉLKÜL. A képet a gazdagépen építjük (docker/florum-docker.sh
    #    epites), Arcane csak lefuttatja.
    # ==================================================================
    # ehhez NEM kell futó docker – csak egy fájlt írunk (Arcane-hoz)
    cel="$GYOKER/docker/arcane/compose.yaml"
    v="$(cat "$GYOKER/VERSION" 2>/dev/null || echo 0)"
    mkdir -p "$(dirname "$cel")"
    cat > "$cel" <<YAML
# ==============================================================
#  FLORUM – Arcane / Git Sync compose fájl (GENERÁLT!)
#
#  Ezt a fájlt a docker/florum-docker.sh compose-frissit készíti.
#  Kézzel ne írd át: a következő frissítés felülírja.
#
#  MIÉRT MÁS, MINT A docker/compose.yaml?
#    · nincs build: – a képet a gazdagépen építjük (docker/florum-docker.sh epites)
#    · nincs relatív build-kontextus, ezért Arcane Git Sync-kel is működik
#    · az adat a compose fájl melletti ./data mappában marad (Arcane projekt-mappa)
#
#  Arcane beállítás ehhez a fájlhoz:
#    Compose File Path:  docker/arcane/compose.yaml
#    Sync Files:         BE (a data mappa és a .env miatt)
#    Auto Sync:          BE, 5–15 perc
#    Redeploy After Sync: BE
# ==============================================================
name: florum

services:
  florum:
    # a .env-ben felülírható (FLORUM_VERSION) – így Arcane is a friss képet veszi
    image: florum:\${FLORUM_VERSION:-__VERZIO__}
    container_name: florum
    restart: unless-stopped
    ports:
      - "127.0.0.1:8777:8777"
    environment:
      TZ: Europe/Budapest
      FLORUM_DATA: /data
    volumes:
      - ./data:/data
    user: "1000:1000"
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8777/api/info',timeout=3).status==200 else 1)"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 15s
    logging:
      driver: json-file
      options:
        max-size: "5m"
        max-file: "3"
YAML
    # herdokumentum helyett egyszerű helyettesítés (a $ {...} maradjon érintetlen)
    python3 - "$cel" "$v" <<'PY2'
import io, sys
cel, v = sys.argv[1], sys.argv[2]
s = io.open(cel, encoding="utf-8").read().replace("__VERZIO__", v)
io.open(cel, "w", encoding="utf-8").write(s)
PY2
    # .env: a konkrét verzió – így az Arcane a friss képet használja
    printf 'FLORUM_VERSION=%s\n' "$v" > "$GYOKER/docker/arcane/.env"
    zold "Kész: $cel (verzió: $v)"
    zold "Kész: $GYOKER/docker/arcane/.env (FLORUM_VERSION=$v)"
    echo "  Arcane-ban ezt add meg: Compose File Path = docker/arcane/compose.yaml"
    ;;

  arcane-mentes)
    # ==================================================================
    #  ADAT-MENTÉS a KONTÉNERBŐL – Arcane frissítés ELŐTT
    #  Ha Arcane új projekt-mappát hoz létre (első szinkron), a korábbi
    #  konténer adatkönyvtára elérhetetlenné válhat. Előbb mentsd ki!
    # ==================================================================
    docker_van
    cim "Adat-mentés a futó konténerből"
    if ! docker ps --format '{{.Names}}' | grep -qx "$KONTENER"; then
      piros "  nem fut a(z) $KONTENER konténer – nincs mit menteni"
      return 1 2>/dev/null || exit 1
    fi
    cel="${2:-$HOME/florum-arcane-mentes-$(date +%Y%m%d-%H%M).zip}"
    # a zip ELŐBB a gazdagépen készül, azt másoljuk a konténerbe (ott nem kell zip)
    cel="${2:-$HOME/florum-arcane-mentes-$(date +%Y%m%d-%H%M).zip}"
    tmp="$(mktemp -d)"
    on="$tmp/florum-data"
    mkdir -p "$on"
    docker cp "$KONTENER:/data/." "$on/" >/dev/null 2>&1 || {
      piros "  a /data kimásolása nem sikerült (van egyáltalán adat a konténerben?)"; rm -rf "$tmp"; exit 1; }
    if command -v zip >/dev/null 2>&1; then
      ( cd "$tmp" && zip -qr "$cel" florum-data ) || { rm -rf "$tmp"; exit 1; }
    else
      # zip nélkül: egyszerű tar
      cel="${cel%.zip}.tar.gz"
      tar -czf "$cel" -C "$tmp" florum-data || { rm -rf "$tmp"; exit 1; }
    fi
    rm -rf "$tmp"
    zold "  mentve: $cel ($(du -h "$cel" | cut -f1))"
    echo
    echo "  Visszatöltés az ÚJ projekt-mappába (a konténer leállítása után):"
    echo "      docker stop $KONTENER"
    if [ "${cel##*.}" = "zip" ]; then
      echo "      unzip -o \"$cel\" -d /tmp/florum-vissza && \\"
      echo "        cp -a /tmp/florum-vissza/florum-data/. /opt/stacks/florum/data/"
    else
      echo "      tar -xzf \"$cel\" -C /tmp/florum-vissza && \\"
      echo "        cp -a /tmp/florum-vissza/florum-data/. /opt/stacks/florum/data/"
    fi
    echo "      docker start $KONTENER"
    echo
    echo "  (az útvonalat igazítsd az Arcane projekt-mappájához – a compose"
    echo "   fájl mellett lévő ./data mappa)"
    ;;

  leallit)
    docker_van
    cim "Leállítás (az adat megmarad)"
    ( cd "$GYOKER/docker" && compose down ) || docker stop "$KONTENER" >/dev/null 2>&1
    zold "Leállítva. Az adatok: $GYOKER/docker/data"
    ;;

  torol)
    docker_van
    cim "Leállítás + kép törlése (az ADAT megmarad)"
    ( cd "$GYOKER/docker" && compose down ) || docker stop "$KONTENER" >/dev/null 2>&1
    docker rmi "$KEP" 2>/dev/null && zold "Kép törölve: $KEP" || sarga "A képet nem tudtam törölni (talán használatban van)."
    echo "  Az adatok érintetlenek: $GYOKER/docker/data"
    ;;

  *)
    sed -n '3,18p' "${BASH_SOURCE[0]}" | sed 's/^#  //'
    ;;
esac
