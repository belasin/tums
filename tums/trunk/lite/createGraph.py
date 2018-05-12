#!/usr/bin/python
import os

BACKGROUND = "#ffffff"

class rrdGraph(object):
    portCache = {}

    def __init__(self, title, type, gprintSplit = "\j", splitEvery = 2):
        self.defs = {}
        self.names = []
        self.gprints = {}
        self.areas = {}
        self.title = title
        self.type = type
        self.gprintSplit = gprintSplit
        self.splitEvery = splitEvery

    def resolvePort(self, port):
        """Get the canonical ARIN name for a port"""
        if not self.portCache:
            ports = open('/etc/services', 'r')
            for ln in ports:
                l = ln.strip()
                if l and l[0] != "#":
                    defn = l.split()
                    self.portCache[int(defn[1].split('/')[0])] = defn[0]
            self.portCache[9680] = 'Thusa Thebe'
            self.portCache[9682] = 'Thusa TUMS'
            self.portCache[9682] = 'Thusa NetFlow Concentrator'
            self.portCache[65535] = 'Unknown Services'

        try:
            p = int(port)
        except:
            return port

        return self.portCache.get(p, str(p))

    def addData(self, name, color, cdef="", label = None, inverse=False, stack=""):
        self.names.append(name)
        
        if inverse:
            cdef = " \"CDEF:%s=0,%s,-,1024,/\" " % (name+'new',name)
            cdef += " \"CDEF:%s=%s,1024,/\" " % (name+'gpr', name)
        else:
            if not label: # only CDEF if it's a bandwidth graph
                cdef = " \"CDEF:%s=%s,1024,/\" " % (name+'new', name)

        self.defs[name] = "\"DEF:%s=/usr/local/tcs/tums/rrd/%s.rrd:%s:AVERAGE\"" % (name, name, name) + cdef
        nlabel = label
        if not label:
            port = name.split('-')[-1]
            nlabel = self.resolvePort(port)
        
        nl=""
        if (len(self.defs)%self.splitEvery)==0:
            nl = self.gprintSplit

        if not label:
            if inverse:
                nlabel += " Out"
            else:
                nlabel += " In"
        if not label:
            name2 = name+'new'
        else:
            name2 = name

        if 'total' in name:
            self.areas[name] = "AREA:%s%s:%s" % (name2, color, nlabel)
        else:
            self.areas[name] = "AREA:%s%s:%s%s" % (name2, color, nlabel, stack)
        if inverse:
            name2 = name+'gpr'
        self.gprints[name] = "GPRINT:%s:AVERAGE:Average\: %%2.1lf%s%s" % (name2, self.type, nl)

    def createGraph(self, file, time="-24h", yaxis = "Data in/out KBps", thumbnail=False):
        colors = "-c SHADEA%s -c SHADEB%s -c BACK%s -c CANVAS%s"  % (BACKGROUND, BACKGROUND, BACKGROUND, "#fee8d0")
        w = 600
        h = 320
        if thumbnail:
            w = 300
            h = 120

        cmd = "rrdtool graph %s %s -v \"%s\" -E -Y -X 0 -a PNG -w %s -h %s -s %s --title=\"%s\" " % (file, colors, yaxis, w, h, time, self.title)
        defs = ""
        for name in self.names:
            item = self.defs[name]
            defs += "%s  " % (item)

        for name in self.names:
            item = self.areas[name]
            gprint = self.gprints[name]
            defs += "\"%s\" \"%s\" " % (item, gprint)

        os.system(cmd+defs)
        #os.system("convert /tmp/tmp.png -crop 680x600+0+0 %s" % (file))
        #os.system("rm /tmp/tmp.png")

"""graph = rrdGraph()
#graph.addData('lcpo-22', '#ff0')
graph.addData('lcpi-22', '#ff0')
graph.createGraph('test.png')"""

rrds = []
# We try and get priority information on first on this graph..
primary = ['total','25', '143', '443', '80', '110']
portcolors = {
    '25'   :    '#d80fca', # Thusa pink
    '80'   :    '#fcaa34', # Thusa yellow - dark
    '443'  :    '#ffd68c', # TUMS dark orange
    'total'  :    '#ffdec9', # TUMS light orangeA
    '110'  :    '#43fab2', # Special green
    '143':    '#b898fa', # Special purple
}

