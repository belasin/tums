#!/usr/bin/python
import datetime, time, os, sys
from Core import Utils
today = datetime.datetime.now()

a_day = 60*60*24
now = int(time.time())

RRAs = [
    'RRA:AVERAGE:0.5:1:600',
    'RRA:AVERAGE:0.5:6:700',
    'RRA:AVERAGE:0.5:24:775',
    'RRA:AVERAGE:0.5:288:797',
]

def createRRD(name, gauge = False):
    try:
        fp = open('/usr/local/tcs/tums/rrd/%s.rrd' % name)
        fp.close()
        return  0 
    except:
        pass
    createcmd = "rrdtool create /usr/local/tcs/tums/rrd/%s.rrd --start %s DS:%s:%s:600:U:U " + ' '.join(RRAs)
    if gauge:
        type = "GAUGE"
    else:
        type = "COUNTER"
    os.system(createcmd % (name, now, name, type))

def updateRRA(name, time, value):
    updatecmd = "rrdtool update /usr/local/tcs/tums/rrd/%s.rrd %s:%s" % (name, time, value)
    os.system(updatecmd)


# Load details
createRRD('sysload-5',  True)
createRRD('sysload-10', True)
createRRD('sysload-15', True)
l = os.popen('uptime').read()
l.strip('\n')
# 10:49:19 up 15 days, 23:21,  6 users,  load average: 0.83, 0.41, 0.35
#    0     1  2   3     4      5  6      7      8        9    10    11
p = l.split(':')[-1].split()
m5 = float(p[0].strip(','))
m10 = float(p[1].strip(','))
m15 = float(p[2])
updateRRA('sysload-5', now, m5)
updateRRA('sysload-10', now, m10)
updateRRA('sysload-15', now, m15)

# IO Details
createRRD('iobi', True)
createRRD('iobo', True)
l = os.popen('vmstat').read().split('\n')
p = l[2].strip().split()
updateRRA('iobi', now, int(p[8]))
updateRRA('iobo', now, int(p[9]))

def sumRRA(rra, timeframe):
    fetch = "/usr/bin/rrdtool fetch /usr/local/tcs/tums/rrd/%s AVERAGE -r 300 -s -%s"
    l = os.popen(fetch % (rra, timeframe))
    total = 0
    timediv = 1
    for i in l:
        if i.replace('\n', '').strip() and ':' in i:
            this = i.split(':')[-1].strip()
            if 'nan' in this:
                value = 0
            else:
                value = float(this)

            if total > 0:
                # After the first zero value only apply the average of bps over 5 minutes
                # to estimate the real consumption for that 5 minutes
                timediv = 300
            total += value * timediv
    return total

for iface, vals in Utils.getIFStat().items():
    tin, tout = vals
    createRRD('iface_%s_in' % iface)
    createRRD('iface_%s_out' % iface)

    updateRRA('iface_%s_in' % iface, now, int(tin))
    updateRRA('iface_%s_out' % iface, now, int(tout))
    
