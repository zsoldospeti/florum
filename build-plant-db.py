#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==============================================================
#  FLORUM 1.7.0  ·  otthoni növénygondozó
#  Fájl:    build-plant-db.py
#  Szerep:  az adatbázis építője (plants-db.json + a HTML-be ágyazott tartalék)
#  Licenc:  szabadon használható, módosítható és terjeszthető
# ==============================================================

"""
Florum növény-adatbázis építő.
Egyetlen forrásból állítja elő:
  - plants-db.json      (a frissíthető/cserélhető adatbázis-fájl)
  - a HTML-be ágyazott tartalék másolatot (BUNDLED_DB)

Formátum (soronként): (magyar név, latin név, álnevek, nehézség, fényigény,
                       öntözés nyáron, öntözés télen, tápoldat, permetezés,
                       átültetés hónap, páratartalom, hőmérséklet, talaj,
                       mérgező?, betegségek ;-vel, kártevők ;-vel, tippek ;-vel
                       [, flag-ek ;-vel])

Opcionális 18. mező (flag-ek, ;-vel):
  telente-nincs-tapoldat   -> fertWinter = 0  (télen pihen: nincs tápoldatozás)
  telente-huvos-hely       -> coldWinter = true (10–12 °C kell a virágzáshoz)
"""

import json
import os
import re
import sys
import unicodedata

FIELDS = [
    "name", "latin", "aliases", "difficulty", "light",
    "water", "waterWinter", "fert", "mist", "repot",
    "humidity", "temp", "soil", "toxic", "diseases", "pests", "tips",
]

# ---------------------------------------------------------------- permetezés vize
# A permetviz.py táblájával egyező értékek. A mészre/fluorra érzékeny fajok
# ioncserélt vizet kapnak, a többiek esővizet; ahol egyáltalán nincs permetezés
# (pozsgás, kaktusz, fűszernövény, pihés levelű), ott „nem”.
VIZKORE_ERZEKENY = ("ficus", "dracaena", "chlorophytum", "spathiphyllum",
                    "goeppertia", "maranta", "citrus", "fittonia", "asplenium")


def mist_water(plant):
    """Milyen vizet kér a permetezés? (permetviz.py: csap/eso/ion/nem)"""
    if int(plant["mist"]) <= 0:
        return "nem"
    latin = (plant["latin"] or "").lower()
    for kulcs in VIZKORE_ERZEKENY:
        if latin.startswith(kulcs) or (" " + kulcs) in latin:
            return "ion"
    return "eso"


