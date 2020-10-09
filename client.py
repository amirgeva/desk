#!/usr/bin/env python3
# from math import copysign
import sys
import subprocess
import vnc
import awm
import globals
from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from panda3d.bullet import BulletSphericalConstraint, BulletHingeConstraint
from window3d import Window3D
from gui_tools import GUIBase
from hand import Hand
from room import Room
from computer import Computer


def nose_pos_str(n):
    p = n.getPos()
    return f'{round(p[0])},{round(p[1])},{round(p[2])}'


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


def normalized_mouse_position(pos, ws):
    x = pos[0] / float(ws[0])
    y = 1.0 - pos[1] / float(ws[1])
    return LPoint2(x * 2 - 1, y * 2 - 1)


alpha = 0
theta = 180
phi = 0
first_time_arrows = True
cam_dist = 2200
cam_offset = LVecBase3d(0, 0, 0)
psi = 0


def process_arrows(key):
    global alpha
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
    elif key == 'control-arrow_left':
        alpha -= 1
    elif key == 'control-arrow_right':
        alpha += 1
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
    p = LVecBase3d(d * p[0], d * p[1], d * p[2]) + cam_offset
    print(p)
    cam = globals.gui.camera
    cam.setPos(p[0], p[1], p[2])
    # cam.lookAt(Point3(0, 0, 0))
    cam.setHpr(0, psi, 0)
    print(f'{cam.getPos()}   {cam.getHpr()}')
    return True


