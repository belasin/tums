import traceback

try:
    # a fuckup
    l = 1 + "asd"

except Exception, e:
    l = traceback.format_exc()

print repr(l)
