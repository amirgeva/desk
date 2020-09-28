#!/usr/bin/env python3
# from math import copysign
import sys
import math
import subprocess
import vnc
import awm
import globals
# from globals import gui
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from window3d import Window3D
from gui_tools import GUIBase


def calculate_display():
    text = subprocess.check_output('ps x', shell=True)
    for line in text.decode('utf-8').split('\n'):
        if 'Xvnc' in line:
            parts = line.split()
            last = parts[-1]
            if last.startswith(':'):
                globals.display = int(last[1:])
                return True
    return False


theta = 180
phi = 0
first_time_arrows = True
cam_dist = 2200
cam_offset = LVecBase3d(0, 0, 0)
psi = 0

def process_arrows(key):
    global theta
    global phi
    global first_time_arrows
    global cam_dist
    global psi
    if key == "arrow_right":
        theta = theta + 10
    elif key == "arrow_left":
        theta = theta - 10
    elif key == "arrow_up":
        phi = phi + 10
    elif key == "arrow_down":
        phi = phi - 10
    elif key == 'page_down':
        cam_dist += 10
    elif key == 'page_up':
        cam_dist -= 10
    elif key == 'control-page_down':
        psi += 1
    elif key == 'control-page_up':
        psi -= 1
    elif key == 'control-arrow_up':
        cam_offset[2] += 100
    elif key == 'control-arrow_down':
        cam_offset[2] -= 100
    elif not first_time_arrows:
        return False
    first_time_arrows = False
    d = cam_dist
    yaw = LMatrix3d.rotateMat(theta, LVecBase3d(0, 0, 1))
    pitch = LMatrix3d.rotateMat(phi, LVecBase3d(1, 0, 0))
    R = yaw * pitch
    p = R.cols[1]
    p = LVecBase3d(d*p[0],d*p[1],d*p[2]) + cam_offset
    print(p)
    cam = globals.gui.camera
    cam.setPos(p[0], p[1], p[2])
    # cam.lookAt(Point3(0, 0, 0))
    cam.setHpr(0,psi,0)
    print(f'{cam.getPos()}   {cam.getHpr()}')
    return True


