import time
import os.path

from LogEntry import *
LOG_PATH = "."
LEADING_WS = "    "

class LogConnection:
    def __init__(self, channame, seconds=True):
        self.emit_seconds = seconds
        self.name = channame
        self.fp = None
        self.needs_date = True

        self.users = { }
        self.contextTime = 0
        self.lastMessageTime = 0
        self.last_line_blank = True

    def adjustedTime(self, hour, minute, second=None):
        tm = [ x for x in time.localtime(self.contextTime) ]
        tm[3] = int(hour)
        tm[4] = int(minute)
        if second is not None:
            tm[5] = int(second)

        ret = time.mktime(tm)
        if ret < self.contextTime:
            # assume next day
            ret += 3600*24
            assert ret > self.contextTime

        self.contextTime = ret

        return ret

    def notify(self, obj, from_conn=None):
        L = obj.serializeLog(self)
        if L:
                prev = self.lastMessageTime

                # maybe write a datestamp or a newline
                ndays = int(obj.time - prev) / (3600*24)
#                assert ndays < 3000
                if obj.time - prev > 15*60:
                    self.writeline()

                if ndays > 0 and prev > 0:
                    if ndays > 1:
                        self.writeline("      ... %s days ..." % ndays)

                if time.localtime(obj.time)[0:3] != time.localtime(prev)[0:3]:
                    assert time.localtime(obj.time)[0:3] > time.localtime(prev)[0:3]
                    self.needs_date = True

                self.lastMessageTime = obj.time
                self.writeline(L)

        self.contextTime = obj.time

    def datestamp(self, t=None):
        t = max(self.contextTime, self.lastMessageTime)
        self.writeline(Datestamp(t).serializeLog(self))

    def set_time(self, t):
        self.contextTime = t

    def writeline(self, L=""):
        if not self.fp:
            self.fp = file(self.filename(), "a")

        if not L:
            if not self.last_line_blank:
                self.fp.write("\n")
                self.last_line_blank = True
        else:
            if self.needs_date:
                self.needs_date = False # avoid recursion
                self.datestamp()

            self.fp.write(L + "\n")
            self.last_line_blank = False

    def filename(self):
        return os.path.join(LOG_PATH, "%s.chatlog" % self.name)

    def read_contents(self):
        ret = [ ]
        try:
            msgnum = 0
            for L in file(self.filename()).readlines():
                L = L.strip()
                if not L: continue
                p = LogItem.parse(L, self) 
                if not p:
                    pass
                elif isinstance(p, str):
                    print("unparsed: %s" % L)
                else:
                    ret.append(( p.time, msgnum, p ))
                    msgnum += 1

        except IOError:
            pass
        
        return ret

    def close(self):
        if self.fp:
            self.writeline("---")
            self.fp.close()
        self.fp = None

    def __del__(self):
        self.close()

