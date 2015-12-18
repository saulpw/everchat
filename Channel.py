from LogConnection import LogConnection
from LogEntry import *

g_channels = { } # [channel_name] = <Channel object>

import time
def now():
    return time.gmtime()[0:6]

class Channel:
    def __init__(self, name):
        self.name = name
        self.members = { }  # ["nick"] = <User object>
        self.listeners = [ ] # list of *Connection objects

        lc = LogConnection(self.name)
        self.listeners.append(lc)  # to log transcript to the filesystem

        self.contents = lc.read_contents()

        self.lastDatestamp = (0,0,0,0,0,0)

    def __str__(self):
        return self.name

    @staticmethod
    def get(channame):
        if channame not in g_channels:
            g_channels[channame] = Channel(channame)
        return g_channels[channame]

    def getNickFromEmail(self, email):
        user = User.get(email)
        for nick, v in self.members.items():
            if v is user:
                return nick

    def irc_id(self, email):
        nick = self.getNickFromEmail(email)
        if nick:
            return "%s!%s" % (nick, user.email)

    def notify(self, obj, conn_from=None):
        self.contents.append(obj)

        for conn in self.listeners:
            conn.notify(obj, conn_from)

    def add_connection(self, conn, nickname):
        if nickname not in self.members:
            self.members[nickname] = conn.user
            self.notify(ChannelJoin(now(), self.name, conn.user, nickname))
        else:
            assert self.members[nickname] == conn.user

        self.listeners.append(conn)

        # replay past log contents
        for L in self.contents[-5:]:
            conn.notify(L)

