#!/usr/bin/python
import os, sys

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

    def addData(self, name, color, cdef="", label = None, inverse=False, stack="", override=False):
        self.names.append(name)
        
        if inverse:
            # Make the inverse negative on the graph
            cdef = " \"CDEF:%s=0,%s,-,1000,/\" " % (name+'new',name)
            # Make the GPrint positive 
            cdef += " \"CDEF:%s=%s,1000,/\" " % (name+'gpr', name)
        else:
            if not label or override: # only CDEF if it's a bandwidth graph
                cdef = " \"CDEF:%s=%s,1000,/\" " % (name+'new', name)

        self.defs[name] = "\"DEF:%s=/usr/local/tcs/tums/rrd/%s.rrd:%s:AVERAGE\"" % (name, name, name) + cdef
        nlabel = label
        if not label:
            port = name.split('-')[-1]
            nlabel = self.resolvePort(port)
        
        nl=""
        if (len(self.defs)%self.splitEvery)==0:
            nl = self.gprintSplit

        if not label:
            # then make one.
            if inverse:
                nlabel += " Out"
            else:
                nlabel += " In"

        if not label or override:
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
        colors = "-c SHADEA%s -c SHADEB%s -c BACK%s -c CANVAS%s"  % (BACKGROUND, BACKGROUND, BACKGROUND, BACKGROUND)
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

portcolorsin = {
    'total': '#a15c12',
    '25':    '#baa302',
    '80':    '#0da102',
    '443':   '#1492ba',
    '110':   '#a802b9',
    '143':   '#4315ba',
}

ifaces = []

for i,d,files in os.walk('/usr/local/tcs/tums/rrd/'):
    for l in files:
        if '.rrd' in l and 'lcpo' in l:
            rrds.append(l)
        elif '.rrd' in l and 'iface_' in l:
            iface = l.split('_')[1]
            if iface not in ifaces:
                ifaces.append(iface)

# We start by cleaning these graphs by running the spike remover over them.
#os.system("for i in /usr/local/tcs/tums/rrd/*; do /usr/local/tcs/tums/removespikes.pl -l 1 $i; done;");
def IntBW():
    for rrd in rrds:
        name = rrd.split('.')[0]
        port = name
        graph = rrdGraph("Bandwidth Usage - %s" % port, "KBps")
        graph.addData(name, portcolors['80'])
        graph.addData('lcpi-%s' % port, portcolorsin['80'], inverse=True)
        graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%s.png' % port)
        graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%sw.png' % port, "-1w")
        graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%sm.png' % port, "-1m")
        graph.createGraph('/usr/local/tcs/tums/images/graphs/graph-%sy.png' % port, "-365d")
        graph = None

IntBW()

for rrd in ifaces:
    face = rrd

    graph = rrdGraph("Total Traffic - Network Interface %s" % face, "KBps")
    graph.addData('iface_%s_out' % rrd, portcolors['443'], label = "Out", override=True)
    graph.addData('iface_%s_in' % rrd, portcolorsin['443'], inverse=True, label = "In", override = True)
    # Create the small graph first with a shorter heading
    graph.title = "Traffic - %s" % face
    graph.createGraph('/usr/local/tcs/tums/images/graphs/iface-%sFS.png'% rrd, "-5h", "", thumbnail=True)
    # Then the large graphs
    graph.title = "Total Traffic - Network Interface %s" % face
    graph.createGraph('/usr/local/tcs/tums/images/graphs/iface-%sF.png' % rrd, "-5h", "")
    graph.createGraph('/usr/local/tcs/tums/images/graphs/iface-%s.png'  % rrd)
    graph.createGraph('/usr/local/tcs/tums/images/graphs/iface-%sw.png' % rrd, "-1w")
    graph.createGraph('/usr/local/tcs/tums/images/graphs/iface-%sm.png' % rrd, "-1m")
    graph.createGraph('/usr/local/tcs/tums/images/graphs/iface-%sy.png' % rrd, "-365d")
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

# IO graph
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
