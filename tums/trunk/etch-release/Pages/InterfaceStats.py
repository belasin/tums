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

    def roundedBlock(self, title, content):
        return tags.div(_class="roundedBlock")[tags.img(src="/images/network-small.png"), tags.h1[title],tags.div[content]]

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
            date = n.split('_')[2].replace('total.nid', '')
            segYear = int(date[-4:])

            date = time.localtime(os.stat('/usr/local/tcs/tums/rrd/%s' % n).st_mtime)
            
            if segYear == date[0]:
                # Probably ok
                segMonth = date[1]
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
        interfaces = Utils.getInterfaces()
        stat = {}
        da = datetime.datetime.now()
        month = "%s%s" % (da.month, da.year)

        lastmonth = "%s%s" % (
            (da.month -1 ) or 12,                     # 12th month if current month is 1
            (da.month -1 ) and da.year or da.year - 1 # Previous year if current month is 1
        )
        today = "%s%s%s" % (da.day, da.month, da.year)
        for i in interfaces:
            if not 'tap' in i and not 'eth' in i and not 'ppp' in i:
                continue
            stat[i] = {
                '24': [0,0],
                'month': [0,0],
                'lastmonth': [0,0]
            }
            # Read the traffic counters
            try:
                p = open('/usr/local/tcs/tums/rrd/iface_%s_%stotal.nid' % (i, today) ).read().split(':')
                stat[i]['24'] = (float(p[0]), float(p[1])) # Last 24 Hours
                # Try figure out the whole day

                for fi in os.listdir('/usr/local/tcs/tums/rrd/'):

                    if 'iface_%s' % i in fi and "%stotal.nid" % month in fi:
                        p = open('/usr/local/tcs/tums/rrd/'+ fi).read().split(':')
                        for j in xrange(2):
                            stat[i]['month'][j] += float(p[j])

                    if 'iface_%s' % i in fi and "%stotal.nid" % lastmonth in fi:
                        p = open('/usr/local/tcs/tums/rrd/'+ fi).read().split(':')
                        for j in xrange(2):
                            stat[i]['lastmonth'][j] += float(p[j])

            except Exception, e:
                stat[i]['24'] = (0,0)
                stat[i]['month'] = (0,0)

        yearStats = self.getStats()

        return ctx.tag[
            tags.h3[tags.img(src="/images/system.png"), " Interface Statistics"],
            tags.table(width="95%")[
                [tags.tr[
                    [tags.td[
                        self.roundedBlock(j, [
                            tags.img(src="/images/graphs/iface-%sFS.png" % j),
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