class Client(vnc.RFB):
    def __init__(self):
        super(Client, self).__init__()
        globals.gui = GUIBase()
        self.stride = 0
        self.hover = 0
        self.display = globals.display
        self.hover_caption = None
        self.rotating = None
        self.moving = None
        self.lateral = True
        self.ignore_next_wheel_up = False
        self.hold_mouse = (0, 0)
        self.mouse_pos = (0, 0)
        self.windows = {}
        self.wm = awm.Manager(self.get_display(), self)
        # self.pusher = CollisionHandlerPusher()
        # globals.gui.desk.add_collider(globals.gui.cTrav, self.pusher)
        globals.gui.accept('keydown', self.key_down)
        globals.gui.accept('keyup', self.key_up)
        globals.gui.accept('keystroke', self.key_char)
        globals.gui.accept('keyrepeat', self.key_repeat)
        #process_arrows('')

    def on_mouse_button(self, button, down):
        if self.hover > 0 and down:
            self.wm.focus(self.hover)
        if button == 1 or button == 3:
            if self.hover_caption and down:
                self.moving = self.hover_caption
                self.lateral = (button == 1)
                self.hold_mouse = (self.mouse_pos[0], self.mouse_pos[1])
                return
            if self.moving and not down:
                self.moving = None
                return
        if button == 2:
            if self.hover_caption and down:
                self.rotating = self.hover_caption
                self.hold_mouse = (int(self.mouse_pos[0]), int(self.mouse_pos[1]))
                globals.gui.mouse_mode(True)
                return
            if self.rotating and not down:
                self.rotating = None
                globals.gui.mouse_mode(False)
                return
        self.handle_mouse_button_event(button, down)

    def on_mouse_move(self, win, pos):
        self.handle_mouse_move_event(pos)

    def key_down(self, key):
        if len(key) > 1:
            print(f'Key: "{key}"')
            # if process_arrows(key):
            #     return
            if key == 'alt-escape':
                pass
                # gui.close_window()
            if key.startswith('mouse'):
                self.on_mouse_button(int(key[5:]), True)
            elif key.startswith('control-wheel'):
                self.handle_control_wheel(key[13:] == '_down')
                self.ignore_next_wheel_up = True
            else:
                self.handle_key_event((key, True))

    def key_up(self, key):
        if len(key) > 1:
            if key.startswith('mouse'):
                self.on_mouse_button(int(key[5:]), False)
            elif key.startswith('wheel') and self.ignore_next_wheel_up:
                self.ignore_next_wheel_up = False
            else:
                self.handle_key_event((key, False))

    def key_char(self, key):
        if len(key)==1 and ord(key) > 32:
            self.handle_key_event((key, True))
            self.handle_key_event((key, False))

    def key_repeat(self, key):
        self.key_down(key)
        self.key_up(key)

    def handle_control_wheel(self, down):
        print(f'Wheel move {down}')

    def hold(self):
        pass

    def remove_old_windows(self, wins):
        existing = list(self.windows.keys())
        for window_id in existing:
            if window_id not in wins:
                self.windows[window_id].close()
                del self.windows[window_id]

    def update_windows(self, wins):
        self.remove_old_windows(wins)
        if globals.front_texture:
            for window_id in wins.keys():
                if window_id not in self.windows:
                    w = Window3D(window_id, wins.get(window_id))
                    self.windows[window_id] = w
                    # print("Adding window collider")
                    # w.add_collider(globals.gui.cTrav, self.pusher)
                    # gui.physicsMgr.attachPhysicalNode(w.box.node)

    def get_display(self):
        return globals.display

    def get_tasks(self):
        return [self.run_gui]

    def poll_mouse(self):
        mouse = globals.gui.win.getPointer(0)
        x = mouse.getX()
        y = mouse.getY()
        if self.mouse_pos[0] == x and self.mouse_pos[1] == y:
            return
        self.mouse_pos = x, y
        if self.rotating:
            self.rotating.rotate(x - self.hold_mouse[0], y - self.hold_mouse[1])
            globals.gui.win.movePointer(0, int(self.hold_mouse[0]), int(self.hold_mouse[1]))
        elif self.moving:
            self.moving.move(x - self.hold_mouse[0], y - self.hold_mouse[1], self.lateral)
            self.hold_mouse = x, y
        else:
            self.hover_caption = None
            w, v = globals.gui.do_picking()
            if w:
                win = self.windows.get(int(w))
                if win:
                    pos = win.calc_desktop_coords(v)
                    if pos is not None:
                        self.hover = w
                        self.on_mouse_move(win, pos)
                    else:
                        self.hover_caption = win

    def run_gui(self):
        taskMgr.step()
        self.wm.handle_events()
        self.poll_mouse()
        globals.gui.loop()

    def copy_rect(self, src_point, dst_rect):
        buffer = globals.front_texture.modifyRamImage()
        h = dst_rect[3]
        w = dst_rect[2]
        src_index = src_point[1] * self.stride + src_point[0] * 4
        dst_index = dst_rect[1] * self.stride + dst_rect[0] * 4
        data = buffer.getData()
        for i in range(h):
            buffer.setSubdata(dst_index, w * 4, data[src_index:(src_index + w * 4)])
            src_index = src_index + self.stride
            dst_index = dst_index + self.stride

    def update_pixels(self, rect, pixels):
        pixels = bytes(pixels)
        if not globals.front_texture:
            globals.desk_rect = (rect[2], rect[3])
            sys.stdout.write("Loading front texture: ")
            globals.front_texture = Texture("screen")
            globals.front_texture.setup2dTexture(rect[2], rect[3], Texture.TUnsignedByte, Texture.FRgba8)
            print(globals.front_texture)
            self.stride = rect[2] * 4
            self.wm.refresh()
        buffer = globals.front_texture.modifyRamImage()
        src_stride = rect[2] * 4
        src = 0
        for i in range(rect[3]):
            index = (rect[1] + i) * self.stride + rect[0] * 4
            buffer.setSubdata(index, src_stride, pixels[src:(src + src_stride)])
            index += self.stride
            src += src_stride


def main():
    if not calculate_display():
        print("VNC not started.  Run:\nXvnc -geometry 3840x2160 -depth 24 :15 &")
        print("xterm -fn 10x20 -fg green -bg black -display :15 &")
    else:
        vnc.run(Client())


if __name__ == '__main__':
    main()
