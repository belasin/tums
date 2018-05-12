#!/usr/bin/python
import datetime, time, os
import Database

db = Database.AggregatorDatabase()

today = datetime.datetime.now()
portStats = db.getPortTotals(today.month, today.year, today.day)

a_day = 60*60*24
now = int(time.time())


RRAs = [
    'RRA:AVERAGE:0.5:1:600',
    'RRA:AVERAGE:0.5:6:700',
    'RRA:AVERAGE:0.5:24:775',
    'RRA:AVERAGE:0.5:288:797',
]


def createRRD(name):
    try:
        fp = open('/usr/local/tcs/tums/rrd/%s.rrd' % name)
        fp.close()
        return  0 
    except:
        pass
    createcmd = "rrdtool create /usr/local/tcs/tums/rrd/%s.rrd --start %s DS:%s:COUNTER:600:U:U " + ' '.join(RRAs)
    os.system(createcmd % (name, now, name))

def updateRRA(name, time, value):
    updatecmd = "rrdtool update /usr/local/tcs/tums/rrd/%s.rrd %s:%s" % (name, time, value)
    os.system(updatecmd)

totali, totalo = (0,0) # reset totals

for port, stats in portStats.items():
    exists = False
    print port, stats
    createRRD('lcpo-%s' % port)
    createRRD('lcpi-%s' % port)
    updateRRA('lcpo-%s' % port, now, stats[0])
    updateRRA('lcpi-%s' % port, now, stats[1])
    totali += stats[1]
    totalo += stats[0]

createRRD('lcpo-total')
createRRD('lcpi-total')
updateRRA('lcpo-total', now, totalo)
updateRRA('lcpi-total', now, totali)

