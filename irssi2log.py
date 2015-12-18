#!/usr/bin/python

import os
import os.path
import sys
import time
import re

from LogEntry import *
import LogConnection

reMsg = re.compile(r'(\d+):(\d+) <([^>]+)>(.*)')
reMe = re.compile(r'(\d+):(\d+) +\* (\S+) (.*)')
reLogOpen = re.compile(r'--- Log opened (.*)')
reDate = re.compile(r'--- Day changed (.*)')
reJoin = re.compile(r'(\d+):(\d+) \S+ (\w+) \[~?([^\]]+)\] ([^#]+)#(\S+)')
reTopic = re.compile(r'(\d+):(\d+) \S+ (\w+) changed the topic [^:]*: (.*)')
reRename = re.compile(r'(\d+):(\d+) \S+ (\S+) is now known as (\S+)')


def adjustTime(tm, h, m):
    tm = [ x for x in tm ]
    tm[3] = int(h)
    tm[4] = int(m)
    return tm

def parseIRSSILog(fn, out):
    currTime = None

    for L in file(fn).readlines():
        L = L.strip()
        m = reLogOpen.match(L)
        if m:
            currTime = time.strptime(m.group(1), "%a %b %d %H:%M:%S %Y")
            t = time.mktime(currTime)
            out.notify(Datestamp(t))
            continue

        m = reDate.match(L)
        if m:
            currTime = time.strptime(m.group(1), "%a %b %d %Y")
            t = time.mktime(currTime)
            out.notify(Datestamp(t))
            continue

        m = reMsg.match(L)
        if m:
            hour, minute, src, msg = m.groups()
            src = src.strip()
            msg = msg.strip()
            if src[0] in "@+":
                src = src[1:]
            currTime = adjustTime(currTime, hour, minute)
            t = time.mktime(currTime)
            out.notify(ChannelMessage(t, src, channame, msg))
            continue

        m = reMe.match(L)
        if m:
            hour, minute, src, msg = m.groups()
            src = src.strip()
            currTime = adjustTime(currTime, hour, minute)
            t = time.mktime(currTime)
            out.notify(ChannelMessage(t, src, channame, "* " + msg))
            continue

        m = reTopic.match(L)
        if m:
            hour, minute, src, msg = m.groups()
            src = src.strip()
            currTime = adjustTime(currTime, hour, minute)
            t = time.mktime(currTime)
            out.notify(ChannelMessage(t, src, channame, "/topic " + msg))
            continue

        m = reJoin.match(L)
        if m:
            hour, minute, nick, email, action, channame = m.groups()
            currTime = adjustTime(currTime, hour, minute)
            t = time.mktime(currTime)
            out.notify(ChannelJoin(t, channame or self.name, email, nick))
            continue

        m = reRename.match(L)
        if m:
            hour, minute, nick, newnick = m.groups()
            currTime = adjustTime(currTime, hour, minute)
            t = time.mktime(currTime)
            out.notify(ChannelJoin(t, channame, out.users.get(nick, "was " + nick), newnick))
            continue

        print "unparsed:", L

for fn in sys.argv[1:]:
    channame = os.path.splitext(fn)[0]
    out = LogConnection.LogConnection(channame, seconds=False)
    if os.path.exists(out.filename()):
        print "removing old '%s'" % out.filename()
        os.remove(out.logfn)

    parseIRSSILog(fn, out)