DATA = """
Monstera|Monstera deliciosa|lyukas levelű filodendron; svájci sajt növény|Könnyű|Világos, szórt|7|12|30|7|24|50–60%|18–27 °C|Laza, levegős keverék: virágföld + perlit + kéreg|Mérgező macskára és kutyára|Sárguló alsó levelek – túlöntözés; Barna levélszél – száraz levegő; Levélfoltok – pangó víz|Pajzstetű; Takácsatka|Adj neki támasztékot, a légzőgyökereket ne vágd le.; Nyáron hetente töröld át a leveleit nedves ruhával.
Anyósnyelv|Dracaena trifasciata|Sansevieria; szobai kardvirág|Nagyon könnyű|Árnyékos|18|28|60|0|36|30–50%|15–29 °C|Homokos, kavicsos, nagyon jó vízelvezetés|Mérgező macskára és kutyára|Gyökérrothadás – túlöntözés; Puha, sárga levél – hideg + nedvesség|Pajzstetű|Inkább kevesebb víz: szárazon hetekig elvan.; Télen alig locsold, 12 °C fölé ne vidd.
Aranypothos|Epipremnum aureum|pothos; sárga levelű filodendron|Nagyon könnyű|Közepes|8|12|30|10|24|40–60%|18–29 °C|Általános virágföld, jó vízelvezetéssel|Mérgező macskára és kutyára|Sárga levelek – túlöntözés; Kopasz, hosszú hajtások – kevés fény|Pajzstetű; Takácsatka|Dugványozni sima pohár vízben is lehet.; A tarka fajtáknak több fény kell a mintázathoz.
Zamioculcas|Zamioculcas zamiifolia|zamiokulkász; ZZ növény|Nagyon könnyű|Árnyékos|18|25|60|0|36|30–50%|16–26 °C|Laza, homokos, kaktuszfölddel keverve|Mérgező macskára és kutyára|Gyökérrothadás – túl gyakori öntözés; Sárga levélke – pangó víz a cserépben|Pajzstetű|Víztároló gumója miatt hetekig bírja locsolás nélkül.; Sötét sarokba is jó, de lassabban nő.
Gumifa|Ficus elastica|szobafikusz; kaucsukfa|Közepes|Világos, szórt|7|12|30|7|24|40–60%|16–27 °C|Tápdús, jó vízelvezetésű virágföld|Mérgező (fehér nedv) macskára és kutyára|Levélesés – huzat vagy helyváltoztatás; Barna foltok – hideg öntözővíz|Pajzstetű; Takácsatka|Ne mozgasd gyakran, szereti a stabil helyet.; A port nedves ruhával töröld le a levelekről.
Hegedűlevelű fikusz|Ficus lyrata|fiddle leaf fig|Nehéz|Világos, szórt|7|12|30|7|24|40–60%|18–24 °C|Laza, tápdús virágföld|Mérgező macskára és kutyára|Barna levélszél – alulöntözés vagy száraz levegő; Levélesés – huzat|Takácsatka; Pajzstetű|Ne forgasd, ne költöztesd – nagyon érzékeny a változásra.; Csak langyos, állott vízzel öntözd.
Csüngő fikusz|Ficus benjamina|benjámin fikusz|Közepes|Világos, szórt|6|10|30|7|24|40–60%|16–26 °C|Tápdús, laza virágföld|Mérgező macskára és kutyára|Levélesés stresszre (huzat, költöztetés, szárazság); Barna levélcsúcs – vízkő|Pajzstetű; Takácsatka|Levélesés után ne öntözd túl – előbb a stresszt szüntesd meg.; Szereti a szórt fényt, de a déli tűző napot nem.
Orchidea|Phalaenopsis|pillangóorchidea|Közepes|Világos, szórt|10|14|30|5|24|50–70%|18–27 °C|Kéregkeverék – nem sima virágföld|Nem mérgező|Gyökérrothadás – pangó víz a cserép alján; Ráncos, petyhüdt levél – kevés víz|Pajzstetű; Meztelen csigák|Áztasd 10 percre, majd hagyd teljesen lecsöpögni.; A még zöld virágszárat ne vágd le, hozhat új bimbót.
Békeliliom|Spathiphyllum|fehér vitorlavirág|Könnyű|Közepes|6|10|30|10|18|50–70%|18–27 °C|Tápdús, laza virágföld|Mérgező macskára és kutyára|Barna levélszél – vízkő vagy száraz levegő; Nem virágzik – kevés fény|Takácsatka; Pajzstetű|A lógó levelei jelzik az öntözést – utána gyorsan helyrejön.; Szűrt vagy langyos vízzel locsold, virágzáskor tápoldatozd.
Csüngő csillagfürt|Chlorophytum comosum|póknövény; póknövényke|Nagyon könnyű|Világos, szórt|7|11|30|7|18|40–60%|15–26 °C|Általános virágföld|Nem mérgező – kisállatbarát|Barna levélcsúcs – fluoros vagy vízköves víz|Takácsatka|Az indáin növő sarjakat tedd vízbe gyökerezni.; Lógó edénybe való, de fény közelébe.
Sárkányfa|Dracaena marginata|madagaskári sárkányfa|Könnyű|Közepes|10|15|45|14|24|40–60%|18–25 °C|Laza, homokos virágföld|Mérgező macskára és kutyára|Barna levélcsúcs – száraz levegő, fluor|Pajzstetű; Tripsz|Langyos, szűrt víz – érzékeny a víz fluorjára.; Az alsó levelek elsárgulása természetes öregedés.
Pálmaliliom|Yucca elephantipes|jukka; szobai pálmaliliom|Könnyű|Napos / déli ablak|12|20|60|0|30|30–50%|15–27 °C|Homokos, kavicsos, jó vízelvezetés|Enyhén mérgező kisállatokra|Gyökérrothadás – túlöntözés; Alsó levelek sárgulása – kevés fény|Pajzstetű|Nyáron akár az erkélyre is kiviheted.; Fény felé nő, forgasd el időnként.
Aloé|Aloe vera|orvosi aloé|Könnyű|Napos / déli ablak|18|30|60|0|30|30–50%|15–30 °C|Kaktuszföld + homok vagy perlit|Enyhén mérgező kisállatokra|Nyálkás, barna levélalap – túlöntözés; Vékony, széteső levél – kevés fény|Pajzstetű|Öntözés után a föld száradjon ki teljesen.; Télen 10–15 °C-on szinte szárazon tartsd.
Gyöngyvirág-pozsgás|Haworthia fasciata|zebrapozsgás|Könnyű|Világos, szórt|18|28|60|0|30|30–50%|15–28 °C|Kaktuszföld + ásványi anyag|Nem mérgező|Gyökérrothadás – pangó víz; Megnyúlt levél – kevés fény|Pajzstetű|Kis cserépben érzi jól magát – ne ültesd túl nagyba.; Nyáron a reggeli napot szereti.
Echeveria|Echeveria elegans|pozsgás rozetta; kőrózsa|Könnyű|Napos / déli ablak|14|24|60|0|30|30–50%|10–28 °C|Kaktuszföld + perlit|Nem mérgező|Megnyúlt rozetta – kevés fény; Rothadás – túlöntözés|Lisztes tetű; Pajzstetű|Sok napfény kell a tömör, színes formához.; Öntözd a földet, ne a levélrózsát.
Pénzfa|Crassula ovata|jade növény; szerencsefa|Könnyű|Napos / déli ablak|14|24|60|0|30|30–50%|15–27 °C|Laza, ásványi anyagokban gazdag|Mérgező macskára és kutyára|Hulló levél – túlöntözés vagy hideg; Megnyúlt hajtás – kevés fény|Lisztes tetű|A levélhullás gyakran túlöntözés jele – adj neki száraz napokat.; Nyáron kiváló az erkély, télen hűvös pihenő.
Karácsonyi kaktusz|Schlumbergera|schlumbergera; karácsonyi kaktusz|Könnyű|Világos, szórt|10|14|30|14|24|50–60%|18–25 °C|Laza, tőzeges, jó vízelvezetés|Nem mérgező|Rügyhullás – huzat, szárazság; Rothadás – pangó víz|Lisztes tetű|Virágzáshoz ősszel 14 óra sötétség kell.; Bimbósan ne forgasd, ne mozgasd.
Kalatea|Goeppertia|Calathea; pávalevél|Nehéz|Közepes|5|8|30|3|18|60–70%|18–26 °C|Laza, tőzeges, levegős|Nem mérgező|Barna levélszél – vízkő vagy száraz levegő; Feltekeredő levél – huzat|Takácsatka; Tripsz|Csak langyos, szűrt vagy desztillált víz.; Ne tedd huzatra vagy radiátor mellé.
Imanövény|Maranta leuconeura|imalevél; maranta|Közepes|Közepes|5|8|30|3|18|60–70%|18–26 °C|Laza, tőzeges|Nem mérgező|Barna levélszél – száraz levegő; Elszíntelenedő minta – erős fény|Takácsatka|Esténként összecsukja a leveleit – ez normális.; Párás hely (fürdőszoba) kedvez neki.
Boston páfrány|Nephrolepis exaltata|bostoni páfrány|Közepes|Közepes|5|8|30|3|18|60–70%|16–24 °C|Tőzeges, laza|Nem mérgező|Barna, száraz levélke – száraz levegő; Levélhullás – huzat|Takácsatka|A fürdőszoba párás levegője ideális neki.; Ne engedd teljesen kiszáradni a földjét.
Madárfészek páfrány|Asplenium nidus|fészekpáfrány|Könnyű|Közepes|7|10|30|5|24|50–70%|18–26 °C|Laza kéregkeverék, levegős|Nem mérgező|Barna levélszél – száraz levegő; Rothadás a fészek közepén – túlöntözés|Pajzstetű|A levelek közé ne önts vizet – a földet locsold.; Félárnyékos, párás hely a legjobb.
Borostyán|Hedera helix|közönséges borostyán|Könnyű|Közepes|7|10|30|7|18|40–60%|12–22 °C|Általános virágföld|Mérgező macskára és kutyára|Levélfoltok – hideg, nedves föld; Ritkuló hajtás – kevés fény|Takácsatka; Pajzstetű|Télen szereti a hűvös (10–18 °C) helyet.; Támasszal vagy csüngő edényben is szép.
Zebratradescantia|Tradescantia zebrina|tradeszkancia; vándorló zsidó|Könnyű|Világos, szórt|7|11|30|7|18|40–60%|15–27 °C|Általános virágföld|Enyhén mérgező macskára és kutyára|Kopasz, megnyúlt hajtás – kevés fény; Foltosodó levél – hideg víz|Takácsatka|Vágd vissza bátran, sűrűbb és színesebb lesz.; A végét dugványként vízbe teheted.
Afrikai ibolya|Saintpaulia ionantha|saintpaulia|Közepes|Világos, szórt|5|8|21|0|12|50–60%|18–24 °C|Laza, tőzeges, alulról öntözve|Nem mérgező|Levélfoltok – hideg víz a levélen; Rothadás – pangó víz a cserépaljban|Tripsz; Lisztes tetű|Alulról öntözd, a levelei ne legyenek vizesek.; A túl nagy cserép lassítja a virágzást.
Begónia|Begonia rex|levéldíszbegónia|Közepes|Világos, szórt|6|10|30|0|18|50–60%|18–24 °C|Laza, tőzeges|Mérgező macskára és kutyára|Lisztes harmat – párás, hűvös levegő; Szárrothadás – túlöntözés|Tripsz|Ne permetezd a levelét – foltosodik.; A fényes, szórt hely adja a levélmintázatot.
Flamingóvirág|Anthurium andraeanum|anthurium|Közepes|Világos, szórt|7|11|30|7|24|60–70%|18–27 °C|Laza, levegős: kéreg + perlit + tőzeg|Mérgező macskára és kutyára|Barna levélszél – száraz levegő; Rothadás – pangó víz|Takácsatka; Pajzstetű|A „virág” valójában fellevel – a valódi virágok rajta aprók.; Virágzáshoz világos, de nem tűző hely kell.
Syngonium|Syngonium podophyllum|nyíllevelű|Könnyű|Közepes|7|11|30|10|18|50–70%|18–27 °C|Laza, tápdús virágföld|Mérgező macskára és kutyára|Sárguló levél – túlöntözés; Megnyúlt hajtás – kevés fény|Takácsatka; Pajzstetű|Fiatalon tömör, később kúszik – adj neki támogatást.; Könnyen gyökerezik vízben.
Kúszó filodendron|Philodendron hederaceum|szívdobogás filodendron|Nagyon könnyű|Közepes|7|11|30|10|18|50–70%|18–27 °C|Laza, tápdús virágföld|Mérgező macskára és kutyára|Sárga levelek – túlöntözés; Kis levelek – kevés fény|Pajzstetű; Takácsatka|Minden leveles csomónál gyökérered, könnyen szaporítható.; Mossa le a poros leveleket.
Aglaonema|Aglaonema commutatum|kínai örökzöld; ezüstös aglaonema|Könnyű|Árnyékos|8|12|45|10|24|50–60%|18–27 °C|Laza, tápdús virágföld|Mérgező macskára és kutyára|Sárguló levél – hideg vagy túlöntözés; Megnyúlt szár – kevés fény|Pajzstetű|Szereti a meleget – 15 °C alatt megáll a növekedése.; Sötétebb helyet is elvisel, de lassabban nő.
Dieffenbachia|Dieffenbachia seguine|szobadíszlevél|Közepes|Közepes|7|10|30|7|18|50–60%|18–27 °C|Laza, tápdús virágföld|Erősen mérgező macskára és kutyára, emberre is|Alsó levelek sárgulása – túlöntözés; Megnyúlt szár – kevés fény|Takácsatka; Pajzstetű|A nedve bőrirritáló – metssz kesztyűben.; Ne tedd kisgyermekes helyre kézmagasságba.
Citrus|Citrus microcarpa|calamondin; szobai citromfa|Nehéz|Napos / déli ablak|5|7|21|14|24|50–60%|15–25 °C|Tápdús, savanyú kémhatású citrusföld|Nem mérgező|Levélesés – kevés fény vagy hőingás; Sárga levél – tápanyaghiány|Takácsatka; Lisztes tetű|Nyáron vidd ki az erkélyre, télen 10–15 °C-on teleljen.; Tavasszal metssz vissza a bokrosodáshoz.
Viaszvirág|Hoya carnosa|hoya|Könnyű|Világos, szórt|10|18|30|7|24|40–60%|18–27 °C|Laza, levegős keverék|Nem mérgező|Bimbóhullás – mozgatásra, huzatra; Levélfoltok – pangó víz|Lisztes tetű; Pajzstetű|A virágzó kocsányt ne vágd le – ott virágzik újra.; Kis cserépben virágzik a legszebben.
Peperomia|Peperomia obtusifolia|kereklevelű peperomia|Könnyű|Világos, szórt|10|15|30|5|18|40–60%|18–26 °C|Laza, levegős virágföld|Nem mérgező|Rothadó szár – túlöntözés; Fonnyadó levél – kiszáradás|Takácsatka|Félpozsgás: a földje öntözés között száradjon ki.; Kicsi cserépben gyönyörűen mutat.
Pilea|Pilea peperomioides|pénzérme növény|Könnyű|Világos, szórt|8|12|30|5|18|40–60%|18–24 °C|Laza, tápdús virágföld|Nem mérgező|Alsó levelek sárgulása – túlöntözés; Apró, göcsörtös levél – kevés fény|Takácsatka|Hetente forgasd el – a növekedés a fény felé húz.; Az indáin növő sarjakat könnyű leválasztani.
Kalanchoe|Kalanchoe blossfeldiana|korallvirág|Könnyű|Napos / déli ablak|10|18|30|0|18|40–60%|18–26 °C|Kaktuszföld, jó vízelvezetés|Mérgező macskára és kutyára|Megnyúlt hajtás – kevés fény; Rothadás – túlöntözés|Lisztes tetű|Az elnyílt virágokat vágd le – újra hoz bimbót.; Nyáron napos, télen világos helyen tartsd.
Ernyőfa|Schefflera arboricola|schefflera; ernyős fa|Könnyű|Világos, szórt|8|12|30|10|24|40–60%|16–26 °C|Tápdús, laza virágföld|Mérgező macskára és kutyára|Lehulló levél – huzat, hideg; Barna levélcsúcs – száraz levegő|Pajzstetű; Takácsatka|A leveleket időnként permetezd be langyos vízzel.; Ne tedd huzatos ajtó közelébe.
Kroton|Codiaeum variegatum|csodacserje|Közepes|Világos, szórt|7|10|30|14|24|50–70%|18–27 °C|Tápdús, laza virágföld|Mérgező macskára és kutyára|Levélesés – huzat, hideg; Színtelen levél – kevés fény|Takácsatka; Pajzstetű|Huzat- és hidegérzékeny – 18 °C alatt hullajtja a leveleit.; A színes levélhez sok szórt fény kell.
Hegyi pálma|Chamaedorea elegans|szobai pálma; chamaedorea|Könnyű|Közepes|7|11|45|10|24|50–60%|18–26 °C|Laza, tápdús virágföld|Nem mérgező|Barna levélcsúcs – száraz levegő; Pajzstetű a levélhónaljban|Pajzstetű|Alacsony, szűrt fényt is elvisel.; Ne engedd kiszárítani – vékony a gyökérzete.
Fittonia|Fittonia albivenis|ideglevélke; mozaiknövény|Nehéz|Közepes|5|8|30|3|18|60–70%|18–25 °C|Laza, tőzeges|Nem mérgező|Azonnal elernyed – kiszáradás; Száraz levélszél – száraz levegő|Takácsatka|Drámai jelzőnövény: ha elernyed, azonnal öntözd meg.; Párás, meleg hely (üvegház, fürdő) ideális.
Alocasia|Alocasia amazonica|elefántfül|Közepes|Világos, szórt|7|12|30|10|18|60–70%|18–27 °C|Laza, levegős: kéreg + perlit|Mérgező macskára és kutyára|Sárguló levél – pangó víz; Barna levélcsúcs – száraz levegő|Takácsatka; Tripsz|Télen dobhatja a leveleit és pihen – ez normális.; A gumót tartsd csak enyhén nedvesen a szünetben.
Kaktusz|Cactaceae|kaktusz|Nagyon könnyű|Napos / déli ablak|21|35|60|0|36|20–40%|10–30 °C|Kaktuszföld + homok vagy perlit|Fajfüggő|Rothadás – túlöntözés; Vékony, nyúlt növés – kevés fény|Pajzstetű|Télen hűvös (8–12 °C) és szinte száraz pihenő kell.; Nyáron csak a föld kiszáradása után öntözd.
Gyöngyfüzér|Senecio rowleyanus|borsós nyaklánc; gyöngyvirág-pozsgás|Közepes|Napos / déli ablak|14|24|60|0|18|30–50%|15–27 °C|Kaktuszföld + perlit|Mérgező macskára és kutyára|Zsugorodó szemek – kevés víz; Rothadó szár – túlöntözés|Lisztes tetű|Csüngő edényben, fény felé nő a legszebben.; A földje öntözés között száradjon ki teljesen.
Kávécserje|Coffea arabica|szobai kávéfa|Közepes|Közepes|7|11|30|10|24|60–70%|18–24 °C|Laza, tápdús, savanyú kémhatású|Enyhén mérgező kisállatokra|Barna levélfoltok – száraz levegő; Levélesés – huzat|Pajzstetű; Takácsatka|Szereti a párás, meleg, szórt fényes helyet.; Ne hagyd kiszáradni – vékonyak a levelei.
Bazsalikom|Ocimum basilicum|bazsalikus; fűszernövény|Közepes|Napos / déli ablak|3|4|14|0|12|50–60%|20–26 °C|Tápdús, laza virágföld|Nem mérgező|Elernyedő levél – kiszáradás; Megnyúlt szár – kevés fény|Levéltetű|A virágot csípd le, hogy a levél maradjon a főszerepben.; Tartsd a konyha legvilágosabb, meleg helyén.
Menta|Mentha spicata|fodormenta; fűszernövény|Könnyű|Világos, szórt|3|4|14|0|12|50–60%|18–25 °C|Tápdús, nyirkos virágföld|Nem mérgező|Sárguló levél – túlöntözés; Elszáradás – kiszáradás|Levéltetű|Tartsd nyirkosan, de ne álljon vízben.; Folyamatos szedéssel bokrosodik.
Rozmaring|Salvia rosmarinus|rosmarinus officinalis; fűszernövény|Közepes|Napos / déli ablak|5|8|30|0|18|40–50%|15–25 °C|Homokos, jó vízelvezetésű|Enyhén mérgező kisállatokra|Elszáradó levél – kiszáradás; Gyökérrothadás – pangó víz|Levéltetű|Szereti a sok napot és a jó szellőzést.; Télen hűvös, világos helyen tartsd.
Levendula|Lavandula angustifolia|lavendula; fűszernövény|Közepes|Napos / déli ablak|10|16|45|0|24|30–50%|12–25 °C|Homokos, meszes, jó vízelvezetés|Enyhén mérgező kisállatokra|Gyökérrothadás – pangó víz; Nyúlt növés – kevés fény|Levéltetű|Imádja a napot és a száraz földet.; Virágzás után vágd vissza a felét.
Ciklámen|Cyclamen persicum|álciklámen|Közepes|Világos, szórt|5|7|30|0|18|50–60%|10–18 °C|Laza, tőzeges, jó vízelvezetés|Mérgező macskára és kutyára|Rothadó gumó – víz a levélrózsában; Bimbóhullás – túl meleg|Pajzstetű|Hűvös (10–18 °C) helyen virágzik sokáig.; Alulról öntözd, a gumót ne áztasd.
Klívia|Clivia miniata|szobaliliom; kafferliliom; clivia; kafirliliom|Közepes|Világos, szórt|7|21|14|0|30|40–60%|10–20 °C (télen 10–12 °C)|Laza, tápdús, jó vízelvezetésű – a vastag gyökereket ne bolygasd|Mérgező macskára és kutyára|Gyökérrothadás – pangó víz a cserép alján; Levélfoltok – hideg víz a levélrózsába; Nincs virágzás – elmaradt a téli hideghatás; Bimbóbeszorulás – túl korán kapott meleget; Megnyúlt, sápadt levél – kevés fény|Pajzstetű; Takácsatka|A virágzás titka a téli pihentetés: októbertől januárig 10–12 °C, szinte semmi víz, nulla tápoldat.; Ne forgasd és ne mozgasd – a bimbók elhalhatnak. Jelöld meg az ablak felőli oldalát.; Csak akkor vidd vissza a meleg (18–20 °C) szobába, ha a virágszár már 10–15 cm-es.; Bimbózáshoz kálium- és foszforgazdag (virágzó növényeknek való) tápoldat, tavasztól 2 hetente.; Szűk cserépben virágzik a legszebben – átültetni 2–3 évente, közvetlenül virágzás után.; Keleti vagy északi ablak a legjobb, nyáron ne érje tűző nap, mert megég a levél.; A leveleit ne permetezd: a levélrózsába jutó víz rothadást okoz.|telente-nincs-tapoldat;telente-huvos-hely
Gyömbér|Zingiber officinale|gyömbérgyökér; konyhai gyömbér; magról nevelhető|Könnyű|Világos, szórt|6|14|21|7|12|50–70%|20–28 °C|Laza, tápdús virágföld + perlit|Nem mérgező|Sárguló levél – túlöntözés vagy téli pangó víz; Rothadó gumó – víz a cserép alján; Barna levélszél – száraz levegő|Pajzstetű; Takácsatka|A bolti gyömbérgumót áztasd be, majd fektesd sekélyen nedves földbe, a rügyek felfelé.; Levelei dísznövényként is mutatósak – 60–90 cm-re is megnő.; Télen hűvösebb, világos helyen tartsd, és alig locsold.
Avokádó|Persea americana|avokádófa; avokádó mag; magról nevelhető|Közepes|Világos, szórt|7|10|30|14|12|40–60%|18–27 °C|Laza, tápdús, jó vízelvezetésű virágföld|Mérgező macskára és kutyára (a levele és a mag)|Barna levélcsúcs – vízkő vagy száraz levegő; Levélhullás – hideg, huzat vagy túlöntözés; Kopasz, nyúlánk szár – kevés fény|Takácsatka; Pajzstetű; Lisztes tetű|A magot fogpiszkálóval víz fölé tedd – 3–6 hét alatt gyökerezik, de földbe fektetve is kihajt.; Ha kopaszra nő, vágd vissza a csúcsát – bokrosodni fog.; Szobában dísznövény: termést csak kertben, nagy fával hoz.
Kurkuma|Curcuma longa|indiai sáfrány; kurkumagyökér; magról nevelhető|Könnyű|Világos, szórt|6|14|21|7|12|50–70%|20–28 °C|Laza, tápdús virágföld + perlit|Nem mérgező|Sárguló levél – túlöntözés vagy pangó víz; Ősszel elszáradó levél – természetes pihenő|Pajzstetű|A bolti kurkumagyökérből ugyanúgy hajt, mint a gyömbér.; Ősszel levelei elsárgulnak és behúznak, télen a gumó pihen – tavasszal újra hajt.; Nagy, díszes levelei miatt kedvelt szobanövény.
Ananász|Ananas comosus|ananászfej; magról nevelhető|Közepes|Napos / déli ablak|10|18|30|7|24|50–60%|18–28 °C|Kaktuszföld és virágföld keveréke, jó vízelvezetés|Nem mérgező|Rothadó levélrózsa – víz a levelek közepén; Barna levélcsúcs – száraz levegő|Pajzstetű|A bolti ananász fejét csavard le, az alsó leveleket hámozd le, 2 napig szárítsd, majd ültesd laza földbe.; Lassan nő, de a levélrózsa mutatós dísz.; Télen kevesebb vizet adj, és ne locsold a levélrózsa közepét.
Édesburgonya|Ipomoea batatas|batáta; indiai burgonya; magról nevelhető|Könnyű|Napos / déli ablak|4|7|21|7|12|40–60%|20–28 °C|Laza, homokos virágföld, jó vízelvezetés|Enyhén mérgező kisállatokra (a levelei)|Sárguló levél – túlöntözés; Rothadó gumó – pangó víz; Megnyúlt hajtás – kevés fény|Pajzstetű; Levéltetű|Egy bolti édesburgonyát félbevágva, fogpiszkálóval víz fölé téve 2–3 hét alatt gyökerezik és hajt.; A hajtásait vízben is gyökereztetheted, majd földbe ültetve futó dísznövény lesz.; Kedveli a meleget – 18 °C alatt alig nő.
Fokhagyma|Allium sativum|fokhagymazöld; hagymazöld; újhagyma zöldje; magról nevelhető|Nagyon könnyű|Világos, szórt|4|7|21|0|12|40–60%|15–24 °C|Általános, lazább virágföld|Mérgező macskára és kutyára (hagymafélék)|Sárguló levélcsúcs – túlöntözés; Elszáradó levél – kiszáradás|Levéltetű|Egy gerezd fokhagymát tedd cserépbe, hegyes végével felfelé – 1–2 hét alatt zöldje nő.; A zöldjét vágd le, a hagyma a földben marad és újra hajt.; Világos ablakban tartsd, nyáron a konyhakertbe is kivihető.
Citrusmag|Citrus spp.|citrommag; narancsmag; citrusfa magról; magról nevelhető|Közepes|Napos / déli ablak|5|8|21|14|18|50–60%|18–26 °C|Tápdús, savanyú kémhatású citrusföld|Nem mérgező|Levélesés – huzat, hőingás; Sárga levél – tápanyaghiány; Barna levélcsúcs – száraz levegő|Takácsatka; Lisztes tetű|A friss magot 1 napig áztasd, majd 1 cm mélyre ültesd laza földbe – 2–4 hét alatt kikel.; Sok fényt és meleget kér, télen 12–15 °C-on teleljen.; Szobában dísznövény: virágzás csak idővel, nagyobb példányon várható.
Datolyapálma|Phoenix dactylifera|datolyamag; datolya; magról nevelhető|Könnyű|Napos / déli ablak|7|12|30|7|24|40–50%|18–28 °C|Laza, homokos, jó vízelvezetés|Nem mérgező|Barna levélcsúcs – száraz levegő; Rothadó mag – túl nedves föld; Megnyúlt levél – kevés fény|Pajzstetű|A kimagozott datolyát 1–2 napig áztasd, majd ültesd – 4–8 hét alatt kikel.; Lassan nő, de a szúrós, legyezős levél nagyon mutatós.; Sok fényt és meleget szeret, nyáron az erkélyre is kivihető.
Mangófa|Mangifera indica|mangómag; mangó; magról nevelhető|Közepes|Napos / déli ablak|6|10|30|10|24|50–70%|20–28 °C|Laza, tápdús virágföld + perlit|Enyhén mérgező kisállatokra|Barna levélcsúcs – száraz levegő; Levélesés – hideg, huzat; Rothadó mag – túlöntözés|Takácsatka; Pajzstetű|A magot bontsd ki a hüvelyéből, 2–3 napig szárítsd, majd lapjával fektesd félig földbe.; Gyorsan nő, de a hideget nem bírja – télen meleg, világos hely kell.; Ha túl nyúlánk, vágd vissza a csúcsát – bokrosodni fog.
Kivi|Actinidia deliciosa|kivimag; kivifa; magról nevelhető|Közepes|Világos, szórt|5|8|21|10|18|50–60%|18–26 °C|Laza, tápdús virágföld|Nem mérgező|Barna levélcsúcs – száraz levegő; Sárguló levél – túlöntözés; Megnyúlt hajtás – kevés fény|Takácsatka; Pajzstetű|Érett kiviből szedd ki a magokat, mosd meg és pár napig szárítsd.; Vetés után 3–6 hét alatt kel – melegen, fólia alatt gyorsabb.; Kúszónövény: adj neki támrudat, hogy felkapaszkodjon.
Maracuja|Passiflora edulis|passion fruit; passiógyümölcs; golgotavirág; magról nevelhető|Közepes|Napos / déli ablak|4|7|21|10|18|50–60%|18–28 °C|Laza, tápdús virágföld|Nem mérgező|Barna levélfoltok – pangó víz; Levélesés – huzat, hideg; Nem virágzik – kevés fény|Takácsatka; Levéltetű|A friss termésből kivett magot mosd meg, majd ültesd – 2–4 hét alatt kikel.; Gyorsan kúszik: rácson neveld, és metszd, hogy ne nyúljon meg.; Nyáron sok vizet és fényt kér, télen hűvösebb, világos helyen tartsd.
Petrezselyem|Petroselinum crispum|fűszernövény; petrezselyemzöld|Könnyű|Világos, szórt|3|5|14|0|12|40–60%|15–25 °C|Tápdús, laza virágföld|Nem mérgező|Sárguló levél – túlöntözés; Elszáradás – kiszáradás|Levéltetű|A szárát vágd, ne a levelek közepét – így újra hajt.; Hűvösebb, világos helyen érzi jól magát, nyáron kint is tartható.; A magja lassan kel (2–4 hét) – áztatás után gyorsabb.
Snidling|Allium schoenoprasum|fűszernövény; metélőhagyma|Nagyon könnyű|Világos, szórt|3|5|21|0|12|40–60%|15–22 °C|Tápdús virágföld|Mérgező macskára és kutyára (hagymafélék)|Sárguló levélcsúcs – túlöntözés; Elszáradás – kiszáradás|Levéltetű|2–3 cm-re a föld felett vágd, gyorsan újra hajt.; Nyáron hozott lila virágai ehetők is.; Hűvösebb, világos hely a legjobb neki.
Oregánó|Origanum vulgare|fűszernövény; szurokfű|Könnyű|Napos / déli ablak|4|6|21|0|18|40–50%|15–25 °C|Laza, homokos, jó vízelvezetés|Nem mérgező|Gyökérrothadás – pangó víz; Megnyúlt szár – kevés fény; Barna levél – szárazság|Levéltetű|Sok napot és kevés vizet szeret.; A virágzó csúcsot csípd le, így a levelei tömöttebbek maradnak.; Nyáron az erkélyre is kivihető.
Kakukkfű|Thymus vulgaris|fűszernövény; timián|Könnyű|Napos / déli ablak|5|8|30|0|18|30–50%|15–25 °C|Homokos, kavicsos, jó vízelvezetés|Nem mérgező|Gyökérrothadás – túlöntözés; Kopaszodó tövű növény – kevés fény|Levéltetű|Mediterrán növény: száraz föld, sok fény, jó szellőzés.; Öntözés között hagyd kiszáradni a földjét.; Télen hűvös, világos helyen tartsd.
Zsálya|Salvia officinalis|fűszernövény|Közepes|Napos / déli ablak|5|8|30|0|18|40–50%|15–25 °C|Homokos, laza virágföld|Nem mérgező|Gyökérrothadás – pangó víz; Elszáradó levél – száraz, meleg levegő|Levéltetű|A fűtött szoba száraz neki – hűvösebb, világos hely kedvez.; Metszd virágzás előtt, hogy ne forduljon el virágba.; Az alsó leveleit szedd, ne a csúcsokat.
Koriander|Coriandrum sativum|fűszernövény; korianderzöld|Közepes|Világos, szórt|3|5|14|0|12|40–60%|15–24 °C|Laza, tápdús virágföld|Nem mérgező|Megnyúlt szár – kevés fény; Sárguló levél – túlöntözés; Hamar virágba fordul – meleg|Levéltetű|Hűvös, világos helyen lassabban fordul virágba.; 2–3 hetente vess új adagot, mert hamar befejezi.; A levelét szedd, a virágzó szárat vágd le.
Citromfű|Melissa officinalis|fűszernövény; melissza|Könnyű|Közepes|3|5|21|5|18|40–60%|15–25 °C|Laza, tápdús virágföld|Nem mérgező|Levélfoltok – túlöntözés; Megnyúlt szár – kevés fény|Levéltetű|Citromos illatú, teának kiváló – rendszeres szedéssel bokrosodik.; Virágzás előtt vágd le, akkor a legillatosabb.; Nyáron a félárnyékot is elviseli.
Majoranna|Origanum majorana|fűszernövény; majoránna|Könnyű|Napos / déli ablak|4|6|21|0|18|40–50%|18–26 °C|Laza, homokos virágföld|Nem mérgező|Gyökérrothadás – pangó víz; Megnyúlt szár – kevés fény|Levéltetű|Meleget és sok napot szeret – a legnaposabb ablak jó neki.; Vágd a csúcsokat használatkor, így sűrű marad.; Télen világos, hűvösebb helyen tartsd.
Leopárdnövény|Drimiopsis maculata|leopárdnövény; pöttyös leopárdnövény; pettyes leopárdnövény; Ledebouria petiolata; afrikai pöttyös hagymás|Könnyű|Világos, szórt|10|18|30|0|30|40–60%|18–24 °C|Laza, jó vízelvezetésű keverék: virágföld + perlit + homok|Nem ismert mérgező hatása – kisállatbarát|Gyökérrothadás – túlöntözés, pangó víz; Sárguló, puha levél – télen hideg és nedves föld; Barna levélcsúcs – meszes öntözővíz|Pajzstetű; Takácsatka|Két öntözés között a föld felszíne száradjon ki – a hagyma a pangó vizet nem bírja.; A pettyek kontrasztja szórt fényben erősödik, tűző napon kifakulhat.; Lassan nő: csak 2-3 évente ültesd át, a kisebb cserépben is jól érzi magát.; Tavasszal fehér fürtvirágzatot hoz a levelek fölé.; Magyar webshopból beszerezhető (tropusinoveny.hu), 12 cm-es cserépben, több tővel érkezik.|telente-nincs-tapoldat
Elefántláb|Beaucarnea recurvata|elefántláb; elefantlab; palackfa; nolina; lófarkú pálma; Nolina recurvata; bokorliliom-fa|Könnyű|Napos / déli ablak|14|35|30|0|24|30–50%|18–27 °C (télen legalább 10 °C)|Kaktuszföld + kevés tőzeg, jó vízelvezetéssel – a szűk cserép jó neki|Nem mérgező – kisállatbarát|Szárrothadás – a leggyakoribb ok a túlöntözés; Levélfoltosság – pangó víz, rossz szellőzés; Bakteriális levélfoltosság – nedves levélzet; Gyökérrothadás – nem tud kiszikkadni a föld|Pajzstetű; Takácsatka|A megvastagodott törzs nedvességtároló: tavasztól őszig mérsékelten öntözd, télen szinte szárazon tartsd.; A kaktuszföld + tőzeg keverék és a szűk cserép védi a legjobban a szárrothadástól.; Télen világos, hűvös hely (legalább 10 °C) kell neki – nyáron a védett erkély is jó.; Tavasztól őszig havonta tápoldat, októbertől február végéig semmi.; Ha nagyobb példányt szeretnél, évente tavasszal ültesd át – ha pedig maradjon kicsi, elég 2–3 évente.; Forrás: szobakertesz.hu – Elefántláb gondozása (részletes útmutató).|telente-nincs-tapoldat
"""



