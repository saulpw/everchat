import re
    
regexUrl = re.compile(r"(http://\S+)", re.IGNORECASE | re.LOCALE)

class HTTPConnection:
    def __init__(self, c):
        self.c = c

    def notify(self, obj, from_conn=None):
        L = obj.serializeHTML(self)
        self.send(L)
