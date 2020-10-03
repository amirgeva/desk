from panda3d.core import *
from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode
import globals


class Room:
    def __init__(self, base):
        self.model = base.loader.load_model("room.egg", )
        self.model.reparentTo(base.render)
        s = 4000

        self.back_shape = BulletBoxShape(Vec3(s,1,s))
        self.back_phy_node = BulletRigidBodyNode('backwall')
        self.back_phy_node.addShape(self.back_shape)
        self.back_node = globals.gui.render.attachNewNode(self.back_phy_node)
        globals.gui.world.attachRigidBody(self.back_phy_node)
        self.back_node.setPos(0,2000,0)

        self.left_shape = BulletBoxShape(Vec3(1,s,s))
        self.left_phy_node = BulletRigidBodyNode('leftwall')
        self.left_phy_node.addShape(self.left_shape)
        self.left_node = globals.gui.render.attachNewNode(self.left_phy_node)
        globals.gui.world.attachRigidBody(self.left_phy_node)
        self.left_node.setPos(-2000,0,0)

        self.right_shape = BulletBoxShape(Vec3(s,1,s))
        self.right_phy_node = BulletRigidBodyNode('rightwall')
        self.right_phy_node.addShape(self.right_shape)
        self.right_node = globals.gui.render.attachNewNode(self.right_phy_node)
        globals.gui.world.attachRigidBody(self.right_phy_node)
        self.right_node.setPos(2000,0,0)

        self.setCollideBit(2)

    def setCollideBit(self, bit):
        self.back_node.setCollideMask(BitMask32.bit(bit))
        self.left_node.setCollideMask(BitMask32.bit(bit))
        self.right_node.setCollideMask(BitMask32.bit(bit))
