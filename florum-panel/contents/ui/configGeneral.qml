// Florum naptár – beállítások
import QtQuick
import QtQuick.Controls as QQC
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {

    property alias cfg_panelUrl: urlMezo.text
    property alias cfg_maxRows: sorokSpi.value
    property alias cfg_refreshMinutes: percSpi.value

    QQC.TextField {
        id: urlMezo
        Kirigami.FormData.label: "Florum címe:"
        placeholderText: "http://127.0.0.1:8777/api/panel.json"
    }
    QQC.Label {
        text: "Üresen hagyva az alapértéket használja. Csak akkor kell kitölteni, ha a Florum más porton fut."
        font.pixelSize: Kirigami.Theme.smallFont.pixelSize
        opacity: 0.75
        wrapMode: Text.WordWrap
        Layout.fillWidth: true
        Layout.maximumWidth: Kirigami.Units.gridUnit * 22
    }

    QQC.SpinBox {
        id: sorokSpi
        Kirigami.FormData.label: "Sorok száma:"
        from: 1
        to: 20
    }

    QQC.CheckBox {
        id: kattSpi
        text: "Kattintásra a Florum nyíljon meg (ne a lista)"
        Kirigami.FormData.label: "Kattintás:"
        property alias cfg_openOnClick: kattSpi.checked
    }

    QQC.SpinBox {
        id: percSpi
        Kirigami.FormData.label: "Frissítés (perc):"
        from: 1
        to: 120
    }
}