# ======================================================================
#  Tápoldat-profilok
#
#  A tápoldatozás nem „N naponta” dolog: függ attól, mivel tápoldatozunk,
#  milyen erősséggel, és hogy a növény éppen növekszik-e. Ezeket a
#  profilokat a felület és a naptár is használja (a hónap-ablakot is).
# ======================================================================
FERT_PROFIL = {
    "level": dict(
        fertKind="tapoldat",
        fertNpk="N-P-K 7-3-5 (univerzális)",
        fertDose="2 ml / 1 l víz",
        fertFrom=3, fertTo=9,
        fertNote="Mindig nedves földre, öntözés helyett – száraz földre soha."),
    "fuszer": dict(
        fertKind="level",
        fertNpk="N-P-K 7-3-5 (univerzális, hígabban)",
        fertDose="1 ml / 1 l víz (fél adag)",
        fertFrom=3, fertTo=9,
        fertNote="Fél adag elég: a túl sok nitrogén ízt ront és levéltetvet hoz."),
    "viragzo": dict(
        fertKind="viragzo",
        fertNpk="N-P-K 5-7-6 (P + K túlsúly)",
        fertDose="2 ml / 1 l víz",
        fertFrom=3, fertTo=9,
        fertNote="Bimbózás előtt kezdd, virágzás közben is adható; télen semmi."),
    "kaktusz": dict(
        fertKind="kaktusz",
        fertNpk="N-P-K 3-5-7 (kaktusz/pozsgás)",
        fertDose="1 ml / 1 l víz",
        fertFrom=4, fertTo=8,
        fertNote="Csak a növekedési időszakban, élő, nedves földre; ősszel állj le vele."),
    "gyumolcs": dict(
        fertKind="level",
        fertNpk="N-P-K 7-3-5 + magnézium",
        fertDose="2 ml / 1 l víz",
        fertFrom=3, fertTo=9,
        fertNote="Termésérés alatt káliumot is adjon (pl. paradicsomtápoldat)."),
    "komposzt": dict(
        fertKind="komposzt",
        fertNpk="",
        fertDose="2–3 marék / m²",
        fertFrom=4, fertTo=7,
        fertNote="Ültetés előtt a talajba dolgozva; istállótrágya csak éretten, ősszel."),
}

