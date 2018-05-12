from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, Database
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, NetUtils, WebUtils
from Pages import Tools, Reports
import formal, datetime

class Page(Reports.Page):
    addSlash = True
    portCache = {}
    flowDb = Database.AggregatorDatabase()

    #docFactory  = loaders.xmlfile('netflow.xml', templateDir=Settings.BaseDir+'/templates')

    def __init__(self, avatarId, db,day=None, month=None, year=None, ip=None, view=None, index=0, *a, **kw):
        if not month:
            today = datetime.datetime.now()
            self.month = today.month
            self.year = today.year
            self.day = 0
        else:
            self.month = month
            self.year = year
        if day:
            if day > 0:
                self.day = day
        else:
            self.day = 0 
    
        self.ip = ip
        self.view = view
        try:
            self.index = int(index)
        except:
            self.index = 0

        Reports.Page.__init__(self, avatarId, db, *a, **kw)

    def form_dateRange(self, ctx):
        form = formal.Form()
        
        months = [(m+1, Utils.months[m+1]) for m in range(12)]
        days = [(0, 'Whole Month')] + [(m+1, m+1) for m in range(31)]
        yearLim = datetime.datetime.now().year
        years = [(y,y) for y in reversed(range(yearLim-3, yearLim+1))]

        form.addField('day', formal.Integer(),
            formal.widgetFactory(formal.SelectChoice, options = days),
            label = "Day")
        
        form.addField('month', formal.Integer(required=True),
            formal.widgetFactory(formal.SelectChoice, options = months),
            label = "Month")

        form.addField('year', formal.Integer(required=True),
            formal.widgetFactory(formal.SelectChoice, options = years),
            label = "Year")

        form.data['month'] = self.month
        form.data['day'] = self.day 
        form.data['year'] = self.year

        form.addAction(self.selectDate)
        return form

    def selectDate(self, ctx, form, data):
        if data['month']:
            self.month = data['month']
        if data['year']:
            self.year = data['year']

        self.day = data['day']

        if self.view and "Host" in self.view:
            return url.root.child('NetworkStats').child(self.view).child(self.ip).child(self.day).child(self.month).child(self.year)
        else:
            if self.view:
                return url.root.child('NetworkStats').child(self.view).child(self.day).child(self.month).child(self.year)
            else:
                return url.root.child('NetworkStats').child(self.day).child(self.month).child(self.year)

    def locateChild(self, ctx, seg):
        try: 
            day = int(seg[1])
            month = int(seg[2])
            year = int(seg[3]) 
        except:
            day = 0 
            month = None
            year = None

        if "Host" == seg[0]:
            try:
                day = int(seg[2])
                month=int(seg[3])
                year=int(seg[4])
            except:
                day = 0 
                month = None
                year = None
            ip = seg[1]
            return Page(self.avatarId, self.db, day, month, year, ip, "Host"), ()

        elif "Ports" == seg[0]:
            return Page(self.avatarId, self.db, day, month, year, None, "Ports"), ()

        elif ("Interface" == seg[0]) or ("InterfacePorts" == seg[0]):
            index = seg[1]
            try:
                day = int(seg[2])
                month=int(seg[3])
                year=int(seg[4])
            except:
                day = 0 
                month = None
                year = None
            return Page(self.avatarId, self.db, day, month, year, None, seg[0], index), ()

        elif "InterfaceIP" == seg[0]:
            index = seg[1]
            ip = seg[2]
            try:
                day = int(seg[3])
                month=int(seg[4])
                year=int(seg[5])
            except:
                day = 0 
                month = None
                year = None
            return Page(self.avatarId, self.db, day, month, year, ip, "InterfaceIP", index), ()

        return Page(self.avatarId, self.db, day, month, year, None, "Overview", None), ()

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
            self.portCache[54321] = 'Thusa HIVE'
            self.portCache[9682] = 'Thusa NetFlow Concentrator'
            self.portCache[65535] = tags.a(href="#us")['Unknown Services*']

        return self.portCache.get(port, str(port))

    def dateStamp(self):
        if self.day>0:
            return "%s %s %s" % (self.day, Utils.months[self.month], self.year)
        else:
            return "%s %s" % (Utils.months[self.month], self.year)

    def render_content(self, ctx, data):
        table = []
        header = []
        title = "?"
        total = 0
        tin = 0 
        tout = 0
        other = []
        extraStats = ""
        internet = None
        if self.ip and self.view == "Host":
            # Render a hosts overview, utilisation by port
            title = "Local Internet Usage by port for %s during %s" % (self.ip.replace('0.0.0.0', 'Vulani Server'), self.dateStamp())
            portStats = self.flowDb.getPortBreakdownForIp(self.month, self.year, self.ip, self.day)
            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]
            for port, inout in portStats.items():
                if (inout[0] + inout[1]) > 1024:
                    table.append([inout[0]+inout[1],self.resolvePort(port), Utils.intToH(inout[0]), Utils.intToH(inout[1])])
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]

        elif self.view == "Ports":
            title = "Local Internet Usage by port for all users during %s" % (self.dateStamp())
            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]
            portStats = self.flowDb.getPortTotals(self.month, self.year, self.day)
            portList = []
            for port, inout in portStats.items():
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]
                if (inout[0] + inout[1]) > 1024:
                    # discard the data if it's not of valuable size
                    table.append([inout[0]+inout[1], self.resolvePort(port), Utils.intToH(inout[0]), Utils.intToH(inout[1])])
                portList.append(port)

            # sort this data before we create the port distribution
            portList.sort()

        elif self.view=="Interface":
            title = "Local Internet Usage by IP or username for all users during %s on interface %s" % (
                self.dateStamp(), 
                Utils.getInterfaceFromIndex(self.sysconf, self.index)
            )
            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]
            ipStats = self.flowDb.getVolumeTotalByIp(self.month, self.year, self.day, self.index)
            for ip, inout in ipStats.items():
                ipn = ip
                if ip == '0.0.0.0':
                    ipn = "Vulani Server"
                    
                table.append([
                    inout[0]+inout[1],
                    tags.a(
                        href=url.root.child("NetworkStats").child("InterfaceIP").child(str(self.index)).child(ip).child(self.day).child(self.month).child(self.year), title="View detail"
                    )[ipn], 
                    Utils.intToH(inout[0]), 
                    Utils.intToH(inout[1])
                ])
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]

        elif self.view=="InterfacePorts":
            title = "Local Internet Usage by port for all users during %s on interface %s" % (
                self.dateStamp(),
                Utils.getInterfaceFromIndex(self.sysconf, self.index)
            )
            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]
            portStats = self.flowDb.getPortTotals(self.month, self.year, self.day, self.index)
            portList = []
            for port, inout in portStats.items():
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]
                if (inout[0] + inout[1]) > 1024:
                    # discard the data if it's not of valuable size
                    table.append([inout[0]+inout[1], self.resolvePort(port), Utils.intToH(inout[0]), Utils.intToH(inout[1])])
                portList.append(port)

            # sort this data before we create the port distribution
            portList.sort()

        elif self.view=="InterfaceIP":
            title = "Local Internet Usage by port for %s during %s on interface %s" % (
                self.ip,
                self.dateStamp(),
                Utils.getInterfaceFromIndex(self.sysconf, self.index)
            )
            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]

            # Render a hosts overview, utilisation by port
            portStats = self.flowDb.getPortBreakdownForIp(self.month, self.year, self.ip, self.day, self.index)

            header = ["Port", "Traffic In", "Traffic Out", "Percentage of Total"]
            for port, inout in portStats.items():
                if (inout[0] + inout[1]) > 1024:
                    table.append([inout[0]+inout[1],self.resolvePort(port), Utils.intToH(inout[0]), Utils.intToH(inout[1])])
                total += inout[0] + inout[1]
                tin += inout[0]
                tout += inout[1]

        else:
            title = "Local Internet Usage by IP or username during %s" % (self.dateStamp())
            header = ["IP Address", "Traffic In", "Traffic Out", "Percentage of Total"]
            ipStats = self.flowDb.getVolumeTotalByIp(self.month, self.year, self.day)
            
            userGraph = "/chart?type=pie&width=500&height=250&legright=y&"
            userSet = []
            for ip, inout in ipStats.items():
                ipn = ip
                if ip == '0.0.0.0':
                    ipn = "Vulani Server"
                merged = inout[0]+inout[1]
                table.append([
                    merged,
                    tags.a(href=url.root.child("NetworkStats").child("Host").child(ip).child(self.day).child(self.month).child(self.year), title="View detail")[ipn], 
                    Utils.intToH(inout[0]), 
                    Utils.intToH(inout[1])
                ])
                total += merged
                tin += inout[0]
                tout += inout[1]

                userSet.append((merged, ipn))
            
            userSet.sort()
            userGraph += "&".join(["lables=%s&data=%s" % (ipn, utotal) for utotal, ipn in reversed(userSet[-5:])])
            otherUsersTotal = total - sum([utotal for utotal, ipn in userSet[-5:]])
            userGraph += "&lables=%s&data=%s" % ("Other Users", otherUsersTotal)

            extraStats = [tags.img(src=userGraph), tags.br]

            # Sort out our interface list
            totals = self.flowDb.getTotalIndex(self.month, self.year, self.day)
            print totals
            indexTable = []
            itotal, itin, itout = (0,0,0)
            ifDone = []

            totalGraph = "/chart?type=pie&width=500&height=250&legright=y&"

            totalSet = []
            interfaces = []
            for index, inout in totals.items():
                iface = Utils.getInterfaceFromIndex(self.sysconf, index)
                if not iface:
                    continue
                interfaces.append(iface)
                indexTable.append([
                    inout[0]+inout[1],
                    tags.a(href=url.root.child("NetworkStats").child("Interface").child(index).child(self.day).child(self.month).child(self.year), title="View detail")[iface],
                    Utils.intToH(inout[0]),
                    Utils.intToH(inout[1])
                ])
                itotal += inout[0] + inout[1]
                itin += inout[0]
                itout += inout[1]

                totalSet.append("lables=%s&data=%s" % (iface, inout[0]+inout[1]))

            totalGraph+= '&'.join(totalSet)

            indexTable.sort()

            indexTable = [i[1:]+[PageHelpers.progressBar(float(i[0])/float(itotal), colour="#f8be0f")] for i in indexTable]
            indexTable.append([
                tags.a(href=url.root.child("NetworkStats").child("Ports").child(self.day).child(self.month).child(self.year), title="View port usage for this time")['Total Usage'], 
                Utils.intToH(itin), Utils.intToH(itout), PageHelpers.progressBar(1)
            ])

            other = [
                tags.h3['Internet usage by network interface'], 
                tags.img(src=totalGraph), tags.br, 
                PageHelpers.dataTable(header, reversed(indexTable)),tags.br
            ]

            if self.day == 0:
                # Generate a bar graph of usage per day
                nids, maxDays, maxunit = NetUtils.getNIDdaySummary(self.year, self.month)

                cstart = "/chart?type=line&width=500&height=200&legright=y"

                if maxunit > (1000**3):
                    scale = 1000**3
                    unit = "GBytes"
                else:
                    scale = 1000**2
                    unit = "MBytes"
                cstart += "&ylab=Data+volume+(%s)" % unit

                tdata = []
                for ifa in interfaces:
                    if not ifa in nids:
                        continue
                    ndata = []
                    dset = ["0" for i in range(maxDays)]
                    for day, vols in nids[ifa]:
                        dset[day-1] = "%d" % int((vols[0]+vols[1])/scale)
                    cstart += "&set=%s&data=%s" % (ifa, '+'.join(dset))
            
                for d in range(maxDays):
                    cstart += "&lables=%s" % (d+1)

                other.insert(0, tags.img(src=cstart))

        # Sort the table and add internet usage
        table.sort()
        if internet:
            table.append(internet)
        
        # Reformat our table with progress bars
        table = [i[1:]+[PageHelpers.progressBar(float(i[0])/float(total), colour="#f8be0f")] for i in table]

        # Add the 'Total' total to the table.
        if self.index:
            table.append([
                tags.a(href=url.root.child("NetworkStats").child("InterfacePorts").child(str(self.index)).child(self.day).child(self.month).child(self.year), title="View port usage for this time")['Total Usage'], 
                Utils.intToH(tin), Utils.intToH(tout), PageHelpers.progressBar(1)
            ])
        else:
            table.append([
                tags.a(href=url.root.child("NetworkStats").child("Ports").child(self.day).child(self.month).child(self.year), title="View port usage for this time")['Total Usage'], 
                Utils.intToH(tin), Utils.intToH(tout), PageHelpers.progressBar(1)
            ])

        return ctx.tag[
            tags.h2[tags.img(src="/images/netflow.png")," Network utilisation"],
            tags.directive('form dateRange'),
            other,
            tags.h3[title],
            extraStats,
            PageHelpers.dataTable(header, reversed(table)),tags.br,
            tags.a(name="us")[''],
            tags.p[tags.strong["* Unknown Services:"],""" Because large volumes of traffic are undefinable (MSN, Bittorrent, etc),
            during the aggregation process we must lump "high ports" (ports >1024) which can not be defined into a bigger subset called "Unknown Services".
            The reason for this is that this data is often a small amount of noise but accounts for many individual packets, 
            accounting the value of each of these ports will not provide any useful data to the person viewing it as the application 
            responsible for it is undefined. Processing the data without this aggregation also increases the volume of data considerably, 
            and the resources required to view it. If the value is extremely high, the most likely reasons are a virus infection or Bittorent activity.
            """]
        ]
