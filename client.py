#!/usr/bin/env python3
#from math import pi, sin, cos
import vnc
import awm
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import *
from windowbox import WindowBox
#from twisted.internet import reactor
#from direct.task import Task


desk_rect=(1000,1000)
front_texture=None
back_texture=None

class Window3D:
    def __init__(self,id,rect):
        print("Creating window ID={}".format(id))
        self.rect=rect
        self.id = id
        self.box = WindowBox(front_texture,back_texture)
        self.box.update_vertices(rect,desk_rect)
        self.box.node.setPos(0,1000,200)
        self.box.node.setTag('wid',str(id))

    def calc_desktop_coords(self,v):
        if v[2]>0:
            return None
        x = int(self.rect[0] + (0.5*self.rect[2]+v[0]))
        y = int(self.rect[1] - v[2])
        return (x,y)

class Picker:  #(DirectObject.DirectObject):
    def __init__(self):
        self.picker= CollisionTraverser()
        self.queue=CollisionHandlerQueue()
        self.pickerNode=CollisionNode('mouseRay')
        self.pickerNP=camera.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
        self.pickerRay=CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.pickerNP = camera.attachNewNode(self.pickerNode)
        self.picker.addCollider(self.pickerNP, self.queue)

    def pick(self, mpos, camNode):
        self.pickerRay.setFromLens(camNode, mpos.getX(),mpos.getY())
        self.picker.traverse(render)
        if self.queue.getNumEntries() > 0:
            self.queue.sortEntries()
            entry = self.queue.getEntry(0)
            o=entry.getIntoNodePath()
            v = entry.getSurfacePoint(o)
            #print(v)
            while o!=render:
                s=o.getTag('wid')
                if s:
                    #print(s)
                    return (s,v)
                else:
                    o=o.getParent()
        return (None,None)


class Desktop(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        global front_texture, back_texture
        back_texture=loader.loadTexture('wood.jpg')
        self.windows={}
        self.buttonThrowers[0].node().setButtonDownEvent('keydown')
        self.accept('keydown', self.keydown)
        self.buttonThrowers[0].node().setButtonUpEvent('keyup')
        self.accept('keyup', self.keyup)
        self.buttonThrowers[0].node().setKeystrokeEvent('keystroke')
        self.accept('keystroke', self.keychar)
        self.keyevents=[]
        self.mouseevents=[]
        self.disableMouse()
        self.picker = Picker()
        taskMgr.add(self.handlePicking,'picking')

    def handlePicking(self,task):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            (w,v)=self.picker.pick(mpos,self.camNode)
            if w:
                w=int(w)
                win=self.windows.get(int(w))
                if win:
                    pos=win.calc_desktop_coords(v)
                    if pos is not None:
                        self.mouseevents.append((w,pos))
        return Task.cont

    def keydown(self,key):
        if len(key)>1:
            self.keyevents.append((key,True))

    def keyup(self,key):
        if len(key)>1:
            self.keyevents.append((key,False))

    def keychar(self,key):
        if ord(key)>32:
            self.keyevents.append((key, True))
            self.keyevents.append((key, False))

    def get_key_events(self):
        res=self.keyevents
        self.keyevents=[]
        return res

    def get_mouse_events(self):
        res=self.mouseevents
        self.mouseevents=[]
        return res

    def handle_collisions(self):
        print("Collision")

    def remove_old_windows(self,wins):
        existing=list(self.windows.keys())
        for id in existing:
            if id not in wins:
                self.windows[id].close()
                del self.windows[id]

    def update_windows(self,wins):
        self.remove_old_windows(wins)
        if front_texture:
            for id in wins.keys():
                if id not in self.windows:
                    self.windows[id]=Window3D(id,wins.get(id))

    def userExit(self):
        vnc.stop()

class Client(vnc.RFB):
    def __init__(self):
        super(Client,self).__init__()
        self.stride=0
        self.desktop = Desktop()
        self.wm = awm.Manager(self.get_display(),self)
        self.hover = 0

    def hold(self):
        pass

    def update_windows(self,wins):
        self.desktop.update_windows(wins)

    def get_display(self):
        return 1

    def get_tasks(self):
        return [self.run_gui]

    def run_gui(self):
        taskMgr.step()
        key_events = self.desktop.get_key_events()
        for event in key_events:
            if event[0].startswith('mouse') and self.hover>0:
                self.wm.focus(self.hover)
            self.handle_key_event(event)
        mouse_events = self.desktop.get_mouse_events()
        for event in mouse_events:
            self.hover=event[0]
            self.handle_mouse_event(event[1])

    def copy_rect(self,src_point,dst_rect):
        #print("Copy rect from {},{}  to {},{},{},{}")
        buffer = front_texture.modifyRamImage()
        h=dst_rect[3]
        w=dst_rect[2]
        src_index = src_point[1] * self.stride + src_point[0] * 4
        dst_index = dst_rect[1] * self.stride + dst_rect[0] * 4
        data=buffer.getData()
        for i in range(h):
            buffer.setSubdata(dst_index,w*4,data[src_index:(src_index+w*4)])
            #data[dst_index:(dst_index+w*4)]=data[src_index:(src_index+w*4)]
            src_index = src_index + self.stride
            dst_index = dst_index + self.stride

    def update_pixels(self,rect,pixels):
        pixels=bytes(pixels)
        global front_texture
        global desk_rect
        if not front_texture:
            desk_rect = (rect[2],rect[3])
            front_texture=Texture("screen")
            front_texture.setup2dTexture(rect[2], rect[3], Texture.TUnsignedByte, Texture.FRgba8)
            self.stride = rect[2] * 4
            self.wm.refresh()
        buffer = front_texture.modifyRamImage()
        src_stride = rect[2]*4
        src=0
        for i in range(rect[3]):
            index = (rect[1]+i)*self.stride + rect[0]*4
            buffer.setSubdata(index,src_stride,pixels[src:(src+src_stride)])
            index += self.stride
            src += src_stride





def main():
    vnc.run(Client())


if __name__=='__main__':
    main()