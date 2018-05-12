from nevow import rend, loaders, tags, athena, context, flat
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure, log
from twisted.internet import defer
from twisted.names import client as dnsClient
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan, entities
from nevow.taglibrary import tabbedPane
from formal import iformal
from zope.interface import implements
from Core import Utils, confparse
from pycha import color as pyColor
from operator import itemgetter
import Tree, Settings, formal, time, os, sha
import re

import cairo, StringIO

try:
    from twisted.web import http
except ImportError:
    from twisted.protocols import http

VERSION = '1.5.0'
CODENAME = "Sunset"

days = [
    "Monday",
    "Tuesday", 
    "Wednesday", 
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday"
]

def IPMaskValidator():
    """ Generates a formal PatternValidator to validate a fully qualified CIDR IP address """
    IP_ADDRESS_PATTERN = '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$'
    return formal.PatternValidator(regex=IP_ADDRESS_PATTERN)
    
def IPValidator():
    """ Generates a formal PatternValidator to validate an IP address"""
    IP_ADDRESS_PATTERN = '^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    return formal.PatternValidator(regex=IP_ADDRESS_PATTERN)

def PortValidator():
    """ Generates a formal PatternValidator to validate a port is between 0 and 65535 """
    PORT_PATTERN = '^(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$'
    return formal.PatternValidator(regex=PORT_PATTERN)

def HostValidator():
    """ Generate a formal PatternValidator to validate a Hostname """
    HOST_PATTERN = '^((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|(([a-zA-Z0-9\-]+\.)+))([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$'
    return formal.PatternValidator(regex=HOST_PATTERN)

class PatternValidator(object):
    """Validate the value is a certain pattern.
    
    The required pattern is defined as a regular expression. The regex will be
    compiled automatically if necessary.
    """
    implements(iformal.IValidator)

    def __init__(self, regex, failedMessage="Invalid format"):
        self.regex = regex
        self.failedMessage = failedMessage

    def validate(self, field, value):
        if value is None:
            return
        # If it doesn't look like a regex object then compile it now
        if not hasattr(self.regex, 'match'):
            self.regex = re.compile(self.regex)
        if self.regex.match(value) is None:
            raise formal.FieldValidationError, self.failedMessage

def getArp():
    f = open('/proc/net/arp', "r")
    lines = f.readlines()
    f.close()
    if len(lines) > 1:
        for line in lines[1:]:
            entries = line.split()
            yield (entries[0], entries[3])

def nmbResolveIP(ip):
    d = defer.Deferred()
    r = os.popen('nmblookup -A %s' % ip)
    res = None
    for line in r:
        ln = line.split()
        if len(ln) > 2:
            if ln[1] == "<00>":
                res = ln[0]
                break
    r.close()
    d.callback(res)
    return d

@defer.inlineCallbacks
def resolveIP(iplist, nmblookup=False, stripHost=True):
    res = {}
    for nip in iplist:
        try:
            ip = nip.split('.')
            ptr = "%s.%s.%s.%s.in-addr.arpa" % (
                ip[3],ip[2],ip[1],ip[0]
            )
            d = yield dnsClient.lookupPointer(ptr)
            for ent in d:
                for i in ent:
                    if i.type == 12:
                        res[nip] = str(i.payload.name)
                        if stripHost:
                            res[nip] = res[nip].replace('.'+Settings.defaultDomain,'')
        except Exception, _exp:
            d = ""
        if nip not in res:
            try:
                d = yield nmbResolveIP(nip)
                res[nip] = d
            except:
                d = ""
    defer.returnValue(res)

class PortRangeValidator(object):
    """
    Validates port ranges
    """
    implements(formal.iformal.IValidator)

    PORT_REGEX = "^(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$"
    PORTRANGE_REGEX = "^(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0):(6553[0-5]|655[0-2]\d|65[0-4]\d\d|6[0-4]\d{3}|[1-5]\d{4}|[1-9]\d{0,3}|0)$"

    def validate(self, field, value):

        portRE = re.compile(self.PORT_REGEX)
        rangeRE = re.compile(self.PORTRANGE_REGEX)
        #Start by checking that it is in the correct text format XXXX:XXXX split by commas

        if not value:
            return
        
        for portRange in str(value).split(","):
            if ":" in portRange:
                (min, max) = portRange.split(":")
                if min >= max:
                    raise formal.FieldValidationError(u'%s is invalid second port in portrange is smaller or the same as first' % value)
                    continue
                if not rangeRE.match(portRange):
                    raise formal.FieldValidationError(u'%s is not a valid range' % value)
            else:
                if not portRE.match(portRange):
                    raise formal.FieldValidationError(u'%s is not a valid port' % value)
                    continue


def progressBar(percent, width=200.0, colour="#EC9600"):
    """ Returns stan tag set to construct a pretty, albeit IE incomplient, progress bar"""
    if percent > 100:
        percent = 100

    length = width
    percentText = "%s%%" % int(percent*100)
    return tags.div(style='border:1px solid black; width: %spx; height:16px;' % (length+2))[
        tags.div(style='float:left; margin-left: %spx;' % int((length/2)-15))[percentText],

        tags.div(style='margin-top:1px; margin-left:1px; width:%spx; height:14px; background: %s;' % (int(length*percent), colour))[''],
    ]

