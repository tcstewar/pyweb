import js
import time

jq = js.jQuery

print(time.ctime())

jq.get('index.py', lambda *x: print(x[0]))
