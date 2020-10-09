#!/usr/bin/env python3
from Xlib.display import Display
from Xlib.error import BadWindow
from Xlib import X
from rectpack import newPacker


class Manager:
    def __init__(self, display, client):
        self.logfile = None # open('awm.log', 'w')
        self.log('-------------------------')
        self.display = Display(':{}'.format(display))
        self.root = self.display.screen().root
        self.root.change_attributes(event_mask=X.SubstructureNotifyMask)
        self.window_rectangles = {}
        self.window_objects = {}
        self.client = client
        self.arrange()

    def refresh(self):
        self.window_rectangles = {}
        self.window_objects = {}
        windows = self.root.query_tree().children
        if len(windows) > 0:
            self.log(f'Checking {len(windows)} windows ({type(windows)}): ')
            for w in windows:
                if w.get_attributes().map_state == 2:
                    g = w.get_geometry()
                    self.log(f'Window {w.id:x}: {g.width}x{g.height} @ {g.x},{g.y}')
                    self.window_rectangles[w.id] = (g.x, g.y, g.width, g.height)
                    self.window_objects[w.id] = w
            self.client.update_windows(self.window_rectangles)

    def focus(self, window_id):
        if window_id in self.window_objects:
            self.log("Raising {}".format(window_id))
            w = self.window_objects.get(window_id)
            w.circulate(X.RaiseLowest)

    def arrange(self):
        packer = newPacker(rotation=False)
        windows = self.root.query_tree().children
        self.window_rectangles = {}
        self.window_objects = {}
        mapped_windows = []
        if len(windows) > 0:
            for w in windows:
                try:
                    self.log(f'window id={w.id:x}  map_state = {w.get_attributes().map_state}')
                    if w.get_attributes().map_state == 2:
                        self.window_objects[w.id] = w
                        mapped_windows.append(w)
                        g = w.get_geometry()
                        width = g.width
                        height = g.height
                        self.log(f"Adding window size: {width}x{height}")
                        packer.add_rect(g.width, g.height, w.id)
                    # else:
                    #     raise Exception()
                except BadWindow:
                    pass
                except Exception as e:
                    print(e)
            g = self.root.get_geometry()
            self.log(f'Packing into root size {g.width}x{g.height}')
            packer.add_bin(g.width, g.height)
            packer.pack()
            rects = packer.rect_list()
            for _, x, y, w, h, wid in rects:
                if wid in self.window_objects:
                    win = self.window_objects.get(wid)
                    win.configure(x=x, y=y, width=w, height=h)
                    self.window_rectangles[wid] = (x, y, w, h)
            else:
                self.log('Packer has no bins')

    def handle_events(self):
        n = self.display.pending_events()
        if n > 0:
            event = self.display.next_event()
            self.log(f'Event: {event}')
            if event.type == X.MapNotify or event.type == X.UnmapNotify:
                self.log('Map' if event.type == X.MapNotify else 'Unmap')
                self.client.hold()
                self.arrange()
                self.client.update_windows(self.window_rectangles)

    def log(self, s):
        if self.logfile:
            self.logfile.write(f'{s}\n')
            self.logfile.flush()
