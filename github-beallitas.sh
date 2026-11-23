#!/usr/bin/env bash
# ==============================================================
#  FLORUM 1.33.4  ·  GitHub-hozzáférés beállítása és diagnózisa
#  Fájl:    github-beallitas.sh
#
#  MIRE JÓ?
#    A leggyakoribb hiba:
#        git@github.com: Permission denied (publickey).
#        fatal: Could not read from remote repository.
#    Ezt a szkript lefordítja magyarra: megmondja, MELYIK lépés
#    hiányzik, és pontosan mit kell beírni.
#
#  HASZNÁLAT
#      bash github-beallitas.sh              # diagnózis (nem változtat semmit)
#      bash github-beallitas.sh --kulcs      # SSH-kulcs készítése + kiírása
#      bash github-beallitas.sh --https FELHASZNALO/REPO   # HTTPS + token
#      bash github-beallitas.sh --ssh  FELHASZNALO/REPO    # SSH-ra állítás
#      bash github-beallitas.sh --proba      # kapcsolat-próba a GitHubbal
#      bash github-beallitas.sh --repo       # létezik-e a repó a GitHubon
#
#  FONTOS: a privát kulcs (id_ed25519) SOHA nem hagyja el a gépedet.
#  Csak a nyilvános kulcs (.pub) megy fel a GitHubra.
# ==============================================================
set -u