class GraphObject(object):

    dataSets = {}

    dataSetData = {}

    type = None

    name = None

    typeOption = {}

    options = None

    colorScheme = None

    sort = True

    mergeSmall = True

    mergePercent = 3 

    mergeLabel = "Other < 3%"

    width = 640

    height = 480

    typeOption = {}

    explodeBiggest = True

    types = ['pie', 'bars', 'candles', 'radar', 'line']

    """Generates a Graphing stan friendly object"""
    def __init__(self, name, type, typeOption={}, options={}):
        """Constructor for Graph Object"""
        self.name = name
        self.type = type
        self.options = options
        self.typeOption = typeOption
        self.dataSets = {}
        self.dataSetData = {}

    def defineDataSet(self, name, label, options = {}):
        """Defines the dataset"""
        self.dataSets[name] = {
            'name': name,
            'label': label,
            'options': options
        }
        if name not in self.dataSetData:
            self.dataSetData[name] = {}
        return True

    def setTitle(self, title, subtitle):
        """Set the title of the graph"""
        self.options["title"] = title
        self.options["subtitle"] = subtitle

    def renderGraph(self):
        """Generates the final list of tags that will implement the graphing"""
        def rgb_to_hex(rgb):
            nRGB = (rgb[0]*255, rgb[1]*255, rgb[2]*255)
            return '#%02x%02x%02x' % nRGB 

        if len(self.dataSets) < 1:
            return []
        style = ""
        options = self.options
        if self.width and self.height:
            style = "width:%spx;height:%spx" % (self.width, self.height)

        if self.type in self.types:
            options[self.type] = self.typeOption
            options[self.type]["show"] = True

        mergeList = []
        mergeTotal = 0
        ignoreList = []
        wrkDataSet = self.dataSetData
        itemList = wrkDataSet.items()
        #This will only happen with Pie Graphs where we merge items that are to small by themselves
        if self.mergeSmall:
            tot = 0
            for k, data in self.dataSetData.items():
                if "__merged_items__" == k:
                        continue
                if type(data) == int:
                    tot += data

            if tot > 0:
                for k,data in self.dataSetData.items():
                    if "__merged_items__" == k:
                        continue
                    if type(data) == int:
                        if (float(data)/float(tot)*100) < self.mergePercent:
                            mergeList.append(k)
                            mergeTotal += data
                    else:
                        ignoreList.append(k)
            wrkDataSet["__merged_items__"] = mergeTotal
            itemList = wrkDataSet.items()
            if(self.sort):
                itemList = sorted(itemList, key=itemgetter(1), reverse=True) #Sort in order of largest to smallest

        setData = []
        dataSets = []
        colorSet = {}
        
        if self.colorScheme:#'#f47a07'
            colorSet = pyColor.generateColorscheme(self.colorScheme,self.dataSets.keys())

        exploded = False

        for k,inData in itemList:
            if k in ignoreList or k in mergeList:
                continue
            if "__merged_items__" != k:
                v = self.dataSets[k]
            else:
                v = {
                    "label":self.mergeLabel,
                    "options": {}
                }
            if not exploded and self.explodeBiggest and self.type == "pie":
                if "pie" not in v["options"]:
                    v["options"]["pie"] = {}
                v["options"]["pie"]["explode"] = 20
                exploded = True
            else:
                if "pie" in v["options"]:
                    del v["options"]["pie"]

            #inData = self.dataSetData[k] 
            if type(inData) != list:
                inData = [inData]
            if k in colorSet:
                color = ',color:"%s"' % rgb_to_hex(colorSet[k])
            else:
                color = ""
            setData.append("var %s = %s;" % (k, repr([[key,val] for key,val in enumerate(inData)])))
            dsInfo = repr(v['options']).replace('True','true').replace('False','false')[1:-1]
            if dsInfo:
                dsInfo = ","+dsInfo
            dataSets.append("""{label:"%s"%s%s,data:%s}""" % (v['label'].replace(' -', '').capitalize(),color,dsInfo,k))

        return [
            tags.div(id="graphing-"+self.name, _class="graph-container", style=style)[""],
            tags.xml("""<script type="text/javascript">
document.observe('dom:loaded', function(){
    //Fill Series
    %(dataSetData)s

    //Draw the graph
    var f = Flotr.draw($('%(containerName)s'),
            [%(dataSets)s],
            %(graphOptions)s    
    );

});</script>""" % {
                'dataSetData': str.join('\n    ',setData),
                'containerName': "graphing-" + self.name,
                'graphOptions': repr(self.options).replace('True','true').replace('False','false'),
                'dataSets': str.join(',',dataSets)})]

    def genInclude(self):
        """Generates the tags to include the required scripts for graphing"""
        return [
                tags.xml("""<script type="text/javascript" src="/scripts/flotr/lib/prototype.js"></script>"""),
                tags.xml("""<!--[if IE]><script type="text/javascript" src="/scripts/flotr/lib/excanvas.js"></script><script type="text/javascript" src="/scripts/flotr/lib/base64.js"></script><![endif]-->"""),
                tags.xml("""<script type="text/javascript" src="/scripts/flotr/lib/canvas2image.js"></script>"""),
                tags.xml("""<script type="text/javascript" src="/scripts/flotr/lib/canvastext.js"></script>"""),
                tags.xml("""<script type="text/javascript" src="/scripts/flotr/flotr.js"></script>""") ]
    
    def __getitem___(self, dsName):
        """Gets the dataset data"""
        if dsName in self.dataSetData:
            return self.dataSetData[dsName]
        raise KeyError("Invalid Dataset")

    def __setitem__(self, dsName, data):
        """Sets the dataset data"""
        if dsName in self.dataSetData:
            self.dataSetData[dsName] = data
        else:
            raise KeyError("Invalid Dataset")

def flatten_graph(self, context):
    return self.renderGraph()

    #def __iter__(self)s
    #    """Returns an iterble instance that can be"""
    #    return iter(self.renderGraph())

flat.registerFlattener(flatten_graph, GraphObject) 

def genGraphInclude():
    """Generates the tags to include the required scripts for graphing"""
    return [
            tags.xml("""<script type="text/javascript" src="/scripts/flotr/lib/prototype.js"></script>"""),
            tags.xml("""<!--[if IE]><script type="text/javascript" src="/scripts/flotr/lib/excanvas.js"></script><script type="text/javascript" src="/scripts/flotr/lib/base64.js"></script><![endif]-->"""),
            tags.xml("""<script type="text/javascript" src="/scripts/flotr/lib/canvas2image.js"></script>"""),
            tags.xml("""<script type="text/javascript" src="/scripts/flotr/lib/canvastext.js"></script>"""),
            tags.xml("""<script type="text/javascript" src="/scripts/flotr/flotr.js"></script>""") ]


