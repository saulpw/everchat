
import re

reHMS = "^(\d+:\d+:\d+)"

months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()

class LogContext:
    def __init__(self, name, start_time, users):
        self.channel = name
        self.time = start_time
        self.users = users

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
            return Datestamp( (y, month, d, 0, 0, 0) )

    def serializeLog(self, c):
        y,month,d,h,m,s = self.time
        return "--- %05u-%02d-%02d UTC" % (y, month, d)

    def serializeIRC(self, c):
        pass # return "PRIVMSG #%s :%s" % self.serializeLog(c)

    def serializeHTML(self, c):
        return """<td class="date"><a class="stardate" timet="%s">%s</a>"""

def timestamp(t):
    y,m,d,h,m,s = t
    return "%02d:%02d:%02d" % (h,m,s)
       
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
        y,m,d,h,m,s = self.time
        return "%s [%s] %s" % (timestamp(self.time), self.src, self.msg)

    def serializeIRC(self, c):
        return ":%s PRIVMSG #%s :%s" % (self.src, self.dest, self.msg)

    def serializeHTML(self, c):
        y,m,d,h,m,s = self.time
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
            u = context.users[email]
            t = parseTime(timestr, context.time)
            
            return ChannelJoin(t, channame, u, nick)
            

    def serializeLog(self, f):
        return "%s *** %s (%s) has joined %s" % (timestamp(self.time), self.nickname, self.user.email, self.channel)

    def serializeIRC(self, c):
        return ":%s JOIN :#%s" % (self.nickname, self.channel)

    def serializeHTML(self, c):
        return ":%s JOIN :#%s" % (self.user.irc_id(), self.channel)

