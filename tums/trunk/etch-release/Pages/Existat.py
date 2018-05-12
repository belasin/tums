from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime, formal, os
import Tree, Settings
from Core import PageHelpers, WebUtils, Utils
from Pages import Reports

# PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib import styles 
from reportlab.lib.units import cm

import copy, StringIO

class MailReport:
    def __init__(self, month, year):
        defaultStyles = styles.getSampleStyleSheet()
        self.pStyle = copy.deepcopy(defaultStyles["Normal"])
        self.pStyle.fontName = "Helvetica"
        self.hStyle = copy.deepcopy(defaultStyles['Heading1'])
        self.hStyle.fontName = "Helvetica"

        self.month, self.year = (month, year)
           
    def getMonth(self, month):
        print month

        MonthData = {}
        topDomains = {}
        topSendDomains = {}
        localSenders = {}
        localRecip = {}
        localDest = {}
        remoteSenders = {}

        statargs = [
            [topDomains, 'receive_domains'],
            [topSendDomains, 'send_domains'],
            [localSenders, 'local_senders'],
            [localRecip,   'destinations'],
            [remoteSenders, 'remote_senders'],
            [localDest,     'recipients']
        ]
        totalMail = [[i,0] for i in range(1,32)]

        fis = os.listdir('/usr/local/tcs/tums/statdb/')
        days = []

        rdays = []
        for n in fis:
            if 'ms.db' != n[-5:]:
                continue 
            if month != n[:6]:
                continue
            
            if not n in days:
                days.append(n)
                rdays.append(int(n[6:8]))
        # why not...
        days.sort()
        rdays.sort()
        
        # Generate the stats..
        for i in days:
            if i.split('/')[-1][:6] == month:
                mp = open('/usr/local/tcs/tums/statdb/%s' % i).read() # this has to exist...
                try:
                    lp = open('/usr/local/tcs/tums/statdb/%s' % i.replace('ms.','rs.')).read()
                except:
                    print "No reject"
                    # this doesn't have to exist..
                    lp = None

                if not lp:
                    lp = "{'blacklist':0, 'spam':0, 'other':0, 'grey':0}"

                stat = eval(lp)
                mstat = eval(mp)
                
                day = int(i.split('/')[-1][6:8])
                
                MonthData[day] = stat
                
                for target, source in statargs:
                    for key,val in mstat[source].items():
                        if key in target:
                            target[key] += val
                        else:
                            target[key] = val

                        if source == 'receive_domains' or source=='send_domains':
                            totalMail[day-1][1] += val
        # URGH!
        def listify(adict):
            trd = [ [i,k] for k,i in adict.items()]
            trd.sort()
            return [k for k in reversed(trd[-10:])]

        topDomains = listify(topDomains)
        topSendDomains = listify(topSendDomains)
        localSenders = listify(localSenders)
        localRecip = listify(localRecip)
        remoteSenders = listify(remoteSenders)
        localDest = listify(localDest)

        ### Spam graph
        xTicks = ['{label: "%s", v: %s}' % (i,i) for i in  range(1,32)]


        spam = []
        blacklist = []
        grey = []
        total = []

        for i in range(1,32):
            try:
                stats = MonthData[i]
            except:
                #print "No rejects"
                stats = {'blacklist':0, 'spam':0, 'other':0, 'grey':0}

            spam.append([i, int(stats['spam'])])
            blacklist.append([i, int(stats['blacklist'])])
            total.append([i, int(stats['other'])])
            try:
                grey.append([i, int(stats['grey'])])
            except:
                print "No greylist data for the %sth" % i

        return rdays, grey, total, blacklist, spam, totalMail, topDomains, topSendDomains, localSenders, localDest, localRecip, remoteSenders

    def peakTrimmer(self, set):
        if len(set) < 2:
            return set
        newSet = []
        dvals = [i for k,i in set]

        #nkeys = dict([k,i] for i,k in set])
        
        ave = sum(dvals)/len(set)
        if ave < 5:
            return set

        for k,n in set:
            if n > (ave*2):
                n = n/ave
            newSet.append([k,n])

        return newSet

    def greyGraph(self, grey, days):
        cstart = "/chart?type=line&width=500&height=200&legright=y&set=Greylisted"
        d = dict(grey)
        cstart += "&data=%s" % ('+'.join([str(d[i]) for i in days]))
        for d in days:
            cstart += "&lables=%s" % d

        return tags.img(src=cstart)

    def mailGraph(self, total, days):
        cstart = "/chart?type=line&width=500&height=200&legright=y"

        d = dict(total)
        cstart += "&set=Mail+Recieved&data=%s" % ('+'.join([str(d[i]) for i in days]))

        for d in days:
            cstart += "&lables=%s" % d

        return tags.img(src=cstart)
        
    def spamGraph(self, total, blacklist, spam, days):
        cstart = "/chart?type=line&width=500&height=200&legright=y"
        
        d = dict(self.peakTrimmer(total))
        cstart += "&set=Viruses,+forgery+and+greylisting&data=%s" % ('+'.join([str(d[i]) for i in days]))
        
        d = dict(self.peakTrimmer(spam))
        cstart += "&set=Spam&data=%s" % ('+'.join([str(d[i]) for i in days]))
        
        d = dict(self.peakTrimmer(blacklist))
        cstart += "&set=Blacklisted+senders&data=%s" % ('+'.join([str(d[i]) for i in days]))
        
        for d in days:
            cstart += "&lables=%s" % d

        return tags.img(src=cstart)

    def pieChartImg(self, values):
        # Values is [[num, 'dom'], [num2, 'dom2'], ...]

        cstart = "/chart?type=pie&width=500&height=250&legright=y"

        for n, l in values:
            cstart += "&lables=%s&data=%s" % (l, n)

        return tags.img(src=cstart)

    def pieChart(self, title, para, values):
        return [
            tags.h3[title], 
            tags.p[para], 
            self.pieChartImg(values)
        ]


    def attributeDecoder(self, tag):
        """ Takes an image tag and returns get arguments from src (ie, converts a graph image to a config)"""
        config = {}
        # Grab get arguments
        get = tag.attributes['src'].split('?')[1]
        ks = get.split('&')
        for n in ks:
            k,v = n.split('=', 1)
            if config.get(k):
                config[k].append(v.replace('+', ' '))
            else:
                config[k] = [v.replace('+', ' ')]
        print config
        return config 

    def PDFGraph(self, func, *a):
        I = Image(WebUtils.createChart(self.attributeDecoder(func(*a))))
        scale = 0.60
        I.drawWidth = scale * I.drawWidth
        I.drawHeight = scale * I.drawHeight
        return I

    def pdfPieChart(self, title, para, values):
        return [
            Paragraph("%s" % title, self.hStyle),
            Paragraph("%s" % para, self.pStyle),
            Spacer(1, 0.5*cm), 
            self.PDFGraph(self.pieChartImg, values),
            Spacer(1, 0.5*cm), 
        ]
    def createReport(self, month):
        # Pull out our stats
        (days, grey, total, blacklist, spam, totalMail, 
        topDomains, topSendDomains, localSenders, 
        localDest, localRecip, remoteSenders) = month
        
        return [
            tags.h3['Spam Statistics'], 
            self.greyGraph(grey, days),
            
            tags.h3['Spam and other mail blocked this month'],
            self.spamGraph(total, blacklist, spam, days),
            
            tags.h3['Mail recieved'], 
            self.mailGraph(totalMail, days),
            
            self.pieChart("Top sender domains", "Top 10 domains which deliver mail to this site", topDomains),
            self.pieChart("Top recipient domains", "Top 10 domains to which mail is delivered from this site", topSendDomains),
            self.pieChart("Top local sender addresses", "Top 10 email addresses from which mail was delivered", localSenders),
            self.pieChart("Top local recipient addresses", "Top 10 email addresses to which mail was delivered at this site", localDest),
            self.pieChart("Top recipient addresses", "Top 10 email addresses to which mail was delivered from this site", localRecip),
            self.pieChart("Top sender addresses", "Top 10 email addresses from which mail was received by this site", remoteSenders)
        ]

    def createPDF(self, month):
        out = StringIO.StringIO()
        doc = SimpleDocTemplate(out)
        
        (days, grey, total, blacklist, spam, totalMail, 
        topDomains, topSendDomains, localSenders, 
        localDest, localRecip, remoteSenders) = month

        
        story = [
            Paragraph("Mail report for %s %s" % (Utils.months[self.month], self.year), self.hStyle),
            Spacer(1, 0.5*cm), 
            Paragraph("1. Spam Statistics", self.hStyle),
            Spacer(1, 0.5*cm), 
            Paragraph("1.1 Greylisting", self.hStyle),
            Paragraph("Mail rejected this month due to greylisting", self.pStyle),
            Spacer(1, 0.5*cm), 
            self.PDFGraph(self.greyGraph, grey, days),
            Paragraph("1.2 Spam and other", self.hStyle),
            Paragraph("Spam and other email blocked during this month", self.pStyle),
            Spacer(1, 0.5*cm), 
            self.PDFGraph(self.spamGraph, total, blacklist, spam, days),
            Spacer(1, 1*cm), 
            Paragraph("2. Mail Statistics", self.hStyle),
            Spacer(1, 0.5*cm), 
            Paragraph("2.1 Mail recieved", self.hStyle),
            Paragraph("Total valid email received during this month", self.pStyle),
            Spacer(1, 0.5*cm), 
            self.PDFGraph(self.mailGraph, totalMail, days),
            Spacer(1, 0.5*cm)
        ]
        story.extend(self.pdfPieChart("2.2 Top sender domains", "Top 10 domains which deliver mail to this site", topDomains))
        story.extend(self.pdfPieChart("2.3 Top recipient domains", "Top 10 domains to which mail is delivered from this site", topSendDomains))
        story.extend(self.pdfPieChart("2.4 Top local sender addresses", "Top 10 email addresses from which mail was delivered", localSenders))
        story.extend(self.pdfPieChart("2.5 Top local recipient addresses", "Top 10 email addresses to which mail was delivered at this site", localDest))
        story.extend(self.pdfPieChart("2.6 Top recipient addresses", "Top 10 email addresses to which mail was delivered from this site", localRecip))
        story.extend(self.pdfPieChart("2.7 Top sender addresses", "Top 10 email addresses from which mail was received by this site", remoteSenders))
        doc.build(story)
        out.seek(0)
        return out 

