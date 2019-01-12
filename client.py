#!/usr/bin/env python3
from math import pi, sin, cos, copysign
import vnc
import awm
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
from windowbox import WindowBox

# from twisted.internet import reactor
# from direct.task import Task


desk_rect = (1000, 1000)
front_texture = None
back_texture = None

def norm_rot(x):
    x=copysign(1,x) * (x**2)
    return x


class Window3D:
    def __init__(self, id, rect):
        print("Creating window ID={}".format(id))
        self.rect = rect
        self.id = id
        self.box = WindowBox(front_texture, back_texture)
        self.box.update_vertices(rect, desk_rect)
        self.box.node.setPos(0, 1000, 200)
        self.box.node.setTag('wid', str(id))

    def rotate(self,dx,dy):
        dx=norm_rot(dx)
        dy=norm_rot(dy)
        v=self.box.node.getHpr()
        v=v+LVecBase3(dx,dy,0)
        self.box.node.setHpr(v)

    def move(self,dx,dy,lateral):
        print("Move by {},{}".format(dx,dy))
        #dx=norm_rot(dx)
        #dy=norm_rot(dy)
        v=self.box.node.getPos()
        if lateral:
            v=v+LVecBase3(dx,0,-dy)
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
        return (x, y)


class Picker:  # (DirectObject.DirectObject):
    def __init__(self):
        self.picker = CollisionTraverser()
        self.queue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode('mouseRay')
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.picker.addCollider(self.pickerNP, self.queue)

    def pick(self, mpos, camNode):
        self.pickerRay.setFromLens(camNode, mpos.getX(), mpos.getY())
        self.picker.traverse(render)
        if self.queue.getNumEntries() > 0:
            self.queue.sortEntries()
            entry = self.queue.getEntry(0)
            o = entry.getIntoNodePath()
            v = entry.getSurfacePoint(o)
            while o != render:
                s = o.getTag('wid')
                if s:
                    return (int(s), v)
                else:
                    o = o.getParent()
        return (None, None)


class GUIBase(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        global front_texture, back_texture
        back_texture = loader.loadTexture('wood.jpg')
        self.buttonThrowers[0].node().setButtonDownEvent('keydown')
        self.buttonThrowers[0].node().setButtonUpEvent('keyup')
        self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.disableMouse()
        self.picker = Picker()
        #if not self.mouseWatcherNode.hasMouse():
        #    raise RuntimeError('No mouse')

    def userExit(self):
        vnc.stop()

    def mouse_mode(self,relative):
        props = WindowProperties()
        props.setCursorHidden(relative)
        #if relative:
        #    props.setMouseMode(WindowProperties.M_relative)
        #else:
        #    props.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(props)

    def doPicking(self):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            return self.picker.pick(mpos, self.camNode)
        return (None, None)


gui = GUIBase()


class Client(vnc.RFB):
    def __init__(self):
        super(Client, self).__init__()
        self.stride = 0
        self.hover = 0
        self.hover_caption = None
        self.rotating = None
        self.moving = None
        self.lateral=True
        self.hold_mouse = (0,0)
        self.mouse_pos = (0,0)
        self.windows = {}
        self.wm = awm.Manager(self.get_display(), self)
        gui.accept('keydown', self.keydown)
        gui.accept('keyup', self.keyup)
        gui.accept('keystroke', self.keychar)

    def on_mouse_button(self, button, down):
        if self.hover > 0 and down:
            self.wm.focus(self.hover)
        if button==1 or button==3:
            if self.hover_caption and down:
                self.moving = self.hover_caption
                self.lateral=(button==1)
                self.hold_mouse = (self.mouse_pos[0], self.mouse_pos[1])
                return
            if self.moving and not down:
                self.moving = None
                return
        if button==2:
            if self.hover_caption and down:
                self.rotating = self.hover_caption
                self.hold_mouse = (int(self.mouse_pos[0]), int(self.mouse_pos[1]))
                gui.mouse_mode(True)
                return
            if self.rotating and not down:
                self.rotating = None
                gui.mouse_mode(False)
                return
        self.handle_mouse_button_event(button, down)

    def on_mouse_move(self, win, pos):
        self.handle_mouse_move_event(pos)

    def keydown(self, key):
        if len(key) > 1:
            if key.startswith('mouse'):
                self.on_mouse_button(int(key[5:]), True)
            else:
                self.handle_key_event((key, True))

    def keyup(self, key):
        if len(key) > 1:
            if key.startswith('mouse'):
                self.on_mouse_button(int(key[5:]), False)
            else:
                self.handle_key_event((key, False))

    def keychar(self, key):
        if ord(key) > 32:
            self.handle_key_event((key, True))
            self.handle_key_event((key, False))

    def hold(self):
        pass

    def remove_old_windows(self, wins):
        existing = list(self.windows.keys())
        for id in existing:
            if id not in wins:
                self.windows[id].close()
                del self.windows[id]

    def update_windows(self, wins):
        self.remove_old_windows(wins)
        if front_texture:
            for id in wins.keys():
                if id not in self.windows:
                    self.windows[id] = Window3D(id, wins.get(id))

    def get_display(self):
        return 2

    def get_tasks(self):
        return [self.run_gui]

    def poll_mouse(self):
        mouse = gui.win.getPointer(0)
        x = mouse.getX()
        y = mouse.getY()
        self.mouse_pos = (x,y)
        if self.rotating:
            self.rotating.rotate(x-self.hold_mouse[0],y-self.hold_mouse[1])
            gui.win.movePointer(0,self.hold_mouse[0],self.hold_mouse[1])
        elif self.moving:
            self.moving.move(x-self.hold_mouse[0],y-self.hold_mouse[1],self.lateral)
            self.hold_mouse=(x,y)
        else:
            self.hover_caption = None
            (w, v) = gui.doPicking()
            if w:
                win = self.windows.get(int(w))
                if win:
                    pos = win.calc_desktop_coords(v)
                    if pos is not None:
                        self.hover = w
                        self.on_mouse_move(win, pos)
                    else:
                        self.hover_caption = win

    def run_gui(self):
        taskMgr.step()
        self.wm.handle_events()
        self.poll_mouse()

    def copy_rect(self, src_point, dst_rect):
        buffer = front_texture.modifyRamImage()
        h = dst_rect[3]
        w = dst_rect[2]
        src_index = src_point[1] * self.stride + src_point[0] * 4
        dst_index = dst_rect[1] * self.stride + dst_rect[0] * 4
        data = buffer.getData()
        for i in range(h):
            buffer.setSubdata(dst_index, w * 4, data[src_index:(src_index + w * 4)])
            src_index = src_index + self.stride
            dst_index = dst_index + self.stride

    def update_pixels(self, rect, pixels):
        pixels = bytes(pixels)
        global front_texture
        global desk_rect
        if not front_texture:
            desk_rect = (rect[2], rect[3])
            front_texture = Texture("screen")
            front_texture.setup2dTexture(rect[2], rect[3], Texture.TUnsignedByte, Texture.FRgba8)
            self.stride = rect[2] * 4
            self.wm.refresh()
        buffer = front_texture.modifyRamImage()
        src_stride = rect[2] * 4
        src = 0
        for i in range(rect[3]):
            index = (rect[1] + i) * self.stride + rect[0] * 4
            buffer.setSubdata(index, src_stride, pixels[src:(src + src_stride)])
            index += self.stride
            src += src_stride


def main():
    vnc.run(Client())


if __name__ == '__main__':
    main()