zold()  { printf '\033[32m%s\033[0m\n' "$*"; }
sarga() { printf '\033[33m%s\033[0m\n' "$*"; }
piros() { printf '\033[31m%s\033[0m\n' "$*"; }
cim()   { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()    { printf '  \033[32m✔\033[0m %s\n' "$*"; }
nem()   { printf '  \033[31m✘\033[0m %s\n' "$*"; }
tipp()  { printf '    \033[33m→\033[0m %s\n' "$*"; }

SSH_KONYVTAR="$HOME/.ssh"

# git ls-remote visszatérési kódjai:
#   0 = van ág (elérhető)   2 = elérhető, de ÜRES repó   128 = nem elérhető
# Az üres repót NEM szabad hibának venni – épp ez a friss repó tipikus esete.
repo_elerheto() {
  local url="$1" kod
  GIT_TERMINAL_PROMPT=0 git ls-remote --exit-code "$url" >/dev/null 2>&1
  kod=$?
  [ "$kod" -eq 0 ] || [ "$kod" -eq 2 ]
}

# ---- 1. van-e egyáltalán kulcs ---------------------------------------------
kulcsok() {
  local f
  for f in "$SSH_KONYVTAR"/id_ed25519.pub "$SSH_KONYVTAR"/id_ecdsa.pub \
           "$SSH_KONYVTAR"/id_rsa.pub; do
    [ -f "$f" ] && echo "$f"
  done
}

kulcs_letrehozas() {
  cim "SSH-kulcs készítése"
  if [ -f "$SSH_KONYVTAR/id_ed25519" ]; then
    ok "már van kulcs: $SSH_KONYVTAR/id_ed25519"
  else
    mkdir -p "$SSH_KONYVTAR"; chmod 700 "$SSH_KONYVTAR"
    if ! command -v ssh-keygen >/dev/null 2>&1; then
      nem "nincs ssh-keygen – telepítsd: sudo pacman -S openssh"; return 1
    fi
    # jelszó nélküli kulcs (a git push-hoz kényelmes; a kulcs a saját gépeden van)
    ssh-keygen -t ed25519 -C "florum@$(hostname)" -f "$SSH_KONYVTAR/id_ed25519" -N "" -q
    ok "kulcs elkészült: $SSH_KONYVTAR/id_ed25519"
  fi
  echo
  sarga "  EZT a NYILVÁNOS kulcsot másold be a GitHubra:"
  echo
  echo "  ┌──────────────────────────────────────────────────────────────"
  cat "$SSH_KONYVTAR/id_ed25519.pub" | sed 's/^/  │ /'
  echo "  └──────────────────────────────────────────────────────────────"
  cat <<EOF

  Hová:  https://github.com/settings/keys  →  „New SSH key”
         Title:  Florum ($(hostname))
         Key type: Authentication key
         Key:    a fenti sor ELEJÉTŐL a VÉGÉIG, egyben

  Utána ellenőrzés:
         bash github-beallitas.sh --proba

EOF
}

# ---- 2. kapcsolat-próba ----------------------------------------------------
proba() {
  cim "Kapcsolat-próba a GitHubbal (SSH)"
  if ! command -v ssh >/dev/null 2>&1; then
    nem "nincs ssh kliens – sudo pacman -S openssh"; return 1
  fi
  local kimenet
  kimenet="$(ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new \
                 -o ConnectTimeout=10 -T git@github.com 2>&1)"
  local kod=$?
  # a GitHub a sikeres azonosítást is 1-es kóddal zárja, az üzenet a lényeg
  if printf '%s' "$kimenet" | grep -q "successfully authenticated"; then
    ok "SSH azonosítás rendben"
    printf '    %s\n' "$(printf '%s' "$kimenet" | grep -i 'Hi ' | head -1)"
    return 0
  fi
  if printf '%s' "$kimenet" | grep -q "Permission denied (publickey)"; then
    nem "a GitHub NEM ismeri a kulcsodat (ezt látod most is)"
    echo
    sarga "  A hiba oka – válassz egyet:"
    cat <<EOF

  ① A nyilvános kulcs nincs feltéve a GitHubra (leggyakoribb)
     Ha van kulcsod:
         cat ~/.ssh/id_ed25519.pub        # ezt másold be
     Ha nincs:
         bash github-beallitas.sh --kulcs
     Hová: https://github.com/settings/keys → New SSH key

  ② A rossz kulcsot kínálja az ssh (több kulcs van a ~/.ssh-ban)
         ssh -vT git@github.com 2>&1 | grep "Offering public key"
     Ez megmutatja, melyiket próbálja. Ha nem a jó, a ~/.ssh/config-ba:
         Host github.com
             IdentityFile ~/.ssh/id_ed25519
             IdentitiesOnly yes

  ③ A 22-es portot tiltja a hálózat (router/tűzfal)
     Teszt:  ssh -T -p 443 git@ssh.github.com
     Ha ez működik, a ~/.ssh/config-ba:
         Host github.com
             HostName ssh.github.com
             Port 443
             User git

  ④ Inkább HTTPS (token) – nem kell SSH egyáltalán:
         bash github-beallitas.sh --https FELHASZNALONEV/florum

EOF
    return 1
  fi
  if printf '%s' "$kimenet" | grep -qi "could not resolve\|Connection refused\|timed out"; then
    nem "a GitHub nem érhető el (hálózat/tűzfal) – lásd ③"
    printf '    %s\n' "$(printf '%s' "$kimenet" | head -1)"
    return 1
  fi
  sarga "  Válasz: $(printf '%s' "$kimenet" | head -1)"
  return 1
}

# ---- 3. remote beállítása --------------------------------------------------
# ---- remote beállítása: akkor is működik, ha az origin MÁR LÉTEZIK ----------
# (a „git remote add” ilyenkor ezt adja: error: remote origin already exists.)
remote_beallit() {
  local url="$1" regi
  regi="$(git remote get-url origin 2>/dev/null || echo '')"
  if [ -n "$regi" ] && [ "$regi" = "$url" ]; then
    ok "origin már jó: $url"
  elif [ -n "$regi" ]; then
    git remote set-url origin "$url"
    sarga "  az origin átállítva:"
    printf '    régi: %s\n    új:   %s\n' "$regi" "$url"
  else
    git remote add origin "$url"
    ok "origin = $url"
  fi
}

# ---- létezik-e a repó a GitHubon? -----------------------------------------
repo_proba() {
  local url; url="$(git remote get-url origin 2>/dev/null || echo '')"
  local nev="${url##*/}"; nev="${nev%.git}"
  [ -n "$url" ] || { nem "nincs origin – előbb: bash github-beallitas.sh --ssh NEVED/florum"; return 1; }
  cim "Repó-ellenőrzés: $url"
  if repo_elerheto "$url"; then
    # üres-e (még nincs ág)?
    if [ -z "$(GIT_TERMINAL_PROMPT=0 git ls-remote "$url" 2>/dev/null)" ]; then
      ok "a repó létezik, de még ÜRES – ez jó (az első push feltölti)"
    else
      ok "a repó létezik és elérhető"
    fi
    return 0
  fi
  nem "a repó NEM érhető el ezen a címen"
  echo
  sarga "  Mit jelent: a GitHub nem találja a repót. Két oka lehet:"
  cat <<EOF

    ① A repó még nem létezik  →  https://github.com/new
       Repository name:  ${nev}
       Private ✔   ·   Add a README ✗   ·   .gitignore ✗

    ② A név/felhasználó nem stimmel. Amit most próbál:
           $url
       Helyes alak:  git@github.com:FELHASZNALONEV/REPO.git
       Átállítás:    bash github-beallitas.sh --ssh FELHASZNALONEV/REPO

  Van egy gyorsabb út is (a repót is létrehozza, nem kell böngésző):
       sudo pacman -S github-cli && gh auth login
       gh repo create FELHASZNALONEV/${nev} --private --source=. --remote=origin --push

EOF
  return 1
}

https_beallitas() {
  local repo="${1:-}"
  [ -n "$repo" ] || { nem "használat: bash github-beallitas.sh --https FELHASZNALO/florum"; return 1; }
  cim "HTTPS + token beállítása ($repo)"
  case "$repo" in
    git@*|ssh://*|http://*|https://*|/*) remote_beallit "$repo" ;;
    *) remote_beallit "https://github.com/${repo%.git}.git" ;;
  esac
  cat <<EOF

  A GitHub 2021 óta NEM fogadja el a jelszót. Token kell:

    1) https://github.com/settings/tokens  →  „Generate new token (classic)”
       vagy  Fine-grained tokens → Repository access: csak a florum
       Jogosultság:  repo  (classic)   /   Contents: Read and write  (fine-grained)
       Lejárat: 90 nap

    2) A tokent NE írd a repóba. Használd a hitelesítés-tárolót:

         git config --global credential.helper store
         git push -u origin main
         # felhasználónév: a GitHub-neved
         # jelszó:        a TOKEN (nem a jelszavad!)

    3) Ellenőrzés:
         git ls-remote origin | head -3

  Ha a token mégis bekerülne egy fájlba: .env / .gitignore (a repóban már tiltott).

