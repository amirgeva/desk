#!/usr/bin/env python3
import sys
import threading
import time
import socket
from select import select
from Xlib.display import Display
from Xlib import X, XK
from rectpack import newPacker

class Manager:
    def __init__(self, display, client):
        self.display = Display(':{}'.format(display))
        self.root = self.display.screen().root
        self.root.change_attributes(event_mask=X.SubstructureNotifyMask)
        self.window_rects = {}
        self.window_objs = {}
        self.client = client
        self.refresh()

    def refresh(self):
        self.window_rects = {}
        self.window_objs = {}
        windows = self.root.query_tree().children
        if len(windows) > 0:
            for w in windows:
                g = w.get_geometry()
                self.window_rects[w.id] = (g.x, g.y, g.width, g.height)
                self.window_objs[w.id] = w
            self.client.update_windows(self.window_rects)

    def focus(self,id):
        if id in self.window_objs:
            w=self.window_objs.get(id)
            w.circulate(X.RaiseLowest)

    def arrange(self):
        packer = newPacker(rotation=False)
        windows = self.root.query_tree().children
        self.window_rects = {}
        self.window_objs = {}
        if len(windows) > 0:
            for w in windows:
                self.window_objs[w.id]=w
                g = w.get_geometry()
                width = g.width
                height = g.height
                print("Adding window size: {}x{}".format(width, height))
                packer.add_rect(g.width, g.height)
            g = self.root.get_geometry()
            packer.add_bin(g.width, g.height)
            packer.pack()
            bag = packer[0]
            n = len(bag)
            for i in range(n):
                r = bag[i]
                win = windows[i]
                win.configure(x=r.x, y=r.y, width=r.width, height=r.height)
                self.window_rects[win.id] = (r.x, r.y, r.width, r.height)

    def handle_events(self):
        n = self.display.pending_events()
        if n > 0:
            event = self.display.next_event()
            if event.type == X.MapNotify or event.type == X.UnmapNotify:
                self.client.hold()
                self.arrange()
                self.client.update_windows(self.window_rects)

