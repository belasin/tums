from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime, os, sys
import Tree, Settings, Database
from Core import PageHelpers, Utils, WebUtils
from Pages import Reports

class Page(Reports.Page):
    docFactory  = loaders.xmlfile('overview.xml', templateDir=Settings.BaseDir+'/templates')

    def roundedBlock(self, image, title, content):
        return tags.div(_class="roundedBlock")[tags.img(src='/images/%s' % image), tags.h1[title],tags.div[content]]

    def yearGraph(self, iface, stat):
        # This guy generates an image tag which makes a pyCha 
        
        inset = []
        outset = []
        lables = []

        tmax = max([i[1] for i in stat])
        tmaxo = max([i[0] for i in stat])
        if tmaxo > tmax:
            tmax = tmaxo

        if tmax > 1000:
            off = 1000
            cstart = "/chart?type=line&width=500&height=200&ylab=Data+volume+(GBytes)&legright=y"
        else:
            off = 1
            cstart = "/chart?type=line&width=500&height=200&ylab=Data+volume+(MBytes)&legright=y"

        for data in stat:
            inset.append(data[0]/off)
            outset.append(data[1]/off)
            lables.append('%.2d %s' % (data[3], data[2]))

        cstart += "&set=In&data=%s" % ('+'.join([str(i) for i in inset]))
        cstart += "&set=Out&data=%s" % ('+'.join([str(i) for i in outset]))
        
        for lable in lables:
            cstart += "&lables=%s" % lable

        return tags.img(src=cstart)

    def getStats(self):
        # Get rolling monthly stats for 12 months on each interface
        interfaces = Utils.getInterfaces()
        stat = {}
        da = datetime.datetime.now()
        
        year = da.year
        
        stats = os.listdir('/usr/local/tcs/tums/rrd/')
        
        for n in stats:
            if not ((str(year) in n) or (str(year-1) in n)):
                # Ditch superflous years without hesitation
                continue 

            if not 'total' in n:
                continue 

            if n[-4:] != ".nid":
                continue
            # Figure out interface
            iface = n.split('_')[1]

            if '-' in n:
                # Very useful file
                date = n.split('_')[2].replace('-total.nid', '').split('-')
                segYear = int(date[2])
                segMonth = int(date[1])
            else:
                # Try and use this legacy file. 
                date = n.split('_')[2].replace('total.nid', '')
                segYear = int(date[-4:])

                fdate = time.localtime(os.stat('/usr/local/tcs/tums/rrd/%s' % n).st_mtime)
            
                if segYear == fdate[0]:
                    # Probably ok
                    segMonth = fdate[1]
                else:   
                    # Someone has messed with the time stamp on the file :(
                    sm = date[-6:-4]
                    if int(sm) > 12:
                        segMonth = int(sm[1])
                    else:
                        segMonth = int(sm)

            # Grab the contents...
            l = open('/usr/local/tcs/tums/rrd/%s' % n)
            try:
                iin, iout = [int(float(i)/1000000) for i in l.read().strip('\n').strip().split(':')]
            except:
                inn, iout = (0,0)
            
            if iface not in stat:
                stat[iface] = {}

            stamp = "%s%.2d" % (segYear, segMonth)
            if stamp in stat[iface]:
                stat[iface][stamp][0] += iin
                stat[iface][stamp][1] += iout
            else:
                stat[iface][stamp] = [iin, iout, segYear, segMonth]
        
        newstat = {}
        for iface, detail in stat.items():
            dlist = detail.keys()
            dlist.sort()
            # Pick the most recent 12
            ourlist = dlist[-12:]
            newstat[iface] = []

            # Reconstruct an ordered set for each interface instead of an unordered dictionary
            for n in ourlist:
                newstat[iface].append(detail[n])
            
        return newstat

    def render_content(self, ctx, seg):
        ci = open('/proc/cpuinfo')
        cpuInfo = {}
        numCPU = 0
        for i in ci:
            l = i.strip('\n').strip().split(':')
            if "processor" in l[0]:
                numCPU += 1
            else:
                try:
                    cpuInfo[l[0].strip()] = l[1].strip()
                except:
                    pass

        pmi = open('/proc/meminfo')
        memDetail = {}
        for i in pmi:
            l = i.strip('\n').strip()
            if l:
                key, val = tuple(l.split(':'))
                val = val.split()[0]
                
                memDetail[key] = int(val)

        interfaces = Utils.getInterfaces()
        stat = {}
        da = datetime.datetime.now()
        month = "%s-%s" % (da.month, da.year)

        lastmonth = "%s-%s" % (
            (da.month -1 ) or 12,                     # 12th month if current month is 1
            (da.month -1 ) and da.year or da.year - 1 # Previous year if current month is 1
        )

        lastmt = ((da.month -1 ) or 12,(da.month -1 ) and da.year or da.year - 1)

        today = "%s-%s-%s" % (da.day, da.month, da.year)
        yearStats = self.getStats()

        for k,v in yearStats.items():
            stat[k] = {
                '24': [0,0],
                'month': [0,0],
                'lastmonth': [0,0]
            }
            # Read the traffic counters
            try:
                p = open('/usr/local/tcs/tums/rrd/iface_%s_%stotal.nid' % (k, today) ).read().split(':')
                stat[k]['24'] = (float(p[0]), float(p[1])) # Last 24 Hours
            except Exception, e:
                stat[k]['24'] = (0,0)


            for dta in v:
                i,o,y,m = dta
                if m == da.month and y == da.year:
                    stat[k]['month'] = (i*1000000, o*1000000)
                if m == lastmt[0] and y == lastmt[1]:
                    stat[k]['lastmonth'] = (i*1000000,o*1000000)

        return ctx.tag[
            tags.h3[tags.img(src="/images/system.png"), " System Stats"],
            tags.br,
            tags.table(width="100%")[
                tags.tr[
                    tags.td(valign="top")[
                        self.roundedBlock('services-small.png',"CPU", [
                            tags.table[
                                tags.tr[
                                    tags.td["Processors:"],
                                    tags.td[numCPU]
                                ],
                                tags.tr[
                                    tags.td["Model:"],
                                    tags.td[cpuInfo['model name']]
                                ],
                                tags.tr[
                                    tags.td["CPU Speed:"],
                                    tags.td["%0.2fGhz" % (float(cpuInfo['cpu MHz'])/1024.0)]
                                ]
                            ],
                            tags.a(href=url.root.child("Graphs").child("load"))[tags.img(src="/images/graphs/graph-loadFS.png")]
                        ]),
                        self.roundedBlock('services-small.png', "Memory Usage", [
                            tags.table[
                                tags.tr[
                                    tags.td["Total Active:"],
                                    tags.td[PageHelpers.progressBar(memDetail['Active']/float(memDetail['MemTotal']))],
                                ]
                            ],
                            tags.a(href=url.root.child("Graphs").child("io"))[tags.img(src="/images/graphs/ioFS.png")],
                        ]),
                    ]
                ],
                [tags.tr[
                    [tags.td[
                        self.roundedBlock('network-small.png', j, [
                            tags.a(href=url.root.child('Graphs').child('iface-%s' % j))[
                                tags.img(src="/images/graphs/iface-%sFS.png" % j)
                            ],
                            tags.h3["Traffic"],
                            self.yearGraph(j, yearStats[j]), 
                            tags.table(cellpadding=5)[
                                tags.tr(valign="top")[
                                    tags.td[tags.strong["Today: "]],
                                    tags.td[
                                        tags.table(cellspacing=0, cellpadding=0)[
                                            tags.tr[
                                                tags.td["Out: "], tags.td[Utils.intToH(stat[j]['24'][1])],
                                            ],
                                            tags.tr[
                                                tags.td["In: "], tags.td[Utils.intToH(stat[j]['24'][0])]
                                            ]
                                        ]
                                    ]
                                ],
                                tags.tr(valign="top")[
                                    tags.td[tags.strong["This Month: "]],
                                    tags.td[
                                         tags.table(cellspacing=0, cellpadding=0)[
                                            tags.tr[
                                                tags.td["Out: "], tags.td[Utils.intToH(stat[j]['month'][1])],
                                            ],
                                            tags.tr[
                                                tags.td["In: "], tags.td[Utils.intToH(stat[j]['month'][0])]
                                            ]
                                        ]
                                    ]
                                ],
                                tags.tr(valign="top")[
                                    tags.td[tags.strong["Previous Month: "]],
                                    tags.td[
                                         tags.table(cellspacing=0, cellpadding=0)[
                                            tags.tr[
                                                tags.td["Out: "], tags.td[Utils.intToH(stat[j]['lastmonth'][1])],
                                            ],
                                            tags.tr[
                                                tags.td["In: "], tags.td[Utils.intToH(stat[j]['lastmonth'][0])]
                                            ]
                                        ]
                                    ]
                                ],
                            ]
                        ])
                    ] for j in i if j]
                ] for i in WebUtils.runIter(1, stat.keys())]
            ]
        ]
