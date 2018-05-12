from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql
import enamel, os

from nevow import inevow, rend, static, compression, loaders, url, guard

from twisted.internet import utils

from Pages import Users, Thebe, Dashboard, Servers, Commands, DNS, DynDNS, Updates, Account, Orders, Tickets
import Settings
from lib import system

class Login(pages.Standard):
    """ Login this provides our authentication wrapper and login page.
    """

    def document(self):
        baseDir = self.enamel.Settings.BaseDir
        theme = self.enamel.Settings.theme
        self.child_css = static.File('%s/themes/%s/css/' % (baseDir, theme))
        self.child_js  = compression.CompressingResourceWrapper(static.File(baseDir + '/js/'))
        self.child_images = compression.CompressingResourceWrapper(static.File('%s/themes/%s/images/' % (baseDir, theme)))
        return pages.template('login.xml', templateDir='%s/themes/%s/templates/' % (baseDir, theme))

    def render_head(self, ctx, data):
        return tags.title['Login']

    def locateChild(self, ctx, segments):
        """Locates login information for authentication"""
        # wraps our child locator,
        ctx.remember(self, inevow.ICanHandleNotFound)
        return super(Login, self).locateChild(ctx, segments) # pass back to the parent child locator

    def renderHTTP_notFound(self, ctx):
        return url.root

class GraphvizResource(pages.Standard):
    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)

        def outputData(fi):
            request.setHeader("content-type", "image/png")
            request.setHeader("content-length", str(len(fi)))

            return fi

        def renderGraph(servers):
            deadServers = []
            for i in servers:
                name = i[1]
                if name not in self.enamel.tcsMaster.connectedNodes:
                    if name not in self.enamel.tcsMaster.knownNodes:
                        deadServers.append(name)

            l = file(Settings.BaseDir+'ascache').read()
            asCache = eval(l.split(' = ')[-1])

            hosts = {}

            for i in servers:
                name, ip = (i[1], i[4])
                id = int(i[0])
                if not ip:
                    continue
                class_c = '.'.join(ip.split('.')[:3])
                if class_c in asCache.keys():
                    if asCache[class_c][0] not in hosts:
                        hosts[asCache[class_c][0]] = []
                    hosts[asCache[class_c][0]].append((name, id))

            nodes = []
            relations = []
            asns = {}
            for k,v in asCache.items():
                asns[v[0]] = v[1]

            for AS, host in hosts.items():
                N = asns[AS].split()[0]
                nodes.append(
                    '  AS_%s [label="%s"];' % (AS, N)
                )
                for h, id in host:
                    colour = h in deadServers and "#ff0000" or "#00ff00"
                    nodes.append(
                        '  "%s" [label="%s", color="%s", style=filled, href="/Servers/Manage/%s"];' % (h, h, colour, id)
                    )
                    relations.append('  AS_%s -- "%s";' % (AS, h))

            l = hosts.keys()
            # Create circular reference
            relations.append('  AS_%s -- AS_%s;' % (l[-1], l[0]))
            lastAS = l[0]
            for AS in l[1:]:
                relations.append('  AS_%s -- AS_%s;' % (lastAS, AS))
                lastAS = AS

            graph = """graph G {
              graph[rankdir="LR"];
              node[shape=rect,fontsize=14, height=0.1, width=2];
              ranksep=3;
              ratio=auto;
              %s
              %s
            }\n""" % ('\n'.join(relations), '\n'.join(nodes))

            l = file(Settings.BaseDir+'tmp.dot', 'wt')
            l.write(graph)

            return system.system('/usr/bin/neato -Tsvg %stmp.dot | rsvg-convert -z 0.3 -f png' % (Settings.BaseDir)).addCallback(outputData)
            return system.system('/usr/bin/fdp -Tsvg %stmp.dot' % (Settings.BaseDir)).addCallback(outputData)

        return self.enamel.storage.getServersInGroup(self.avatarId.gids).addCallback(renderGraph)