def TabSwitcher(tabs, id="A"):
    tabNames = [i for j,i in tabs]
    tabLables = [i for i,j in tabs]

    closeTabs = ';\n'.join(["    hideElement('%s'); getElement('tab%s').style.color='#666666';" % (i,i) for i in tabNames])

    switchFunc = """
        tabSwitcher%s = function (tab) {
            %s
            getElement('tab'+tab).style.color='#E710D8';
            showElement(tab);
            createCookie('tabOpen%s', tab);
            return false;
        };
    """ % (id, closeTabs, id)

    return [
        tags.xml("""<script type="text/javascript">
        function createCookie(name,value) {
            var date = new Date();
            date.setTime(date.getTime()+(24*60*60*1000));
            var expires = "; expires="+date.toGMTString();
            document.cookie = name+"="+value+expires+"; path=/";
        }

        function readCookie(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        createTabSwitcher%s = function() {
            %s
            var firstTab = '%s';
            showElement(firstTab);
            getElement('tab'+firstTab).style.color='#E710D8';
            try {
                var tab = readCookie('tabOpen%s');
                if (tab) {
                    %s
                    showElement(tab);
                    getElement('tab'+tab).style.color='#E710D8';
                }
            } catch(dontCare){
                showElement(firstTab);
                getElement('tab'+ firstTab).style.color='#E710D8';
            }
        };
        %s
        </script>""" % (id, closeTabs, tabNames[0], id, closeTabs, switchFunc)),
        tags.br, tags.br,
        tags.table(cellspacing=0, cellpadding=0)[tags.tr[
            [
                tags.td(_class = "tabTab", style="padding:0;background-image: url(/images/tabcenter.png); background-repeat: repeat-x;" ,
                    onclick = "return tabSwitcher%s('%s');" % (id,j)
                    )[
                        tags.a(
                            id="tab"+j, 
                            href="#",
                            style="color:#666666; text-decoration:none;", 
                            title="Switch to the tab: %s" % i,
                            onclick = "return tabSwitcher%s('%s');" % (id,j)
                        )[
                            tags.img(src='/images/lefttab.png', align="absmiddle"), 
                            tags.strong[i],
                            tags.img(src='/images/righttab.png', align="absmiddle")
                        ], 
                ] for i,j in tabs]
        ]]
    ]

def DialogTabSwitcher(tabs, id="A"):
    tabNames = [i for j,i in tabs]
    tabLables = [i for i,j in tabs]

    closeTabs = ';\n'.join(["    hideElement('%s'); getElement('tab%s').style.color='#666666';" % (i,i) for i in tabNames])

    switchFunc = """
        tabSwitcher%s = function (tab) {
            %s
            getElement('tab'+tab).style.color='#E710D8';
            showElement(tab);
            createCookie('tabOpen%s', tab);
            return false;
        };
    """ % (id, closeTabs, id)

    return [
        tags.xml("""<script type="text/javascript">
        function createCookie(name,value) {
            var date = new Date();
            date.setTime(date.getTime()+(24*60*60*1000));
            var expires = "; expires="+date.toGMTString();
            document.cookie = name+"="+value+expires+"; path=/";
        }

        function readCookie(name) {
            var nameEQ = name + "=";
            var ca = document.cookie.split(';');
            for(var i=0;i < ca.length;i++) {
                var c = ca[i];
                while (c.charAt(0)==' ') c = c.substring(1,c.length);
                if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
            }
            return null;
        }

        createTabSwitcher%s = function() {
            %s
            var firstTab = '%s';
            showElement(firstTab);
            getElement('tab'+firstTab).style.color='#E710D8';
            try {
                var tab = readCookie('tabOpen%s');
                if (tab) {
                    %s
                    showElement(tab);
                    getElement('tab'+tab).style.color='#E710D8';
                }
            } catch(dontCare){
                showElement(firstTab);
                getElement('tab'+ firstTab).style.color='#E710D8';
            }
        };
        %s
        </script>""" % (id, closeTabs, tabNames[0], id, closeTabs, switchFunc)),
        tags.table(cellspacing=0, cellpadding=0)[tags.tr[
            [
                tags.td(_class = "DtabTab", style="padding:0;background-image: url(/images/dCtab.png); background-repeat: repeat-x;" ,
                    onclick = "return tabSwitcher%s('%s');" % (id,j)
                    )[
                        tags.a(
                            id="tab"+j, 
                            href="#",
                            style="color:#666666; text-decoration:none;", 
                            title="Switch to the tab: %s" % i,
                            onclick = "return tabSwitcher%s('%s');" % (id,j)
                        )[
                            tags.img(src='/images/dLtab.png', align="absmiddle"), 
                            tags.strong[i],
                            tags.img(src='/images/dRtab.png', align="absmiddle")
                        ], 
                ] for i,j in tabs]
        ]]
    ]

def LoadTabSwitcher(id="A"):
    return tags.script(type="text/javascript")["createTabSwitcher%s();" % id]

def dataTable(headings, content, sortable = False, tabid=None):
    """ Produces a tabular listing which is either sortable or not. Sortable expects headings to be a 
        list of tuples, but if it is not a list of tuples the 'string' type will be assumed for every cell """
    if sortable:
        if isinstance(headings[0], tuple):
            header = [ tags.th(colformat=j)[i] for j,i in headings ]
        else:
            header = [ tags.th(colformat='istr')[i] for i in headings ]
        tclass = 'sortable'
    else:
        header = [ tags.th[i] for i in headings ]
        tclass = 'listing'

    if not content: 
        rows = tags.tr[ tags.td(colspan=len(headings))[tags.em["No entries."]]]
    else:
        rows = [tags.tr[ [tags.td[col] for col in row] ]
        for row in content]

    return tags.table(id = tabid, cellspacing=0,  _class=tclass)[
        tags.thead(background="/images/gradMB.png")[
            tags.tr[
                header
            ]
        ],
        tags.tbody[
            rows
        ]
    ]