class Client(vnc.RFB):
    def __init__(self):
        super(Client, self).__init__()
        globals.gui = GUIBase()
        self.catch_iter_count = 0
        self.stride = 0
        self.hover = 0
        self.display = globals.display
        self.dragged_window = None
        self.hover_caption = None
        self.hover_caption_pos = None
        self.ignore_next_wheel_up = False
        self.rotate_window = None
        self.hang_target = Point3(0, 0, 0)
        self.hold_mouse = 0, 0
        self.mouse_pos = 0, 0
        self.reset_mouse = False
        self.windows = {}
        self.sphere = None
        self.first_frame_update = True
        # self.sphere = globals.gui.loader.load_model('models/sphere20.egg', )
        # self.sphere.reparentTo(globals.gui.render)
        # self.sphere.setPos(0, 2000, 0)
        # self.sphere.setBin("unsorted", 0)
        # self.sphere.setDepthTest(False)
        # self.sphere.setDepthWrite(False)

        self.wm = awm.Manager(self.get_display(), self)
        self.hand = Hand(globals.gui)
        self.hand_constraint = None
        self.room = Room(globals.gui)
        # self.computer = Computer(globals.gui)
        globals.gui.accept('keydown', self.key_down)
        globals.gui.accept('keyup', self.key_up)
        globals.gui.accept('keystroke', self.key_char)
        globals.gui.accept('keyrepeat', self.key_repeat)

    def stop_drag(self, enable_physics):
        if self.dragged_window:
            if enable_physics:
                self.dragged_window.set_physics(True)
            self.dragged_window = None
            globals.gui.world.remove(self.hand_constraint)
            self.hand.node.setPos(5000, 0, 0)
            globals.gui.mouse_mode(False)

    def on_mouse_button(self, button, down):
        if self.hover > 0 and down:
            self.wm.focus(self.hover)
        if button == 1 and self.hover_caption and down:
            if self.dragged_window:
                self.stop_drag(True)
                globals.gui.mouse_mode(False)
            else:
                self.dragged_window = self.hover_caption
                self.dragged_window.set_physics(True)
                offset = LVector3(0, 0, 50)
                self.hand.node.setPos(self.hover_caption_pos + offset)
                self.hand_constraint = BulletHingeConstraint(self.hand.phy_node, self.dragged_window.phy_node,
                                                             Point3(0, 0, 0),
                                                             self.dragged_window.box.node.getPos() + offset,
                                                             LVector3(1, 0, 0), LVector3(1, 0, 0), False)
                # self.hand_constraint = BulletSphericalConstraint(self.hand.phy_node, self.dragged_window.phy_node,
                #                                                  Point3(0, 0, 0), self.dragged_window.box.node.getPos())
                globals.gui.world.attachConstraint(self.hand_constraint)
                # self.dragged_window.set_physics(False)
                self.hold_mouse = self.mouse_pos[0], self.mouse_pos[1]
                globals.gui.mouse_mode(True)
            return
        if button == 3 and (self.dragged_window or self.rotate_window):
            self.reset_mouse = True
            self.rotate_window = self.dragged_window if down else None
            if self.dragged_window:
                self.dragged_window.set_physics(False)
            globals.gui.mouse_mode(down)
            self.stop_drag(False)
            return
        self.handle_mouse_button_event(button, down)

    def on_mouse_move(self, win, pos):
        self.handle_mouse_move_event(pos)

    def handle_drag_wheel(self, direction):
        p = self.hand.node.getPos()
        if direction == 'down':
            p[1] -= 100
        else:
            p[1] += 100
        self.hand.node.setPos(p)

    def hang_window(self):
        w = self.dragged_window
        angle = 0
        if abs(self.hang_target[0]) > 1950:
            if self.hang_target[0] < -1950:
                angle = 90
            elif self.hang_target[0] > -1950:
                angle = -90
        w.node.setHpr(angle, 0, 0)
        w.node.setPos(self.hang_target)
        w.set_physics(False)
        self.stop_drag(False)

    def front_window(self):
        w = self.dragged_window
        w.node.setHpr(0, 0, 0)
        w.node.setPos(0, -1000, 100)
        w.set_physics(False)
        self.stop_drag(False)

    def key_down(self, key):
        if len(key) > 1:
            print(f'Key: "{key}"')
            # if process_arrows(key):
            #     return
            if key == 'tab' and self.dragged_window:
                self.hang_window()
            if key == 'shift-tab' and self.dragged_window:
                self.front_window()
            if key.startswith('wheel') and self.dragged_window:
                self.handle_drag_wheel(key[6:])
            if key == 'alt-escape':
                globals.gui.closeWindow(globals.gui.win)
                globals.gui.userExit()
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
        if len(key) == 1 and ord(key) > 32:
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
                r = wins.get(window_id)
                if window_id not in self.windows:
                    w = Window3D(window_id, r)
                    self.windows[window_id] = w
                else:
                    self.windows.get(window_id).update_rectangle(r)

    def get_display(self):
        return self.display

    def get_tasks(self):
        return [self.run_gui]

    def poll_mouse(self):
        if not globals.gui.win:
            return
        if self.windows:
            window_ids = list(self.windows.keys())
            w = self.windows.get(window_ids[0])
            s = nose_pos_str(w.node)
            # globals.gui.set_debug_text(s)
        mouse = globals.gui.win.getPointer(0)
        x = mouse.getX()
        y = mouse.getY()
        if self.mouse_pos[0] == x and self.mouse_pos[1] == y:
            return
        self.mouse_pos = x, y
        # globals.gui.set_debug_text(f'mouse: {x},{y}')
        if self.dragged_window or self.rotate_window:
            delta = LVecBase3(x - self.hold_mouse[0], 0, -(y - self.hold_mouse[1]))
            self.hold_mouse = x, y
            if self.rotate_window is not None:
                # globals.gui.set_debug_text(f'delta={delta}')
                if self.reset_mouse:
                    self.reset_mouse = False
                else:
                    a = self.rotate_window.node.getHpr()
                    a = a + LVecBase3(delta[0], -delta[2], 0)
                    self.rotate_window.node.setHpr(a)
            else:
                p = self.dragged_window.node.getPos()
                self.dragged_window.move(delta)
                self.hand.move(delta)
                cam = globals.gui.camera.getPos()
                prel = p - cam
                ax = abs(prel[0])
                if ax > prel[1]:
                    prel = prel * (1980 / ax)
                else:
                    prel = prel * ((1980 - cam[1]) / prel[1])
                    p = prel + cam
                if abs(p[0]) > 1980:
                    p = p * (1980 / abs(p[0]))
                if self.sphere:
                    self.sphere.setPos(p)
                # globals.gui.set_debug_text(f'{p}')
                self.hang_target = p
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
                        self.hover_caption_pos = win.get_hook_pos()

    def catch_dropped_windows(self):
        self.catch_iter_count += 1
        if self.catch_iter_count > 10:
            for wid in self.windows.keys():
                win = self.windows.get(wid)
                p = win.node.getPos()
                if p[2] < -1000:
                    win.reset_position()

    def run_gui(self):
        taskMgr.step()
        self.wm.handle_events()
        self.poll_mouse()
        globals.gui.loop()
        self.catch_dropped_windows()

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
            globals.desk_rect = self.width, self.height
            globals.front_texture = Texture("screen")
            globals.front_texture.setup2dTexture(self.width, self.height, Texture.TUnsignedByte, Texture.FRgba8)
            print(globals.front_texture)
            self.stride = self.width * 4
        buffer = globals.front_texture.modifyRamImage()
        src_stride = rect[2] * 4
        src = 0
        for i in range(rect[3]):
            index = (rect[1] + i) * self.stride + rect[0] * 4
            buffer.setSubdata(index, src_stride, pixels[src:(src + src_stride)])
            index += self.stride
            src += src_stride

    def rects_done(self):
        if self.first_frame_update:
            self.first_frame_update = False
            self.wm.refresh()


def main():
    if not calculate_display():
        print("VNC not started.  Run:\nXvnc -geometry 3840x2160 -depth 24 -Protocol3.3 -SecurityTypes None :15 &")
        print("xterm -fn 10x20 -fg green -bg black -display :15 &")
    else:
        c = Client()
        vnc.run(c)


if __name__ == '__main__':
    main()
