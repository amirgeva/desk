#!/usr/bin/env python3
import sys
import threading
import time
import socket
from select import select
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
        self.clients = {}
        self.refresh()

    def refresh(self):
        self.windows = {}
        windows = self.root.query_tree().children
        if len(windows) > 0:
            for w in windows:
                g = w.get_geometry()
                self.windows[w.id] = (g.x, g.y, g.width, g.height)

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
            bag = packer[0]
            n = len(bag)
            for i in range(n):
                r = bag[i]
                win = windows[i]
                win.configure(x=r.x, y=r.y, width=r.width, height=r.height)
                self.windows[win.id] = (r.x, r.y, r.width, r.height)

    def run(self):
        while not Done:
            n = self.display.pending_events()
            if n == 0:
                time.sleep(0.01)
                continue
            event = self.display.next_event()
            if event.type == X.MapNotify or event.type == X.UnmapNotify:
                self.hold()
                self.arrange()
                self.update_clients()

    def build(self):
        wins = []
        for w in self.windows.keys():
            r = self.windows.get(w)
            wins.append('{},{},{},{},{}'.format(w, r[0], r[1], r[2], r[3]))
        return ' '.join(wins)

    def update_clients(self):
        if len(self.clients) > 0:
            msg = self.build()
            for sock in self.clients.keys():
                self.clients.get(sock).write(msg)

    def hold(self):
        for sock in self.clients.keys():
            self.clients.get(sock).write('HOLD')

    def handle(self, cmd):
        print("Handling '{}'".format(cmd))
        if cmd == 'UPDATE':
            self.refresh()
            self.update_clients()
        return 'OK'


class Client:
    def __init__(self, sock):
        self.sock = sock
        self.text = ''
        self.queue = []

    def write(self, response):
        if len(response) > 0:
            self.queue.append(response + '\n')

    def read(self):
        data = self.sock.recv(1024)
        if len(data) == 0:
            return False
        text = str(data, 'ascii')
        self.text = self.text + text
        while '\n' in self.text:
            p = self.text.index('\n')
            cmd = self.text[0:p].strip()
            self.text = self.text[p + 1:]
            self.write(mgr.handle(cmd))
        return True


def server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(('127.0.0.1', 0xA330))
    srv.listen(5)
    readers = [srv]
    while not Done:
        writers = []
        for sock in mgr.clients.keys():
            c = mgr.clients.get(sock)
            if len(c.queue) > 0:
                writers.append(sock)
        rd, wr, xl = select(readers, writers, [], 0.01)
        for sock in rd:
            if sock == srv:
                (sock, address) = sock.accept()
                print("Connection from: {}".format(address))
                sock.setblocking(0)
                mgr.clients[sock] = Client(sock)
                readers.append(sock)
            else:
                if sock in mgr.clients:
                    c = mgr.clients.get(sock)
                    if not c.read():
                        print("Client disconnected")
                        del mgr.clients[sock]
                        readers = [srv] + list(mgr.clients.keys())
        for sock in wr:
            c = mgr.clients.get(sock)
            s = c.queue[0]
            del c.queue[0]
            sock.send(s.encode('ascii'))


def main():
    if len(sys.argv) > 1:
        display = Display(sys.argv[1])
    else:
        display = Display()
    tkbd = threading.Thread(target=kbd)
    tkbd.start()
    global mgr
    mgr = Manager(display)

    tsrv = threading.Thread(target=server)
    tsrv.start()

    mgr.run()

    tsrv.join()
    tkbd.join()


if __name__ == '__main__':
    main()
