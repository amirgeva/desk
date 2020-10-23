#!/usr/bin/env python3
import sys
import json
import subprocess
from PyQt5 import QtCore, QtWidgets, QtGui

main_window=None

class AppWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image = None
        self.cmd = ''
        self.name=''
        self.pressed = False

    def set_name(self, name):
        self.name=name

    def set_image(self, path):
        self.image = QtGui.QImage(path)

    def set_command(self, cmd):
        self.cmd = cmd

    def activate(self):
        if self.cmd:
            args = self.cmd.split()
            subprocess.Popen(args)
            if self.name=='launcher':
                main_window.close()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == QtCore.Qt.LeftButton:
            self.pressed = True
            self.update()
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == QtCore.Qt.LeftButton:
            self.pressed = False
            self.update()
            self.activate()
        super().mouseReleaseEvent(e)

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        qp = QtGui.QPainter(self)
        c1 = QtCore.Qt.gray
        c2 = QtCore.Qt.black
        qp.setPen(c2 if self.pressed else c1)
        qp.drawLine(0, 0, 127, 0)
        qp.drawLine(0, 0, 0, 127)
        qp.drawLine(1, 1, 126, 0)
        qp.drawLine(1, 1, 0, 126)
        qp.setPen(c1 if self.pressed else c2)
        qp.drawLine(127, 1, 127, 127)
        qp.drawLine(126, 2, 126, 126)
        qp.drawLine(2, 126, 126, 126)
        qp.drawLine(1, 127, 127, 127)
        if self.image:
            o = 1 if self.pressed else 0
            qp.drawImage(o, o, self.image)
        else:
            qp.drawLine(0, 0, 127, 127)
            qp.drawLine(0, 127, 127, 0)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        try:
            cfg = json.load(open('launcher.json'))
            self.group = QtWidgets.QGroupBox(self)
            rows = cfg['rows']
            cols = cfg['cols']
            layout = QtWidgets.QGridLayout()
            for i in range(rows):
                layout.setRowMinimumHeight(i, 128)
            for i in range(cols):
                layout.setColumnMinimumWidth(i, 128)
            y = 0
            x = 0
            apps = cfg['apps']
            app_names = apps.keys()
            for app_name in app_names:
                details = apps.get(app_name)
                w = AppWidget(self)
                w.set_name(app_name)
                w.set_image(details['icon'])
                w.set_command(details['cmd'])
                layout.addWidget(w)
            self.group.setLayout(layout)
            self.setCentralWidget(self.group)
        except OSError:
            QtWidgets.QMessageBox.critical(self, 'Failed to load launcher.json')


def main():
    app = QtWidgets.QApplication(sys.argv)
    global main_window
    main_window = MainWindow()
    main_window.show()
    app.exec_()


if __name__ == '__main__':
    main()
