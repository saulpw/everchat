#!/usr/bin/python

import os
import os.path
import sys
import time
import re

from LogEntry import *
import LogConnection

mynick = 'saul'

reDate = re.compile(r'Conversation with (\S+) at (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) (\S+) on (\S+) (.*)')
reMsg = re.compile(r'\((\d+):(\d+):(\d+) (\w+)\) ([^:]+): (.*)')
#(07:00:26 AM) dougthonus is now known as DougThonus.
#reRename = re.compile(r'((\d+):(\d+):(\d+)\) (\w+)\) ([^:]+): (.*)')

def parseAIMLine(L, out):
        m = reDate.match(L)
        if m:
            dest, dotw, day, monthabbr, year, hms, ampm, tz, channel, rest = m.groups()
            t = time.mktime(time.strptime(" ".join([ year, monthabbr, day ]), "%Y %b %d"))
            out.set_time(t)
            return None

        m = reMsg.match(L)
        if m:
            hour, minute, second, ampm, src, msg = m.groups()
            h = int(hour)
            if ampm == "PM":
                h += 12
            src = src.strip()
            msg = msg.strip()
            t = out.adjustedTime(h, int(minute), int(second))
            return ChannelMessage(t, src, out.name, msg)

        # continuation of previous message
        return L

control_chars = ''.join(map(unichr, range(0,32) + range(127,160)))

control_char_re = re.compile('[%s]' % re.escape(control_chars))

def remove_control_chars(s):
    return control_char_re.sub('', s)

def main():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-o", "--output", dest="output")
    (options, args) = parser.parse_args()

    channame = options.output or os.path.splitext(args[0])[0]

    contents = {}

    out = LogConnection.LogConnection(channame, seconds=True)
    if os.path.exists(out.filename()):
        print "removing old '%s'" % out.filename()
        os.remove(out.filename())

    for fn in args:
        print fn
        channame = out.name
        msgnum = 0
    
        for L in file(fn).readlines():
            L = remove_control_chars(L)
            obj = parseAIMLine(L.strip(), out)
            if obj is None:
                pass # time already set, etc
            elif type(obj) == str:
                print "cont:", obj
                prevobj.msg += "\n" + obj
            else:
                msgnum += 1
                contents[(obj.time, msgnum)] = obj
                prevobj = obj # for continuations

    scontents = sorted(contents.items())
    for t, v in scontents:
        out.set_time(t[0])
        out.notify(v)

main()