EOF
}

ssh_beallitas() {
  local repo="${1:-}"
  [ -n "$repo" ] || { nem "használat: bash github-beallitas.sh --ssh FELHASZNALO/florum"; return 1; }
  cim "SSH-ra állítás ($repo)"
  case "$repo" in
    git@*|ssh://*|http://*|https://*|/*) remote_beallit "$repo" ;;
    *) remote_beallit "git@github.com:${repo%.git}.git" ;;
  esac
  sarga "  Előbb a kapcsolat legyen jó: bash github-beallitas.sh --proba"
}

# ---- 4. diagnózis (alap) ---------------------------------------------------
diagnozis() {
  cim "GitHub-hozzáférés – diagnózis"
  printf '  gép:       %s\n' "$(hostname)"
  printf '  felhasználó: %s\n' "$(whoami)"

  # git
  if command -v git >/dev/null 2>&1; then ok "git: $(git --version)"; else nem "nincs git"; fi

  # repó
  if git rev-parse --git-dir >/dev/null 2>&1; then
    ok "git repó: $(pwd)"
    local r
    r="$(git remote get-url origin 2>/dev/null || echo '')"
    if [ -n "$r" ]; then
      ok "origin: $r"
      if repo_elerheto "$r"; then
        ok "a repó elérhető a GitHubon"
      else
        nem "a repó NEM érhető el (Repository not found) – lásd: --repo"
      fi
    else
      nem "nincs origin (git remote add origin …)"
    fi
    printf '      ág: %s · verzió: %s\n' "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" \
           "$(cat VERSION 2>/dev/null || echo '?')"
  else
    sarga "  ez a mappa nem git repó – cd ~/florum, majd: bash florum-kiadas.sh --git-elokeszites"
  fi

  # kulcsok
  cim "SSH-kulcsok"
  local lista; lista="$(kulcsok)"
  if [ -z "$lista" ]; then
    nem "nincs SSH-kulcs a ~/.ssh mappában"
    tipp "bash github-beallitas.sh --kulcs"
  else
    local f
    for f in $lista; do
      ok "$(basename "$f")  ($(cut -d' ' -f1 "$f"))"
    done
    if [ -f "$SSH_KONYVTAR/id_ed25519" ]; then
      ok "van privát kulcs is: id_ed25519 (ez marad a gépen!)"
    else
      nem "csak .pub van, a privát kulcs (id_ed25519) hiányzik – új kulcs kell"
    fi
    # ssh-agent
    if command -v ssh-add >/dev/null 2>&1; then
      if ssh-add -l >/dev/null 2>&1; then
        ok "ssh-agent: $(ssh-add -l | wc -l) kulcs betöltve"
      else
        sarga "  ssh-agent: nincs kulcs betöltve (nem hiba, a fájlból is megy)"
        tipp "eval \$(ssh-agent -s) && ssh-add ~/.ssh/id_ed25519"
      fi
    fi
  fi

  # ismert host
  if [ -f "$SSH_KONYVTAR/known_hosts" ] && grep -q "github.com" "$SSH_KONYVTAR/known_hosts" 2>/dev/null; then
    ok "a github.com host-kulcsa ismert (a „yes” már megvolt – helyes volt)"
  else
    sarga "  a github.com host-kulcsa még nincs a known_hosts-ban (az első kapcsolatnál kérdez)"
  fi

  # tényleges próba
  echo
  proba
  local allapot=$?

  # összefoglaló
  cim "Összefoglaló"
  if [ "$allapot" -eq 0 ]; then
    zold "  A hozzáférés rendben. Feltöltés:"
    echo "      bash florum-kiadas.sh --feltoltes"
  else
    sarga "  A hozzáférés MÉG nem jó. A leggyorsabb út:"
    cat <<EOF

      # 1) kulcs (ha nincs) és a nyilvános rész kimásolása
      bash github-beallitas.sh --kulcs

      # 2) a kulcs felvétele:  https://github.com/settings/keys

      # 3) újra próba
      bash github-beallitas.sh --proba

      # 4) ha az SSH nem megy, HTTPS tokennel:
      bash github-beallitas.sh --https FELHASZNALONEV/florum

  A hiba, amit láttál („Permission denied (publickey)”), MINDIG ezt jelenti:
  a GitHub nem ismeri fel a gépedet. A repó jogosultsága ehhez semmi köze –
  előbb az azonosításnak kell működnie, utána jön a repó.
EOF
  fi
}

# ---- main -----------------------------------------------------------------
case "${1:-}" in
  --kulcs) kulcs_letrehozas ;;
  --proba) proba ;;
  --repo)  repo_proba ;;
  --https) https_beallitas "${2:-}" ;;
  --ssh)   ssh_beallitas "${2:-}" ;;
  ""|--diagnozis|-h|--help) diagnozis ;;
  *) printf 'ismeretlen kapcsoló: %s\n' "$1"; exit 1 ;;
esac
