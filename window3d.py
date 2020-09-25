from panda3d.core import *
from windowbox import WindowBox
import globals
from math import copysign



def norm_rot(x):
    x = copysign(1, x) * (x ** 2)
    return x


class Window3D:
    def __init__(self, window_id, rect):
        print("Creating window ID={}".format(window_id))
        self.rect = rect
        self.window_id = window_id
        self.box = WindowBox(globals.front_texture, globals.back_texture)
        self.box.update_vertices(rect, globals.desk_rect)
        self.box.node.setPos(0, 1000, 200)
        self.box.node.setTag('wid', str(window_id))

    def rotate(self, dx, dy):
        dx = norm_rot(dx)
        dy = norm_rot(dy)
        v = self.box.node.getHpr()
        v = v + LVecBase3(dx, dy, 0)
        self.box.node.setHpr(v)

    def move(self, dx, dy, lateral):
        # print("Move by {},{}".format(dx, dy))
        # dx=norm_rot(dx)
        # dy=norm_rot(dy)
        v = self.box.node.getPos()
        if lateral:
            v = v + LVecBase3(dx, 0, -dy)
        else:
            v = v + LVecBase3(dx, dy, 0)
        self.box.node.setPos(v)

    def close(self):
        self.box.close()

    def calc_desktop_coords(self, v):
        if v[2] > 0:
            return None
        x = int(self.rect[0] + (0.5 * self.rect[2] + v[0]))
        y = int(self.rect[1] - v[2])
        return x, y

