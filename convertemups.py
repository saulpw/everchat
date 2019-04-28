#!/usr/bin/env python3

import re
import time
import fileinput

reTimestamp = re.compile(r'<(?:table|div) class="msg timestamp">(?:<tr>)?<(?:td|div) class="date".*?</(?:td|div)>(?:</tr>)?</(?:table|div)>')
reMsg = re.compile(r'timet="(\d+)">[\d:]+</(?:td|div)>\s*<(?:td|div) class="src"> ([^<]+)</(?:td|div)><(?:td|div) class="contents"> ?(.*)</td></tr></table>')
reUrl = re.compile(r'<a href="([^"]+)" target="_blank">\1</a>')

endtag = "</td></tr></table>"

current = ''
for line in fileinput.input():
    current += line.strip()
    if not current.endswith(endtag):
        continue

    m = reMsg.search(current)
    if not m:
        print("PROBLEM: '''%s'''" % current)
        break
    t, src, msg = m.groups()
    ts = time.localtime(int(t))
    print('%s %s %s' % (time.strftime('%Y-%m-%d %H:%M', ts), src, msg))
    current = ''
