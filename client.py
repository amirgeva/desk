#!/usr/bin/env python3
from math import pi, sin, cos
from vnc import RFB, run
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Texture, CardMaker
from twisted.internet import reactor
from direct.task import Task
import random
import numpy as np
import cv2

class Desktop(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        cm=CardMaker('card')
        cm.setFrame(-1,1,-0.5,0.5)
        self.card = render.attachNewNode(cm.generate())
        #card.setTexture(self.t2)
        self.card.setPos(1,10,0)

class Client(RFB):
    def __init__(self):
        super(Client,self).__init__()
        self.texture=None
        self.stride=0
        self.desktop=None

    def get_display(self):
        return 1

    def get_tasks(self):
        return [self.gui]

    def gui(self):
        self.desktop = Desktop()
        if self.texture:
            self.desktop.card.setTexture(self.texture)
        self.desktop.run()
        reactor.stop()

    def copy_rect(self,src_point,dst_rect):
        pass

    def update_pixels(self,rect,pixels):
        pixels=bytes(pixels)
        if not self.texture:
            self.texture=Texture("screen")
            self.texture.setup2dTexture(rect[2], rect[3], Texture.TUnsignedByte, Texture.FRgba8)
            if self.desktop:
                self.desktop.card.setTexture(self.texture)
            self.stride = rect[2] * 4
        buffer = self.texture.modifyRamImage()
        src_stride = rect[2]*4
        src=0
        for i in range(rect[3]):
            index = (rect[1]+i)*self.stride + rect[0]*4
            buffer.setSubdata(index,src_stride,pixels[src:(src+src_stride)])
            index += self.stride
            src += src_stride





def main():
    run(Client())


if __name__=='__main__':
    main()