#!/usr/bin/python

import os
import os.path
import sys
import time
import re

from LogEntry import *
import LogConnection

mynick = 'saul'

rePrivMsg = re.compile(r'(\d+):(\d+) \[msg\(([^\)]+)\)\](.*)')
reMsg = re.compile(r'(\d+):(\d+) <([^>]+)>(.*)')
reMe = re.compile(r'(\d+):(\d+) +\* (\S+) ?(.*)')
reLogOpen = re.compile(r'--- Log opened (.*)')
reDate = re.compile(r'--- Day changed (.*)')
reJoin = re.compile(r'(\d+):(\d+) \S+ (\S+) \[~?([^\]]+)\] ([^#]+)#(\S+)')
reTopic = re.compile(r'(\d+):(\d+) \S+ (\w+) changed the topic [^:]*: (.*)')
reRename = re.compile(r'(\d+):(\d+) \S+ (\S+) is now known as (\S+)')

def parseIRSSILine(L, out):
        m = reLogOpen.match(L)
        if m:
            currTime = time.strptime(m.group(1), "%a %b %d %H:%M:%S %Y")
            t = time.mktime(currTime)
            out.set_time(t)
            return None

        m = reDate.match(L)
        if m:
            currTime = time.strptime(m.group(1), "%a %b %d %Y")
            t = time.mktime(currTime)
            out.set_time(t)
            return None

        m = reMsg.match(L)
        if m:
            hour, minute, src, msg = m.groups()
            src = src.strip()
            msg = msg.strip()
            if src[0] in "@+":
                src = src[1:]
            t = out.adjustedTime(hour, minute)
            return ChannelMessage(t, src, out.name, msg)

        m = rePrivMsg.match(L)
        if m:
            hour, minute, dest, msg = m.groups()
            src = mynick
            msg = msg.strip()
            t = out.adjustedTime(hour, minute)
            return ChannelMessage(t, src, out.name, msg)

        m = reMe.match(L)
        if m:
            hour, minute, src, msg = m.groups()
            src = src.strip()
            t = out.adjustedTime(hour, minute)
            return ChannelMessage(t, src, out.name, "* " + msg)

        m = reTopic.match(L)
        if m:
            hour, minute, src, msg = m.groups()
            src = src.strip()
            t = out.adjustedTime(hour, minute)
            return ChannelMessage(t, src, out.name, "/topic " + msg)

        m = reJoin.match(L)
        if m:
            hour, minute, nick, email, action, channame = m.groups()
            t = out.adjustedTime(hour, minute)
            return ChannelJoin(t, channame or out.name, email, nick)

        m = reRename.match(L)
        if m:
            hour, minute, nick, newnick = m.groups()
            t = out.adjustedTime(hour, minute)
            return ChannelJoin(t, out.name, out.users.get(nick, "was " + nick), newnick)

        return L

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-o", "--output", dest="output")
    parser.add_option("-a", "--append", action="store_true", dest="append", default=False)
    (options, args) = parser.parse_args()

    channame = options.output or os.path.splitext(args[0])[0]

    out = LogConnection.LogConnection(channame, seconds=False)
    if args.append:
        contents = out.read_contents()
    else:
        contents = []

    for fn in args:
        print fn
        channame = out.name
        msgnum = 0

        ext = os.path.splitext(fn)[1]
    
        for L in file(fn).readlines():
            if ext == ".txt":
                obj = parseAIMLine(L.strip(), out)
            elif ext == ".log":
                obj = parseIRSSILine(L.strip(), out)
            elif ext == ".chatlog" or ext == ".chatlog1":
                obj = LogItem.parse(L.strip(), out)
            else:
                print "unknown ext", ext
                break

            if not obj:
                pass
            elif isinstance(obj, str):
                pass
                print "unparsed:", obj
            else:
                msgnum += 1
                contents.append( (obj.time, msgnum, obj) )

    if os.path.exists(out.filename()):
        print "renaming old '%s'" % out.filename()
        os.rename(out.filename(), out.filename() + ".bak")

    scontents = sorted(contents)
    out.set_time(scontents[0][0])
    for t, n, v in scontents:
        out.notify(v)

main()
