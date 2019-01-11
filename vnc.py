#!/usr/bin/env python3
from twisted.internet import reactor, task
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
import re
from struct import pack, unpack


class RFB(Protocol):
    def __init__(self):
        self.buffer = bytearray()
        self.handler = None
        self.expected_len = 0
        self.expect(self.handle_version, 12)
        self.rectangles_left = 0
        self.mouse_buttons = 0
        self.mouse=(0,0)
        self.buttonnames = {
            'mouse1': 1,
            'mouse2': 2,
            'mouse3': 3
        }
        self.keycodes = {
            'escape': 0xff1b,
            'backspace': 0xff08,
            'insert': 0xff63,
            'home': 0xff50,
            'page_up': 0xff55,
            'page_down': 0xff56,
            'tab': 0xff09,
            'delete': 0xffff,
            'end': 0xff57,
            'enter': 0xff0d,
            'arrow_left': 0xff51,
            'arrow_up': 0xff52,
            'arrow_down': 0xff54,
            'arrow_right': 0xff53,
            'lshift': 0xffe1,
            'rshift': 0xffe2,
            'lcontrol': 0xffe3,
            'rcontrol': 0xffe4,
            'lalt': 0xffe9,
            'ralt': 0xffea,
            'space': 0x0020
        }
        for i in range(12):
            self.keycodes['f{}'.format(i + 1)] = 0xffbe + i

    def handle_key_event(self, event):
        key = event[0]
        down = event[1]
        if len(key) == 1:
            self.send_key(ord(key), down)
        else:
            if key in self.keycodes:
                self.send_key(self.keycodes.get(key), down)
            elif key in self.buttonnames:
                button_index = self.buttonnames.get(key)
                mask = (1 << (button_index - 1))
                if down:
                    self.mouse_buttons = self.mouse_buttons | mask
                else:
                    self.mouse_buttons = self.mouse_buttons & ~mask
                self.send_mouse_event(self.mouse_buttons,self.mouse)
            else:
                print("Unknown event '{}'".format(key))

    def handle_mouse_event(self,pos):
        if self.mouse[0]!=pos[0] or self.mouse[1]!=pos[1]:
            #print("mouse: {},{}".format(pos[0],pos[1]))
            self.mouse=(pos[0],pos[1])
            self.send_mouse_event(self.mouse_buttons,self.mouse)

    def nop(self, block):
        pass

    def fail(self, reason):
        print(reason)
        reactor.stop()

    def handle_version(self, block):
        versions = [b'RFB 003.003\n', b'RFB 003.007\n', b'RFB 003.008\n']
        if block in versions:
            self.transport.write(b'RFB 003.003\n')
            self.expect(self.handleAuthType, 4)
        else:
            self.fail('Invalid protocol version')

    def handleAuthType(self, block):
        type, = unpack('!I', block)
        if type != 1:
            self.fail('Unsupported Authentication')
        else:
            self.transport.write(pack('!B', 0))
            self.expect(self.handleServerInit, 24)

    def handleServerInit(self, block):
        width, height = unpack('!HH', block[0:4])
        print("ServerInit: {}x{}".format(width, height))
        self.width = width
        self.height = height
        n, = unpack('!I', block[20:24])
        self.expect(self.handleServerName, n)

    def handleServerName(self, block):
        self.server_name = str(block, 'utf-8')
        # SetEncodings to RAW and CopyRect only
        self.transport.write(pack('!BBHII', 2, 0, 2, 0, 1))
        self.request_update(True)

    def request_update(self, full):
        incr = 1
        if full:
            incr = 0
        #print("Request Update incremental={}".format(incr))
        self.transport.write(pack('!BBHHHH', 3, incr, 0, 0, self.width, self.height))

    def send_key(self, keycode, down):
        flag = 0
        if down:
            flag = 1
        self.transport.write(pack('!BBHI', 4, flag, 0, keycode))

    def send_mouse_event(self, buttons, pos):
        self.transport.write(pack('!BBHH', 5, buttons, pos[0], pos[1]))

    def expect(self, handler, block_len):
        if len(self.buffer) >= block_len:
            block = self.buffer[0:block_len]
            self.buffer = self.buffer[block_len:]
            handler(block)
        else:
            self.handler = handler
            self.expected_len = block_len

    def dataReceived(self, data):
        self.buffer += data
        while len(self.buffer)>0 or self.rectangles_left>0:
            if self.handler:
                if len(self.buffer) >= self.expected_len:
                    block = self.buffer[0:self.expected_len]
                    self.buffer = self.buffer[self.expected_len:]
                    handler = self.handler
                    self.handler = None
                    self.expected_len=0
                    handler(block)
                else:
                    break
            else:
                self.handle()

    def handle(self):
        if self.rectangles_left > 0:
            self.rectangles_left = self.rectangles_left - 1
            self.expect(self.handle_rectangle, 12)
        elif self.buffer[0] == 0:
            self.expect(self.frame_buffer_update, 4)
        elif self.buffer[0] == 1:
            self.expect(self.colormap_update,6)
        elif self.buffer[0] == 2:
            print("Bell")
            self.buffer = self.buffer[1:]
        elif self.buffer[0] == 3:
            self.expect(self.server_cut, 8)
        else:
            print("Unknown message {}".format(int(self.buffer[0])))

    def colormap_update(self,block):
        header,first,n = unpack('!HHH',block)
        print("Colormap update ({})".format(n))
        self.expect(self.colormap_colors,6*n)

    def colormap_colors(self,block):
        pass

    def server_cut(self, block):
        header, n = unpack('!II', block)
        self.expect(self.clipboard_copy, n)

    def clipboard_copy(self, block):
        print("Clipboard '{}'".format(str(block, 'ascii')))

    def frame_buffer_update(self, block):
        header, n = unpack('!HH', block)
        #print("BUFFER_UPDATE ({})".format(n))
        self.rectangles_left = n - 1
        self.expect(self.handle_rectangle, 12)

    def handle_rectangle(self, block):
        x, y, w, h, e = unpack('!HHHHI', block)
        #print("Handle {},{},{},{}".format(x, y, w, h))
        self.cur_rect = (x, y, w, h)
        if e == 0:
            self.expect(self.handle_raw, w * h * 4)
        elif e == 1:
            self.expect(self.handle_copy_rect, 4)
        if self.rectangles_left == 0:
            self.request_update(False)

    def handle_raw(self, block):
        # print("Received block size: {}, for rect: {},{},{},{}".format(len(block),*self.cur_rect))
        self.update_pixels(self.cur_rect, block)
        #if self.rectangles_left > 0:
        #    self.handle()

    def handle_copy_rect(self, block):
        srcx, srcy = unpack('!HH', block)
        print("Received copy from {},{}   to  rect: {},{},{},{}".format(srcx,srcy,*self.cur_rect))
        self.copy_rect((srcx, srcy), self.cur_rect)
        #if self.rectangles_left > 0:
        #    self.handle()

    def copy_rect(self, src_point, dst_rect):
        pass

    def update_pixels(self, rect, pixels):
        pass


def run(client):
    d = client.get_display()
    ep = TCP4ClientEndpoint(reactor, "localhost", 5900 + d)
    d = connectProtocol(ep, client)
    tasks = client.get_tasks()
    for t in tasks:
        l = task.LoopingCall(t)
        l.start(0.01)
    reactor.run()


def stop():
    reactor.stop()
