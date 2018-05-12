from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import time, datetime
import Tree, Settings, Database
from Core import PageHelpers, Utils
from Pages import Reports

class Page(Reports.Page):
    docFactory  = loaders.xmlfile('overview.xml', templateDir=Settings.BaseDir+'/templates')

    def render_content(self, ctx, seg):
        datetup = datetime.datetime.now()
        month = datetup.month
        datetup = datetup.replace(month=month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        year = datetup.year
        date = "%s %s" % (Utils.months[datetup.month], datetup.year)

        periodStart = int(time.mktime(datetup.timetuple()))
        periodEnd = int(time.mktime(datetup.replace(month=month).timetuple()))

        if datetup.month<10:
            month = "0%s" % datetup.month
        else:
            month = datetup.month
        try:
            latestEximstat = open('/var/www/localhost/htdocs/eximstat/%s%s.html'%(datetup.year, month))
            doc = ""
            cnt = 0
            for ln in latestEximstat:
                cnt += 1
                thisln = ln.replace('src="./', '/auth/local/eximstat/').replace('src="images', 'src="/auth/local/eximstat/images')
                if not "html" in thisln and not "body" in thisln and cnt > 27:
                    doc+=thisln
        except Exception, e:
            print e
            doc = "No statistics for the last month"

        return ctx.tag[
            tags.h3[tags.img(src="/images/maillog.png"), " Monthly Report for %s" % date],
            tags.br,
            tags.h3["Internet Traffic"],
            tags.img(src="/images/graphs/totalsm.png"),
            tags.br,
            tags.xml(doc)
        ]
