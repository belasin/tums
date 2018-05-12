from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP, Database
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, NetUtils, WebUtils, confparse
from Pages import Tools, Reports
import formal, datetime

"""
    Ok going to put this in soon
        blah = PageHelpers.GraphObject("test", "pie")
        blah.options["HtmlText"] = False
        blah.options["grid"] = { "verticalLines":False, "horizontalLines": False }
        blah.options["xaxis"] = { "showLabels":False}
        blah.options["yaxis"] = { "showLabels":False}
        blah.options["legend"] = { "position": "se", "backgroundColor": "#D2E8FF"}

        blah.defineDataSet("d1", "Test")
        blah.defineDataSet("d2", "Test two")
        blah.defineDataSet("d3", "Test three")

        blah["d1"] = 500
        blah["d2"] = 700
        blah["d3"] = 45
"""

class Page(Reports.Page):
    addSlash = True
    portCache = {}

    userName = {}

    def __init__(self, avatarId, db, day=None, month=None, year=None, entry=None, view=None, index=0, *a, **kw):
        self.DB = db[5]['telDB']
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

        self.view = view
        self.entry = entry
        self.sysconf = confparse.Config()
        self.updateNames()

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

        if self.entry: #Assume View
            return url.root.child('TelReport').child(self.view).child(self.entry).child(self.day).child(self.month).child(self.year)
        if self.view:
            return url.root.child('TelReport').child(self.view).child(self.day).child(self.month).child(self.year)
        else:
            return url.root.child('TelReport').child(self.day).child(self.month).child(self.year)

    def updateNames(self):
        for user, ext in self.sysconf.PBXExtensions.items():
            self.setName(user, ext['fullcallerID'])

    def setName(self, user, clid):
        if len(clid) > 4:
            if '"' in clid:
                name = clid.split('"')[1]
            else:
                name = clid
            if user not in self.userName:
                self.userName[user] = name

    def getName(self, user):
        return self.userName.get(user, "")
    
    def locateChild(self, ctx, seg):
        """Returns page instances depending on the URL"""
        base = 0
        entry = None
        view = "Overview"
        if seg[0] == "User":
            base = 1
            view = seg[0]
            entry = seg[1]
        try: 
            day = int(seg[base+1])
            month = int(seg[base+2])
            year = int(seg[base+3])
        except:
            day = 0 
            month = None
            year = None
        return Page(self.avatarId, self.db, day, month, year, entry, view), ()

    def procUserField(self, userField):
        output = {'vals': []}
        for entry in userField.split(';'):
            if '=' in entry:
                k, val = entry.split('=',1)
                output[k] = val
            else:
                vals.append(entry)
        return output

    def gen_overview(self):
        header = ["User", "Name", "Dial Time","Count", "Receive Time", "Count", "Queue Time", "Count", "Total Time","Count"]
        data = []
        totals = {}
        userName = {}
           
        def touchEnt(user):
            if user not in totals:
                totals[user] = {'rec':[0,0,0], 'out':[0,0,0], 'que':[0,0,0], 'tot':[0,0,0]}

        def processUserOutTotals(oRes):
            """Processes the sql result of the user's dialing out"""
            if len(oRes) > 0:
                for entry in oRes:
                    srcExt = entry['accountcode']
                    self.setName(srcExt, entry['clid'])
                    touchEnt(srcExt)
                    totals[srcExt]['out'] = [int(entry[2]), int(entry[3]), int(entry[4])]
                    totals[srcExt]['tot'][0] += int(entry[2])
                    totals[srcExt]['tot'][1] += int(entry[3])
                    totals[srcExt]['tot'][2] += int(entry[4])
            return self.DB.getUserQueueIn(self.year, self.month, self.day).addBoth(processUserQueueIn)
        def processUserQueueIn(qRes):
            """Process users queue time"""
            if len(qRes) > 0:
                for entry in qRes:
                    uD = self.procUserField(entry['userField'])
                    dstExt = uD['dst']
                    touchEnt(dstExt)
                    totals[dstExt]['que'][0] += int(entry['duration'])
                    totals[dstExt]['que'][1] += int(entry['billsec'])
                    totals[dstExt]['que'][2] += 1
                    totals[dstExt]['tot'][0] += int(entry['duration']) 
                    totals[dstExt]['tot'][1] += int(entry['billsec'])
                    totals[dstExt]['tot'][2] += 1
            return self.DB.getUserIn(self.year, self.month, self.day).addBoth(processUserIn)
            
        def processUserIn(iRes):
            if len(iRes) > 0:
                for entry in iRes:
                    uD = self.procUserField(entry['userField'])
                    dstExt = uD['dst']
                    touchEnt(dstExt)
                    totals[dstExt]['rec'][0] += int(entry['duration'])
                    totals[dstExt]['rec'][1] += int(entry['billsec'])
                    totals[dstExt]['rec'][2] += 1
                    totals[dstExt]['tot'][0] += int(entry['duration']) 
                    totals[dstExt]['tot'][1] += int(entry['billsec'])
                    totals[dstExt]['tot'][2] += 1
            return generateRep()

        def generateRep():
            userPie = PageHelpers.GraphObject("userPieTel", "pie")
            #userPie.options["HtmlText"] = True 
            userPie.options["grid"] = { "verticalLines":False, "horizontalLines": False, "outlineWidth": 0}
            userPie.options["xaxis"] = { "showLabels":False}
            userPie.options["yaxis"] = { "showLabels":False}
            userPie.options["legend"] = {"show": True }#"position": "se", "backgroundColor": "#D2E8FF"}

            for user,ent in totals.items():
                userPie.defineDataSet(user, self.getName(user))
                userPie[user] = ent['tot'][1]
   
                data.append([
                    tags.a(href=url.root.child('TelReport').child("User").child(user).child(self.day).child(self.month).child(self.year))[user],
                    self.getName(user),
                    self.genDuration(ent['out'][1]),
                    ent['out'][2],
                    self.genDuration(ent['rec'][1]),
                    ent['rec'][2],
                    self.genDuration(ent['que'][1]),
                    ent['que'][2],
                    self.genDuration(ent['tot'][1]),
                    ent['tot'][2],
                ])
               
            return [
                tags.h3["Overview Telephone Stats"], 
                userPie,
                PageHelpers.dataTable(header, data, sortable=True)
            ]
        #return self.DB.getReportData(self.year, self.month, self.day).addBoth(processResult)
        return self.DB.getUserOutTotals(self.year, self.month, self.day).addBoth(processUserOutTotals) #TODO Error Handeling

    def genDuration(self, seconds):
        hours = seconds / 3600
        seconds -= 3600*hours
        minutes = seconds / 60
        seconds -= 60*minutes
        return "%02d:%02d:%02d" % (hours, minutes, seconds)
 

    def gen_user(self):
        """Generate user specific report"""
        if not self.entry:
            return ""

        outHeader = ["Call Date", "Dialed Number", "Call Status", "Duration", "Provider", "Router", "Recording"]
        inHeader =  ["Call Date", "Caller ID", "Call Status", "Duration", "Provider", "Queue(*)", "Recording"]
        outData = []
        inData = []

        def processUserOut(oRes):
            formatOrder = ["mp3", "wav"]
            basePath = "/var/lib/samba/data/vRecordings/"
            for entry in oRes:
                uD = self.procUserField(entry['userField'])
                rec = ""
                if uD.get('rec', False):
                    if "." in uD['rec']:
                        fSplit = uD['rec'].split('.')
                        if fSplit[-1] == "wav" or fSplit[-1] == "mp3":
                            uD['rec'] = ".".join(fSplit[:-1])
                    for fmt in formatOrder:
                        if os.path.exists(basePath+uD['rec']+'.'+fmt):
                            rec = tags.a(href="/vRecordings/"+uD['rec']+"."+fmt)["Recording"]
                outData.append([
                    str(entry['calldate']),
                    entry['dst'],
                    entry['disposition'].capitalize(),
                    self.genDuration(entry['billsec']),
                    uD.get('dstProv', ""),
                    uD.get('dstRouter', ""),
                    rec,
                ])
            return self.DB.getUserInAll(self.year, self.month, self.day, self.entry).addBoth(processUserIn)
        def processUserIn(iRes):
            formatOrder = ["mp3", "wav"]
            basePath = "/var/lib/samba/data/vRecordings/"
            for entry in iRes:
                uD = self.procUserField(entry['userField'])
                rec = ""
                if uD.get('rec', False):
                    if "." in uD['rec']:
                        fSplit = uD['rec'].split('.')
                        if fSplit[-1] == "wav" or fSplit[-1] == "mp3":
                            uD['rec'] = ".".join(fSplit[:-1])
                    for fmt in formatOrder:
                        if os.path.exists(basePath+uD['rec']+'.'+fmt):
                            rec = tags.a(href="/vRecordings/"+uD['rec']+"."+fmt)["Recording"]
                queue = uD.get('queue', "")
                if entry['disposition'].upper() != 'ANSWERED':
                    rec = ""

                if entry['lastapp'] == 'Queue':
                    queue = entry['lastdata']
                dstExt = uD['dst']
                inData.append([
                    str(entry['calldate']),
                    entry['clid'],
                    entry['disposition'].capitalize(),
                    self.genDuration(entry['billsec']),
                    uD.get('dstProv', ""),
                    queue,
                    rec,
                ])
            return generateReport()
        def generateReport():
           return [
                tags.a(href=url.root.child('TelReport').child('Overview').child(self.day).child(self.month).child(self.year))["Back to Overview"],
                tags.h3['Outbound'],
                PageHelpers.dataTable(outHeader, outData, sortable=False), tags.br,
                tags.h3['Inbound'],
                PageHelpers.dataTable(inHeader, inData, sortable=False)
            ]

        return self.DB.getUserOut(self.year, self.month, self.day, self.entry).addCallback(processUserOut)

    def render_report(self, ctx, data):
        rep = ""
        if self.view == 'Overview':
            rep = self.gen_overview()
        if self.view == 'User':
            rep = self.gen_user()
        return rep 

    def render_content(self, ctx, data):
        title = "Telephone Usage Reports"
        graphIncludes = PageHelpers.genGraphInclude()

        return ctx.tag[
            tags.h2[tags.img(src="/images/mailsrv.png")," Telephone Utilisation"],
            tags.directive('form dateRange'),
            #other,
            #extraStats,
            graphIncludes,
            tags.directive('report'),
            #PageHelpers.dataTable(header, reversed(table)),tags.br,
            tags.a(name="us")['']
        ]