portcolors = {
    'total': '#EC9D48',
    '25': '#ECD748',
    '80': '#54EC48',
    '443': '#48C4EC',
    '110': '#DE48EC',
    '143': '#7648EC',
}
for i,d,files in os.walk('/usr/local/tcs/tums/rrd/'):
    for l in files:
        if '.rrd' in l and 'lcpo' in l:
            rrds.append(l)

# We start by cleaning these graphs by running the spike remover over them.
os.system("for i in /usr/local/tcs/tums/rrd/*; do /usr/local/tcs/tums/removespikes.pl -l 15 $i; done;");

mainGraph = rrdGraph("Bandwidth Usage - Common Ports", "KBps")
for l in primary:
    name = 'lcpo-%s.rrd' % l
    name2 = 'lcpi-%s.rrd' % l 
    if name in rrds:
        rrd = name
        name = rrd.split('.')[0]
        rrd2 = name2
        name2 = rrd2.split('.')[0]
        port = name.split('-')[-1]
        mainGraph.addData(name, portcolors[port])
        mainGraph.addData(name2, portcolors[port], inverse=True)

mainGraph.createGraph('/usr/local/tcs/tums/images/graphs/totalsF.png', "-5h")
mainGraph.createGraph('/usr/local/tcs/tums/images/graphs/totalsFS.png', "-5h", thumbnail=True)
mainGraph.createGraph('/usr/local/tcs/tums/images/graphs/totals.png')
mainGraph.createGraph('/usr/local/tcs/tums/images/graphs/totalsw.png', time="-1w")
mainGraph.createGraph('/usr/local/tcs/tums/images/graphs/totalsm.png', time="-1m")
mainGraph.createGraph('/usr/local/tcs/tums/images/graphs/totalsy.png', time="-356d")

for rrd in rrds:
    name = rrd.split('.')[0]
    port = name.split('-')[-1]
    graph = rrdGraph("Bandwidth Usage - Port %s" % port, "KBps")
    graph.addData(name, "#fcaa34")
    graph.addData('lcpi-%s' % port, "#fcaa34", inverse=True)
    graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%s.png' % port)
    graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%sw.png' % port, "-1w")
    graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%sm.png' % port, "-1m")
    graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%sy.png' % port, "-365d")
    graph = None

# Create load graph
graph = rrdGraph("System Load", "", splitEvery = 1)
graph.addData('sysload-5', '#d80fca',  label = "1 Minute")
graph.addData('sysload-10', '#fcaa34', label = "5 Minute")
graph.addData('sysload-15', '#ffd68c', label = "15 Minute")

graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-loadF.png', "-5h", "")
graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-loadFS.png', "-5h", "", thumbnail=True)
graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-load.png', yaxis="")
graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-loadw.png', "-1w", "")
graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-loadm.png', "-1m", "")
graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-loady.png', "-365d", "")

graph = rrdGraph("System IO", "", splitEvery = 1)
graph.addData('iobi', '#d80fca',  label = "IO In")
graph.addData('iobo', '#fcaa34', label = "IO Out")

graph.createGraph('/usr/local/tcs/tums/images/graphs/ioF.png',"-5h", yaxis="Blocks/s")
graph.createGraph('/usr/local/tcs/tums/images/graphs/ioFS.png', "-5h", thumbnail=True, yaxis="Blocks/s")
graph.createGraph('/usr/local/tcs/tums/images/graphs/io.png', yaxis="Blocks/s")
graph.createGraph('/usr/local/tcs/tums/images/graphs/iow.png', "-1w", yaxis="Blocks/s")
graph.createGraph('/usr/local/tcs/tums/images/graphs/iom.png', "-1m", yaxis="Blocks/s")
graph.createGraph('/usr/local/tcs/tums/images/graphs/ioy.png', "-365d", yaxis="Blocks/s")

# Cleanup
os.system("rm /tmp/matapicos.dump.*")
os.system("rm /usr/local/tcs/tums/rrd/*.old")
