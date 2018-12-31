#!/usr/bin/env python3
import sys
import threading
import time
import socketserver
from Xlib.display import Display
from Xlib import X, XK
from rectpack import newPacker

Done = False
mgr = None


def kbd():
    global Done
    input()
    Done = True


class Manager:
    def __init__(self, display):
        self.display = display
        self.root = display.screen().root
        self.root.change_attributes(event_mask=X.SubstructureNotifyMask)
        self.windows = {}

    def arrange(self):
        packer = newPacker(rotation=False)
        windows = self.root.query_tree().children
        self.windows = {}
        if len(windows) > 0:
            for w in windows:
                g = w.get_geometry()
                width = g.width
                height = g.height
                print("Adding window size: {}x{}".format(width, height))
                packer.add_rect(g.width, g.height)
            g = self.root.get_geometry()
            packer.add_bin(g.width, g.height)
            packer.pack()
            bin = packer[0]
            n = len(bin)
            for i in range(n):
                r = bin[i]
                win = windows[i]
                win.configure(x=r.x, y=r.y, width=r.width, height=r.height)
                self.windows[win.id] = r

    def run(self):
        while not Done:
            n = self.display.pending_events()
            if n == 0:
                time.sleep(0.01)
                continue
            event = self.display.next_event()
            if event.type == X.MapNotify or event.type == X.UnmapNotify:
                self.arrange()
                self.update_clients()

    def update_clients(self):
        pass

    def process(self, cmd):
        print('Got: {}'.format(cmd))
        return 'OK'


class WMHandler(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            while not Done:
                cmd = self.rfile.readline()
                cmd=str(cmd,'ascii').strip()
                if cmd == 'QUIT':
                    break
                response = mgr.process(cmd).strip()+'\n'
                self.wfile.write(response.encode('ascii'))
        except ValueError:
            pass


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


def main():
    if len(sys.argv) > 1:
        display = Display(sys.argv[1])
    else:
        display = Display()
    t = threading.Thread(target=kbd)
    t.start()

    HOST, PORT = "localhost", 0xA330
    server = ThreadedTCPServer((HOST, PORT), WMHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    global mgr
    mgr = Manager(display)
    mgr.run()
    t.join()

    server.shutdown()
    server.server_close()


if __name__ == '__main__':
    main()
