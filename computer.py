from panda3d.core import *
from panda3d.bullet import BulletBoxShape, BulletRigidBodyNode
import globals


class Computer:
    def __init__(self, base):
        self.model = base.loader.load_model("monitor.egg", )
        self.model.reparentTo(base.render)
        self.model.setPos(0,100,-400)
        self.model.setHpr(0,90,0)
