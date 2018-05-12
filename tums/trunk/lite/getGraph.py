#!/usr/bin/python
import datetime, time, os

today = datetime.datetime.now()

a_day = 60*60*24
now = int(time.time())

RRAs = [
    'RRA:AVERAGE:0.5:1:600',
    'RRA:AVERAGE:0.5:6:700',
    'RRA:AVERAGE:0.5:24:775',
    'RRA:AVERAGE:0.5:288:797',
]

def getipac(name):
    inn = os.popen('iptables -L %s_in -v -x -t filter' % name).read().split('\n')
    out = os.popen('iptables -L %s_out -v -x -t filter' % name).read().split('\n')
    
    trin = int(inn[2].strip().split()[1])
    trout = int(out[2].strip().split()[1])
    return trout, trin


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

accounts = {
    80: 'http', 
    143: 'imap', 
    110: 'pop',
    25: 'smtp',
    443: 'https',
    22: 'ssh'
}

for port, name in accounts.items():
    try:
        stats = getipac(name)
        createRRD('lcpo-%s' % port)
        createRRD('lcpi-%s' % port)
        updateRRA('lcpo-%s' % port, now, stats[0])
        updateRRA('lcpi-%s' % port, now, stats[1])
    except:
        print "No ipac entry :("


(totalo, totali) = getipac('total')

createRRD('lcpo-total')
createRRD('lcpi-total')
updateRRA('lcpo-total', now, totalo)
updateRRA('lcpi-total', now, totali)

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