# melyik növény melyik profilt kapja (név szerint; a többi „level”)
PROFIL_SZERINT = {
    "fuszer": ["Bazsalikom", "Menta", "Rozmaring", "Levendula", "Petrezselyem", "Snidling",
               "Oregánó", "Kakukkfű", "Zsálya", "Koriander", "Citromfű", "Majoranna",
               "Babér", "Kapor", "Tárkony", "Lestyán"],
    "viragzo": ["Klívia", "Ciklámen", "Afrikai ibolya", "Hibiszkusz", "Orchidea", "Jácint",
                "Tulipán", "Nárcisz", "Hortenzia", "Kála", "Rózsa", "Begónia", "Kamélia",
                "Gardenia", "Lepkekezű virág", "Kália", "Amarillisz", "Freesia", "Gerbera"],
    "kaktusz": ["Kaktusz", "Pozsgás", "Aloe vera", "Aloe", "Echeveria", "Haworthia",
                "Sedum", "Kőrózsa", "Lepkekaktusz", "Fügekaktusz", "Sárkánygyümölcs",
                "Gyöngyfüzér", "Varjúköröm", "Kövirózsa", "Adenium", "Jade", "Pénzfa"],
    "gyumolcs": ["Citrusmag", "Füge", "Avokádó", "Mangófa", "Kivi", "Maracuja", "Ananász",
                 "Datolyapálma", "Kávécserje", "Banán", "Grándátalma", "Csillaggyümölcs"],
}

