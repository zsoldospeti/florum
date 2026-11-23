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
#  Építés (a zip kicsomagolt mappájában, ahol a florum.py van):
#      docker build -f docker/Dockerfile -t florum:1.33.4 .
#  vagy a kényelmi szkripttel:
#      bash docker/epit-es-indit.sh
# ==============================================================
FROM python:3.13-slim

# a kép verziója – a felület ezt írja ki a «futó példány» helyén
ARG FLORUM_VERSION=1.33.4
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
# a VERSION a build-argumentumból íródik felül (így a kép sosem hazudik verziót)
ARG FLORUM_VERSION=1.33.4
RUN printf '%s\n' "$FLORUM_VERSION" > /app/VERSION \
 && chown -R florum:florum /app

USER florum

# az adatmappa a kötet; a konténer indításakor jön létre
VOLUME ["/data"]
EXPOSE 8777

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8777/api/info',timeout=3).status==200 else 1)"

# FIGYELEM: --host 0.0.0.0 kötelező, különben a konténeren kívülről nem érhető el
ENTRYPOINT ["python3", "florum.py"]
CMD ["--szerver", "--port", "8777", "--host", "0.0.0.0", "--no-browser", "--data-dir", "/data"]