def isLocked():
    try:
        lockStatus = open('/tmp/tumsLock').read().split()
        lockTime = int(time.time() - float(lockStatus[1]))
        lockUser = lockStatus[0]
        lockStatus = True
    except:
        lockStatus = False
        lockTime = 0
        lockUser = False

    # Have a time limit on how long the system can be locked for
    if lockTime > 3600:
        os.remove('/tmp/tumsLock')
        return (False, 0, False)

    return (lockStatus, lockTime, lockUser)
    

def render_userBar(self, ctx, data):

    if self.lockStatus:
        if self.avatarId.isAdmin:
            locker = tags.a(href="/auth/Lock", title="Unlock interface", _class="user-button lock")["Lock"]
            #locker = tags.a(href="/auth/Lock", title="Unlock interface")[tags.img(src="/images/lock.png")]
        else:
            locker = tags.img(src="/images/lock.png")
    else:
        if self.avatarId.isAdmin:
            locker = tags.a(href="/auth/Lock", title="Lock interface", _class="user-button unlock")["Unlock"]
            #locker = tags.a(href="/auth/Lock", title="Lock interface")[tags.img(src="/images/unlock.png")]
        else:
            locker=""

    return ctx.tag[
        tags.strong[self.avatarId.username.capitalize()], 
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        locker,
        #tags.a(href=url.root.child('Settings'), title="Personal account settings")[tags.img(src='/images/tbar-settings.png'), " Account Settings"],
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        tags.a(href=url.root.child(guard.LOGOUT_AVATAR), title="Logout of Vulani", _class="user-button logout")["Logout"],
        #tags.a(href="http://wiki.vulani.net", target="blank", title="Vulani Documentation Site")[tags.img(src='/images/tbar-help.png'), " Help"],
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        tags.a(href="http://wiki.vulani.net", target="blank", title="Vulani Documentation Site", _class="user-button help")["Help"],
        #tags.a(href=url.root.child(guard.LOGOUT_AVATAR), title="Logout of Vulani")[tags.img(src='/images/tbar-logout.png'), " Logout"],
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        entities.nbsp,
        tags.a(href=url.root.child('Settings'), title="Personal account settings", _class="user-button accounts")["Account Settings"],
    ]   

 
class VulaniMixin(object):
    menu = [
            ('/auth/Status/', '/images/statusMB.png',None, "Current system status"),
            ('/auth/Users/', '/images/usersMB.png',None, "Add or Modify system users"),
            ('/auth/Reports/', '/images/reports.png',None, "View system reports"),
            ('/auth/Tools/', '/images/tools.png',None, "System configuration and tools"),
    ]
    userMenu = [
         ('http://$ME$/roundcube/', '/images/webmailMB.png', None, "Web based email client"),
         ('/auth/Settings/', '/images/mysetMB.png',None, "Edit your personal account settings"),
         (url.root.child(guard.LOGOUT_AVATAR), "/images/logout.png",None, "Log out of Vulani"),
    ]
 
    def render_mailBar(self, ctx, data):
        l = [
            ('Mail',        'Mail',     '', 'users-top.png'),
            ('Calendar',    'Calendar', '', 'users-top.png'),
        ]
        
        return ctx.tag[
            [
                tags.td[
                    tags.a(href=url.root.child(base))[
                        tags.span(_class="itemTopImage")[
                            tags.img(src="/images/%s" % (image))
                        ],
                        tags.span(_class="itemTopText")[
                            tags.h1[name],
                            description
                        ],
                    ]
                ]
 
                #tags.td[
                #    tags.span(_class="itemTopText")[
                #        tags.h1[
                #            tags.a(href=url.root.child(base))[name]
                #        ], 
                #        description
                #    ],
                #    tags.span(_class="itemTopImage")[
                #    ]
                #]
            for base, name, description, image in l]
        ]

    def render_menu(self, ctx, data):
        host = str(url.URL.fromContext(ctx)).split('//')[-1].split(':')[0]
        if self.avatarId.isUser:
            self.menu= []
        if self.avatarId.reports:
            try:
                del self.menu[3]
            except:
                pass
        if self.menu:
            newBlock = tags.img(src="/images/blockMB.png")
        else:
            newBlock = ""
        return ctx.tag[
            tags.img(src="/images/blockMB.png"),
            [
                tags.a(href=elm[0].replace('$ME$',host), title=elm[3])[tags.img(src=elm[1])]
            for elm in self.menu],
            newBlock,
            [
                tags.a(href=elm[0].replace('$ME$',host), title=elm[3])[tags.img(src=elm[1])]
            for elm in self.userMenu],
            self.addedMenu(),
        ]


    def render_topBar(self, ctx, data):
        l = [
            ('Status', 'Dashboard', 'View system status',           'dashboard-top.png'),
            ('Users',  'Users',     'Manage users',         'users-top.png'),
            ('Reports','Reports',   'View reports',          'reports-top.png'),
            ('Tools',  'Tools',     'Configure settings',    'tools-top.png')
        ]
        
        return ctx.tag[
            [ 
                tags.td[
                    tags.a(href=url.root.child(base))[
                        tags.span(_class="itemTopImage")[
                            tags.img(src="/images/%s" % (image))
                        ],
                        tags.span(_class="itemTopText")[
                            tags.h1[name], 
                            description
                        ],
                    ]
                ]
            for base, name, description, image in l]
        ]

    def render_footerBar(self, ctx, data):
        return ctx.tag[
            tags.a(href=url.root.child('About'))["Vulani ", VERSION]
        ]

    def addedMenu(self):
        if self.pageMenu:
            return [
                tags.img(src="/images/blockMB.png"),
                [
                    tags.a(href=elm[0], title=elm[3])[tags.img(src=elm[1])]
                for elm in self.pageMenu]
            ]
        else:
            return []

    def render_sideMenu(self, ctx, data):
        return ctx.tag['']

    def render_pageName(self, ctx, data):
        return ctx.tag['']

    def render_content(self, ctx, data):
        return ctx.tag['']

    def render_version(self, ctx, data):
        return VERSION

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.p[""]
        ]