class PDFPage(rend.Page):
    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)
        args = request.args

        month = args['m'][0]

        m = MailReport(int(month[4:]), int(month[:4]))
        stats = m.getMonth(month)
        pdf = m.createPDF(stats).read()
        
        request.setHeader('content-type', 'application/pdf')
        request.setHeader('content-disposition', 'attachment; filename=vulanimail%s.pdf' % month)
        request.setHeader('content-length', str(len(pdf)))

        return pdf

class Page(Reports.Page):
    docFactory  = loaders.xmlfile('mailstats.xml', templateDir=Settings.BaseDir+'/templates')
    def __init__(self, avatarId = None, db = None, year = 0, month = 0, *a, **kw):
        today = datetime.datetime.now()
        if not year:
            self.year = today.year
        else:
            self.year = year
        if not month:
            self.month = today.month
        else:
            self.month = month

        self.mailReport = MailReport(month, year)
        Reports.Page.__init__(self,avatarId, db, *a, **kw)

    def form_selectDate(self, ctx):
        form = formal.Form()
        statdir = os.listdir('/var/www/localhost/htdocs/eximstat/')
        dates = []
        for d in statdir:
            if ".html" in d  and "index" not in d: # Not index but is html
                dD = "%s %s" % (d[4:].strip('.html'), d[:4])
                dates.append((d.strip('.html'), dD))
        
        dates.sort()
        form.addField('stats', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = dates),
            label = "Date "
        )
        if self.month < 10:
            month = "0" + str(self.month)
        else:
            month = str(self.month)
        
        form.addAction(self.selectDate)
        form.data = {'stats': "%s%s" % (self.year,month)}
        return form

    def selectDate(self, ctx, form, data):
        return url.root.child('Existat').child(data['stats'])

    def render_content(self, ctx, data):
        month = "%s%.2d" % (self.year, self.month)
        
        stats = self.mailReport.getMonth(month)
        try:
            self.mailReport.createPDF(stats)
        except:
            print "Unable to create PDF mail report"

        return ctx.tag[
            tags.h3[tags.img(src="/images/maillog.png"), " Mail Statistics"],
            tags.directive('form selectDate'),
            tags.br, 
            tags.a(href="/auth/Existat/PDF?m=%s" % month)["Download PDF"],
            tags.br, 
            self.mailReport.createReport(stats)
       ]

    def childFactory(self, ctx, segment):
        if "PDF" in segment:
            return PDFPage()
        year  = int(segment[:4])
        month = int(segment[4:])
        return Page(self.avatarId, self.db, year, month)
