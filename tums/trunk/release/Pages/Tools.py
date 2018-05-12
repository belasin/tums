from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings
from Core import PageHelpers, AuthApacheProxy

class Page(PageHelpers.ToolsPage):

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h2[self.text.tools],
            tags.p[self.text.toolsInstruction]
        ]
