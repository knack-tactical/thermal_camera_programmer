import sys, os
from datetime import datetime

from PyQt5 import QtCore, QtWidgets, QtSerialPort, QtGui
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QAction,
    QStatusBar,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QActionGroup,
    QComboBox,
    QLabel,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtSerialPort import QSerialPortInfo

import HM_TM5X

basedir = os.path.dirname(__file__)

class MenuSettings(QMainWindow):
    portName = pyqtSignal(str)
    timestampSig = pyqtSignal(bool)

    def __init__(self, parent, menu):
        super().__init__(parent)

        self.port = ""
        portMenu = menu.addMenu("Port Select")
        portGroup = QActionGroup(parent)
        portGroup.setExclusive(True)
        info_list = QSerialPortInfo()
        serial_list = info_list.availablePorts()
        serial_ports = [port.portName() for port in serial_list]
        serial_ports.sort()
        for port in serial_ports:
            txt = port
            button_action = QAction(txt, self)
            button_action.setCheckable(True)
            if port == "COM1":
                button_action.setChecked(True)
            button_action.triggered.connect(
                lambda checked, txt=txt: self.chooseCOMPortClick(txt)
            )
            portGroup.addAction(button_action)
            portMenu.addAction(button_action)

        # Settings Menu
        # settingsMenu = menu.addMenu("Settings")
        # sGroup = QActionGroup(parent)
        # sGroup.setExclusive(False)
        # timestampAction = QAction("Show Timestamp")
        # timestampAction.setCheckable(True)
        # timestampAction.setChecked(False)
        # timestampAction.triggered.connect(lambda checked: self.timestampClick(checked))
        # sGroup.addAction(timestampAction)
        # settingsMenu.addAction(timestampAction)

    def chooseCOMPortClick(self, port):
        self.port = port
        self.portName.emit(port)

    def timestampClick(self, checked):
        self.timestampSig.emit(checked)

    def closeEvent(self, event):
        self.close()


class LoginPopup(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setAttribute(QtCore.Qt.WA_StyledBackground)
        self.setAutoFillBackground(True)
        self.setStyleSheet("""
            LoginPopup {
                background: rgba(64, 64, 64, 64);
            }
            QWidget#container {
                border: 2px solid darkGray;
                border-radius: 4px;
                background: rgb(64, 64, 64);
            }
            QWidget#container > QLabel {
                color: white;
            }
            QPushButton#close {
                color: white;
                font-weight: bold;
                background: none;
                border: 1px solid gray;
            }
        """)

        fullLayout = QtWidgets.QVBoxLayout(self)

        self.container = QtWidgets.QWidget(
            autoFillBackground=True, objectName="container"
        )
        fullLayout.addWidget(self.container, alignment=QtCore.Qt.AlignCenter)
        self.container.setSizePolicy(
            QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Maximum
        )

        buttonSize = self.fontMetrics().height()
        self.closeButton = QtWidgets.QPushButton(
            "×", self.container, objectName="close"
        )
        self.closeButton.setFixedSize(buttonSize, buttonSize)
        self.closeButton.clicked.connect(self.reject)

        layout = QtWidgets.QVBoxLayout(self.container)
        layout.setContentsMargins(
            buttonSize * 2, buttonSize, buttonSize * 2, buttonSize
        )

        title = QtWidgets.QLabel(
            "Are you certain you'd like to factory reset your device?\nAll saved settings will be lost.",
            objectName="title",
            alignment=QtCore.Qt.AlignCenter,
        )
        layout.addWidget(title)

        buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Yes | QtWidgets.QDialogButtonBox.Cancel
        )
        layout.addWidget(buttonBox, alignment=Qt.AlignCenter)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.okButton = buttonBox.button(buttonBox.Ok)

        parent.installEventFilter(self)

        self.loop = QtCore.QEventLoop(self)

    def accept(self):
        self.loop.exit(True)

    def reject(self):
        self.loop.exit(False)

    def close(self):
        self.loop.quit()

    def showEvent(self, event):
        self.setGeometry(self.parent().rect())

    def resizeEvent(self, event):
        r = self.closeButton.rect()
        r.moveTopRight(self.container.rect().topRight() + QtCore.QPoint(-5, 5))
        self.closeButton.setGeometry(r)

    def eventFilter(self, source, event):
        if event.type() == event.Resize:
            self.setGeometry(source.rect())
        return super().eventFilter(source, event)

    def exec_(self):
        self.show()
        self.raise_()
        res = self.loop.exec_()
        self.hide()
        return res


