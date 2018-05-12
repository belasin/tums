from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane
import os
import Tree, Settings, formal
from Core import PageHelpers, Utils
from Pages import Users, Reports

class Page(PageHelpers.DefaultPage):
    addSlash = True
    def __init__(self, avatarId=None, db=None, graph="totals", period="",*a, **kw):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **kw)
        self.graph =graph
        self.period = period

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Reports"]]

    def form_selectLog(self, ctx):
        form = formal.Form()
        graphdir = os.listdir(Settings.BaseDir + '/images/graphs/')
        graphs = [('totals', 'Total Bandwidth'), ('io', 'System IO')]
        for g in graphdir:
            if "graph-" in g:
                #standard graph generaly per port or a load..
                name = g.split('-')[-1].split('.')[0]
                if name[-1] in ['m', 'F', 'S', 'y', 'w']:
                    # If we have a time thingy, get rid of it...
                    newname = name[:-1]
                    name = newname
                    # IF we still have an "F" then it was "FS"
                    if name[-1] == "F":
                        name = name[:-1] # Chomp again..

                value = name
                if not "load" in name:
                    try:
                        name = "Routed Traffic - %s" % Utils.resolvePort(int(name))
                    except:
                        name = "Routed Traffic - %s" % name
                    value = "port" + value
                else:
                    name = "System Load"
                if not (value, name) in graphs:
                    graphs.append((value, name))

        graphs.sort()

        form.addField('graph', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = graphs),
            label = "Graph to view")

        form.addAction(self.selectLog)
        form.data = {'graph': self.graph}
        return form

    def selectLog(self, ctx, form, data):
        return url.root.child('Graphs').child(data['graph'])

    def locateChild(self, ctx, seg):
        if seg[0]:
            return Page(self.avatarId, self.db, seg[0], seg), ()

        return Page(self.avatarId, self.db), ()

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Reports.Page.sideMenu(Reports.Page(), self.avatarId)]

    def render_content(self, ctx, seg):
        if self.graph == "totals":
            graphName = "totals"
        elif self.graph == "io":
            graphName = "io"
        elif "port" in self.graph:
            graphName = "graph-%s" % self.graph.replace('port', '')
        else:
            graphName = "graph-%s" % self.graph
        return ctx.tag[
                tags.h3["Select Graph"],
                tags.directive('form selectLog'),
                tags.h3["Last day"],
                tags.img(src="/images/graphs/%s.png" % graphName),
                tags.h3["Last week"],
                tags.img(src="/images/graphs/%sw.png" % graphName),
                tags.h3["Last month"],
                tags.img(src="/images/graphs/%sm.png" % graphName),
                tags.h3["Last year"],
                tags.img(src="/images/graphs/%sy.png" % graphName),
        ]
        
