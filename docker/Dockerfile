# ==============================================================
#  FLORUM – Docker kép
#
#  Miért épp így:
#    · a Florum NEM webalkalmazás-terhelés: egy Python-fájlszerver
#      + egyetlen HTML, ami a fájlrendszerbe ment (nincs adatbázis),
#    · a felület böngészőben fut, tehát a konténernek csak a HTTP
#      portot kell kiszolgálnia (8777),
#    · az ADATOK a /data kötetben vannak → konténer újrahúzás után is
#      megmaradnak,
#    · nem root-ként fut (uid 1000), csak a /data-hoz kell joga.
#
#  Építés (a repó gyökerében, ahol a florum.py van):
#      bash docker/florum-docker.sh epites
#  (ez a VERSION fájlból veszi a címkét ÉS ellenőrzi, hogy a HTML nem régebbi)
#
#  A VERZIÓ EGYETLEN igazsága a VERSION fájl – nem a --build-arg.
# ==============================================================
FROM python:3.13-slim

# --build-arg csak tartalék (ha a VERSION fájl hiányozna); az építés után a
# VERSION fájl tartalma a mérvadó. Így a kép nem hazudhat verziót.
ARG FLORUM_VERSION=""
ENV FLORUM_IMAGE_VERSION=${FLORUM_VERSION}
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLORUM_DATA=/data \
    TZ=Europe/Budapest

# nem root: 1000-es uid, a /data a köteté
RUN useradd --uid 1000 --user-group --create-home --shell /usr/sbin/nologin florum \
 && mkdir -p /app /data && chown -R florum:florum /app /data

WORKDIR /app

# csak a futtatáshoz kellő fájlok (a teszt/patch/előnézet NEM kerül bele)
COPY florum.py florum.html plants-db.json VERSION /app/
COPY naptar_ics.py naptar_forras.py mentes.py permetviz.py fotonezo.py \
     novenykereso.py emlekezteto.py florum.svg README.md OLVASSEL.txt /app/
# A VERSION fájl a repóból jön (COPY ... VERSION) – NEM írjuk felül a
# build-argumentummal. MIÉRT: ha a --build-arg és a VERSION eltér, a régi kód
# «új» verziót hazudna. Ellenőrizzük és figyelmeztetünk.
ARG FLORUM_VERSION=""
RUN set -eu; \
    felirt="$(cat /app/VERSION 2>/dev/null || true)"; \
    if [ -z "$felirt" ]; then \
      printf '%s\n' "${FLORUM_VERSION:-ismeretlen}" > /app/VERSION; \
      echo "VERSION fájl nem volt a repóban – a build-arg került a helyére"; \
    elif [ -n "$FLORUM_VERSION" ] && [ "$FLORUM_VERSION" != "$felirt" ]; then \
      echo "FIGYELEM: --build-arg=$FLORUM_VERSION, a VERSION fájl=$felirt"; \
      echo "          A VERSION fájl nyer (a kép nem hazudik verziót)."; \
    fi; \
    echo "Florum kép verziója: $(cat /app/VERSION)"; \
    chown -R florum:florum /app

USER florum

# az adatmappa a kötet; a konténer indításakor jön létre
VOLUME ["/data"]
EXPOSE 8777

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8777/api/info',timeout=3).status==200 else 1)"

# FIGYELEM: --host 0.0.0.0 kötelező, különben a konténeren kívülről nem érhető el
ENTRYPOINT ["python3", "florum.py"]
CMD ["--szerver", "--port", "8777", "--host", "0.0.0.0", "--no-browser", "--data-dir", "/data"]