class DefaultAthena(formal.ResourceMixin, athena.LivePage, VulaniMixin):
    addSlash = True
    moduleName = ''
    moduleScript = ''
    fragmentPage = None
    isTool = False
    childPages = {}
    BOOTSTRAP_MODULES = ['Divmod', 'Divmod.Base', 'Divmod.Defer', 'Divmod.Runtime', 'Nevow', 'Nevow.Athena']

    docFactory  = loaders.xmlfile('default.xml', templateDir=Settings.BaseDir+'/templates')

    userMenu = [
         ('http://$ME$/roundcube/', '/images/webmailMB.png', None, "Web based email client"),
         ('/auth/Settings/', '/images/mysetMB.png',None, "Edit your personal account settings"),
         (url.root.child(guard.LOGOUT_AVATAR), "/images/logout.png",None, "Log out of Vulani"),
    ]

    pageMenu = []

    def __init__(self, avatarId = None, db = None, *a, **k):
        mods = athena.jsDeps.mapping
        mods[self.moduleName] = Settings.BaseDir+'/scripts/'+self.moduleScript
        athena.LivePage.__init__(self, jsModules = athena.JSPackage(mods))
        self.avatarId = avatarId
        self.db = db
        self.lockStatus, self.lockTime, self.lockUser = isLocked()
        self.sysconf = confparse.Config()
        self.render_userBar = render_userBar

    def childFactory(self, ctx, seg):
        if seg in self.childPages:
            return self.childPages[seg](self.avatarId, self.db)
        return athena.LivePage.childFactory(self,ctx,seg)

    def render_thisFragment(self, ctx, data):
        """ Render overviewFragment instance """
        f = self.fragmentPage(self.db)
        f.setFragmentParent(self)
        return ctx.tag[f]

    def render_content(self, ctx, data):
        return ctx.tag[
            tags.invisible(render=tags.directive('thisFragment'))
        ]

    def logout(self):
        print "Logged out"

class TemplateFragment(formal.ResourceMixin, rend.Fragment):
    def __init__(self, avatarId = None, db = None, *a, **k):
        formal.ResourceMixin.__init__(self, *a, **k)
        rend.Fragment.__init__(self, *a, **k)
        self.avatarId = avatarId
        self.db = db
        self.sysconf = confparse.Config()
        self.render_userBar = render_userBar
        self.lockStatus, self.lockTime, self.lockUser = isLocked()
        try:
            self.text = db[2]
            self.handler = db[3]
        except:
            print "Failed to get i18l module"
   

class DefaultPage(formal.ResourceMixin, rend.Page, VulaniMixin):
    isTool = False
    addSlash = True
    childPages = {}
    docFactory  = loaders.xmlfile('default.xml', templateDir=Settings.BaseDir+'/templates')

    pageMenu = []

    def __init__(self, avatarId = None, db = None, *a, **k):
        formal.ResourceMixin.__init__(self, *a, **k)
        rend.Page.__init__(self, *a, **k)
        self.avatarId = avatarId
        self.db = db
        self.sysconf = confparse.Config()
        self.render_userBar = render_userBar

        self.lockStatus, self.lockTime, self.lockUser = isLocked()
        try:
            self.text = db[2]
            self.handler = db[3]
        except:
            print "Failed to get i18l module"

    def childFactory(self, ctx, seg):
        if seg in self.childPages:
            return self.childPages[seg](self.avatarId, self.db)
        print "Passing childFactory"
        return rend.Page.childFactory(self, ctx, seg)

    def logout(self):
        print "Logged out"

class AdminLocked(DefaultPage):
    def render_content(self, ctx, data):
        return ctx.tag[
            tags.h3["Interface locked"],
            tags.p[
                "The interface is currently locked by %s. The administrative lock will automatically expire in %s seconds or when " %(
                    self.lockUser, 
                    (3600-self.lockTime)
                ),
                "they unlock the interface."
            ]
        ]

class ToolsPage(DefaultPage):
    addSlash = True
    isTool = True
    docFactory = loaders.xmlfile('tools.xml', templateDir = Settings.BaseDir + '/templates')

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src="/images/tools-lg.png")," ", self.text.tools]]

    def sideMenu(self, ctx, data):
        menu = {
            'Storage': {
                'Backups':      ('Backup',          'Manage backup system'),
                'File Browser': ('FileBrowser',     'Manage files')
            },
            'Diagnostics':{
                'Mail':             ('MailDiagnose', 'Perform mail diagnostics'), 
                'Network':          ('Diagnose',     'Perform network diagnostics'),
            }, 
            'Network': {
                'Routing':          ('Routing',     'Configure network routing'),
                'Firewall':         ('FirewallAjax',    'Configure Firewall rules and access policies'),
                #'FirewallAjax':     ('FirewallAjax',    'Configure Firewall rules and access policies'),
                'Interfaces':       ('Network',     'Configure network interface settings'),
                'Broadband':        ('PPP',         'Configure PPPoE broadband accounts'),
                'DHCP':             ('Dhcp',        'Configure DHCP settings'),
                'DNS':              ('DNS',         'Configure DNS settings')
            },
            'Telephony': {
                'PBX':              ('VoIP',        'Configure Voice over IP and Asterisk Configuration'),
            },
            'Remote Access': {
                'VPN':              ('VPN',         'Configure VPN settings'),
                'SSH':              ('SSH',         'Configure SSH settings'),
            },
            'Windows Network':{
                'Domain':           ('Domain',      'Configure groups and policies'),
                #'Setup':            ('DomainSetup', 'Domain settings')
                'Shares':           ('Samba',       'Configure file shares')
            },
            'Applications': {
                'Manage':          ('ManageApps',       'Manage add-on applications'),
            },
            'Mail': {
                'Mail Server':      ('Mailserver',  'Configure mail server and filtering'),
            },
            'Reporting':            ('Reporting',   'Configure reporting configuration'), 
            'UPS':                  ('UPS',         'UPS setup'), 
            'Updates':              ('SystemUpdate','Update Vulani'), 
            'Web Proxy':            ('Squid',       'Configure web proxy and content filtering'),
            'Profiles':             ('Profiles',    'Manage Vulani profiles'),
            #'High Availability':    ('HA',          'Configure high availability')
        }

        self.db[6].integrateTools(menu)
        
        menuStruct = []

        for k,v in menu.items():
            if isinstance(v, dict):
                # Is a sub menu
                subMenu = []
                for sk, sv in v.items():
                    subMenu.append(
                        tags.div(_class='sideMenuSub')[
                            tags.a(title=sv[1], href=url.root.child(sv[0]))[sk]
                        ]
                    )

                seg = tags.div(_class='sideMenuPrimary')[
                    tags.div(_class='sideMenuNames')[
                        k
                    ],
                    tags.div(_class='sideMenuSubExpander')[
                        subMenu
                    ]
                ]
            else:
                seg = tags.div(_class='sideMenuPrimary')[
                    tags.div(_class='sideMenuNames')[
                        tags.a(title=v[1], href=url.root.child(v[0]))[k]
                    ]
                ]

            menuStruct.append(seg)

        return [
            tags.div(_onclick="toggleSideMenu();", _class="sideMenuButtonShow") [
                tags.img(align="absmiddle", _class="sideMenuButtonLeft", src="/images/lefttab.png"),
                "Tools Menu",
                tags.img(align="absmiddle", _class="sideMenuButtonRight", src="/images/righttab.png")
            ],
            tags.div(id="sideMenuContent", _class="sideMenuContent", style="display: none")[
                tags.div(id="sideContTools")[
                    menuStruct
                ]
            ]
        ]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[
            self.sideMenu(ctx, data)
        ]

