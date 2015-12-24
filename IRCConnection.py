import socket
import time

from User import User
from Channel import Channel
from LogEntry import *

VERSION = 1.0

RPL_NAMREPLY = 353
RPL_ENDOFNAMES = 366
RPL_WELCOME = 1
RPL_YOURHOST = 2
RPL_CREATED = 3
RPL_MYINFO = 4

flDebug = False

def log(s):
    print s

def now():
    return time.gmtime()[0:6]

# a user that is connected with an IRC client
class IRCConnection:
    def __init__(self, sock, addr):
        self.sock = sock
        self.sock_file = sock.makefile('rw')
        self.ip = addr[0]
        self.user = None
        self.nick = None
        self.servername = "localhost"
        self.channels = { } # ["channel_name"] = ( <Channel>, "nickname" )

        log("%s: connected" % self.ip)

        while True:
            L = self.sock_file.readline().strip()
            try:
                if not L:
                    break

                if flDebug:
                    print "%s> %s" % (self.nick, L)

                cmd, rest = L.split(' ', 1)
                funcname = "cmd_" + cmd
                if funcname not in IRCConnection.__dict__:
                    print "unhandled: ", L
                else:
                    cease = IRCConnection.__dict__[funcname](self, rest)
                    if cease:
                        break
            except socket.error, ex:
                log("%s: disconnected: %s" % (self.ip, ex))

        log("%s: ceasing" % self.ip)
        return

    def notify(self, obj, from_conn=None):
        L = obj.serializeIRC(self)
        if self is not from_conn: # filter by default; use None for system/global messages
            self.send(L)

    def cmd_QUIT(self, rest):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        self.sock_file.close()
        return "quit"

    def cmd_MODE(self, rest):
        pass

    def cmd_PING(self, rest):
        self.send("PONG " + rest)

    def cmd_NICK(self, rest):
        if self.nick is None:
            self.nick = rest
        else:
            # nickname is fixed for duration of connection
            self.reply(433, rest) # ERR_NICKNAMEINUSE
        
    def cmd_USER(self, rest):
        username, hostname, servername, realname = rest.split(' ', 3)
        self.realname = realname[1:]

        email = "%s@%s" % (username, hostname)
        u = User.find(email)
        if not u:
            # initiate registration sequence
            u = User.create(email)

        self.user = u
        self.identifier = "%s!%s" % (self.nick, email)
        log("%s: registered: %s" % (self.ip, self.identifier))
        self.reply(RPL_WELCOME, self.identifier)
        self.reply(RPL_YOURHOST, "%s %s" % (self.ip, "0.0001"))
        self.reply(RPL_CREATED, "2016-01-01")
        self.reply(RPL_MYINFO, "%s %s" % (servername, VERSION))

    def cmd_MOTD(self, rest):
        self.reply(422, "ERR_NOMOTD")

    def cmd_INVITE(self, rest):
        invitee, destchan = rest.split()

        invitees = set([ invitee ])

        for chan, mynick in self.channels.values():
            for nickname, user in chan.members.items():
                if nickname == invitee:
                    invitees.add(user)            

        if len(invitees) == 0:
            self.reply(422, "no such nickambiguous invitee (%d possible users)" % len(invitees))
        elif len(invitees) > 1:
            self.reply(422, "ambiguous invitee (%d possible users)" % len(invitees))
        else:
            invitees.pop().invite(destchan)
            

    def cmd_PRIVMSG(self, rest):
        dest, msg = rest.split(" ", 1)
        if dest[0] == "#":
            channame = dest[1:]
            assert channame in self.channels
            chan, mynick = self.channels[channame]
            chan.notify(ChannelMessage(now(), mynick, channame, msg[1:]), self)
        # else: parse for email (userauth) or nickname in one of the self.channels

    def cmd_JOIN(self, rest):
        for channame in rest.split(","):
            channame = channame[1:] # strip leading '#'

            assert channame not in self.channels
            chan = Channel.get(channame)
            chan.add_connection(self, self.nick)
            self.channels[channame] = (chan, self.nick)

    def cmd_PART(self, channame): # unsubscribe to channel
        self.send(":%s PART %s" % (self.identifier, channame))

    def cmd_NAMES(self, channame):
        self.reply(RPL_NAMREPLY, "%s @ %s :%s" % (self.nick, channame, " ".join(channel.members.keys())))
        self.reply(RPL_ENDOFNAMES, "%s @ %s :%s" % (self.nick, channame))

    def reply(self, numcode, rest):
        self.send(":%s %03d %s :%s" % (self.servername, numcode, self.nick, rest))

    def send(self, s):
        if not s: return
        if flDebug:
            print "%s< %s" % (self.nick, s)
        self.sock.send(s + "\n")


