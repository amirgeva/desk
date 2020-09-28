from panda3d.core import *
from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode


class Desktop:
    def __init__(self, base):
        self.model = base.loader.load_model("desk3.egg", )
        # self.model.setPos(0, 2000, -1500)
        # self.model.reparent_to(base.render)

        # collider_node = CollisionNode("desktop")
        # collider_node.addSolid(CollisionBox(LPoint3(-925, -435, 0), LPoint3(925, 435, 770)))
        # self.collider = self.model.attachNewNode(collider_node)
        # self.collider.show()

        # Physics and collisions
        self.shape = BulletBoxShape(Vec3(925, 435, 385))
        self.physics_node = BulletRigidBodyNode('desk')
        self.physics_node.addShape(self.shape)
        o = base.render.attachNewNode(self.physics_node)
        self.model.reparentTo(o)
        self.model.setPos(0,0,-385)
        base.world.attachRigidBody(self.physics_node)
        o.setPos(0,0,-770)

    def loop(self):
        self.model.setPos(0, 2000, -1500)

    def add_collider(self, traverser, pusher):
        pass
        # import globals
        # traverser.addCollider(self.collider, pusher)
        # pusher.addCollider(self.collider, self.model, globals.gui.drive.node())