class Topology(rend.Page):
    addSlash = True
    def __init__(self, *a, **k):
        rend.Page.__init__(self, *a, **k)
        self.sysconf = confparse.Config()

    def drawImage(self, c, filename, position, center=False):
        x, y = position
        isurf = cairo.ImageSurface.create_from_png(filename)
        if center:
            h = isurf.get_height()
            w = isurf.get_width()
            x = position[0] - (w/2)
            y = position[1] - (h/2)

        c.set_source_surface(isurf, x, y)
        c.paint()

    def line(self, c, x,y, x1,y1):
        c.set_source_rgb(0.8, 0.8, 0.8)
        c.move_to(x, y)
        c.line_to(x1, y1)
        c.close_path()
        c.stroke()

    def text(self, cr, text, size, x, y):
        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.select_font_face("Georgia")
        cr.set_font_size(size)

        x_bearing, y_bearing, width, height = cr.text_extents(text)[:4]

        relx, rely = (width / 2, height / 2 )
        cr.move_to(x-relx, y-rely)
        cr.show_text(text)

    def parseTree(self, c, set, pheight, posY, posX, parent, xoffset):
        maxH = pheight
        if len(set) < 1:
            # Error
            return 
        partSize = maxH/len(set)
        #nodeGap = maxH/(len(set) - 1)

        topGap = partSize/2
        if isinstance(set, dict):
            setIter = set.items()
        else:
            setIter = set
        for node,edges in setIter:
            myPosY = posY + topGap
            if isinstance(edges, dict):
                self.parseTree(c, edges, partSize, posY, posX + xoffset, (posX, myPosY), xoffset)

            # Draw the node...
            text = node[1]
            skipped = False
            if node[1] == "Internet":
                if node[2] in self.balanced:
                    if not self.iLoc:
                        self.iLoc = (posX, myPosY)
                        y = myPosY + 33 
                        self.text(c, "%s" % text, 10, posX, y)
                        posY += partSize

                    self.drawLater.append(('/usr/local/tcs/tums/images/%s-general-64.png' % node[0], self.iLoc[0], self.iLoc[1]))
                    self.line(c, self.iLoc[0], self.iLoc[1], *parent)
                    return 
                else:
                    y = myPosY + 33 
            else:
                y = myPosY + 30
            
            self.drawLater.append(('/usr/local/tcs/tums/images/%s-general-64.png' % node[0], posX, myPosY))

            if text == "-":
                text = "<Device Route>"

            if "-" in text:
                text, iface = tuple(text.split('-'))
                self.text(c, "[%s]" % iface, 10, posX, y+12)

            self.text(c, text, 10, posX, y)
            if xoffset < 1:
                self.line(c, posX+15, myPosY, *parent)
            else:
                self.line(c, posX-15, myPosY, *parent)
            posY += partSize


    def renderHTTP(self, ctx):
        request = inevow.IRequest(ctx)
        
        def render(data):
            # Set our content dispositions and write the stream
            request.setHeader("content-type", "image/png")
            request.setHeader("content-length", str(len(data)))
            return data
        width = 700
        height = 64
        rHeight, lHeight = 0, 0

       
        # Internet side (left)
        locals = Utils.getLans(self.sysconf)

        wans = {}
        lans = {}
        leftSize = 0
        rightSize = 0

        balanceZones = {}

        for zone, ip, type in self.sysconf.ShorewallBalance:
            balance = 'balance' in type
            balanceZones[zone] = (balance, ip)
        self.balanced = []
        idefer = []
        for k,net in Utils.getNetworks(self.sysconf).items():
            routes = {}
            size = 1
            
            zone = Utils.getZone(self.sysconf, k)
            doneInet = False
            if zone in balanceZones:
                if balanceZones[zone][0]:
                    self.balanced.append(k)
                gate = balanceZones[zone][1]
                if gate:
                    # otherwise... wtf
                    routes[('router', gate)] = {('internet', 'Internet', k):None}
                    size = 3
                else:
                    # Get a new router icon for Link-route devices like PPPoE
                    routes[('router', 'LINK')]= {('internet', 'Internet', k):None}

            for dst,gate in self.sysconf.EthernetDevices[k].get('routes', []):
                if (dst == 'default') and (not doneInet):
                    if Utils.matchIP(net, gate):
                        # The default router sits on this segment
                        routes[('router', gate)] = {('internet', 'Internet', k): None}
                        if 3>size:
                            size = 3
                else:
                    # Another switch behind a router
                    routes[('router', gate)] = {('switch', dst): None}
                    size = 3

            if k in locals:
                node = ('switch', net+'-'+k)
                lans[node] = routes
                if size > rightSize:
                    rightSize = size
                rHeight += 64
            else:
                node = ('switch', net+'-'+k)
                if k in self.balanced:
                    idefer.append((node, routes))
                else:
                    wans[node] = routes

                if size > leftSize:
                    leftSize = size
                lHeight += 64

        for k,v in self.sysconf.WANDevices.items():
            routes = {}
            zone = Utils.getZone(self.sysconf, k)
            lHeight += 64
            if zone in balanceZones:
                if balanceZones[zone][0]:
                    self.balanced.append(k)
                gate = balanceZones[zone][1]
                # Get a new router icon for Link-route devices like PPPoE
                routes[('internet', 'Internet', k)] = None

            if 'defaultroute' in v.get('pppd', []):
                routes[('internet', 'Internet', k)] = None
            else:
                if k == self.sysconf.LocalRoute:
                    # Put a ZA flag here...
                    routes[('internet', 'Internet', k)] = None
            if not routes:
                routes[('switch', 'Cloud', k)] = None
                
            node = ('netlink', 'PPP '+k[-1])
            wans[node] = routes

        # Figure out our best dimensions
        mHeight = max([rHeight, lHeight])

        print "Total height", mHeight, rHeight, lHeight
        height = mHeight

        # Configure our context
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height+16)
        c = cairo.Context(surface)
        
        c.set_line_width(2)
 
        vloc = (width/2, height/2)  # Center of image (where vulani goes)

        wans = [i for i in wans.items()]
        wans.extend(idefer)
        #for node, routes in idefer:
        #    wans.append((node] = routes

        totalBreadth = leftSize + rightSize + 1
        print "Total width", totalBreadth, leftSize, rightSize
        xSteps = (width)/totalBreadth
        if leftSize:
            if leftSize == rightSize:
                vx = width/2
            else:
                vx = (xSteps * leftSize) + 56
        else:
            vx = 56

        vloc = (vx, height/2)

        self.drawLater = []
        posX = 64

        # Wans (left)
        self.iLoc = None
        self.parseTree(c, wans, height, 0, vloc[0]-xSteps, vloc, -xSteps)
        # Lans (right)
        self.parseTree(c, lans, height, 0, vloc[0]+xSteps, vloc, +xSteps)

        #self.text(c, "Hello", 10.5, 30,30)

        for i in self.drawLater:
            self.drawImage(c, i[0], (i[1], i[2]), True)
        self.drawImage(c, '/usr/local/tcs/tums/images/vulani-globe-64.png', vloc, True)
        
        out = StringIO.StringIO()
        surface.write_to_png(out)
        out.seek(0)
        return render(out.read())

