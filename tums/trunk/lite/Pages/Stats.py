from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os
from Core import PageHelpers
from Pages import Users

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Tools"]]

    def childFactory(self, ctx, seg):
        if seg in self.childPages.keys():
            return self.childPages[seg].Page(self.avatarId)

    def render_content(self, ctx, seg):
        log = "net status sessions parseable"
        mail = "mailq"
        f = os.popen(log)
        l = f.read()
        
        lastList = reversed(l.split('\n'))
        
        f = os.popen(mail)
        l = f.read()

        mailqList = reversed(l.split('\n'))
        

        return ctx.tag[
            tags.div(id="rightBlock")[
                [ [i, tags.br]
                for i in lastList]
                
                ,tags.br,
                
                [ [i, tags.br]
                for i in mailqList]
            ]
        ]

        
        
