
import time
import re

from User import User

reDatestamp = r'^[-_]+ *(\d+-\d+-\d+).*'
reHMS = r'^(\d+:\d+(?::\d+)?)'
reMsg = reHMS + r' \[(.*)\] ?(.*)$'
reRename = reHMS + r' \+* (\S+) was (\S+)'
reJoin1 = reHMS + r' \** (\S+) \((\S+)\) has joined \S+$'
reJoin2 = reHMS + r' \+* (\S+) (.*)'

def datestamp(t):
    return time.strftime("%Y-%m-%d  %A", time.gmtime(t)) # %z for timezone

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
        for c in [ ChannelMessage, ChannelJoin ]:
            r = c.parse(line, context)
            if r:
                return r

        if Datestamp.parse(line, context):
            return None

        return line
        
class Datestamp:
    def __init__(self, t):
        self.time = t

    @classmethod
    def parse(classtype, line, context):
        g = re.match(reDatestamp, line)
        if g:
            datestr = g.group(1)
            tm = time.strptime(datestr, "%Y-%m-%d")
            t = time.mktime(tm)
            context.set_time(t)

            return Datestamp(t)

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
        g = re.match(reMsg, line)
        if g:
            timestr,nick,rest = g.groups()
            hms = timestr.split(":")
            t = context.adjustedTime(*hms)
            return ChannelMessage(t, nick, context.name, rest)

    def serializeLog(self, log):
        firstLine = True
        ret = ""
        for L in self.msg.splitlines():
            ts = timestamp(self.time, log.emit_seconds)
            if firstLine:
                ret += "%s [%s] %s" % (ts, self.src, L)
                firstLine = False
            else:
                ret += "\n...%s %s" % (" " * (len(ts) + len(self.src)), L)
        return ret

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

class ChannelJoin:
    def __init__(self, t, chan, user, nickname):
        self.time = t
        self.channel = chan
        self.user = user
        self.nickname = nickname

    @classmethod
    def parse(classtype, line, context):
        g = re.match(reJoin1, line)
        if not g:
            g = re.match(reJoin2, line)

        if g:
            timestr, nick, email = g.groups()
            u = User.find(email)
            if not u:
                u = User.create(email)
            hms = timestr.split(":")
            t = context.adjustedTime(*hms)
            
            return ChannelJoin(t, context.name, u, nick)
            
    def serializeLog(self, f):
        if self.nickname not in f.users:
            f.users[self.nickname] = self.user
            assert f.users[self.nickname] == self.user
            return "%s +++ %s %s" % (timestamp(self.time, f.emit_seconds), self.nickname, self.user)

    def serializeIRC(self, c):
        return ":%s JOIN :#%s" % (self.nickname, self.channel)

    def serializeHTML(self, c):
        return ":%s JOIN :#%s" % (self.nickname, self.channel)

class NickChange:
    pass