# ======================================================================
#  Kerti növények (zöldség, gyümölcs) – szezonhoz kötve
#  A kertben a „tápoldat” helyett komposzt / istállótrágya a szokás.
# ======================================================================
KERTI = [
    dict(name="Vöröshagyma", latin="Allium cepa",
         aliases=["hagyma", "dughagyma", "vöröshagyma", "kerti hagyma"],
         light="Napos", water=7, fert=30, seasonFrom=3, seasonTo=8,
         sow="március–április (magról vagy dughagymából)", harvest="július–augusztus",
         temp="10–25 °C", humidity="40–60%",
         soil="Laza, humuszos, jó vízelvezetésű kerti talaj",
         toxic="Mérgező macskára és kutyára (hagymafélék)",
         diseases=["Peronoszpóra – csapadékos, hűvös idő", "Hagymalégy – sárguló, lankadó levél",
                   "Rothadás – pangó víz a talajban"],
         pests=["Hagymalégy", "Tripsz"],
         tips=["Ne öntözd túl: a hagyma a pangó vizet nem szereti, könnyen rothad.",
               "A leveleit ne vágd le a betakarítás előtt – azok táplálják a hagymát.",
               "Ugyanarra az ágyásra 3–4 évig ne kerüljön újra hagymaféle."],
         fertDose="2–3 marék érett komposzt / m²",
         fertNote="Ültetés előtt a talajba dolgozva; műtrágya helyett komposzt."),
    dict(name="Kerti fokhagyma", latin="Allium sativum",
         aliases=["fokhagyma", "dughagymás fokhagyma", "őszi fokhagyma"],
         light="Napos", water=8, fert=45, seasonFrom=3, seasonTo=7,
         sow="október–november (gerezdenként) vagy kora tavasszal", harvest="június–július",
         temp="8–25 °C", humidity="40–60%",
         soil="Laza, tápdús, jó vízelvezetésű talaj",
         toxic="Mérgező macskára és kutyára (hagymafélék)",
         diseases=["Rozsda – narancssárga levélfoltok", "Baktériumos rothadás – pangó víz",
                   "Fehérpenész – túl sűrű vetés"],
         pests=["Hagymalégy"],
         tips=["A gerezdeket hegyes végükkel felfelé, 5 cm mélyre tedd.",
               "A virágzó szárat vágd le, hogy a hagymába menjen az erő.",
               "Akkor szedd fel, amikor a levelek alsó harmada már sárgul."],
         fertDose="2 marék érett komposzt / m²",
         fertNote="Csak a tavaszi növekedéskor; nyáron már ne kapjon nitrogént."),
    dict(name="Sárgarépa", latin="Daucus carota",
         aliases=["répa", "sárgarépa", "kerti répa"],
         light="Napos", water=5, fert=30, seasonFrom=3, seasonTo=10,
         sow="március–június (2–3 hetente, elhúzva)", harvest="július–október",
         temp="10–24 °C", humidity="50–70%",
         soil="Mély, laza, kőmentes talaj – a görcsös répa jele a köves föld",
         toxic="Nem mérgező",
         diseases=["Répa-légy – kis lyukak a gyökéren", "Sárguló levél – tápanyaghiány",
                   "Villás, görcsös gyökér – köves, tömör talaj"],
         pests=["Répa-légy", "Levéltetű"],
         tips=["Vékonyítsd ki 4–6 cm-re, különben apró répák lesznek.",
               "A magot ne takard be mélyen – 1 cm elég, és tartsd nedvesen a kelésig.",
               "Homokos, laza földben lesz egyenes és szép."],
         fertDose="2–3 marék érett komposzt / m²",
         fertNote="Friss istállótrágyát ne kapjon – villás gyökeret okoz."),
    dict(name="Cékla", latin="Beta vulgaris",
         aliases=["céklarépa", "vörös cékla", "béta"],
         light="Napos", water=5, fert=30, seasonFrom=4, seasonTo=10,
         sow="április–június", harvest="július–október",
         temp="10–25 °C", humidity="50–70%",
         soil="Laza, humuszos, enyhén meszes talaj",
         toxic="Nem mérgező",
         diseases=["Levélfoltosság – nedves lombozat", "Rothadó gyökér – pangó víz"],
         pests=["Levéltetű", "Földibolha"],
         tips=["A magot 2–3 cm mélyre vesd, a sort 25–30 cm-re hagyd.",
               "Ritkítsd 8–10 cm-re; a kitépett levelet meg is eheted.",
               "A levelét is használhatod – salátába kiváló."],
         fertDose="2–3 marék érett komposzt / m²",
         fertNote="Bórax (bór) hiányában fekete folt jelenhet meg a gyökéren."),
    dict(name="Retek", latin="Raphanus sativus",
         aliases=["hónapos retek", "piros retek", "jégcsap retek"],
         light="Napos", water=4, fert=30, seasonFrom=3, seasonTo=9,
         sow="március–augusztus (2 hetente)", harvest="április–október",
         temp="10–22 °C", humidity="50–70%",
         soil="Laza, homokos, tápdús talaj",
         toxic="Nem mérgező",
         diseases=["Csípős, üreges gyökér – vízhiány", "Földibolha – lyukas levelek"],
         pests=["Földibolha", "Répa-légy"],
         tips=["A legkönnyebb kerti növény: 25–30 nap alatt már szedhető.",
               "Ne hagyd kiszáradni – a vízhiánytól csípős és üreges lesz.",
               "Nyárra félárnyékba vesd, mert a melegben hamar virágzik."],
         fertDose="1–2 marék érett komposzt / m²",
         fertNote="Sokat nem kér – a friss trágya csúf, leveles növést okoz."),
    dict(name="Fejes saláta", latin="Lactuca sativa",
         aliases=["saláta", "fejes saláta", "jégsaláta"],
         light="Világos, szórt", water=4, fert=21, seasonFrom=3, seasonTo=9,
         sow="március–augusztus (folyamatosan)", harvest="május–október",
         temp="10–22 °C", humidity="60–70%",
         soil="Laza, tápdús, nyirkos talaj",
         toxic="Nem mérgező",
         diseases=["Csúcsrothadás – kalciumhiány, egyenetlen öntözés",
                   "Levéltetű a fej belsejében", "Nyálkás rothadás – túlöntözés"],
         pests=["Levéltetű", "Csigák"],
         tips=["Egyenletesen öntözd – a hirtelen szárazság után csúcsrothadás jön.",
               "Nyáron árnyékold, mert 25 °C felett magba szökik.",
               "Fejenként 2–3 hetente vess egy adagot, hogy folyamatos legyen a szedés."],
         fertDose="1–2 marék érett komposzt / m²",
         fertNote="Nitrogénből sokat kér, de friss trágyától nyálkás lesz."),
    dict(name="Paradicsom", latin="Solanum lycopersicum",
         aliases=["paradicsom", "kerti paradicsom", "koktélparadicsom"],
         light="Napos", water=3, fert=14, seasonFrom=4, seasonTo=10,
         sow="február–március (palántának), kiültetés májusban", harvest="július–október",
         temp="15–28 °C", humidity="50–65%",
         soil="Tápdús, laza, komposzttal javított talaj",
         toxic="Mérgező macskára és kutyára (levél, zöld termés)",
         diseases=["Fitoftóra – barna foltok, esős-hűvös idő", "Csúcsrothadás – kalciumhiány",
                   "Repedő termés – egyenetlen öntözés", "Lisztharmat – rossz szellőzés"],
         pests=["Levéltetű", "Takácsatka", "Bagolylepke"],
         tips=["Karózva neveld, és a hónaljhajtásokat törd le – így lesz termés.",
               "Leveleit alulról szedd, hogy szellőzzön és ne kapjon fitoftórát.",
               "Terméséréskor káliumos tápoldatot adjon (nem nitrogént)."],
         fertDose="3 marék komposzt / m² + 2 hetente káliumos tápoldat",
         fertilizing=14, fertKind="komposzt",
         fertNpk="magas kálium (pl. N-P-K 5-5-10)",
         fertFrom=5, fertTo=8,
         fertNote="Palántázás után 2 héttel kezdd; virágzástól káliumtúlsúly."),
    dict(name="Paprika", latin="Capsicum annuum",
         aliases=["kerti paprika", "csípős paprika", "kaliforniai paprika"],
         light="Napos", water=4, fert=21, seasonFrom=4, seasonTo=10,
         sow="február–március (palánta), kiültetés májusban", harvest="július–október",
         temp="18–28 °C", humidity="50–65%",
         soil="Tápdús, laza, meleg talaj",
         toxic="Nem mérgező (a szem (mag) enyhén irritáló)",
         diseases=["Csúcsrothadás – kalciumhiány", "Lombkorhadás – túlöntözés",
                   "Napégés – hirtelen tűző nap"],
         pests=["Levéltetű", "Takácsatka"],
         tips=["Meleget kér: 15 °C alatt megáll a növekedése.",
               "Kiültetés előtt szoktasd a naphoz és a kinti levegőhöz.",
               "A termést éretten szedd – a piros/sárga szín a jel."],
         fertDose="3 marék komposzt / m² + 3 hetente tápoldat",
         fertilizing=21,
         fertKind="komposzt",
         fertNpk="kiegyenlített, kevés nitrogén",
         fertFrom=5, fertTo=8,
         fertNote="Virágzás után kálium felé toljuk; nitrogént csak tavasszal."),
    dict(name="Uborka", latin="Cucumis sativus",
         aliases=["kerti uborka", "kígyóuborka", "befőttes uborka"],
         light="Napos", water=2, fert=14, seasonFrom=4, seasonTo=9,
         sow="április–május (vagy palántából májusban)", harvest="június–szeptember",
         temp="18–28 °C", humidity="60–80%",
         soil="Tápdús, laza, nyirkos talaj – sok komposzt",
         toxic="Nem mérgező",
         diseases=["Lisztharmat – fehér bevonat a levélen", "Peronoszpóra – sárguló foltok",
                   "Keserű termés – vízhiány vagy hőstressz"],
         pests=["Levéltetű", "Takácsatka"],
         tips=["Naponta-kétnaponta öntözd – a rendszertelen víz keserű termést ad.",
               "Kúszva vagy rácson is nevelhető; a rácson szebb, egyenes termés lesz.",
               "A termést fiatalon szedd, akkor folyamatosan hoz újat."],
         fertDose="3 marék komposzt / m² + 2 hetente tápoldat",
         fertilizing=14,
         fertKind="komposzt",
         fertNpk="N-P-K 7-3-5 (sok vizet és nitrogént kér)",
         fertFrom=5, fertTo=8,
         fertNote="Öntözéssel együtt, mindig nedves földre."),
    dict(name="Burgonya", latin="Solanum tuberosum",
         aliases=["krumpli", "kerti burgonya", "korai burgonya"],
         light="Napos", water=5, fert=30, seasonFrom=3, seasonTo=9,
         sow="március–április (csíráztatott gumóval)", harvest="július–szeptember",
         temp="12–25 °C", humidity="50–70%",
         soil="Laza, humuszos, mély talaj",
         toxic="Mérgező macskára és kutyára (zöld gumó, levél)",
         diseases=["Burgonyabogár – lerágott levél", "Fitoftóra – barna foltok, esős idő",
                   "Zöld gumó – fény éri a gumókat"],
         pests=["Burgonyabogár", "Levéltetű"],
         tips=["Töltögesd fel a tövét – a fényt kapó gumó megzöldül és mérgező lesz.",
               "A gumót csak a virágzás után kezdd kiásni, akkor nagyobb.",
               "Ugyanoda 3 évig ne kerüljön – a talajban maradó betegségek miatt."],
         fertDose="3–4 marék érett istállótrágya / m² ősszel",
         fertKind="istallo",
         fertNpk="",
         fertFrom=9, fertTo=10,
         fertNote="Istállótrágyát ősszel a talajba; tavasszal komposzt is elég."),
    dict(name="Eper", latin="Fragaria × ananassa",
         aliases=["kerti eper", "szamóca", "eperpalánta"],
         light="Napos", water=4, fert=21, seasonFrom=3, seasonTo=10,
         sow="augusztus–szeptember (tővel) vagy tavasszal", harvest="május–június",
         temp="12–26 °C", humidity="60–70%",
         soil="Laza, tápdús, enyhén savanyú talaj",
         toxic="Nem mérgező",
         diseases=["Szürkepenész – nedves, meleg idő", "Levélfoltosság",
                   "Gyökérrothadás – pangó víz"],
         pests=["Levéltetű", "Csigák", "Madarak"],
         tips=["A töveket 25–30 cm-re ültesd, a szívlevél a talajszinten legyen.",
               "Szalmával takard a tövét – így a termés tiszta marad.",
               "Szedés után vágd vissza az indákat, és ritkítsd a töveket."],
         fertDose="2 marék komposzt / m² tavasszal",
         fertNote="Terméséréskor már ne kapjon nitrogént – az a levelet növeli."),
    dict(name="Zöldborsó", latin="Pisum sativum",
         aliases=["borsó", "zöldborsó", "kifejtő borsó"],
         light="Napos", water=4, fert=45, seasonFrom=3, seasonTo=8,
         sow="március–április (minél előbb)", harvest="június–július",
         temp="8–22 °C", humidity="50–70%",
         soil="Laza, meszes, jó vízelvezetésű talaj",
         toxic="Nem mérgező",
         diseases=["Lisztharmat – nyár végi fehér bevonat", "Borsó-levéltetű",
                   "Gyökérrothadás – pangó víz"],
         pests=["Borsó-levéltetű", "Borsómoly"],
         tips=["A borsó maga köti a nitrogént – utána zöldséget érdemes utána vetni.",
               "Kapaszkodó ágat adj neki, vagy vessük sűrűbben.",
               "A hüvelyt fiatalon szedd, akkor édes."],
         fertDose="1 marék komposzt / m²",
         fertKind="komposzt",
         fertNote="Nitrogén-trágyát ne kapjon: maga is köti a levegőből."),
]