class ImageResource(rend.Page):
    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)

        def outputData(fi):
            request.setHeader("content-type", "image/png")
            request.setHeader("content-length", str(len(fi)))

            return fi

        getArgs = request.args
        
        source = getArgs['source'][0]
        type = getArgs['type'][0]
        timeframe = getArgs['timeframe'][0]
        height = getArgs.get('height', ['170'])[0]
        width = getArgs.get('width', ['550'])[0]
        noGprint = getArgs.get('nog', [''])[0] == "yes"
        
        rrdpath = Settings.BaseDir+"rrd"

        if type == "inetglobal":
            rrdcmd = """rrdtool graph - -E --imgformat 'PNG' --height %(height)s --width %(width)s  \
                --color SHADEA#ffffff --color SHADEB#ffffff --color BACK#ffffff --color CANVAS#ffffff """ % {'height':height, 'width':width}
            dsList = []
            for path,v,filel in os.walk(rrdpath):
                for file in filel:
                    if file[-3:] == "rrd":
                        if "eth" in file or "ppp" in file:
                            dsList.append((path+'/'+file, file[:-4]))

            defs = ""
            num = 0
            cdef = ""
            idsnList = []
            odsnList = []
            for i in dsList:
                num += 1
                if i[1][-1] == 'i':
                    idsnList.append( "ds%s" % (num))
                else:
                    odsnList.append("ds%s" % (num))
                defs += " 'DEF:vds%(num)s=%(rrd)s:%(dsname)s:AVERAGE' \\\n" % {
                    'num': num,
                    'dsname': i[1],
                    'rrd': i[0],
                }
                cdef += " 'CDEF:ds%(num)s=vds%(num)s,UN,0,vds%(num)s,IF' \\\n " % { 'num': num } 
            # Construct a cdef to add all the data sources

            cdef += ' \'CDEF:itotal=1,' + ',+,'.join(idsnList) + ',+\''
            cdef += ' \'CDEF:ototal=1,' + ',+,'.join(odsnList) + ',+\''

            represent = " 'AREA:itotal#00FF00:Download' 'LINE1:ototal#0000FF:Upload' "

            rrdcmd += defs + cdef.strip(',') + represent
            rrdcmd += "-s %s" % timeframe

        elif type == "net":
            rrdcmd = """rrdtool graph - -E --imgformat 'PNG' --height %(height)s --width %(width)s  \
                --color SHADEA#ffffff --color SHADEB#ffffff --color BACK#ffffff --color CANVAS#ffffff \
                'DEF:A=%(rrdpath)s/%(source)s/iface-eth1i.rrd:iface-eth1i:AVERAGE' \
                'DEF:B=%(rrdpath)s/%(source)s/iface-eth1o.rrd:iface-eth1o:AVERAGE' \
            """ % {'height':height, 'width':width, 'source':source, 'rrdpath':rrdpath}

            comments = """ 'AREA:A#0000FF:Download' \
            'GPRINT:A:MIN:(min=%%.0lf' 'GPRINT:A:AVERAGE:ave=%%.0lf' 'GPRINT:A:MAX:max=%%.0lf)' \
            'COMMENT:\\n' \
            'LINE1:B#00FF00:Upload' \
            'GPRINT:B:MIN:(min=%%.0lf' 'GPRINT:B:AVERAGE:ave=%%.0lf' 'GPRINT:B:MAX:max=%%.0lf)' \
            """
            
            if noGprint:
                rrdcmd += " 'AREA:A#0000FF:Download' 'LINE1:B#00FF00:Upload' "
                rrdcmd += " -g -s %s" % timeframe
            else:
                rrdcmd += comments
                rrdcmd += " -g -s %s" % timeframe

            print rrdcmd

        elif type == "load":
            rrdcmd = """rrdtool graph - -E --imgformat 'PNG' --height %(height)s --width %(width)s \
                --color SHADEA#ffffff --color SHADEB#ffffff --color BACK#ffffff --color CANVAS#ffffff \
                'DEF:A=%(rrdpath)s/%(source)s/load-5.rrd:load-5:AVERAGE' \
                'DEF:B=%(rrdpath)s/%(source)s/load-10.rrd:load-10:AVERAGE' \
                'DEF:C=%(rrdpath)s/%(source)s/load-15.rrd:load-15:AVERAGE' \
            """ % {'source':source, 'rrdpath':rrdpath, 'timeframe':timeframe, 'height':height, 'width':width}

            comments =  """                'LINE1:A#00FF00: 5 Minute' \
                'GPRINT:A:MIN:(min=%%.0lf' 'GPRINT:A:AVERAGE:ave=%%.0lf' 'GPRINT:A:MAX:max=%%.0lf)' \
                'COMMENT:\\n' \
                'LINE1:B#0000FF:10 Minute' \
                'GPRINT:B:MIN:(min=%%.0lf' 'GPRINT:B:AVERAGE:ave=%%.0lf' 'GPRINT:B:MAX:max=%%.0lf)' \
                'COMMENT:\\n' \
                'LINE1:C#FF0000:15 Minute' \
                'GPRINT:C:MIN:(min=%%.0lf' 'GPRINT:C:AVERAGE:ave=%%.0lf' 'GPRINT:C:MAX:max=%%.0lf)' \
                'COMMENT:\\n' -s %(timeframe)s
            """ % {'source':source, 'rrdpath':rrdpath, 'timeframe':timeframe, 'height':height, 'width':width}

            if noGprint:    
                rrdcmd += "'LINE1:A#00FF00: 5 Minute' 'LINE1:B#0000FF:10 Minute' 'LINE1:C#FF0000:15 Minute' "
                rrdcmd += " -g -s %s" % timeframe
            else:
                rrdcmd += comments
                rrdcmd += " -g -s %s" % timeframe

        elif type == "exim":
            rrdcmd = """rrdtool graph - -E -Y -X 0 --imgformat 'PNG' --height %(height)s --width %(width)s -v 'Mails per minute' \
                --color SHADEA#ffffff --color SHADEB#ffffff --color BACK#ffffff --color CANVAS#ffffff \
                'DEF:AA=%(rrdpath)s/%(source)s/exim-rcvd.rrd:exim-rcvd:AVERAGE' \
                'DEF:BB=%(rrdpath)s/%(source)s/exim-delv.rrd:exim-delv:AVERAGE' \
                'DEF:CC=%(rrdpath)s/%(source)s/exim-rejc.rrd:exim-rejc:AVERAGE' \
                'CDEF:A=AA,60,*' 'CDEF:B=BB,60,*' 'CDEF:C=CC,60,*' \
                'AREA:A#00FF00:Recieved Mail' \
                'GPRINT:A:MIN:(min=%%.0lf' 'GPRINT:A:AVERAGE:ave=%%.0lf' 'GPRINT:A:MAX:max=%%.0lf)' \
                'COMMENT:\\n' \
                'LINE1:B#0000FF:Delivered Mail' \
                'GPRINT:B:MIN:(min=%%.0lf' 'GPRINT:B:AVERAGE:ave=%%.0lf' 'GPRINT:B:MAX:max=%%.0lf)' \
                'COMMENT:\\n' \
                'LINE1:C#FF0000:Rejected Mail' \
                'GPRINT:C:MIN:(min=%%.0lf' 'GPRINT:C:AVERAGE:ave=%%.0lf' 'GPRINT:C:MAX:max=%%.0lf)' \
                'COMMENT:\\n' -s %(timeframe)s
            """ % {'source':source, 'rrdpath':rrdpath, 'timeframe':timeframe, 'height':height, 'width':width}

        elif type == "latency":
            def cont(data):
                max = 0
                for i in data.split('\n'):
                    if "No such file" in i:
                        continue
                    if i:
                        n = i.split(': ')[-1].replace('nan', '0.0').split()
                        for x in n[2:]:
                            if float(x) > max: 
                                max = float(x)
                #max = 0.45841725
                print max
                defs = ""
                cdefs = ""
                areas = ""
                hostname = source
                colours = [
                    'f0f0f0', 'dddddd', 'cacaca', 'b7b7b7',
                    'a4a4a4', '919191', '7e7e7e', '6b6b6b',
                    '585858', '454545', '535353', '666666',
                    '797979', '8c8c8c', '9f9f9f', 'b2b2b2',
                    'c5c5c5', 'd8d8d8', 'ebebeb', 'fefefe'
                ]

                for i in range(1,21):
                    defs += "'DEF:ping%s=/var/lib/smokeping/THEBE/%s.rrd:ping%s:AVERAGE' " % (i, hostname, i)
                for i in reversed(range(1,21)):
                    cdefs += "'CDEF:cp%s=ping%s,0,%s,LIMIT' "   % (i, i, max)
                    areas += "'AREA:cp%s#%s' " % (i, colours[20-i])

                rrdcmd = """rrdtool graph - -s %(timeframe)s -E --height %(height)s --width %(width)s \\
                    --rigid --upper-limit %(max)s --lower-limit 0 --vertical-label Seconds --imgformat PNG \\
                    --color SHADEA#ffffff --color SHADEB#ffffff --color BACK#ffffff --color CANVAS#ffffff \\
                    %(def)s \\
                    %(cdef)s \\
                    %(area)s \\
                    'DEF:median=/var/lib/smokeping/THEBE/%(h)s.rrd:median:AVERAGE' \\
                    'DEF:loss=/var/lib/smokeping/THEBE/%(h)s.rrd:loss:AVERAGE' \\
                    'CDEF:ploss=loss,20,/,100,*' 'GPRINT:median:AVERAGE:Median Ping RTT (%%.1lf %%ss avg)' 'LINE1:median#202020' \\
                    'CDEF:me0=loss,-1,GT,loss,0,LE,*,1,UNKN,IF,median,*' 'CDEF:meL0=me0,%(swidth)s,-' \\
                    'CDEF:meH0=me0,0,*,%(swidth)s,2,*,+' 'AREA:meL0' 'STACK:meH0#26ff00:0' \\
                    'CDEF:me1=loss,0,GT,loss,1,LE,*,1,UNKN,IF,median,*' 'CDEF:meL1=me1,%(swidth)s,-' \\
                    'CDEF:meH1=me1,0,*,%(swidth)s,2,*,+' 'AREA:meL1' 'STACK:meH1#00b8ff:1/20' \\
                    'CDEF:me2=loss,1,GT,loss,2,LE,*,1,UNKN,IF,median,*' 'CDEF:meL2=me2,%(swidth)s,-' \\
                    'CDEF:meH2=me2,0,*,%(swidth)s,2,*,+' 'AREA:meL2' 'STACK:meH2#0059ff:2/20' \\
                    'CDEF:me3=loss,2,GT,loss,3,LE,*,1,UNKN,IF,median,*' 'CDEF:meL3=me3,%(swidth)s,-' \\
                    'CDEF:meH3=me3,0,*,%(swidth)s,2,*,+' 'AREA:meL3' 'STACK:meH3#5e00ff:3/20' \\
                    'CDEF:me4=loss,3,GT,loss,4,LE,*,1,UNKN,IF,median,*' 'CDEF:meL4=me4,%(swidth)s,-' \\
                    'CDEF:meH4=me4,0,*,%(swidth)s,2,*,+' 'AREA:meL4' 'STACK:meH4#7e00ff:4/20' \\
                    'CDEF:me10=loss,4,GT,loss,10,LE,*,1,UNKN,IF,median,*' 'CDEF:meL10=me10,%(swidth)s,-' \\
                    'CDEF:meH10=me10,0,*,%(swidth)s,2,*,+' 'AREA:meL10' 'STACK:meH10#dd00ff:10/20' \\
                    'CDEF:me19=loss,10,GT,loss,19,LE,*,1,UNKN,IF,median,*' 'CDEF:meL19=me19,%(swidth)s,-' \\
                    'CDEF:meH19=me19,0,*,%(swidth)s,2,*,+' 'AREA:meL19' 'STACK:meH19#ff0000:19/20' \\
                    'COMMENT:\\l' 'GPRINT:ploss:AVERAGE:Packet Loss\\: %%.2lf %%%% average' \\
                    'GPRINT:ploss:MAX:%%.2lf %%%% maximum' 'GPRINT:ploss:LAST:%%.2lf %%%% current\\l' \\
                    HRULE:0#000000 'COMMENT:\\s' 'COMMENT:Probe\\: 20 ICMP Echo Pings (56 Bytes) every 300 seconds'""" % {
                        'h': hostname,
                        'swidth': max/170.0,
                        'max': max,
                        'def': defs, 'cdef': cdefs, 'area': areas, 'timeframe':timeframe,
                        'height':height, 'width':width
                    }
                return system.system(rrdcmd).addCallback(outputData)
            return system.system("rrdtool fetch /var/lib/smokeping/THEBE/%s.rrd AVERAGE -s -24h | grep \":\"" % source).addCallback(
                cont
            )
        return system.system(rrdcmd).addCallback(outputData)