class dataTableDelete(rend.Page):
    def __init__(self, avatarId = None, deleter = lambda _:None, post_delete = lambda _: None, *a, **k):
        formal.ResourceMixin.__init__(self, *a, **k)
        rend.Page.__init__(self, *a, **k)
        self.avatarId = avatarId
        self.sysconf = confparse.Config()
        self.deleter = deleter
        self.post_delete = post_delete
        
    def locateChild(self, ctx, segs):
        
        self.deleter(int(segs[0]))
        
        return self.post_delete(segs), ()

class DataTable(object):

    showDelete = True

    def __init__(self, page, name, description, base=None, sub=None):
        self.name = name
        self.description = description

        self.avatarId = page.avatarId
        self.sysconf = page.sysconf
        self.dtd = dataTableDelete(avatarId = page.avatarId, deleter = self.deleteItem, post_delete = self.returnAction)
        
        setattr(page, 'child_Delete%s'% self.name, self.dtd)
        setattr(page, 'form_add%s' % self.name, self.formAdd)

        self.base = base
        self.sub = sub 
        
    def formAdd(self, data):
        form = formal.Form()
        
        form.addField('editIndexNode', formal.Integer(), widgetFactory=formal.Hidden)
        self.addForm(form)
        
        form.addAction(self.submitAdd)
        
        return form
        
    def getTable(self):
        pass
        
    def addForm(self, form):
        pass

    def filterData(self, data):
        return data
        
    def addAction(self, idata):
        # A simple default action
        data = self.filterData(idata)
        conf = getattr(self.sysconf, self.base)
        heads = self.getTable()[0]
        if len(heads) > 1:
            block = []
            for d, i in heads:
                block.append(data[i].encode('ascii', 'replace'))
        else:
            block = data[heads[0][1]].encode('ascii', 'replace')

        if self.sub:
            if not conf.get(self.sub):
                conf[self.sub] = []
            conf[self.sub].append(block)
        else:
            conf.append(block)
 
        setattr(self.sysconf, self.base, conf)

    def deleteItem(self, item):
        conf = getattr(self.sysconf, self.base)
        
        if self.sub:
            print conf[self.sub]
            del conf[self.sub][int(item)]
        else:
            # If no sub item assume it is a direct list
            del conf[int(item)]

        setattr(self.sysconf, self.base, conf)

    def editAction(self, item, data):
        """ Default edit command which just deletes and then adds a new element """
        self.deleteItem(item)
        del data['editIndexNode']
        self.addAction(data)

    def submitAdd(self, c, f, data):
        if data['editIndexNode'] != None:
            self.editAction(data['editIndexNode'], data)
        else:
            self.addAction(data)
        
        return self.returnAction(data)
        
    def returnAction(self, data):
        pass

    def jsData(self, headings, rows):
        """ Creates the JS row data table for populating the form """
        headings, rows = self.getTable()
        mrows = []
        for c,r in enumerate(rows):
            # Listify anything
            if not (isinstance(r, list) or isinstance(r, tuple)):
                r = [r.encode('ascii', 'replace')]

            mrows.append(map(str, r))

        return mrows

    def formatTable(self, headings, rows):
        newRows = []
        for c,r in enumerate(rows):
            # Listify stuff
            if not(isinstance(r, list) or isinstance(r, tuple)):
                r = [r.encode('ascii', 'replace')]
            # Create our actual row renderers
            actionLinks = [
                    self.showDelete and tags.a(href="Delete%s/%s/" % (self.name, c))[tags.img(src="/images/ex.png")] or "",
                    " ",
                    tags.img(src="/images/edit.png", onclick="editElm%s(%s);" % (self.name, c))
            ]
            newRows.append(
                tuple(list(r) + [actionLinks])
            )
        return newRows

    def extraJs(self):
        return ""
        
    def applyTable(self, page):
        headings, rows = self.getTable()
        headings.append(('', ''))

        mrows = self.jsData(headings, rows)
        newRows = self.formatTable(headings, rows)

        return [
            tags.xml("""
            <script type="text/javascript">
            function editElm%(name)s(index){
                var exRows = %(rows)s;
                var heads = %(headings)s;
                getElement('add%(name)s-editIndexNode').value=index;
                var c = 0;
                forEach(heads, function(el){
                    try {
                        var input = getElement('add%(name)s-'+el);
                        if (!input) {
                            $$('#add%(name)s-'+el+'-field').each(function(nel) {
                                alert(nel);
                            });
                            alert ("GOTHERE");
                        } 
                        else if (input.nodeName == "INPUT"){
                            if (input.type == "checkbox"){
                                var newVal = exRows[index][c].toLowerCase();
                                //if("," in newVal) {
                                //    newVal = newVal.split(",");
                                //    alert(newVal);
                                //    alert(input);
                                //} else {
                                    input.checked = (newVal == "yes") || (newVal == "true");
                                //}
                            }
                            else {
                                input.value = exRows[index][c];
                            }
                        }
                        else if (input.nodeName == "SELECT") {
                            var inc = 0
                            forEach(input.options, function(opt){
                                if (opt.value == exRows[index][c]){
                                        input.selectedIndex = inc;
                                }
                                inc ++;
                            });
                        };
                    }
                    catch (dc) {}; // Ignore colums which are unparsable - look at PPP config for why ;)
                    %(extra)s
                    c++;
                });
                hideElement('addHead%(name)s');
                showElement('editHead%(name)s');
            }
            </script>
            """ % {
                'name': self.name,
                'rows': mrows, 
                'headings': map(lambda _:_[1].encode('ascii', 'replace') ,headings[:-1]), 
                'extra': self.extraJs()
            }),
            dataTable(map(lambda _:_[0] ,headings), newRows, sortable = True),
            tags.br,
            tags.h3(id='addHead%s' % self.name)["Add %s" % self.description],
            tags.h3(id='editHead%s' % self.name, style='display: none;')["Edit %s" % self.description],
            tags.directive('form add%s' % self.name)
        ]

