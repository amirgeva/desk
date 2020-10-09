#!/usr/bin/env python3
import sys
import numpy as np
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
import vnc
from awm import Manager

app = None
display = 15


def run_gui():
    app.processEvents()


def csvformat(img):
    h, w, c = img.shape
    rows = []
    for y in range(h):
        row = []
        for x in range(w):
            pixel = []
            for i in range(c):
                pixel.append(f'{img[y, x, i]:02x}')
            row.append(' '.join(pixel))
        rows.append('|'.join(row))
    return '\n'.join(rows)


class QTClient(vnc.RFB):
    def __init__(self, listener):
        super().__init__()
        self.image = None
        self.listener = listener
        self.log = open('qtvnc.log', 'w')
        self.wm = Manager(display, self)
        self.key_names = {
            Qt.Key_Escape: 'escape',
            Qt.Key_Tab: 'tab',
            Qt.Key_Backtab: 'backtab',
            Qt.Key_Backspace: 'backspace',
            Qt.Key_Return: 'enter',
            Qt.Key_Enter: 'enter',
            Qt.Key_Insert: 'insert',
            Qt.Key_Delete: 'delete',
            Qt.Key_Pause: 'pause',
            Qt.Key_Print: 'print',
            Qt.Key_SysReq: 'sysreq',
            Qt.Key_Clear: 'clear',
            Qt.Key_Home: 'home',
            Qt.Key_End: 'end',
            Qt.Key_Left: 'arrow_left',
            Qt.Key_Up: 'arrow_up',
            Qt.Key_Right: 'arrow_right',
            Qt.Key_Down: 'arrow_down',
            Qt.Key_PageUp: 'page_up',
            Qt.Key_PageDown: 'page_down',
            Qt.Key_Shift: 'lshift',
            Qt.Key_Control: 'lcontrol',
            Qt.Key_Meta: 'meta',
            Qt.Key_Alt: 'lalt',
            Qt.Key_AltGr: 'ralt',
            Qt.Key_CapsLock: 'caps',
            Qt.Key_NumLock: 'num',
            Qt.Key_ScrollLock: 'scroll',
            Qt.Key_F1: 'f1',
            Qt.Key_F2: 'f2',
            Qt.Key_F3: 'f3',
            Qt.Key_F4: 'f4',
            Qt.Key_F5: 'f5',
            Qt.Key_F6: 'f6',
            Qt.Key_F7: 'f7',
            Qt.Key_F8: 'f8',
            Qt.Key_F9: 'f9',
            Qt.Key_F10: 'f10',
            Qt.Key_F11: 'f11',
            Qt.Key_F12: 'f12'
        }

    def get_display(self):
        return display

    def initialize_image(self):
        if self.width > 0 and self.height > 0:
            self.image = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            return True
        return False

    def check_image_size(self):
        if self.image is None:
            return self.initialize_image()
        s = self.image.shape
        if s[0] != self.height or s[1] != self.width:
            return self.initialize_image()
        return True

    def copy_rect(self, src_point, dst_rect):
        if self.check_image_size():
            sx, sy = src_point
            x, y, w, h = dst_rect
            self.image[y:(y + h), x:(x + w), :] = self.image[sy:(sy + h), sx:(sx + w)]
            if self.listener:
                self.listener.on_pixels()

    def update_pixels(self, rect, pixels):
        if self.check_image_size():
            x, y, w, h = rect
            arr = np.frombuffer(pixels, dtype=np.uint8)
            img = np.reshape(arr, (h, w, 4))
            # self.log.write(f'update_pixels: {x},{y}: {w}x{h}\n{csvformat(img)}')
            self.image[y:(y + h), x:(x + w), :] = img
            if self.listener:
                self.listener.on_pixels()

    def wm_task(self):
        self.wm.handle_events()

    def get_tasks(self):
        return [run_gui, self.wm_task]

    def key_event(self, key, down):
        if key < 256:
            self.handle_key_event((chr(key), down))
        elif key in self.key_names:
            self.handle_key_event((self.key_names.get(key), down))

    def hold(self):
        pass

    def update_windows(self, rects):
        print(rects)


class VNCWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rfb = None
        self.image = None
        self.mouse_pos = 0, 0
        self.mouse_buttons = 0
        self.setMouseTracking(True)

    def set_rfb(self, rfb):
        self.rfb = rfb

    def on_pixels(self):
        h, w, c = self.rfb.image.shape
        img = np.zeros((h, w, 3), dtype=np.uint8)
        img[:, :, 0] = self.rfb.image[:, :, 2]
        img[:, :, 1] = self.rfb.image[:, :, 1]
        img[:, :, 2] = self.rfb.image[:, :, 0]
        h, w, c = img.shape
        self.image = QtGui.QImage(img.data, w, h, w * c, QtGui.QImage.Format_RGB888)
        self.setMinimumSize(w, h)
        self.update()

    def paintEvent(self, e: QtGui.QPaintEvent) -> None:
        if self.image:
            qp = QtGui.QPainter(self)
            p = QtCore.QPoint(0, 0)
            qp.drawImage(p, self.image)

    def send_mouse_event(self):
        self.rfb.send_mouse_event(self.mouse_buttons, self.mouse_pos)

    def mouseMoveEvent(self, e: QtGui.QMouseEvent) -> None:
        if self.rfb:
            self.mouse_pos = e.x(), e.y()
            self.send_mouse_event()

    def get_button_bit(self, button):
        if button == QtCore.Qt.LeftButton:
            return 1
        if button == QtCore.Qt.MidButton:
            return 2
        if button == QtCore.Qt.RightButton:
            return 4
        return 0

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        bit = self.get_button_bit(event.button())
        if bit > 0:
            self.mouse_buttons = self.mouse_buttons | bit
            self.send_mouse_event()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        bit = self.get_button_bit(event.button())
        if bit > 0:
            self.mouse_buttons = self.mouse_buttons & ~bit
            self.send_mouse_event()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if self.rfb:
            text = event.text()
            if len(text) == 1:
                self.rfb.key_event(ord(text), True)
            else:
                self.rfb.key_event(event.key(), True)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        if self.rfb:
            text = event.text()
            if len(text) == 1:
                self.rfb.key_event(ord(text), False)
            else:
                self.rfb.key_event(event.key(), False)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.vnc_widget = VNCWidget(self)
        self.setCentralWidget(self.vnc_widget)
        self.rfb = QTClient(self.vnc_widget)
        self.vnc_widget.set_rfb(self.rfb)
        self.vnc_widget.setFocus()

    def closeEvent(self, event):
        super().closeEvent(event)
        vnc.stop()


def main():
    global app
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    vnc.run(w.rfb)


if __name__ == '__main__':
    main()
