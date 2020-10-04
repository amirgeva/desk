from panda3d.core import *
from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode
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
        x0 = int(rect[0]*1.1) - 2000 + int(0.7 * rect[2])
        y0 = 1980
        z0 = int(rect[1]*1.1) - 500
        self.default_position = Point3(x0,y0,z0)
        self.box.node.setTag('wid', str(window_id))

        size = [0.5 * (a - b) for a, b in zip(self.box.mx, self.box.mn)]
        self.shape = BulletBoxShape(Vec3(size[0], size[1], size[2] + 10))
        self.phy_node = BulletRigidBodyNode('window')
        volume = size[0] * size[1] * size[2]
        self.phy_node.setMass(0.001 * volume)
        self.phy_node.addShape(self.shape)
        self.node = globals.gui.render.attachNewNode(self.phy_node)
        self.phy_node.setLinearDamping(0.6)
        self.phy_node.setAngularDamping(0.6)
        globals.gui.world.attachRigidBody(self.phy_node)
        self.node.setCollideMask(BitMask32.bit(1))
        self.box.node.reparentTo(self.node)
        self.box.node.setPos(0, 0, size[2] - 10)
        self.node.setPos(x0, y0, z0)
        self.set_physics(False)

    def reset_position(self):
        self.node.setPos(self.default_position)
        self.node.setHpr(0,0,0)
        self.set_physics(False)

    def get_hook_pos(self):
        return self.node.getPos() + self.box.node.getPos()

    def update_rectangle(self, rect):
        self.rect = rect
        self.box.update_vertices(rect, globals.desk_rect)

    def set_physics(self, state):
        if state:
            self.phy_node.setMass(1.0)
        else:
            self.phy_node.setMass(0.0)
            self.phy_node.setLinearVelocity(LVector3(0, 0, 0))
            self.phy_node.setAngularVelocity(LVector3(0, 0, 0))

    def rotate(self, dx, dy):
        dx = norm_rot(dx)
        dy = norm_rot(dy)
        v = self.box.node.getHpr()
        v = v + LVecBase3(dx, dy, 0)
        self.box.node.setHpr(v)

    def move(self, delta):
        v = self.node.getPos()
        for i in range(len(delta)):
            v[i] = v[i] + delta[i]
        self.node.setPos(v)
        # self.phy_node.setAngularVelocity(LVector3(0,0,0))

    def close(self):
        self.box.close()

    def calc_desktop_coords(self, v):
        if v[2] > 0:
            return None
        x = int(self.rect[0] + (0.5 * self.rect[2] + v[0]))
        y = int(self.rect[1] - v[2])
        return x, y
