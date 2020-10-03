from panda3d.core import *
from panda3d.bullet import BulletSphereShape, BulletRigidBodyNode
import globals


class Hand:
    def __init__(self, base):
        self.model = base.loader.load_model("models/hand.egg", )
        self.shape = BulletSphereShape(1)
        self.phy_node = BulletRigidBodyNode('hand')
        self.phy_node.addShape(self.shape)
        self.node = globals.gui.render.attachNewNode(self.phy_node)
        self.model.reparentTo(self.node)
        globals.gui.world.attachRigidBody(self.phy_node)
        self.node.setPos(2220, 300, -133)
        self.node.setCollideMask(BitMask32.bit(31))

    def move(self, delta):
        v = self.node.getPos()
        for i in range(len(delta)):
            v[i] = v[i] + delta[i]
        self.node.setPos(v)