def resUrlQuery(ctx,maxItems=15):
    if not ctx:
        return {}
    queryList = url.URL.fromContext(ctx).queryList()
    if len(queryList) > 15:
        raise Exception("Max items in the URL queryList")
    output = {}
    for i in queryList:
        output[i[0]] = i[1]
    return output

# Dragable tables

class TableWidget(athena.LiveFragment):
    jsClass = u"tableWidget"

    docFactory = loaders.xmlfile('tableWidget.xml', templateDir = '/usr/local/tcs/tums/templates')

    tableName = "dragTable"

    def __init__(self, *a, **kw):
        athena.LiveFragment.__init__(self, *a, **kw)
        self.sysconf = confparse.Config()

    def getData(self):
        # Returns 2D array of table data, and the headers
        return [[u"<a href='/'>Foo!</a>",2], [3,4]], [u"Number 1", u"Number 2"]
    athena.expose(getData)

    def tableChanged(self, rowOrder):
        print "New row order", rowOrder
        pass
    athena.expose(tableChanged)

    def getTableName(self):
        return unicode(self.tableName)

    athena.expose(getTableName)

    def render_tableSlot(self, ctx, tag):
        return ctx.tag[tags.div(id=self.tableName)[""]]


class TumsExceptionHandler:
    implements(inevow.ICanHandleException)

    def renderHTTP_exception(self, ctx, reason):
        conf = confparse.Config()
        now = time.time()
        hash = sha.sha("%s%s" % (conf.CompanyName, now)).hexdigest()
        refNo = sum([ord(i) for i in hash+hash])
        log.err(reason)
        request = inevow.IRequest(ctx)
        request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        request.write('<html><head><title>Vulani Error</title><link rel="stylesheet" type="text/css" href="/css/style.css"/></head><body>')
        request.write('<div id="pageTitle"><img id="pageTitleLogo" src="/images/vulani-tums.png" alt=""/>')
        request.write('</div>')
        request.write('<div id="sideContainer"><div id="pageNote">Error</div>')
        request.write('<div id="pageSide">&nbsp;</div></div>')
        request.write('<div id="pageContent">')
        request.write("<h3>An error has occured</h3><p>An error has occurred. We apologise for this inconvenience.</p>")
        request.write('<div style="height:25em; width:50em; overflow: auto;">')
        
        from nevow import failure
        st = flat.flatten(failure.formatFailure(reason))
        print type(st), "ERROR"
        result = ''.join(st)
        resHead = result.split('<a href="#tracebackEnd">')[0].replace('font-size: large;', '')
        realError = result.split('<div class="frame">')[-1]
        print realError
        result = resHead + '<div><div class="frame">' + realError

        if not 'stfu' in dir(Settings):
            Utils.sendMail("%s <tums@thusa.net>" % Settings.LDAPOrganisation, ["notify@thusa.co.za"], "[REF: %s] TUMS Error" % refNo, result, html=True)

        request.write(result)
        request.write('</div></div>')
        request.write("</body></html>")

        request.finishRequest( False )

    def renderInlineException(self, context, reason):
        from nevow import failure
        formatted = failure.formatFailure(reason)
        desc = str(reason)
        return flat.serialize([
            stan.xml("""<div style="border: 1px dashed red; color: red; clear: both" onclick="this.childNodes[1].style.display = this.childNodes[1].style.display == 'none' ? 'block': 'none'">"""),
            desc,
            stan.xml('<div style="display: none">'),
            formatted,
            stan.xml('</div></div>')
        ], context)


