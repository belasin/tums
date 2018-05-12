from enamel import authentication, deployment, pages, servers, storage, deferreds, tags
from enamel import sql, form, url
import enamel, sha

from custom import Widgets

from twisted.internet import utils

from lib import PageBase

class Page(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        baseDir = self.enamel.Settings.BaseDir
        theme = self.enamel.Settings.theme
        # Images, javascript and CSS locations
        # derived from base directory and theme 
        self.child_css = pages.static.File('%s/themes/%s/css/' % (baseDir, theme))
        self.child_js  = pages.static.File(baseDir + '/js/')
        self.child_images = pages.static.File('%s/themes/%s/images/' % (baseDir, theme))
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (baseDir, theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Configurations"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def rollupBlock(self, title, content):
        return tags.div(_class="roundedBlock")[title,tags.div[content]]

    def render_content(self, ctx, data):
        def renderServers(servers):
            return ctx.tag[
                tags.h2["Configuration Profiles"]
            ]

        return self.enamel.storage.getServersInGroup(self.avatarId.gids).addCallback(renderServers)