def fert_profil_neve(p):
    """Melyik tápoldat-profilt kapja a növény (név és aliasok alapján)."""
    nevek = [p.get("name", "")] + list(p.get("aliases") or [])
    for profil, lista in PROFIL_SZERINT.items():
        for n in nevek:
            for kulcs in lista:
                if n and (kulcs.lower() in n.lower()):
                    return profil
    return "level"


def fert_mezok(p):
    """A profil mezőit ráteszi a bejegyzésre (ha még nincs saját értéke)."""
    profil = FERT_PROFIL.get(fert_profil_neve(p), FERT_PROFIL["level"])
    for kulcs, ertek in profil.items():
        p.setdefault(kulcs, ertek)
    return p


def kerti_hozzaad(plants):
    """A kerti növények bejegyzései (szezonhoz kötve)."""
    for alap in KERTI:
        p = {
            "id": "", "name": alap["name"], "latin": alap["latin"],
            "aliases": alap.get("aliases", []),
            "difficulty": "Könnyű",
            "light": alap.get("light", "Napos"),
            "water": alap.get("water", 5),
            "waterWinter": 0,
            "fert": alap.get("fertilizing", alap.get("fert", 30)),
            "mist": 0,
            "repot": 0,
            "humidity": alap.get("humidity", "50–70%"),
            "temp": alap.get("temp", "10–26 °C"),
            "soil": alap.get("soil", "Laza, tápdús kerti talaj"),
            "toxic": alap.get("toxic", "Nem mérgező"),
            "diseases": alap.get("diseases", []),
            "pests": alap.get("pests", []),
            "tips": alap.get("tips", []),
            "mistWater": "nem",
            "fertWinter": 0,
            # kerti szezon
            "garden": True,
            "seasonFrom": alap.get("seasonFrom", 4),
            "seasonTo": alap.get("seasonTo", 10),
            "sow": alap.get("sow", ""),
            "harvest": alap.get("harvest", ""),
            # trágyázás
            "fertKind": alap.get("fertKind", "komposzt"),
            "fertNpk": alap.get("fertNpk", ""),
            "fertDose": alap.get("fertDose", "2–3 marék érett komposzt / m²"),
            "fertFrom": alap.get("fertFrom", 4),
            "fertTo": alap.get("fertTo", 7),
            "fertNote": alap.get("fertNote", "Ültetés előtt a talajba dolgozva."),
        }
        p["id"] = slug(p["latin"])
        plants.append(p)
    return plants


