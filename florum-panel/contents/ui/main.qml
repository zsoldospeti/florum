// Florum naptár – Plasma 6 panel widget
// A Florum futó szerverétől kéri el a következő teendőket (alap: 127.0.0.1:8777).
// Nem kell hozzá Akonadi, PIM-plugin, Python-modul vagy .ics-beállítás.

import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.kirigami as Kirigami

PlasmoidItem {
    id: root

    // A Florum a 8777-es porton figyel; ha az foglalt, 8778, 8779… jön.
    // Ezért a widget sorban végigpróbálja őket, a beállított cím pedig elsőbbséget kap.
    readonly property var jeloltek: {
        var lista = [];
        if (plasmoid.configuration.panelUrl.length > 0) {
            lista.push(plasmoid.configuration.panelUrl);
        }
        for (var i = 0; i < 6; ++i) {
            lista.push("http://127.0.0.1:" + (8777 + i) + "/api/panel.json");
        }
        return lista;
    }
    property int probaIndex: 0
    property string aktivUrl: ""

    // Monokróm ikon: a panel szövegszínéhez igazodik (sötét panel → világos,
    // világos panel → sötét). A két SVG a csomagban van, nem kell témába telepíteni.
    // FONTOS: hsvValue a színezet (hue), nem a világosság – a hslLightness a jó.
    readonly property bool vilagosPanel: Kirigami.Theme.textColor.hslLightness > 0.5
    readonly property url ikonForras: vilagosPanel
                                      ? Qt.resolvedUrl("../icons/florum-vilagos.svg")
                                      : Qt.resolvedUrl("../icons/florum-sotet.svg")
    readonly property int maxRows: plasmoid.configuration.maxRows > 0 ? plasmoid.configuration.maxRows : 5
    readonly property int frissitesPerc: plasmoid.configuration.refreshMinutes > 0 ? plasmoid.configuration.refreshMinutes : 2

    property var sorok: []
    property int lejart: 0
    property int mai: 0
    property string hiba: ""
    property bool voltAdat: false

    function napSzoveg(r) {
        if (r.late) {
            var n = -r.daysLeft;
            return n === 1 ? "1 napja lejárt" : n + " napja lejárt";
        }
        if (r.daysLeft === 0) {
            return "ma";
        }
        if (r.daysLeft === 1) {
            return "holnap";
        }
        return r.daysLeft + " nap múlva";
    }

    function rovidDatum(iso) {
        var t = String(iso || "").slice(0, 10);        // "2026-10-25T08:00" → "2026-10-25"
        var p = t.split("-");
        if (p.length !== 3) {
            return iso;
        }
        return p[1] + ". " + p[2] + ".";
    }

    // A megnyitáshoz a futó szerver címét használjuk (a betöltött cím portját).
    readonly property string alapCim: {
        if (root.aktivUrl.length > 0) {
            return String(root.aktivUrl).replace("/api/panel.json", "");
        }
        if (plasmoid.configuration.panelUrl.length > 0) {
            return String(plasmoid.configuration.panelUrl).replace("/api/panel.json", "");
        }
        return "http://127.0.0.1:8777";
    }

    // A Florum megnyitása (a háttérszerver indítja a KDE-ablakot / böngészőt).
    function megnyit() {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== XMLHttpRequest.DONE) {
                return;
            }
            if (xhr.status !== 200) {
                // ha a végpont nem elérhető, nyissuk a böngészőt
                Qt.openUrlExternally(root.alapCim + "/");
            }
        };
        xhr.open("GET", root.alapCim + "/api/megnyitas");
        xhr.timeout = 3000;
        xhr.send();
    }

    function betolt() {
        root.probaIndex = 0;
        root.probal(root.jeloltek[0]);
    }

    function probal(cim) {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== XMLHttpRequest.DONE) {
                return;
            }
            if (xhr.status === 200) {
                try {
                    var d = JSON.parse(xhr.responseText);
                    root.sorok = d.rows || [];
                    root.lejart = d.lateCount || 0;
                    root.mai = d.todayCount || 0;
                    root.aktivUrl = cim;
                    root.hiba = "";
                    root.voltAdat = true;
                } catch (e) {
                    root.hiba = "Hibás válasz érkezett a Florumtól.";
                }
                return;
            }
            // következő port
            if (root.probaIndex + 1 < root.jeloltek.length) {
                root.probaIndex += 1;
                root.probal(root.jeloltek[root.probaIndex]);
                return;
            }
            root.voltAdat = false;
            root.sorok = [];
            root.hiba = "A Florum nem fut (8777–8782). Indítsd el a Florumot, vagy: bash florum-szolgaltatas.sh indit";
        };
        xhr.open("GET", cim);
        xhr.timeout = 2500;
        xhr.send();
    }

    Component.onCompleted: betolt()

    Timer {
        interval: Math.max(1, root.frissitesPerc) * 60000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.betolt()
    }

    // ha nem érhető el a Florum, 15 másodpercenként újrapróbálja
    Timer {
        interval: 15000
        running: root.hiba.length > 0
        repeat: true
        onTriggered: root.betolt()
    }

    toolTipMainText: "Florum – növénygondozás"
    toolTipSubText: {
        if (root.hiba.length > 0) {
            return root.hiba;
        }
        if (!root.voltAdat) {
            return "Betöltés…";
        }
        if (root.sorok.length === 0) {
            return "Nincs esedékes teendő.";
        }
        var t = [];
        if (root.lejart > 0) {
            t.push(root.lejart + " lejárt");
        }
        if (root.mai > 0) {
            t.push(root.mai + " mai");
        }
        return (t.length > 0 ? t.join(" · ") + " · " : "") + root.sorok.length + " tétel a következő napokra";
    }

    // ---------------------------------------------------------------- panel (kompakt)
    compactRepresentation: MouseArea {
        id: compact

        Layout.minimumWidth: Kirigami.Units.iconSizes.smallMedium + (szam.visible ? szam.implicitWidth + Kirigami.Units.smallSpacing : 0)
        Layout.preferredWidth: Layout.minimumWidth
        Layout.maximumWidth: Layout.minimumWidth * 1.6
        Layout.minimumHeight: Kirigami.Units.iconSizes.smallMedium
        Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium

        hoverEnabled: true
        onClicked: {
            // Beállítás: kattintásra a Florum nyíljon meg (nem a lista)
            if (plasmoid.configuration.openOnClick) {
                root.megnyit();
            } else {
                root.expanded = !root.expanded;
            }
        }
        // középső gomb: mindig megnyitás
        onPressed: function (mouse) {
            if (mouse.button === Qt.MiddleButton) {
                root.megnyit();
            }
        }

        RowLayout {
            anchors.centerIn: parent
            spacing: Kirigami.Units.smallSpacing

            // A panel-ikon (Layout.preferred*, mert az implicit* csak olvasható)
            Image {
                id: panelIkon
                source: root.ikonForras
                sourceSize.width: Kirigami.Units.iconSizes.smallMedium
                sourceSize.height: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                fillMode: Image.PreserveAspectFit
                smooth: true
                visible: root.hiba.length === 0
                // lejárt teendőnél halványabb – a szám mellette viszi a hangsúlyt
                opacity: root.lejart > 0 ? 0.8 : 1
            }

            // hiba esetén (nem fut a Florum) figyelmeztető jel
            PlasmaComponents3.Label {
                visible: root.hiba.length > 0
                text: "⚠"
                font.pixelSize: Kirigami.Units.iconSizes.smallMedium
            }

            PlasmaComponents3.Label {
                id: szam
                visible: root.lejart + root.mai > 0
                text: (root.lejart > 0 ? String(root.lejart) : "")
                      + (root.lejart > 0 && root.mai > 0 ? "+" : "")
                      + (root.mai > 0 ? String(root.mai) : "")
                color: root.lejart > 0 ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
                font.bold: true
            }
        }
    }

    // ---------------------------------------------------------------- teljes nézet
    fullRepresentation: Item {
        Layout.preferredWidth: Kirigami.Units.gridUnit * 20
        Layout.preferredHeight: Kirigami.Units.gridUnit * 17

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Kirigami.Units.smallSpacing
            spacing: Kirigami.Units.smallSpacing

            RowLayout {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Image {
                    source: root.ikonForras
                    sourceSize.width: Kirigami.Units.iconSizes.small
                    sourceSize.height: Kirigami.Units.iconSizes.small
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    fillMode: Image.PreserveAspectFit
                    opacity: 0.85
                }

                PlasmaComponents3.Label {
                    Layout.fillWidth: true
                    text: "Florum – teendők"
                    font.bold: true
                }

                PlasmaComponents3.Label {
                    visible: root.voltAdat
                    text: root.lejart + root.mai > 0 ? (root.lejart + root.mai) + " esedékes" : "minden rendben"
                    opacity: 0.7
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                }

                PlasmaComponents3.Button {
                    icon.name: "view-refresh"
                    text: "Frissítés"
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    onClicked: root.betolt()
                }

                PlasmaComponents3.Button {
                    icon.name: "window-new"
                    text: "Megnyitás"
                    font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                    onClicked: root.megnyit()
                }
            }

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: root.hiba.length > 0
                text: root.hiba + "\n\nA lenti gomb el is indítja:"
                color: Kirigami.Theme.negativeTextColor
                wrapMode: Text.WordWrap
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            }

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: root.voltAdat && root.hiba.length === 0 && root.sorok.length === 0
                text: "Nincs esedékes teendő a következő napokban 🎉"
                wrapMode: Text.WordWrap
            }

            ListView {
                id: lista
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: root.sorok.length > 0
                clip: true
                spacing: Kirigami.Units.smallSpacing
                model: root.sorok.slice(0, root.maxRows)

                delegate: RowLayout {
                    id: sor
                    width: ListView.view ? ListView.view.width : 0
                    spacing: Kirigami.Units.smallSpacing

                    PlasmaComponents3.Label {
                        text: modelData.icon
                        font.pixelSize: Kirigami.Theme.defaultFont.pixelSize * 1.15
                    }

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0

                        PlasmaComponents3.Label {
                            Layout.fillWidth: true
                            text: modelData.plant + " · " + modelData.label
                            elide: Text.ElideRight
                            color: modelData.late ? Kirigami.Theme.negativeTextColor : Kirigami.Theme.textColor
                            font.bold: modelData.today || modelData.late
                        }

                        PlasmaComponents3.Label {
                            Layout.fillWidth: true
                            text: root.napSzoveg(modelData)
                                  + (modelData.hint ? " · " + modelData.hint : "")
                                  + (modelData.room ? " · " + modelData.room : "")
                                  + " · " + root.rovidDatum(modelData.due)
                            opacity: 0.7
                            font.pixelSize: Kirigami.Theme.smallFont.pixelSize
                            elide: Text.ElideRight
                        }
                    }
                }
            }

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: root.sorok.length > root.maxRows
                text: "… és további " + (root.sorok.length - root.maxRows) + " tétel a Florumban"
                opacity: 0.7
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            }

            PlasmaComponents3.Button {
                Layout.fillWidth: true
                icon.name: "window-new"
                text: "Florum megnyitása"
                onClicked: root.megnyit()
            }

            PlasmaComponents3.Label {
                Layout.fillWidth: true
                visible: root.aktivUrl.length > 0
                text: (root.voltAdat ? "Forrás: " : "") + root.aktivUrl
                opacity: 0.45
                elide: Text.ElideRight
                font.pixelSize: Kirigami.Theme.smallFont.pixelSize
            }
        }
    }
}
