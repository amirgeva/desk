#!/usr/bin/env python3
from Xlib.display import Display
from Xlib import X
from rectpack import newPacker


class Manager:
    def __init__(self, display, client):
        self.display = Display(':{}'.format(display))
        self.root = self.display.screen().root
        self.root.change_attributes(event_mask=X.SubstructureNotifyMask)
        self.window_rectangles = {}
        self.window_objects = {}
        self.client = client
        self.refresh()

    def refresh(self):
        self.window_rectangles = {}
        self.window_objects = {}
        windows = self.root.query_tree().children
        if len(windows) > 0:
            print(f'Checking {len(windows)} windows: ')
            for w in windows:
                if w.get_attributes().map_state == 2:
                    g = w.get_geometry()
                    print(f'Window {w.id}: {g.width}x{g.height} @ {g.x},{g.y}')
                    self.window_rectangles[w.id] = (g.x, g.y, g.width, g.height)
                    self.window_objects[w.id] = w
            print('------------------------')
            self.client.update_windows(self.window_rectangles)

    def focus(self, window_id):
        if window_id in self.window_objects:
            print("Raising {}".format(window_id))
            w = self.window_objects.get(window_id)
            w.circulate(X.RaiseLowest)

    def arrange(self):
        packer = newPacker(rotation=False)
        windows = self.root.query_tree().children
        self.window_rectangles = {}
        self.window_objects = {}
        if len(windows) > 0:
            for w in windows:
                if w.get_attributes().map_state == 2:
                    self.window_objects[w.id] = w
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
                self.window_rectangles[win.id] = (r.x, r.y, r.width, r.height)

    def handle_events(self):
        n = self.display.pending_events()
        if n > 0:
            event = self.display.next_event()
            if event.type == X.MapNotify or event.type == X.UnmapNotify:
                self.client.hold()
                self.arrange()
                self.client.update_windows(self.window_rectangles)
