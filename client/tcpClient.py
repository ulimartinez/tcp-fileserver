import random
import sys
import traceback
from select import *
from socket import *

import re
import params

switchesVarDefaults = (
    (('-s', '--server'), 'server', "127.0.0.1:50000"),
    (('-d', '--debug'), "debug", False),  # boolean (set if present)
    (('-?', '--usage'), "usage", False)  # boolean (set if present)
)

paramMap = params.parseParams(switchesVarDefaults)
server, usage, debug = paramMap["server"], paramMap["usage"], paramMap["debug"]

if usage:
    params.usage()

try:
    serverHost, serverPort = re.split(":", server)
    serverPort = int(serverPort)
except:
    print "Can't parse server:port from '%s'" % server
    sys.exit(1)

sockNames = {}  # from socket to name


class Client:
    def __init__(self, af, socktype, saddr):
        self.saddr = saddr  # addresses
        self.numSent, self.numRecv = 0, 0
        self.allSent = 0
        self.error = 0
        self.isDone = 0
        self.ssock = ssock = socket(af, socktype)
        self.buf = ""
        self.filename = None
        print "New client #%d to %s" % (1, repr(saddr))
        sockNames[ssock] = "C%d:ToServer" % 1
        ssock.setblocking(False)
        ssock.connect_ex(saddr)

    def doSend(self):
        try:
            self.numSent += self.ssock.send(self.filename)
            self.ssock.shutdown(SHUT_WR)
        except Exception as e:
            self.errorAbort("can't send: %s" % e)
            return

    def doRecv(self):
        try:
            d = self.ssock.recv(1024)
            n = len(d)
            self.buf += d
        except Exception as e:
            print "doRecv on dead socket"
            print e
            self.done()
            return

        self.numRecv += n
        if n != 0:
            return
        if debug: print "client %d: zero length read" % 1
        # zero length read (done)
        self.done()

    def doErr(self, msg=""):
        error("socket error")

    def checkWrite(self, file_name):
        if not self.filename:
            self.filename = file_name
            return self.ssock
        else:
            return None

    def checkRead(self):
        if self.isDone:
            return None
        elif self.numSent == 0:
            return None
        else:
            return self.ssock

    def done(self):
        self.isDone = 1
        self.allSent = 1
        try:
            self.ssock(close)
        except Exception:
            pass
        print "client %d done (error=%d)" % (1, self.error)
        if not self.error:
            f = open(self.filename, 'w')
            f.write(self.buf)
            f.close()

    def errorAbort(self, msg):
        self.allSent = 1
        self.error = 1
        print "FAILURE client %d: %s" % (1, msg)
        self.done()


client = Client(AF_INET, SOCK_STREAM, (serverHost, serverPort))
filename = raw_input("filename?")
while not client.isDone:
    rmap, wmap, xmap = {}, {}, {}  # socket:object mappings for select
    sock = client.checkRead()
    if (sock): rmap[sock] = client
    sock = client.checkWrite(filename)
    if (sock): wmap[sock] = client
    xmap[client.ssock] = client
    if debug: print "select params (r,w,x):", [repr([sockNames[s] for s in sset]) for sset in
                                               [rmap.keys(), wmap.keys(), xmap.keys()]]
    rset, wset, xset = select(rmap.keys(), wmap.keys(), xmap.keys(), 60)
    # print "select r=%s, w=%s, x=%s" %
    if debug: print "select returned (r,w,x):", [repr([sockNames[s] for s in sset]) for sset in [rset, wset, xset]]
    for sock in xset:
        xmap[sock].doErr()
    for sock in rset:
        rmap[sock].doRecv()
    for sock in wset:
        wmap[sock].doSend()

