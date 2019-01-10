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
        self.rect=rect
        self.id = id
        self.box = WindowBox(front_texture,back_texture)
        self.box.update_vertices(rect,desk_rect)
        self.box.node.setPos(0,1000,0)

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
            pickedObj=entry.getIntoNodePath()
            print(entry.getSurfacePoint(pickedObj))

#         parent=self.pickedObj.getParent()
#         self.pickedObj=None

#         while parent != render:
#            if parent.getTag('pickable')=='true':
#               self.pickedObj=parent
#               return parent
#            else:
#               parent=parent.getParent()
#      return None



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
        self.keyevents=[]
        self.disableMouse()
        self.picker = Picker()
        taskMgr.add(self.handlePicking,'picking')

    def handlePicking(self,task):
        if self.mouseWatcherNode.hasMouse():
            mpos = self.mouseWatcherNode.getMouse()
            self.picker.pick(mpos,self.camNode)
        return Task.cont

    def keydown(self,key):
        self.keyevents.append((key,True))

    def keyup(self,key):
        self.keyevents.append((key,False))

    def get_key_events(self):
        res=self.keyevents
        self.keyevents=[]
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
            self.handle_key_event(event)

    def copy_rect(self,src_point,dst_rect):
        pass

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