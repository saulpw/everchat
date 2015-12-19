
import time
import re

from User import User

reHMS = "^(\d+:\d+:\d+)"

def datestamp(t):
    return time.strftime("%Y-%m-%d  %A", time.localtime(t)) # %z for timezone

def datetimestamp(t):
    return time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime(t))

def timestamp(t, flSeconds=True):
    tm = time.localtime(t)
    if flSeconds:
        return "%02d:%02d:%02d" % tuple(tm[3:6])
    else:
        return "%02d:%02d" % tuple(tm[3:5])
       
def duration(secs):
    return "%d minutes" % (secs / 60)

class LogContext:
    def __init__(self, name, start_time):
        self.channel = name
        self.time = start_time

class LogItem:
    @classmethod
    def parse(classtype, line, context):
        for c in [ Datestamp, ChannelMessage, ChannelJoin ]:
            r = c.parse(line, context)
            if r:
                return r
        
class Datestamp:
    def __init__(self, t):
        self.time = t

    @classmethod
    def parse(classtype, line, context):
        g = re.match("^--- (\d+-\d+-\d+) ", line)
        if g:
            datestr = g.group(1)
            y, month, d = [ int(x) for x in datestr.split("-") ]
            context.time = (y, month, d, 0, 0, 0)

    def serializeLog(self, c):
        return "--- " + datestamp(self.time)

    def serializeIRC(self, c):
        pass # return "PRIVMSG #%s :%s" % self.serializeLog(c)

    def serializeHTML(self, c):
        return """<td class="date"><a class="stardate" timet="%s">%s</a>"""

class ChannelMessage:
    def __init__(self, t, src, dest, msg):
        assert "\n" not in msg
        self.time = t
        self.src = src
        self.dest = dest
        self.msg = msg

    @classmethod
    def parse(classtype, line, context):
        """chanmsg = ChannelMessage.parseLog(L)"""
        g = re.match(reHMS + " \[(.*)\] (.*)$", line)
        if g:
            timestr,nick,rest = g.groups()
            t = parseTime(timestr, context.time)
            return ChannelMessage(t, nick, context.channel, rest)

    def serializeLog(self, log):
        y,m,d,h,m,s = time.localtime(self.time)[0:6]
        return "%s [%s] %s" % (timestamp(self.time, log.emit_seconds), self.src, self.msg)

    def serializeIRC(self, c):
        return ":%s PRIVMSG #%s :%s" % (self.src, self.dest, self.msg)

    def serializeHTML(self, c):
        y,m,d,h,m,s = self.time[0:6]
        hrmin = "%02d:%02d" % (h,m)

        # spaces included for reasonable cut'n'paste
        return """<table class="chanmsg %(classes)s"><tr>
        <td class="time" timet="%(time)s">%(hrmin)s</td>
        <td class="src"> %(src)s</td>
        <td class="msg"> %(msg)s</td>
        </tr></table>""" % (self.kwargs["classes"], self.time.time_t, self.src, self.msg)

def parseTime(timestr, basetime):
    h,m,s = timestr.split(":")
    h = int(h)
    m = int(m)
    s = int(s)
    y,mon,d = basetime[0:3]

    return (y,mon,d,h,m,s)

class ChannelJoin:
    def __init__(self, t, chan, user, nickname):
        self.time = t
        self.channel = chan
        self.user = user
        self.nickname = nickname

    @classmethod
    def parse(classtype, line, context):
        g = re.match(reHMS + " \** (\S+) \((\S+)\) has joined (\S+)$", line)
        if g:
            timestr, nick, email, channame = g.groups()
            u = User.find(email)
            t = parseTime(timestr, context.time)
            
            return ChannelJoin(t, channame, u, nick)
            

    def serializeLog(self, f):
        if self.nickname not in f.users:
            f.users[self.nickname] = self.user
            assert f.users[self.nickname] == self.user
            return "%s +++ %s %s" % (timestamp(self.time, f.emit_seconds), self.nickname, self.user)

    def serializeIRC(self, c):
        return ":%s JOIN :#%s" % (self.nickname, self.channel)

    def serializeHTML(self, c):
        return ":%s JOIN :#%s" % (self.nickname, self.channel)

