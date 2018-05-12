from lib import system
import os 
import Settings

RRAs = [
    'RRA:AVERAGE:0.5:1:600',
    'RRA:AVERAGE:0.5:6:700',
    'RRA:AVERAGE:0.5:24:775',
    'RRA:AVERAGE:0.5:288:797',
]

rrdpath = Settings.BaseDir+"rrd/"

def updateRRACMD(source, name, time, value, gauge = False):
    fname = '%s%s/%s.rrd' % (rrdpath, source, name)

    def doUpdate(_):
        updatecmd = "rrdtool update %s %s:%s" % (fname, time, value)
        return updatecmd

    if os.path.exists(fname):
        return doUpdate(None)
    else:
        createcmd = "mkdir -p %s%s; rrdtool create %s --start %s DS:%s:%s:600:U:U " + ' '.join(RRAs)
        if gauge:
            type = "GAUGE"
        else:
            type = "COUNTER"
        return createcmd % (rrdpath, source, fname, time, name, type)

def updateRRA(source, name, time, value, gauge = False):
    fname = '%s%s/%s.rrd' % (rrdpath, source, name)

    def done(l):
        return True
    
    def doUpdate(_):
        updatecmd = "rrdtool update %s %s:%s" % (fname, time, value)
        return system.system(updatecmd).addCallback(done)


    if os.path.exists(fname):
        return doUpdate(None)
    else:
        createcmd = "mkdir -p %s%s; rrdtool create %s --start %s DS:%s:%s:600:U:U " + ' '.join(RRAs)
        if gauge:
            type = "GAUGE"
        else:
            type = "COUNTER"
        return system.system(createcmd % (rrdpath, source, fname, time, name, type)).addCallback(doUpdate)
