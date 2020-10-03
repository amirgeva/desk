from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from panda3d.core import *
# from panda3d.physics import *
from panda3d.bullet import BulletWorld, BulletDebugNode
import globals
import vnc
import time
from desktop import Desktop

loadPrcFileData("", "load-file-type p3assimp")


class Picker:  # (DirectObject.DirectObject):
    def __init__(self):
        self.picker = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        # noinspection PyArgumentList
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.picker.addCollider(self.pickerNP, self.queue)

    def pick(self, mouse_position, camera_node):
        self.pickerRay.setFromLens(camera_node, mouse_position.getX(), mouse_position.getY())
        # noinspection PyArgumentList
        self.picker.traverse(render)
        if self.queue.getNumEntries() > 0:
            self.queue.sortEntries()
            entry = self.queue.getEntry(0)
            o = entry.getIntoNodePath()
            v = entry.getSurfacePoint(o)
            while o != render:
                s = o.getTag('wid')
                if s:
                    return int(s), v
                else:
                    o = o.getParent()
        return None, None


class GUIBase(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        self.setBackgroundColor(0.1, 0.5, 0.7)
        # self.enableParticles()
        # self.cTrav = CollisionTraverser()
        globals.back_texture = loader.loadTexture('wood.jpg')
        self.buttonThrowers[0].node().setButtonDownEvent('keydown')
        self.buttonThrowers[0].node().setButtonUpEvent('keyup')
        self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.buttonThrowers[0].node().setButtonRepeatEvent('keyrepeat')
        self.disableMouse()
        self.picker = Picker()
        props = WindowProperties(self.win.getProperties())
        props.setTitle('desk')
        # props.setFullscreen(True)
        # props.setUndecorated(True)
        props.setSize(3800, 2000)
        self.win.requestProperties(props)

        self.lights = []
        self.add_point_light((0.9, 0.9, 0.9, 1), (0, -1000, -1500))
        self.add_point_light((0.9, 0.9, 0.9, 1), (0, 1000, 1800))

        self.camLens.setFov(70)
        self.camera.setPos(0, -2080, 200)
        self.camera.setHpr(0, -8, 0)

        render.setShaderAuto()

        # debugNode = BulletDebugNode('Debug')
        # debugNode.showWireframe(True)
        # debugNode.showConstraints(True)
        # debugNode.showBoundingBoxes(False)
        # debugNode.showNormals(False)
        # debugNP = self.render.attachNewNode(debugNode)
        # debugNP.show()

        self.world = BulletWorld()
        self.world.setGravity(Vec3(0, 0, -1000))
        # self.world.setDebugNode(debugNP.node())

        self.last_time = None
        self.desk = Desktop(self)
        self.debug_text = OnscreenText(text='', pos=(-1, 0.8), scale=0.05)

    def add_point_light(self, color, position):
        index = len(self.lights)
        plight = PointLight(f'plight{index}')
        plight.setColor(color)
        plnp = render.attachNewNode(plight)
        plnp.setPos(position[0], position[1], position[2])
        plnp.node().setScene(render)
        plnp.node().setShadowCaster(True)
        self.lights.append((plight, plnp))
        render.setLight(plnp)

    def loop(self):
        cur = time.time()
        if self.last_time is None:
            dt = 0.01
        else:
            dt = cur - self.last_time
        self.last_time = cur
        self.world.doPhysics(dt)
        # self.desk.loop()

    def userExit(self):
        vnc.stop()

    def mouse_mode(self, relative):
        props = WindowProperties()
        props.setCursorHidden(relative)
        # props.setUndecorated(True)
        # if relative:
        #    props.setMouseMode(WindowProperties.M_relative)
        # else:
        #    props.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(props)

    def do_picking(self):
        if self.mouseWatcherNode.hasMouse():
            mouse_position = self.mouseWatcherNode.getMouse()
            return self.picker.pick(mouse_position, self.camNode)
        return None, None

    def set_debug_text(self, text):
        self.debug_text.setText(text)