class Index(pages.Standard):
    childPages = {
        'ServerUsers':Users.Page,
        'Thebe':Thebe.Page,
        'Servers': Servers.Page,
        'Dashboard': Dashboard.Page,
        'Commands': Commands.Page,
        'Updates': Updates.Page,
        'Account': Account.Page,
        'RRD': ImageResource,
        'Sexy': GraphvizResource,
        'DNS': DNS.Page,
        'nic': DynDNS.Page,
        'Orders': Orders.Page,
        'Tickets': Tickets.Page
    }

    def __init__(self, *a, **kw):
        pages.Standard.__init__(self, *a, **kw)

    def document(self):
        baseDir = self.enamel.Settings.BaseDir
        theme = self.enamel.Settings.theme
        # Images, javascript and CSS locations
        # derived from base directory and theme 
        self.child_css = static.File('%s/themes/%s/css/' % (baseDir, theme))
        self.child_js  = compression.CompressingResourceWrapper(static.File(baseDir + '/js/'))
        self.child_images = compression.CompressingResourceWrapper(static.File('%s/themes/%s/images/' % (baseDir, theme)))

        return pages.stan(
                    tags.html[
                        tags.head[
                            tags.title["TUMS"],
                            tags.xml('<meta http-equiv="refresh" content="0;url=Dashboard/"/>')
                        ],
                        tags.body[ 
                            ""
                        ]
                    ]
                )

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Dashboard"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_contentLeft(self, ctx, data):
        return ctx.tag[""
        ]

    def render_contentRight(self, ctx, data):
        return ctx.tag[""
        ]
