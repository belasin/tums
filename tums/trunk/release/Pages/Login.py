"""Login Page"""
from nevow import inevow, rend, loaders, tags, vhost, appserver, static, guard, url

import Settings

class rootPage(rend.Page):
    """ RootPage this provides our authentication wrapper and login page
    uses templates/login.xml
    """

    addSlash    = True
    docFactory  = loaders.xmlfile('login.xml', templateDir=Settings.BaseDir+'/templates')

    def render_form(self, ctx, data):
        """Renders our login form"""
        # Pass our guard.LOGIN context to the page renderer
        return ctx.tag(action=guard.LOGIN_AVATAR)

    def locateChild(self, ctx, segments):
        """Locates login information for authentication"""
        # wraps our child locator,
        ctx.remember(self, inevow.ICanHandleNotFound)
        return super(rootPage, self).locateChild(ctx, segments) # pass back to the parent child locator

    def renderHTTP_notFound(self, ctx):
        return url.root

Page = rootPage