def slug(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "noveny"


def split_list(value: str):
    return [part.strip() for part in value.split(";") if part.strip()]


def build():
    plants = []
    seen = set()
    for raw in DATA.strip().splitlines():
        row = [c.strip() for c in raw.split("|")]
        flags = []
        if len(row) == 18:
            flags = split_list(row[17])
            row = row[:17]
        if len(row) != 17:
            raise SystemExit("Hibás sor (%d mező): %s" % (len(row), row[0] if row else "?"))
        p = dict(zip(FIELDS, row))
        p["water"] = int(p["water"])
        p["waterWinter"] = int(p["waterWinter"])
        p["fert"] = int(p["fert"])
        p["mist"] = int(p["mist"])
        p["repot"] = int(p["repot"])
        p["aliases"] = split_list(p["aliases"])
        p["diseases"] = split_list(p["diseases"])
        p["pests"] = split_list(p["pests"])
        p["tips"] = split_list(p["tips"])
        if "telente-nincs-tapoldat" in flags:
            p["fertWinter"] = 0
        if "telente-huvos-hely" in flags:
            p["coldWinter"] = True
        base = slug(p["latin"])
        pid, i = base, 2
        while pid in seen:
            pid = "%s-%d" % (base, i)
            i += 1
        seen.add(pid)
        p["id"] = pid
        ordered = {"id": p["id"]}
        ordered.update({k: p[k] for k in FIELDS})
        ordered["mistWater"] = mist_water(p)
        fert_mezok(ordered)
        for flag_field in ("fertWinter", "coldWinter"):
            if flag_field in p:
                ordered[flag_field] = p[flag_field]
        plants.append(ordered)

    # kerti növények (zöldség, gyümölcs) a lista végére
    kerti_hozzaad(plants)

    db = {
        "format": "florum-plants-db",
        "app": "Florum 1.33.2",
        "file": "plants-db.json",
        "version": "2026.10.9",
        "updated": "2026-10-25",
        "count": len(plants),
        "source": "Florum beépített adatbázis",
        "license": "Saját összeállítás, szabadon használható és bővíthető.",
        "plants": plants,
    }
    return db


def main(argv=None):
    """--html ÚTVONAL: hova ágyazza be az adatbázist (több példány is lehet).

    SZÜKSÉGES, mert a `kinezet-egyesites.sh` a `minden_html-original/`
    példányból generál – ott is frissíteni kell a beágyazott adatbázist,
    különben a generálás visszateszi a régit.
    """
    argv = list(sys.argv[1:] if argv is None else argv)
    cel = []
    for i, arg in enumerate(argv):
        if arg == "--html" and i + 1 < len(argv):
            cel.append(argv[i + 1])
        elif arg.startswith("--html="):
            cel.append(arg.split("=", 1)[1])
    here = os.path.dirname(os.path.abspath(__file__))
    db = build()
    out = os.path.join(here, "plants-db.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(db, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("plants-db.json: %d növény, %.1f kB" % (db["count"], os.path.getsize(out) / 1024.0))

    # HTML-be ágyazott tartalék (a saját példány + a --html-lel megadottak)
    utak = [os.path.join(here, "florum.html")] + cel
    for html_path in utak:
        if not os.path.exists(html_path):
            continue
        html = open(html_path, encoding="utf-8").read()
        blob = json.dumps(db, ensure_ascii=False, separators=(",", ":"))
        start = '<script id="bundledDb" type="application/json">'
        end = "</script>"
        block = start + blob + end
        if start in html:
            i = html.index(start)
            j = html.index(end, i) + len(end)
            html = html[:i] + block + html[j:]
        else:
            html = html.replace("</body>", block + "\n</body>")
        open(html_path, "w", encoding="utf-8").write(html)
        print("%s: adatbázis beágyazva (%.1f kB)" % (html_path, os.path.getsize(html_path) / 1024.0))


if __name__ == "__main__":
    main()
