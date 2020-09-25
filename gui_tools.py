from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
import globals
import vnc


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
        globals.back_texture = loader.loadTexture('wood.jpg')
        self.buttonThrowers[0].node().setButtonDownEvent('keydown')
        self.buttonThrowers[0].node().setButtonUpEvent('keyup')
        self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.disableMouse()
        self.picker = Picker()
        # if not self.mouseWatcherNode.hasMouse():
        #    raise RuntimeError('No mouse')

    def userExit(self):
        vnc.stop()

    def mouse_mode(self, relative):
        props = WindowProperties()
        props.setCursorHidden(relative)
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
