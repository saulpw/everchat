#!/usr/bin/python

import sys
import os.path
import time
import fileinput
import re

def datestamp(t):
    return time.strftime("%Y-%m-%d  %A", time.localtime(t))

def datetimestamp(t):
    return time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime(t))

def timestamp(t):
    return time.strftime("%H:%M:%S", time.localtime(t))

def dateOf(t):
    return time.localtime(int(t))[0:3]

def duration(secs):
    return "%d minutes" % (secs / 60)

endtag = "</td></tr></table>"
endtag2 = "</div></div>"

reTimestamp = re.compile(r'<(?:table|div) class="msg timestamp">(?:<tr>)?<(?:td|div) class="date".*?</(?:td|div)>(?:</tr>)?</(?:table|div)>')
reMsg = re.compile(r'timet="(\d+)">[\d:]+</(?:td|div)>\s*<(?:td|div) class="src"> ([^<]+)</(?:td|div)><(?:td|div) class="contents"> ?(.*)')
reUrl = re.compile(r'<a href="([^"]+)" target="_blank">\1</a>')
newfp = None

leader = " " * 16

def replUrl(matchobj):
    return matchobj.group(1)

def endConversation(t):
    global newfp, convStartTime
    if convStartTime > 0:
        newfp.write("^^^ %s %s - %s (%s)\n" % (leader, datetimestamp(convStartTime), timestamp(lastMessageTime), duration(lastMessageTime - convStartTime)))
        time.localtime(t)[7]
        for daily in range(1, time.localtime(t)[7] - time.localtime(lastMessageTime)[7]):
            newfp.write("--- %s\n" % (datestamp(lastMessageTime + daily * 3600*24)))
    convStartTime = t


def parseEntry(packetfull):
    global lastMessageTime, newfp
    packet = reTimestamp.sub("", packetfull)

    packet = packet.strip()
    if not packet:
        return

    m = reMsg.search(packet)
    if m:
        t, src, msg = m.groups()
        if src not in users:
            users[src] = [ 0, 0, 0, 0 ]  # lines, words, all letters, non-ws letters

        u = users[src]
        u[0] += 1

        if msg.endswith(endtag):
            msg = msg[:-len(endtag)]
        elif msg.endswith(endtag2):
            msg = msg[:-len(endtag2)]

        msg = reUrl.sub(replUrl, msg)
        t = int(t)

        msgdate = time.localtime(t)
        lastdate = time.localtime(lastMessageTime)
        if msgdate[0] != lastdate[0]: # year has changed
            endConversation(t)
            if newfp:
                newfp.close()

            newfn = "%s-%4d.log" % (channame, msgdate[0])
            newfp = file(newfn, "w")
            newfp.write("___ %s %s\n" % (leader, datestamp(t)))
        elif t - lastMessageTime > 2*3600:
            endConversation(t)
            newfp.write("___ %s %s\n" % (leader, datestamp(t)))
        elif t - lastMessageTime > 15*60:
            newfp.write("\n")
        else:
            u[1] += len(msg.split())
            u[2] += len(msg)
            u[3] += len([x for x in msg if not x.isspace()])
            # tally src user with letter/word/line count
            pass

        newfp.write("%s [%s] %s\n" % (timestamp(t), src[1:-1], msg))
        lastMessageTime = t
    else:
        print "no match around %s" % datetimestamp(lastMessageTime)
        return lastMessageTime

    return t

def parseOldLog(fn):
    global lastMessageTime, convStartTime
    global users, newfp

    convStartTime = 0
    lastMessageTime = 0
    users = { }

    orig_contents = "".join([x.strip() for x in file(fn).readlines()])
    contents = orig_contents
    while contents:
        r = contents.find(endtag2)
        if r > 0:
            lastMesageTime = parseEntry(contents[:r+len(endtag2)])
            contents = contents[r+len(endtag2):]
        else:
            r = contents.find(endtag)
            if r > 0:
                parseEntry(contents[:r+len(endtag)])
                contents = contents[r+len(endtag):]
            else:
                print "remainder:", contents

    print "done outputting log, checking msg counts..."

    for k, v in users.items():
        nraw = orig_contents.count(k)
        if nraw != v[0]:
            print '"%s" occurred %s times in source text, but only %s messages recorded' % (k, nraw, v[0])
    endConversation(lastMessageTime)

    stats = [ ]
       
    for k, v in users.items():
        lines, words, letters, nonwsletters = v
        stats.append("%s=%s/%s" % (k,lines,words)) # ,letters,nonwsletters))

    newfp.write("--- %s\n" % "  ".join(stats))
    newfp.close()
#    print "total chats:", sum(users.values())

reMsg = re.compile(r'(\d+:\d+) <([^>]+)> (.*)')
reDate = re.compile(r'--- Log opened (.*)')
currTime = None

def parseIRSSILog(fn):
    for L in file(fn).readlines():
        m = reDate.match(L)
        if m:
            currTime = time.strptime(m.group(1), "%a %b %d %H:%M:%S %Y")
            continue

        m = reMsg.match(L)
        if m:
            hour, minute, src, msg = m.groups()
#            print "%02d:02d"
            currTime.tm_hour = hour
            currTime.tm_min = minute
            time.strp
            continue

        print "unparsed:", L

for fn in sys.argv[1:]:
    channame = os.path.splitext(fn)[0]
#    parseOldLog(fn)
    parseIRSSILog(fn)