# noinspection PyArgumentList,PyUnresolvedReferences
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.lastFunctionSent = None
        portname = "None"
        self.incoming_bytes = b''

        self.setStatusBar(QStatusBar(self))

        menu = self.menuBar()
        self.portFinder = MenuSettings(self, menu)
        self.portFinder.portName.connect(self.chooseCOMPort)
        self.portFinder.timestampSig.connect(self.toggleTimestamp)
        self.showTimestamp = False

        self.setWindowTitle("HM-TM5X Thermal Camera Programmer")

        self.message_le = QLineEdit()
        self.send_btn = QPushButton(text="Send", clicked=self.send)
        self.message_le.returnPressed.connect(self.send_btn.click)

        self.output_te = QTextEdit(readOnly=True)
        self.connectPortButton = QPushButton(
            text="Connect to port", checkable=True, toggled=self.on_toggled
        )
        self.clearButton = QPushButton(text="Clear", clicked=self.clearOutput)
        self.testButton = QPushButton(text="Get Model Name", clicked=self.readModel)

        self.palettes = QComboBox()
        self.palettes.addItems(
            [
                "White Hot",
                "Black Hot",
                "Fusion 1",
                "Rainbow",
                "Fusion 2",
                "Iron Red 1",
                "Iron Red 2",
                "Dark Brown",
                "Color 1",
                "Color 2",
                "Ice Fire",
                "Rain",
                "Green Hot",
                "Red Hot",
                "Deep Blue",
            ]
        )
        self.palettes.setCurrentIndex(0)
        self.writePaletteButton = QPushButton(
            text="Set Palette", clicked=self.writePalette
        )
        self.readPaletteButton = QPushButton(
            text="Read Current Palette", clicked=self.readPalette
        )

        self.brightnessLE = QLineEdit()
        self.brightnessButton = QPushButton(
            text="Set Brightness (0-100)", clicked=self.writeBrightness
        )
        self.brightnessLE.returnPressed.connect(self.brightnessButton.click)
        self.contrastLE = QLineEdit()
        self.contrastButton = QPushButton(
            text="Set Contrast (0-100)", clicked=self.writeContrast
        )
        self.contrastLE.returnPressed.connect(self.contrastButton.click)

        self.mirrorModes = QComboBox()
        self.mirrorModes.addItems(["None", "Central", "Left/Right", "Up/Down"])
        self.mirrorModes.setCurrentIndex(0)
        self.writeMirrorModeButton = QPushButton(
            text="Set Mirror Mode", clicked=self.writeMirrorMode
        )

        self.saveSettingsButton = QPushButton(
            text="Save Current Device Settings to Device", clicked=self.saveSettings
        )

        self.factoryResetButton = QPushButton(text="Factory Reset Device", clicked=self.showDialog)

        lay = QVBoxLayout(self)
        hlay = QHBoxLayout()
        hlay.addWidget(self.connectPortButton)
        hlay.addWidget(self.message_le)
        hlay.addWidget(self.send_btn)
        lay.addLayout(hlay)
        # lay.addWidget(self.output_te)
        # lay.addWidget(self.clearButton)
        lay.addWidget(QFrame(frameShape=QFrame.HLine))
        # lay.addWidget(self.testButton)
        hlay2 = QHBoxLayout()
        hlay2.addWidget(QLabel("Pallete:"))
        hlay2.addWidget(self.palettes)
        hlay2.addWidget(self.writePaletteButton)
        # hlay2.addWidget(self.readPaletteButton)
        lay.addLayout(hlay2)
        lay.addWidget(QFrame(frameShape=QFrame.HLine))

        hlay3 = QHBoxLayout()
        hlay3.addWidget(QLabel("Brightness: "))
        hlay3.addWidget(self.brightnessLE)
        hlay3.addWidget(self.brightnessButton)
        lay.addLayout(hlay3)

        hlay4 = QHBoxLayout()
        hlay4.addWidget(QLabel("Contrast: "))
        hlay4.addWidget(self.contrastLE)
        hlay4.addWidget(self.contrastButton)
        lay.addLayout(hlay4)
        lay.addWidget(QFrame(frameShape=QFrame.HLine))

        hlay5 = QHBoxLayout()
        hlay5.addWidget(QLabel("Mirror Mode: "))
        hlay5.addWidget(self.mirrorModes)
        hlay5.addWidget(self.writeMirrorModeButton)
        lay.addLayout(hlay5)
        lay.addWidget(QFrame(frameShape=QFrame.HLine))

        lay.addWidget(self.saveSettingsButton)
        lay.addWidget(QFrame(frameShape=QFrame.HLine))
        lay.addWidget(self.factoryResetButton)

        widget = QWidget()
        widget.setLayout(lay)
        self.setCentralWidget(widget)

        self.serial = QtSerialPort.QSerialPort(
            portname,
            baudRate=QtSerialPort.QSerialPort.Baud115200,
            readyRead=self.receive,
        )

    def receive(self):
        while self.serial.bytesAvailable():
            b = self.serial.readAll().data()
            self.incoming_bytes += b
            if len(self.incoming_bytes) > 20:
                self.incoming_bytes = b''

        if b[-1] == 255:
            text = self.incoming_bytes
            # text = text.rstrip("\r\n")
            if len(text) >= 20 and text[:2] == "0x":
                data = HM_TM5X.handleReply(text, self.lastFunctionSent)
                if data[:2] == "-1":
                    self.updateText(data[3:], False)
                else:
                    self.updateText(data, False)
            else:
                self.updateText(text, False)

    def send(self):
        text = self.message_le.text()
        if text == "":
            return
        if text[:2] == '0x':
            text = text[2:]
        try:
            int(text, 16)
        except ValueError:
            self.statusBar().showMessage("You must send a hexadecimal value", 1000)
            self.message_le.clear()
            return
        if len(text) %2 != 0:
            self.statusBar().showMessage("You must send a hexadecimal value", 1000)
            self.message_le.clear()
            return
        b = bytes.fromhex(text)
        self.serial.write(b)
        self.message_le.clear()
        self.updateText(text)

    def readModel(self):
        self.lastFunctionSent = 1
        text = HM_TM5X.readModel()
        if text[:2] != -1:
            self.serial.write(bytes.fromhex(text))
        self.updateText(text)
        self.statusBar().showMessage("Reading Model Name", 1000)

    def writePalette(self):
        val = self.palettes.currentIndex()
        self.lastFunctionSent = 14
        text = HM_TM5X.palette(val, True)
        if text[:2] != -1:
            self.serial.write(bytes.fromhex(text))
        self.updateText(text)
        self.statusBar().showMessage(
            f"Writing {self.palettes.itemText(val)} to Palette", 1000
        )

    def readPalette(self):
        self.lastFunctionSent = 14
        text = HM_TM5X.palette(0)
        if text[:2] != -1:
            self.serial.write(bytes.fromhex(text))
        self.updateText(text)
        self.statusBar().showMessage("Reading Palette", 1000)

    def writeBrightness(self):
        self.lastFunctionSent = 9
        val = self.brightnessLE.text()
        if not val.isnumeric():
            self.statusBar().showMessage(
                "Brightness must by a number between 0 and 100", 1000
            )
            self.brightnessLE.clear()
            return
        text = HM_TM5X.brightness(int(val), True)
        self.brightnessLE.clear()
        if text[:2] != -1:
            self.serial.write(bytes.fromhex(text))
        self.updateText(text)
        self.statusBar().showMessage(f"Setting brightness to {val}", 1000)

    def writeContrast(self):
        self.lastFunctionSent = 10
        val = self.contrastLE.text()
        if not val.isnumeric():
            self.statusBar().showMessage(
                "Contrast must by a number between 0 and 100", 1000
            )
            self.contrastLE.clear()
            return
        text = HM_TM5X.contrast(int(val), True)
        self.contrastLE.clear()
        if text[:2] != -1:
            self.serial.write(bytes.fromhex(text))
        self.updateText(text)
        self.statusBar().showMessage(f"Setting contrast to {val}", 1000)

    def writeMirrorMode(self):
        val = self.mirrorModes.currentIndex()
        self.lastFunctionSent = 15
        text = HM_TM5X.imageMirroring(val, True)
        if text[:2] != -1:
            self.serial.write(bytes.fromhex(text))
        self.updateText(text)
        self.statusBar().showMessage(
            f"Writing mirror mode as {self.mirrorModes.itemText(val)}", 1000
        )

    def saveSettings(self):
        self.lastFunctionSent = 3
        text = HM_TM5X.saveCurrentSettings()
        if text[:2] != -1:
            self.serial.write(bytes.fromhex(text))
        self.updateText(text)
        self.statusBar().showMessage(
            "Saving current device settings to device... please wait", 10000
        )

    @QtCore.pyqtSlot()
    def clearOutput(self):
        self.output_te.clear()
        self.statusBar().showMessage("Output cleared", 1000)

    @QtCore.pyqtSlot(bool)
    def on_toggled(self, checked):
        self.connectPortButton.setText("Disconnect" if checked else "Connect")
        if checked:
            if not self.serial.isOpen():
                self.serial.open(QtCore.QIODevice.ReadWrite)
                if not self.serial.isOpen():
                    self.connectPortButton.setChecked(False)
                else:
                    self.statusBar().showMessage(
                        f"Connected to {self.portFinder.port}", 1000
                    )
            else:
                self.statusBar().showMessage("COM Port not selected or available", 1000)
                self.connectPortButton.setChecked(False)
        else:
            self.serial.close()
            self.statusBar().showMessage("Serial connection closed", 1000)

    def showDialog(self):
        dialog = LoginPopup(self)
        if dialog.exec_():
            self.lastFunctionSent = 4
            text = HM_TM5X.factoryReset()
            if text[:2] != -1:
                self.serial.write(bytes.fromhex(text))
            self.updateText(text)
            self.statusBar().showMessage(
                "Resetting device to Factory settings... please wait", 10000
            )

    def chooseCOMPort(self, newPort):
        serOpen = False
        if self.serial.isOpen():
            serOpen = True
            self.serial.close()
        self.serial.setPortName(newPort)
        if serOpen:
            self.serial.open(QtCore.QIODevice.ReadWrite)
            if not self.serial.isOpen():
                self.connectPortButton.setChecked(False)
        self.statusBar().showMessage(f"{newPort} selected", 1000)
        print(newPort)

    def toggleTimestamp(self, enable):
        print(f"timestamp is {enable}")
        self.showTimestamp = enable

    def closeEvent(self, event):
        self.serial.close()
        self.statusBar().showMessage("Disconnected", 1000)
        print("COM Port closed")

    def updateText(self, text, sending=True):
        if sending:
            if self.showTimestamp:
                t = datetime.now()
                self.output_te.append(
                    f"{t.hour}:{t.minute}:{t.second}.{round(t.microsecond / 1000)} ->>> {text}"
                )
            else:
                self.output_te.append(f">> {text}")
        else:
            if self.showTimestamp:
                t = datetime.now()
                self.output_te.append(
                    f"{t.hour}:{t.minute}:{t.second}.{round(t.microsecond / 1000)} -> {text}"
                )
            else:
                self.output_te.append(f"{text}")
            self.statusBar().showMessage(f'"{text}" received', 1000)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(basedir, 'favicon.ico')))
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
