import time
import os.path

from LogEntry import *
LOG_PATH = "."
LEADING_WS = "    "

class LogConnection:
    def __init__(self, channame, seconds=True):
        self.emit_seconds = seconds
        self.name = channame
        self.year = None

        self.users = { }
        self.lastMessageTime = None
        self.convStartTime = None
        self.fp = None

    def notify(self, obj, from_conn=None):
        L = obj.serializeLog(self)
        if L:
            self.maybe_datestamp(obj.time)
            self.fp.write(L + "\n")

#        if src not in self.users:
#            self.users[src] = [ 0, 0, 0, 0 ]  # lines, words, all letters, non-ws letters
#        u = self.users[src]
#        u[0] += 1
            # tally src user with letter/word/line count
#            u[1] += len(msg.split())
#            u[2] += len(msg)
#            u[3] += len([x for x in msg if not x.isspace()])

    def filename(self, year=None):
        if year:
            return os.path.join(LOG_PATH, "%s-%04d.chatlog" % (self.name, year))
        else:
            return os.path.join(LOG_PATH, "%s.chatlog" % self.name)

    def maybe_datestamp(self, t):
        msgdate = time.localtime(t)
        lastdate = time.localtime(self.lastMessageTime)
        if msgdate[0] != lastdate[0]: # year has changed
            self.close()
            self.fp = file(self.filename(msgdate[0]), "a")
        elif t - self.lastMessageTime > 2*3600:
            self.end_conversation(t)
#            self.fp.write("___ %s %s\n" % (LEADING_WS, datestamp(t)))
        elif t - self.lastMessageTime > 15*60:
            self.fp.write("\n")

        self.lastMessageTime = t

    def read_contents(self):
        ret = [ ]
        context = LogContext(self.name, time.gmtime(0))
        try:
            for L in file(self.filename()).readlines():
                L = L.strip()
                if not L: continue
                p = LogItem.parse(L, context) 
                if not p:
                    print("not parsed: %s" % L)
                elif type(p) is Datestamp:
                    context.time = p.to_time() # update context only
                else:
                    ret.append(p)

        except IOError:
            pass
        
        return ret

    def end_conversation(self, t=None):
        if t is None:
            t = self.lastMessageTime

        if self.convStartTime > 0:
#            if True: # self.numMessages > 10:something:
#                self.fp.write("--- %s %s - %s (%s)\n\n" % (LEADING_WS, datetimestamp(self.convStartTime), timestamp(self.lastMessageTime), duration(self.lastMessageTime - self.convStartTime)))
#            else:
            self.fp.write("\n")

            for daily in range(1, time.localtime(t)[7] - time.localtime(self.lastMessageTime)[7]):
                self.fp.write("--- %s\n" % (datestamp(self.lastMessageTime + daily * 3600*24)))

        self.convStartTime = t

    def get_stats(self):
        stats = [ ]
       
        for k, v in self.users.items():
            lines, words, letters, nonwsletters = v
            stats.append("%s=%s/%s" % (k,lines,words)) # ,letters,nonwsletters))

        self.fp.write("--- %s\n" % "  ".join(stats))

    def close(self):
        self.end_conversation()
        if self.fp:
            self.fp.write("---\n")
            self.fp.close()
        self.fp = None

    def __del__(self):
        self.close()

