from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings
from Core import PageHelpers
from Pages import Users

class Page(PageHelpers.DefaultPage):
    addSlash = True
    docFactory  = loaders.xmlfile('t.xml', templateDir=Settings.BaseDir+'/templates')


