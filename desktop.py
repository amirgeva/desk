from panda3d.core import *
from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode


class Desktop:
    def __init__(self, base):
        self.model = base.loader.load_model("models/desk3.egg", )
        # self.model.setPos(0, 2000, -1500)
        # self.model.reparent_to(base.render)

        # collider_node = CollisionNode("desktop")
        # collider_node.addSolid(CollisionBox(LPoint3(-925, -435, 0), LPoint3(925, 435, 770)))
        # self.collider = self.model.attachNewNode(collider_node)
        # self.collider.show()

        # Physics and collisions
        self.shape = BulletBoxShape(Vec3(925, 435, 385))
        self.phy_node = BulletRigidBodyNode('desk')
        self.phy_node.addShape(self.shape)
        self.node = base.render.attachNewNode(self.phy_node)
        self.model.reparentTo(self.node)
        self.model.setPos(0, 0, -385)
        base.world.attachRigidBody(self.phy_node)
        self.node.setPos(0, 0, -770)
        self.node.setCollideMask(BitMask32.bit(1))

    def loop(self):
        self.model.setPos(0, 2000, -1500)

    def add_collider(self, traverser, pusher):
        pass
        # import globals
        # traverser.addCollider(self.collider, pusher)
        # pusher.addCollider(self.collider, self.model, globals.gui.drive.node())
