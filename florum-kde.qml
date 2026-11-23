// ==============================================================
//  FLORUM 1.33.4  ·  KDE-ablak (QML)
//  Fájl:    florum-kde.qml
//
//  A Florum felülete natív KDE-ablakban: toolbár, KDE-s kinézet,
//  a WebEngineView-ban a megszokott florum.html (ugyanaz a program,
//  ugyanazok az adatok – nem kell semmit újraírni).
//
//  A Qt oldaláról érkező változók (florum-kde.py):
//    backendUrl, appVersion, dataDir, iconPath
// ==============================================================

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtWebEngine

ApplicationWindow {
    id: win
    visible: true
    width: 1200
    height: 840
    minimumWidth: 720
    minimumHeight: 520
    title: "🌿 Florum " + appVersion + " – növénygondozó"
    color: "#0f1a15"

    // ---- eszköztár (vissza / újratöltés / fotók / naptár)
    header: ToolBar {
        id: bar
        background: Rectangle { color: "#152a20" }
        RowLayout {
            anchors.fill: parent
            spacing: 4

            ToolButton {
                text: "←"
                enabled: view.canGoBack
                onClicked: view.goBack()
                ToolTip.visible: hovered
                ToolTip.text: "Vissza"
            }
            ToolButton {
                text: "⟳"
                onClicked: view.reload()
                ToolTip.visible: hovered
                ToolTip.text: "Újratöltés"
            }
            ToolButton {
                text: "🏠"
                onClicked: view.url = backendUrl
                ToolTip.visible: hovered
                ToolTip.text: "Kezdőlap"
            }
            ToolButton {
                text: "📷"
                onClicked: view.url = backendUrl + "foto"
                ToolTip.visible: hovered
                ToolTip.text: "Fotók – nagy nézet (feh / chafa / böngésző)"
            }
            ToolButton {
                text: "📅"
                onClicked: view.url = backendUrl + "api/calendar.ics"
                ToolTip.visible: hovered
                ToolTip.text: "Naptárfájl (.ics) letöltése"
            }

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 8
                elide: Text.ElideRight
                text: view.loading ? "Betöltés…" : (view.title || "Florum")
                color: "#cfe6d8"
                font.pixelSize: 13
            }

            Label {
                text: "🔌 " + backendUrl.replace("http://", "").replace(/\/$/, "")
                color: "#7fae93"
                font.pixelSize: 11
                visible: win.width > 900
            }
        }
    }

    // ---- a Florum felülete
    WebEngineView {
        id: view
        anchors.fill: parent
        url: backendUrl
        backgroundColor: "#0f1a15"

        // a belső linkek ne nyissanak új ablakot, hanem itt töltődjenek be
        onNewWindowRequested: function(request) {
            view.url = request.requestedUrl
            request.accepted = true
        }

        onLoadingChanged: function(loadRequest) {
            if (loadRequest.status === WebEngineView.LoadFailedStatus) {
                hibasav.visible = true
            } else if (loadRequest.status === WebEngineView.LoadSucceededStatus) {
                hibasav.visible = false
            }
        }
    }

    // ---- hiba (pl. nem fut a háttérszerver)
    Rectangle {
        id: hibasav
        visible: false
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: 46
        color: "#4a2320"
        RowLayout {
            anchors.fill: parent
            anchors.margins: 8
            Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: "#ffd9d2"
                font.pixelSize: 12
                text: "Nem érhető el a Florum szervere. Indítsd el: " +
                      "python3 florum.py --szerver   (adat: " + dataDir + ")"
            }
            Button {
                text: "Újra"
                onClicked: { hibasav.visible = false; view.reload() }
            }
        }
    }

    // ---- F5 / Ctrl+R / Alt+←  (mint egy rendes KDE-programban)
    Shortcut { sequence: "F5"; onActivated: view.reload() }
    Shortcut { sequence: "Ctrl+R"; onActivated: view.reload() }
    Shortcut { sequence: "Ctrl+Q"; onActivated: Qt.quit() }
    Shortcut {
        sequence: "Alt+Left"
        enabled: view.canGoBack
        onActivated: view.goBack()
    }

    Component.onCompleted: console.log("Florum KDE-ablak kész: " + backendUrl)
}
