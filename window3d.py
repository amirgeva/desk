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
        y0 = 300
        z0 = 100
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
        self.node.setPos(0, y0, z0)

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

    def drag(self, mouse_pos, old_mouse_pos):
        v = self.node.getPos()
        cam_node = globals.gui.camNode
        cam = globals.gui.camera
        Rcw = cam.getMat()
        Rwc = LMatrix4f(cam.getMat())
        Rwc.invertInPlace()
        vrel = Rwc.xformPoint(v)
        y = vrel[1]
        ray = CollisionRay()
        ray.setFromLens(cam_node, old_mouse_pos)
        direction = ray.getDirection()
        old_pos = direction * (y / direction[1])
        ray.setFromLens(cam_node, mouse_pos)
        direction = ray.getDirection()
        new_pos = direction * (y / direction[1])
        delta = new_pos - old_pos
        pos = vrel + delta
        pos = Rcw.xformPoint(pos)
        self.node.setPos(pos)
        return True

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
