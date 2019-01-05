#!/usr/bin/env python3
from twisted.internet import reactor
from twisted.internet.protocol import Protocol
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol
import re
from struct import pack, unpack

class RFB(Protocol):
    def __init__(self):
        self.buffer=bytearray()
        self.handler=None
        self.expected_len=0
        self.expect(self.handle_version,12)
        self.rectangles_left=0

    def nop(self,block):
        pass

    def fail(self,reason):
        print(reason)
        reactor.stop()

    def handle_version(self,block):
        versions = [b'RFB 003.003\n',b'RFB 003.007\n',b'RFB 003.008\n']
        if block in versions:
            self.transport.write(b'RFB 003.003\n')
            self.expect(self.handleAuthType,4)
        else:
            self.fail('Invalid protocol version')

    def handleAuthType(self,block):
        type, = unpack('!I',block)
        if type != 1:
            self.fail('Unsupported Authentication')
        else:
            self.transport.write(pack('!B',0))
            self.expect(self.handleServerInit,24)

    def handleServerInit(self,block):
        width,height = unpack('!HH',block[0:4])
        print("ServerInit: {}x{}".format(width,height))
        self.width = width
        self.height = height
        n, = unpack('!I',block[20:24])
        self.expect(self.handleServerName,n)

    def handleServerName(self,block):
        self.server_name = str(block,'utf-8')
        # SetEncodings to RAW and CopyRect only
        self.transport.write(pack('!BBHII',2,0,2,0,1))
        self.request_update(True)

    def request_update(self,full):
        incr=0
        if full:
            incr=1
        self.transport.write(pack('!BBHHHH',3,incr,0,0,self.width,self.height))

    def expect(self,handler,block_len):
        if len(self.buffer)>=block_len:
            block = self.buffer[0:block_len]
            self.buffer=self.buffer[block_len:]
            handler(block)
        else:
            self.handler = handler
            self.expected_len = block_len

    def dataReceived(self, data):
        self.buffer += data
        #print("Received {} bytes.  Total available: {} bytes".format(len(data),len(self.buffer)))
        if self.handler:
            if len(self.buffer)>=self.expected_len:
                block=self.buffer[0:self.expected_len]
                self.buffer=self.buffer[self.expected_len:]
                handler = self.handler
                self.handler=None
                handler(block)
        else:
            self.handle()

    def handle(self):
        if self.rectangles_left > 0:
            self.rectangles_left = self.rectangles_left - 1
            self.expect(self.handle_rectangle,12)
        elif self.buffer[0]==0:
            self.expect(self.frame_buffer_update,4)
        elif self.buffer[0]==2:
            print("Bell")
            self.buffer=self.buffer[1:]
        elif self.buffer[0]==3:
            self.expect(self.server_cut,8)

    def server_cut(self,block):
        header, n = unpack('!II',block)
        self.expect(self.cliboard_copy,n)

    def clipboard_copy(self,block):
        print("Clipboard '{}'".format(str(block,'ascii')))

    def frame_buffer_update(self,block):
        header, n = unpack('!HH',block)
        self.rectangles_left = n-1
        self.expect(self.handle_rectangle,12)

    def handle_rectangle(self,block):
        x,y,w,h,e = unpack('!HHHHI',block)
        self.cur_rect = (x,y,w,h)
        if e==0:
            self.expect(self.handle_raw,w*h*4)
        elif e==1:
            self.expect(self.handle_copy_rect,4)
        #if self.rectangles_left == 0:
        #    self.request_update(False)

    def handle_raw(self,block):
        #print("Received block size: {}, for rect: {},{},{},{}".format(len(block),*self.cur_rect))
        self.update_pixels(self.cur_rect,block)

    def handle_copy_rect(self,block):
        srcx,srcy = unpack('!HH',block)
        #print("Received copy from {},{}   to  rect: {},{},{},{}".format(srcx,srcy,*self.cur_rect))
        self.copy_rect((srcx,srcy),self.cur_rect)

    def copy_rect(self,src_point,dst_rect):
        pass

    def update_pixels(self,rect,pixels):
        pass

def run(client):
    d = client.get_display()
    ep = TCP4ClientEndpoint(reactor, "localhost", 5900+d)
    d = connectProtocol(ep, client)
    tasks = client.get_tasks()
    for task in tasks:
        reactor.callLater(0.1,task)
    reactor.run()
