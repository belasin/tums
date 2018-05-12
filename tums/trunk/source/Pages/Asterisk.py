from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from zope.interface import implements
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy, confparse, Utils, WebUtils, PBXUtils
from Pages import Tools
import formal

import datetime
import time

from twisted.python import log

PageRoot = "VoIP"

def restartAsterisk():
    return WebUtils.system(Settings.BaseDir+"/configurator --debzaptel; "+Settings.BaseDir+'/configurator --pbx; /etc/init.d/asterisk reload; asterisk -r -x "ael reload"')

def restartSnom(macAddr):
    return WebUtils.system('/usr/sbin/asterisk -r -x "sip notify reboot-snom %s"' % macAddr)

def returnRoot(_):
    return url.root.child('VoIP')

def checkForAsterisk():
    """Check that asterisk exists"""
    return os.path.exists('/etc/asterisk/') and os.path.exists('/usr/sbin/asterisk')

class DevicePortList(PageHelpers.DataTable):

    showDelete = False

    def __init__(self, page, name, description, device, hw):
        PageHelpers.DataTable.__init__(self, page, name, description)
        self.device = device
        self.deviceName = device.name
        self.hw = hw

    def genFormElements(self, form, paramList):
        def flattenDict(dictIn):
            return [(k, dictIn[k])for k in dictIn.keys()]
        for param in paramList:
            form.addField(param.name, formal.String(required=False),
                formal.widgetFactory(formal.SelectChoice, options=flattenDict(param.options)), label = param.human_name)

    def addForm(self, form):

        #contexts = self.sysconf.PBX.get('contexts', {}).keys()

        form.addField('portnum', formal.Integer(required=True), 
            formal.widgetFactory(formal.SelectChoice, options=self.getPortList()), label = "Port Name")
        #form.addField('context', formal.String(required=True),
        #    formal.widgetFactory(formal.SelectChoice, options=[(i,i) for i in contexts]), label = "Routing Context")
        self.genFormElements(form, self.device.portParam)

    def addAction(self, data):
        Utils.log.msg('Port %s configured' % (data['portnum']))
        dataOut = {}
        #if data['context'] == self.device['context']:
        #    dataOut = {}
        #else:
        #    dataOut = {
        #        'context': data['context']
        #    }
        for param in self.device.portParam:
            dataOut[param.name] = data[param.name]

        print dataOut
        self.device[data['portnum']] = dataOut
        
    def returnAction(self, data):
        return restartAsterisk().addCallback(returnRoot)

    def deleteItem(self, item):
        pass

    def getPortList(self):
        return [(k,port[0]) for k, port in enumerate(self.device)]

    def getTable(self):
        portDetails = []
        headings = [("#", 'portnum'), ("Port Name", "name"), ("Status", "status"), ("Context",'context'), ("Groups", 'groups')]
        for param in self.device.portParam:
            headings.append((param.human_name, param.name))

        for k, port in enumerate(self.device):
            pn = k
            if self.device.isEnabled():
                status = "Enabled %s" % (port[2] or "")
            else:
                status = "Disabled"
            vals = [
                k,
                port[0],
                status,
                self.device[pn]['context'],
                str.join(",", self.device.getPortGroups(k)),
            ]
            for param in self.device.portParam:
                vals.append(self.device[k][param.name])
            portDetails.append(vals)

        return headings, portDetails
    

class DeviceEditPage(Tools.Page):

    deviceName = None

    device = None

    def __init__(self, avatarId, db, deviceName=None, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, avatarId, db, *a, **kw)
        self.hw = PBXUtils.PBXHardware()
        self.hw.detect()
        if deviceName:
            self.deviceName = deviceName
            self.device = self.hw[deviceName]
            self.deviceportlist = DevicePortList(self, "DevicePortList", "deviceport", self.device, self.hw)
            print self.device
            
    def genFormElements(self, form, paramList):
        def flattenDict(dictIn):
            return [(k, dictIn[k])for k in dictIn.keys()]
        for param in paramList:
            form.addField(param.name, formal.String(required=True),
                formal.widgetFactory(formal.SelectChoice, options=flattenDict(param.options)), label = param.human_name)

    def form_confdev(self, ctx):
        form = formal.Form()
        form.addField('enabled', formal.Boolean(), label = "Enable Device")
        #contexts = self.sysconf.PBX.get('contexts', {}).keys()
        #form.addField('context', formal.String(required=True), 
        #    formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in contexts]), 
        #    label = "Default context", 
        #    description = "The default context that handles routing of initiated calls from this device")
        self.genFormElements(form, self.device.cardParam)
        data = {
            "enabled": self.device.isEnabled(),
            #"context": self.device["context"],
        }
        for param in self.device.cardParam:
            data[param.name] = self.device[param.name]
        form.data = data
        form.addAction(self.confdev)
        return form
        
    def confdev(self, ctx, form, data):

        if data['enabled']:
            self.device.enable();
        else:
            self.device.disable();

        for param in self.device.cardParam:
            self.device[param.name] = data[param.name]

        #currentContext = self.device['context']
        #for k,port in enumerate(self.device):
        #    if self.device[k]['context'] == currentContext:
        #        self.device[k]['context'] = data['context']
            
        #self.device['context'] = data['context']
        return restartAsterisk().addCallback(returnRoot)
        #return url.root.child('VoIP')

    def render_content(self,ctx,data):
        return ctx.tag[
            tags.h3["Edit Device %s" % self.deviceName],
            PageHelpers.TabSwitcher((
                ('Settings'    , 'panelConfig'),
                ('Ports'       , 'panelMembers'),
            ), id = "zones"),
            tags.div(id="panelConfig", _class="tabPane")[
                tags.directive("form confdev")
            ],
            tags.div(id="panelMembers", _class="tabPane")[
                self.deviceportlist.applyTable(self)
            ],
            PageHelpers.LoadTabSwitcher(id="zones")
        ]


    def childFactory(self, ctx, segs):
        if not self.deviceName:
            devName = segs.replace('_','/')
            try:
                dev = self.hw[devName]
            except Exception, exp:
                print exp
                return Tools.Page.childFactory(self, ctx, segs) #Hmm Not found go away
            return DeviceEditPage(self.avatarId, self.db, devName) #Here is your new instance
        return Tools.Page.childFactory(self, ctx, segs)
        
class HardwareProvider(PageHelpers.DataTable):
    
    def __init__(self, page, name, description):
        PageHelpers.DataTable.__init__(self, page, name, description)
        self.hw = page.hw

    def getDevList(self):
        devList = []

        for pluginName, plugin in self.hw.plugins.items():
            for groupNum in plugin.getGroupList():
                gn = str(plugin._genGroupNumName(groupNum))
                devList.append((gn,gn))

        for dev in self.hw:
            for port in dev:
                if dev.pluginEntity.getPortGroup(port[0]):
                    continue
                devList.append((port[0],port[0]))
        return devList

    def getTable(self):
        headings = [
            ('Name',            'name'),
            ('Trunk',           'trunk'),
            #('Default Context', 'context'),
            ('Device',          'device'),
        ]
        providers = self.sysconf.PBXProviders
        providerTable = []
        for name, pr in providers.items():
            if pr['type'] == "hardware":
                providerTable.append(
                    [
                        name,
                        pr['trunk'],
                        #pr['context'],
                        pr['device']
                    ]
                )

        # Try to ensure we have the same order (dicts are not ordered)
        providerTable.sort()

        return headings, providerTable

    def addForm(self, form):
        #contexts = self.sysconf.PBX.get('contexts', {}).keys()

        form.addField('name', formal.String(required=True), label = "Provider Name", 
            description = "A single alpha-numeric word describing this provider. If Branch is selected, this MUST match the remote username for IAX")

        #form.addField('context', formal.String(required=True), 
        #    formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in contexts]), 
        #    label = "Default context(Inbound Context)", 
        #    description = "The default context for calls proceding over this provider")

        form.addField('trunk', formal.Boolean(), label = "Trunking", 
            description = "Enable call trunking for this provider")

        form.addField('device', formal.Sequence(formal.String(), required=True),
            formal.widgetFactory(formal.CheckboxMultiChoice, options=self.getDevList()),
            label = "Devices",
            description = "Devices to try and terminate the call onto")

        form.data['trunk'] = True

    def deleteItem(self, item):
        conf = self.sysconf.PBXProviders
        rt = self.getTable()[1]
        del conf[rt[int(item)][0]]
        self.sysconf.PBXProviders = conf

    def addAction(self, idata):
        conf = self.sysconf.PBXProviders

        cb = {
            'type': "hardware", 
            'context': 'incomming', 
            'trunk': idata['trunk'], 
            'device': [i.encode('ascii', 'replace') for i in idata['device']]
        }
        cbName = Utils.filterString(idata['name'].encode('ascii', 'replace'), Utils.F_ALPHANUM)

        if cbName in conf:
            if conf[cbName]['type'] != "hardware":
                return

        conf[cbName] = cb

        self.sysconf.PBXProviders = conf
    
    def returnAction(self, data):
        return restartAsterisk().addCallback(returnRoot)

class Queues(PageHelpers.DataTable):

    strategyOptions = [
        'ringall',
        'roundrobin',
        'leastrecent',
        'fewestcalls',
        'random',
        'rrmemory',
        'linear',
    ]

    def getTable(self):
        headings = [
            ('Name',            'name'),
            ('Stategy',         'strategy'),
            ('Timeout',         'timeout'),
            ('Announce',        'announce'),
            ('Answer',          'answer'),
            ('Extension',       'extNumber0'),
            ('',                'extNumber1'),
            ('',                'extNumber2'),
            ('',                'extNumber3'),
        ]

        queueTable = []

        for name, qDetails in self.sysconf.PBX.get('queues', {}).items():
            ext = ['','','','']
            for k, extNum in enumerate(qDetails.get('extensions', [])):
                ext[k] = extNum
            queueTable.append([
                name,
                qDetails['strategy'],
                qDetails['timeout'] and qDetails['timeout'] or 0,
                qDetails['announce'] and 'Yes' or 'No',
                qDetails.get('answer', True) and 'Yes' or 'No',
                ext[0],
                ext[1],
                ext[2],
                ext[3]
            ])

        return headings, queueTable

    def addForm(self, form):
        extList = PBXUtils.getAvaExtenNumSelect(False)
        #for ext in PBXUtils.getAvailibleExtensions():
        #    extList.append((str(ext), str(ext)))

        form.addField('name', formal.String(required=True), label = "Queue Name")
        form.addField('extNumber0', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber1', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber2', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber3', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('strategy', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in self.strategyOptions]),
            label = "Strategy", 
            description = tags.ul[
                tags.li["ringall: ring all available channels until one answers"],
                tags.li["roundrobin: take turns ringing each available interface"],
                tags.li["leastrecent: ring interface which was least recently called by this queue"],
                tags.li["fewestcalls: ring the one with fewest completed calls from this queue"],
                tags.li["random: ring random interface", "rrmemory: round robin with memory, remember where we left off last ring pass"],
                tags.li["linear: Rings interfaces in the order they are listed in the configuration file."]]
        )
        form.addField('timeout', formal.Integer(), label = "Ring Timeout", description = "How long a phone should before we try the next one")
        form.addField('announce', formal.Boolean(), label = "Announce", description = "Announnce queue posistion every 30 seconds")
        form.addField('answer', formal.Boolean(), label = "Answer Call", description = "Should we answer calls and play music, or should we just send ringing")

    def addAction(self, data):
        queues = self.sysconf.PBX.get('queues', {})
        nData = {
            'strategy': data['strategy'],
            'timeout': data['timeout'],
            'announce': data['announce'],
            'answer': data['answer'],
            'extensions': []
        }
        for i in range(4):
            ext = data['extNumber%s'%i]
            if ext:
                nData['extensions'].append(ext)
        queues[data['name']] = nData
        PBX = self.sysconf.PBX
        PBX['queues'] = queues
        self.sysconf.PBX = PBX

    def deleteItem(self, item):
        PBXQueues = self.sysconf.PBX.get('queues', {})
        if item < len(PBXQueues):
            k, entry = PBXQueues.items()[item]
            del PBXQueues[k]
            PBX = self.sysconf.PBX
            PBX['queues'] = PBXQueues
            self.sysconf.PBX = PBX

    def returnAction(self, data):
        return restartAsterisk().addCallback(returnRoot)

class Faxing(PageHelpers.DataTable):

    def getTable(self):
        headings = [
            ('Name',            'name'),
            ('Email',           'email'),
            ('Extension',       'extNumber0'),
            ('',                'extNumber1'),
            ('',                'extNumber2'),
            ('',                'extNumber3'),
        ]

        queueTable = []

        for name, qDetails in self.sysconf.PBX.get('faxing', {}).items():
            ext = ['','','','']
            for k, extNum in enumerate(qDetails.get('extensions', [])):
                ext[k] = extNum
            queueTable.append([
                name,
                qDetails['email'],
                ext[0],
                ext[1],
                ext[2],
                ext[3]
            ])

        return headings, queueTable

    def addForm(self, form):
        extList = PBXUtils.getAvaExtenNumSelect(False)

        form.addField('name', formal.String(required=True), label = "Fax Name")
        form.addField('email', formal.String(required=True), label = "Delivery Email", description="Destination email addresses that should be used to deliver recieved faxes (use a comma to seperate multiple email addresses)")
        form.addField('extNumber0', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber1', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber2', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber3', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))

    def addAction(self, data):
        faxing = self.sysconf.PBX.get('faxing', {})
        nData = {
            'email': data['email'],
            'extensions': []
        }
        for i in range(4):
            ext = data['extNumber%s'%i]
            if ext:
                nData['extensions'].append(ext)
        faxing[data['name']] = nData
        PBX = self.sysconf.PBX
        PBX['faxing'] = faxing
        self.sysconf.PBX = PBX

    def deleteItem(self, item):
        PBXFax = self.sysconf.PBX.get('faxing', {})
        if item < len(PBXFax):
            k, entry = PBXFax.items()[item]
            del PBXFax[k]
            PBX = self.sysconf.PBX
            PBX['faxing'] = PBXFax
            self.sysconf.PBX = PBX

    def returnAction(self, data):
        return restartAsterisk().addCallback(returnRoot)

class MeetMe(PageHelpers.DataTable):
    """Provides MeetMe forms to facilitate the configuration of the conferencing functionality"""
    def getTable(self):
        headings = [
            ('Number',          'confno'),
            ('Pin',             'pin'),
            ('AdminPin',        'adminpin'),
            ('Extension',       'extNumber0'),
            ('',                'extNumber1'),
            ('',                'extNumber2'),
            ('',                'extNumber3'),

        ]

        meetMeTable = []

        for confno, mDetails  in self.sysconf.PBX.get('meetme', {}).items():
            ext = ['','','','']
            for k, extNum in enumerate(mDetails.get('extensions', [])):
                ext[k] = extNum
            meetMeTable.append([
                confno,
                mDetails['pin'] and mDetails['pin'] or "",
                mDetails['adminpin'] and mDetails['pin'] or "",
                ext[0],
                ext[1],
                ext[2],
                ext[3]
            ])

        return headings, meetMeTable

    def addForm(self, form):
        extList = PBXUtils.getAvaExtenNumSelect(False)

        form.addField('confno', formal.String(required=True), label = "Conference Number", description = "A number that uniquely sets this conference room apart from the other conference rooms")
        form.addField('pin', formal.String(), label= "Pin Number", description="In order to access the conference you will be prompted for this number")
        form.addField('adminpin', formal.String(), label="Admin Pin")
        form.addField('extNumber0', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber1', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber2', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))
        form.addField('extNumber3', formal.String(required=False), formal.widgetFactory(formal.SelectChoice, options = extList))

    def addAction(self, data):
        meetme = self.sysconf.PBX.get('meetme', {})
        nData = {
            'pin': data['pin'],
            'adminpin': data['adminpin'],
            'extensions': []
        }
        for i in range(4):
            ext = data['extNumber%s'%i]
            if ext:
                nData['extensions'].append(ext)
        meetme[data['confno']] = nData
        PBX = self.sysconf.PBX
        PBX['meetme'] = meetme
        self.sysconf.PBX = PBX

    def deleteItem(self, item):
        PBXMeetMe = self.sysconf.PBX.get('meetme', {})
        if item < len(PBXMeetMe):
            k, entry = PBXMeetMe.items()[item]
            del PBXMeetMe[k]
            PBX = self.sysconf.PBX
            PBX['meetme'] = PBXMeetMe
            self.sysconf.PBX = PBX

    def returnAction(self, data):
        return restartAsterisk().addCallback(returnRoot)

class VoipProvider(PageHelpers.DataTable):
    matchableType = ['iax2', 'sip', 'vox', 'worldchat']

    def getTable(self):
        headings = [
            ('Name',            'name'),
            ('Hostname',        'hostname'),
            ('Username',        'username'),
            ('Password',        'password'),
            ('Type',            'type'),
            ('Codecs',          'codecs'), 
            ('Trunk',           'trunk'),
            ('Call Limit',      'callLimit'),
            #('Default Context', 'context'),
            ('Register',          'register')
        ]
        providers = self.sysconf.PBXProviders

        providerTable = []

        for name, pr in providers.items():
            if pr['type'] in self.matchableType:
                providerTable.append(
                    [
                        name,
                        pr['hostname'], 
                        pr['username'], 
                        pr['password'],
                        pr['type'],
                        ', '.join(pr['codecs']),
                        pr['trunk'],
                        pr.get('calllimit', ""),
                        #pr['context'], 
                        pr['register']
                    ]
                )

        # Try to ensure we have the same order (dicts are not ordered)
        providerTable.sort()

        return headings, providerTable

    def addForm(self, form):
        providerTypes = [
            #("vulani", "Vulani"),
            ("iax2",   "IAX2"), 
            ("sip",    "SIP"),
            (None,    "--Presets--"),
            ("vox",    "Vox Telecom"),
            ("worldchat", "Worldchat")
        ]

        #contexts = self.sysconf.PBX.get('contexts', {}).keys()

        codecs = PBXUtils.getCodecs()

        form.addField('name', formal.String(required=True), label = "Provider Name", 
            description = "A single alpha-numeric word describing this provider. If Branch is selected, this MUST match the remote username for IAX")
        form.addField('hostname', formal.String(required=True), label = "Hostname", 
            description = "The hostname of the provider server")
        form.addField('username', formal.String(required=True), label = "Username")
        form.addField('password', formal.String(required=True), label = "Password")
        form.addField('callLimit', formal.Integer(), label="Call Limit", description="Set this to define the maximum allowed concurrent calls through this provider")
        
        form.addField('type', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = providerTypes), 
            label = "Type", 
            description = "The type of provider")
        
        form.addField('codecs', formal.Sequence(formal.String()), formal.widgetFactory(formal.CheckboxMultiChoice, [(i,i) for i in codecs]),
            label = "Codecs")

        #form.addField('context', formal.String(required=True), 
        #    formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in contexts]), 
        #    label = "Default context(Inbound Context)", 
        #    description = "The default context for calls proceding over this provider")

        form.addField('trunk', formal.Boolean(), label = "Trunking", 
            description = "Enable call trunking for this provider")

        #form.addField('branch', formal.Boolean(), label = "Branch", 
        #    description = "Tick this option if this is a branch exchange")

        form.addField('register', formal.Boolean(), label= "Register",
            description = "Register with the end point")

        #rouList = self.sysconf.PBXRouters.keys()


        #form.addField('providerExtOutbound', formal.Sequence(formal.String()),
        #    formal.widgetFactory(formal.CheckboxMultiChoice,
        #        options=[(i,i) for i in rouList]),
        #    label = "Allowed Routers",
        #    description = "Exposes the selected routers to the provider for routing their calls"),

        form.data = {
            'trunk': True
        }

    def deleteItem(self, item):
        conf = self.sysconf.PBXProviders
        rt = self.getTable()[1]

        del conf[rt[int(item)][0]]

        self.sysconf.PBXProviders = conf

    def addAction(self, idata):
        conf = self.sysconf.PBXProviders

        cb = {
            'hostname': idata['hostname'].encode('ascii', 'replace'), 
            'username': idata['username'].encode('ascii', 'replace'), 
            'password': idata['password'].encode('ascii', 'replace'), 
            'type': idata['type'].encode('ascii', 'replace'), 
            'calllimit': idata['callLimit'],
            'context': 'incomming', 
            'register': idata['register'],
            'trunk': idata['trunk'], 

            'codecs': [i.encode('ascii', 'replace') for i in idata['codecs']]
        }
        cbName = Utils.filterString(idata['name'].encode('ascii', 'replace'), Utils.F_ALPHANUM)

        conf[cbName] = cb

        self.sysconf.PBXProviders = conf
    
    def returnAction(self, data):
        Utils.log.msg('%s added relay mail domain %s' % (self.avatarId.username, repr(data)))
        return restartAsterisk().addCallback(returnRoot)

class ExtensionSets(PageHelpers.DataTable):
    def getTable(self):
        headings = [('Extension', 'extension'), ('Extension Count', 'noExtensions')]
        extensions = self.sysconf.PBX.get('extension', {})
        data = [[ext, extensions[ext]] for ext in extensions]
        return headings, data 

    def addForm(self, form):
        form.addField('extension', formal.Integer(required = True), label="Extension", description="First number in the extension list that will be made availible for routing internal extension termination")
        form.addField('noExtensions', formal.Integer(required = True), label="Extension Count", description="Number of availible extension from this base extension")
        form.addField('removeConflict', formal.Boolean(), label = "Remove Conflicts", description = "If the current entry conflicts with an existing extension range then we should remove those entries")

    def addAction(self, data):
        ext = data['extension']
        cnt = data['noExtensions']
        PBXExt = self.sysconf.PBX.get('extension', {})
        removeList = []
        for curExt in PBXExt:
            maxExt = PBXExt[curExt] + curExt
            if ext > curExt and ext <= maxExt:
                removeList.append(curExt)
        if data['removeConflict']:
            for remEnt in removeList:
                del PBXExt[remEnt]

            removeList = None

        if not removeList: #if there are no resolved conflicts then add
            PBXExt[ext] = cnt
            PBX = self.sysconf.PBX
            PBX['extension'] = PBXExt
            self.sysconf.PBX = PBX

    def deleteItem(self, item):
        PBXExt = self.sysconf.PBX.get('extension', {})
        if item < len(PBXExt):
            k, entry = PBXExt.items()[item]
            del PBXExt[k]
            PBX = self.sysconf.PBX
            PBX['extension'] = PBXExt
            self.sysconf.PBX = PBX

    def returnAction(self, data):
        #Utils.log.msg('%s added allowed domain %s' % (self.avatarId.username, repr(data)))
        return restartAsterisk().addCallback(returnRoot)

class Page(Tools.Page):
    addSlash = True

    def __init__(self, *a, **kw):
        PageHelpers.DefaultPage.__init__(self, *a, **kw)
        self.addVoipProvider        = VoipProvider  (self, 'VoipProvider',  'VoIP provider', 'PBXProviders')
        self.addExtensionSet        = ExtensionSets (self, 'ExtensionSets', 'Extensions Set')
        self.queueManagement        = Queues(self,'Queues', 'Queue Management')
        self.faxManagement          = Faxing(self,'Faxing', 'Fax Management')
        self.MeetMeManagement       = MeetMe(self,'MeetMe', 'Conference/MeetMe Management')
        try:
            self.hw = PBXUtils.PBXHardware()
            #Get a list of Routable Endpoints
            self.hw.detect()
            self.addHardwareProvider    = HardwareProvider  (self, 'HardwareProvider',  'Hardware provider')
        except Exception, _exp:
            print "Caught Exception %s" % _exp
            self.hw = None
            self.addHardwareProvider = ""

    def form_pbxConfig(self, data):
        form = formal.Form()

        form.addField('enablePBX', formal.Boolean(), label = "Enable PBX", 
            description = "When selected says that Vulani will maintain the configuration files for asterisk")

        if PBXUtils.enabled():
            form.addField('recordAll', formal.Boolean(), label = "PBX Recording",
                description = "Enables call monitoring on the switchboard")
            form.addField('timeout', formal.Integer(), label = "Default Timeout", description = "The default amount of time that should be allowed to expire before assuming that the extension is away")
            form.addField('fallThrough', formal.String(),
                formal.widgetFactory(formal.SelectChoice, options = PBXUtils.getExtensionSelect()),
                label = "Default Fallthrough",
                description = "If for any reason a call is not routable or picked up (with the exception when voicemail exists on an extension) the call will be forwarded to this extension"
            )
            form.addField('qtimeout', formal.Integer(), label = "Default Queue Timeout", description = "Default amount of time that should be allowed to expirebefore attempting the next member in a queue")

        form.addField('addPCodec', formal.Boolean(), label = "Enable g729/g723",
            description = [
                "Installs and enables g729 and g723 codecs for this server", tags.br,
                tags.b["Warning:"],
                "To use G.729 or G.723.1 you may need to pay a royalty fee. Please see http://www.sipro.com for details. If a patent exists in your country for G.729 or G.723.1 then you should contact the owner of that patent and request their permission before installing this codec, also note that you will need a valid internet connection in order to allow for the software to aquire the codec for you."])

        form.data = {
            'enablePBX': PBXUtils.enabled(),
            'addPCodec': self.sysconf.PBX.get('addPCodec', False),
            'recordAll': self.sysconf.PBX.get('recordCalls', True),
            'fallThrough': self.sysconf.PBX.get('fallThrough', ""),
            'timeout': self.sysconf.PBX.get('timeout', 30),
            'qtimeout': self.sysconf.PBX.get('qtimeout', 30),
            'addPCodec': self.sysconf.PBX.get('enablePCodec', False)
        }

        form.addAction(self.submitForm)
        return form

    def submitForm(self, ctx, form, data):
        Utils.log.msg('%s altered pbx configuration %s' % (self.avatarId.username, repr(data)))
        blockedFiles = []
        pbxConf = self.sysconf.PBX

        if data['enablePBX']:
            pbxConf["enabled"] = True
        else:
            pbxConf["enabled"] = False

        pbxConf['addPCodec'] = data.get('addPCodec', False)
        pbxConf['recordAll'] = data.get('recordAll', True)
        pbxConf['fallThrough'] = data.get('fallThrough', "")
        pbxConf['timeout'] = data.get('timeout', 30)
        pbxConf['qtimeout'] = data.get('qtimeout', 30)
        pbxConf['enablePCodec'] = data.get('addPCodec', False)

        self.sysconf.PBX = pbxConf
        return restartAsterisk().addCallback(returnRoot)

    def render_contexts(self, ctx, data):
        #context = self.sysconf.PBX.get('contexts', {})
        context = None

        if not context:
            # Create a default and save it
            context = {
                'incomming': {},
                'outgoing': {},
                'local'   : {}
            }
        
            p = self.sysconf.PBX
            p['contexts'] = context
            self.sysconf.PBX = p
        
        dt = []
        for k in context:
            dt.append((k, tags.a(href="DelContext/%s" % k)[tags.img(src="/images/firewall/delete-icon-hover.png")]))

        return ctx.tag[
            PageHelpers.dataTable([('istr', 'Context'), ('istr', '')], dt, sortable=True)
        ]


    def form_addExtensionGroup(self, data):
        form = formal.Form()
        form.addField('group', formal.String(), label = "Group")
        form.addAction(self.addExtensionGroup)
        return form

    def addExtensionGroup(self, ctx, form, data):
        Utils.log.msg('%s created extension group %s' % (self.avatarId.username, repr(data)))
        pbxConf = self.sysconf.PBXExtensions

        gname = Utils.filterString(data['group'].encode('ascii', 'replace'), Utils.F_ALPHANUM)

        pbxConf[gname] = {}

        self.sysconf.PBXExtensions = pbxConf
        return restartAsterisk().addCallback(returnRoot)

    def render_extensions(self, ctx, data):
        tabList = [
            ("Queues", "panelQueue"),
            ("Faxing", "panelFax"),
            ("Conferencing", "panelMeetMe"),
            ("Extension Sets", "panelExten"),
        ]

        return ctx.tag[
            PageHelpers.TabSwitcher(tabList, id="pbxextens"),
            tags.div(id="panelQueue", _class="tabPane")[
                self.queueManagement.applyTable(self)
            ],
            tags.div(id="panelFax", _class="tabPane")[
                self.faxManagement.applyTable(self)
            ],
            tags.div(id="panelMeetMe", _class="tabPane")[
                self.MeetMeManagement.applyTable(self)
            ],
            tags.div(id="panelExten", _class="tabPane")[
                self.addExtensionSet.applyTable(self)
            ],
            PageHelpers.LoadTabSwitcher(id="pbxextens")
        ]


    def render_routing(self, ctx, data):
        tabList = [
            ("Number Routing", "panelNumRouting"),
        ]

        tabs = []
        dt = []

        numberRouters = self.sysconf.PBXRouters

        for k in numberRouters:
            dt.append((
                k,
                tags.a(href="DelExtenGroup/%s" % k)[tags.img(src="/images/firewall/delete-icon-hover.png")]
            ))

            tabList.append((k.capitalize(), "panelRouter%s" % k))

            res = numberRouters[k]
            pd = []

            for ky, num in enumerate(res):
                edit = tags.a(onclick="populateNumExpression('%s','%s','%s',%s,'%s','%s','%s');" % (
                    k,num[0],num[1],
                    len(num) > 5 and num[5] and "1" or "0",
                    num[2] and str(num[2]) or "",
                    num[3] and str(num[3]) or "0",
                    num[4] and str(num[4]) or ""
                ))[tags.img(src="/images/firewall/edit-icon-hover.png")]
                row = (
                    num[0],num[1],
                    num[2] and str(num[2]) or "N/A",
                    num[3] and str(num[3]) or "0",
                    num[4] and str(num[4]) or "Default",
                    len(num) > 5 and num[5] and str(num[5]) or "False",
                    [edit, tags.a(href='DelExtenGroup/%s/%s' % (k,ky))[tags.img(src="/images/firewall/delete-icon-hover.png")]]
                )
                pd.append(row)
 
            tabs.append(
                    tags.div(id="panelRouter%s"%k, _class="tabPane")[
                        PageHelpers.dataTable(['Number Expression','Provider','Prefix','Start Pos','Priority','Pin Auth',''], pd, sortable=False),
                        tags.h3['Add Number Expression to ' + k.capitalize()],
                        tags.directive('form addNumberExpression %s' % k)
                    ]
            )
 

        return ctx.tag[
            PageHelpers.TabSwitcher(tabList, id="pbxrouters"),
            tags.div(id="panelNumRouting", _class="tabPane")[
                PageHelpers.dataTable(['Router', ''], dt, sortable=True),
                tags.h3['Add Router'],
                tags.directive('form addNumberRouter') 
            ],
            tabs,
            PageHelpers.LoadTabSwitcher(id="pbxrouters")
        ]

    def customForm_addNumberExpression(self, ctx, strData):
        def genNumberSelect(rangeBeg, rangeEnd):
            return formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in range(rangeBeg, rangeEnd)])
        form = formal.Form()


        form.addField('numExp', formal.String(required = True), label="Number Expression",
            description="Number expressions help to match numbers dialing out, it uses the standard asterisk expression for extensions. _X. for example would match all numbers while _031X. would match all numbers begining with 031 and so on")

        prov = [(str(provider),str(provider)) for provider in self.sysconf.PBXProviders]
        form.addField('provider', formal.String(required=True),
            formal.widgetFactory(formal.SelectChoice, options = prov),
            label="Routing Provider",
            description = "Select a provider that you would like to terminate calls matching this rule")

        form.addField('pinauth', formal.Boolean(), label="Require Pin Auth", description="Check this if you would like to enable pin dialing for this router")
        
        form.addField('prefix', formal.String(), label="Dialing Prefix",
            description="An added prefix to add to matched number extensions after the left")

        form.addField('ltrim', formal.Integer(), genNumberSelect(1,50), label="Left Trim",
            description="Number of characters to trim of the begining of the matched dialed number")

        form.addField('priority', formal.Integer(), genNumberSelect(1,20), label="Rule Priority",
            description="The priority is used to decide which of the routers with the same expression is used when successfully matched. The higher the more likely it will be used")
        def addNo(ctx, form, data):
            #Find existing entry that matches the extension numbering and the
            #provider and adjust

            routers = self.sysconf.PBXRouters.get(strData[0], [])
            idx = -1
            for k, num in enumerate(routers):
                if num[0] == data['numExp'] and num[1] == data['provider']:
                    idx = k
                    break
            
            nData = (
                data['numExp'],
                data['provider'],
                data['prefix'],
                data['ltrim'],
                data['priority'],
                data["pinauth"],
            )

            if idx >= 0:
                routers[k] = nData
            else:
                routers.append(nData)

            PBXR = self.sysconf.PBXRouters
            PBXR[strData[0]] = routers
            self.sysconf.PBXRouters = PBXR
            return restartAsterisk().addCallback(returnRoot)

        form.addAction(addNo)
        return form

    def form_addNumberRouter(self, data):
        form = formal.Form()

        form.addField('name', formal.String(required = True), label="Router Name")
        form.addAction(self.addNumberRouter)
        return form

    def addNumberRouter(self, ctx, form, data):
        if data['name'] and data['name'] not in self.sysconf.PBXRouters:
            rt = self.sysconf.PBXRouters 
            rt[data['name']] = [] 
            self.sysconf.PBXRouters = rt
        return restartAsterisk().addCallback(returnRoot)

    def form_addHandset(self, data):
        form = formal.Form()
        
        # Get a user list
        #users = [(i,i) for i in WebUtils.getUsers()]
        #userExtensions = []

        #macList = self.sysconf.PBX.get('snomMAC', [])
        #for name, handset in self.sysconf.PBX.get('phones', {}).items():
        #    if 'mac' in handset:
        #        if handset['mac'] in macList:
        #            macList.remove(handset['mac'])
        #macOptions = formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in macList])

        #for user in users:
        #    username = user[0].split('@')[0]
        #    if username in self.sysconf.PBXExtensions:
        #        userExtensions.append((username,username))

        #fKeyOptions = formal.widgetFactory(formal.SelectChoice, options = userExtensions)


        #form.addField('vuser', formal.String(), 
        #    formal.widgetFactory(formal.SelectChoice, options = users), 
        #    label = "Vulani User", 
        #    description="The Vulani user associated with this handset. Leave blank if you do not wish to associate this handset")

        form.addField('username', formal.String(), label="Username", 
            description="A username for this handset. Usualy this is the extension to dial this handset")

        form.addField('password', formal.String(), label = "Password", 
            description="The password for this handset. Leave blank for no password")

        #form.addField('callerid', formal.String(), label="Caller ID")

        #form.addField('context', formal.String(), label="Outgoing Context")

        #form.addField('calllimit', formal.Integer(), label = "Outbound Call limit", 
        #    description="The number if similtaneous outgoing calls this device can make")

        #phones = [
        #    "Standard SIP", 
        #    "Snom 320"
        #]

        #form.addField('phonetype', formal.String(), 
        #    formal.widgetFactory(formal.SelectChoice, options = [(i,i) for i in phones]), 
        #    label = "Phone Type", 
        #    description = "Select a phone for extended options on supported handsets, or choose 'Standard SIP'.")

        #for i in range(11):
        #    form.addField('Snom320fkeys%s' % i, formal.String(), fKeyOptions, label = "Key %s" % i)

        #form.addField('Snom320fkeys12', formal.String(), fKeyOptions, label = "Key 12", 
        #    description = "Enter the extension for the function keys above")

        #form.addField('Snom320MAC', formal.String(), macOptions, label = "MAC Address", 
        #    description = "The MAC address for this Snom phone to allow automatic configuration")

        form.addAction(self.addHandset)
        return form

    def addHandset(self, ctx, form, data):
        pxconf = self.sysconf.PBX
        if 'phones' not in pxconf:
            pxconf['phones'] = {}

        user = data['username'].encode('ascii', 'replace')

        cblock = {
            'callerid': user,
            'username': user, 
            'phone':{
                'type': "Standard SIP" 
            },
            'secret': data['password'].encode('ascii', 'replace')
        }

        pxconf['phones'][user] = cblock
        self.sysconf.PBX = pxconf
        
        return restartAsterisk().addCallback(returnRoot)

    def render_handsets(self, ctx, data):
        phoneTable = []
        phoneData = self.sysconf.PBX.get('phones', {})
        devExt = {}
        for user, extension in self.sysconf.PBXExtensions.items():
            for dev in extension['devices']:
                if 'Phone/' == dev[0:6]:
                    devExt[dev[6:]] = user
        for user,sets in phoneData.items():
            phoneTable.append([
                user,
                sets['callerid'], 
                devExt.get(user, "Not Assigned") or "Not Assigned", 
                sets['phone']['type'],
                tags.a(href='DelHandSet/%s' % user)[tags.img(src="/images/firewall/delete-icon-hover.png")]
            ])

        return ctx.tag[
            PageHelpers.dataTable(['Name', 'Caller ID', 'User', 'Phone',''], phoneTable, sortable=True), 
            tags.h3['Add handset'],
            tags.directive('form addHandset')
        ]

    def render_providers(self, ctx, data):
        tabList = [
            ("Hardware Providers", "panelHardwareProv"),
            ("VoIP Providers", "panelVoipProv"),
        ]

        hwprov = tags.h3["Please note that there is an issue with the current hardware setup"]

        if self.addHardwareProvider:
            hwprov = self.addHardwareProvider.applyTable(self)
            

        return ctx.tag[ 
            PageHelpers.TabSwitcher(tabList, id="pbxprovider"),
            tags.div(id="panelHardwareProv", _class="tabPane")[
                hwprov
            ],
            tags.div(id="panelVoipProv", _class="tabPane")[
                self.addVoipProvider.applyTable(self)
            ],
            PageHelpers.LoadTabSwitcher(id="pbxprovider")

        ]

    def render_hardware(self, ctx, data):
        dt = []
        tabList = [
                ("Devices",      "panelDevices"),
                ("Groups",       "panelMainGroups")
        ]
        
        DeviceGroups = []

        if not self.hw:
            return "No Hardware support"

        for pluginName in self.hw.plugins:
            plugin = self.hw.plugins[pluginName]

            DeviceGroups.extend([
                (str(plugin._genGroupNumName(groupNum)), plugin.getGroup(groupNum),pluginName, groupNum) for groupNum in plugin.getGroupList()
            ])

        tabs = []
        for k in DeviceGroups:
            dt.append((
                k[0],
                len(k[1]),
                tags.a(href="DelHardwareGroup/%s" % k[0].replace('/','_'))[tags.img(src="/images/firewall/delete-icon-hover.png")]
                #XXX XXX TODO add DelHardwareGroup handler
            ))
            
            tabList.append((k[0].capitalize(), "panelHardware%s" % k[0]))
            pd = [(port, tags.a(href='DelHardwareGroupPort/%s/%s' % (k[0].replace('/','_'), port.replace('/','_')))[tags.img(src="/images/firewall/delete-icon-hover.png")])
                   for port in k[1]
            ]
            methodName = "form_addPortsToGroup_"+k[0].replace('/','_')
            tabs.append(
                    tags.div(id="panelHardware%s" % k[0], _class="tabPane")[
                        PageHelpers.dataTable(['Port Name',''], pd, sortable=False),
                        tags.h3['Add Ports to ' + k[0]],
                        tags.directive('form addPortsToGroup %s %s' % (k[3], k[2]))
                    ]
            )
        
        return ctx.tag[
            PageHelpers.TabSwitcher(tabList, id="pbxhardware"),
            tags.div(id="panelDevices", _class="tabPane")[
                tags.invisible(render=tags.directive('hardwareDevice'))
            ],
            tags.div(id="panelMainGroups", _class="tabPane")[
                PageHelpers.dataTable([('istr', 'Hardware Group'),('', 'Member Count'), ('istr', '')], dt, sortable=True), 
                tags.h3['Add Hardware Group'], 
                tags.directive('form addHardwareGroup')
            ],
            tabs,
            PageHelpers.LoadTabSwitcher(id="pbxhardware")
        ]

    def formFactory(self, ctx, name):
        """OverLoad the Factory Hackity Smackity :)"""
        if len(name.split()) > 1:
            factory = getattr(self, "customForm_"+name.split()[0], None)
            if factory is not None:
                return factory(ctx, name.split()[1:])
        return Tools.Page.formFactory(self,ctx,name)

    def customForm_addPortsToGroup(self, ctx, strData):
            
        form = formal.Form()
        pluginName = strData[1]
        plugin = self.hw.plugins[pluginName]
        groupList = plugin.getGroup(int(strData[0]))
        portList = []
        for devName in plugin.devices:
            for port in plugin.devices[devName]:
                if port[0] in groupList:
                    continue
                portList.append((port[0], port[0]))

        form.addField('portList', formal.String(required=True),
            formal.widgetFactory(formal.MultiselectChoice, options = portList),
            label = "Port Name")

        def addPortsToGroup(ctx, form, data):
            portList = data["portList"]
            portList.extend(groupList)
            plugin.setGroup(int(strData[0]), portList)

        form.addAction(addPortsToGroup)
        return form


    def form_addHardwareGroup(self, data):
        form = formal.Form()
        
        pluginList = [(str(pluginName),str(self.hw.plugins[pluginName].name)) for pluginName in self.hw.plugins]

        form.addField('plugin', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = pluginList),
            label = "Plugin Technology",
            description="Specifies a hardware technology in which to use to for defining a group")

        form.addField('groupNumber', formal.Integer(required=True), label="Group Number") 

        form.addField('allPorts', formal.Boolean(), label = "Populate with All", 
            description="Should we initially populate the group with all availible channels")

        form.addAction(self.addHardwareGroup)
 
        return form

    def addHardwareGroup(self, ctx, form, data):
        plugin = self.hw.plugins[data["plugin"]]
        portList = []
        if data["allPorts"]:
            for devName in plugin.devices:
                portList.extend([port[0] for port in plugin.devices[devName]])

        if data["groupNumber"] not in plugin.getGroupList():
            plugin.setGroup(data["groupNumber"], portList)
        return restartAsterisk().addCallback(returnRoot)

    def render_hardwareDevice(self, ctx, data):
        try:
            hw = PBXUtils.PBXHardware()
            hw.detect()
        except Exception, _exp:
            return ctx.tag[
                "Hardware page is not ready, due to %s." % _exp.message
            ]
        deviceTable = []
        for device in hw:
            deviceTable.append([
                device.name,
                device.pluginEntity.name,
                len(device),
                tags.a(href="EditDevice/%s" % (device.name.replace("/","_")))[tags.img(src="/images/firewall/edit-icon-hover.png")]
            ])
        return ctx.tag[
            tags.h3['Device List'],
            "Each of these devices represents a hardware device that has been detected on this machine, to enable and configure simply select the edit button to proceed",
            PageHelpers.dataTable(['Device', 'Type', 'Ports', ''], deviceTable, sortable=True)
        ]

    def render_menus(self, ctx, data):
        dt = []
        tabList = [
                #("Call Landing", "panelLanding"),
                ("Response Menu","panelIVR")
        ]
        tabs = []

        for ivrName,ivrData in self.sysconf.PBX.get('ivr', {}).items():
            extensions = str.join(', ',ivrData['extensions'])
            dt.append([
                ivrName,
                extensions,
                tags.a(href='DelIVR/%s' % ivrName)[tags.img(src="/images/firewall/delete-icon-hover.png")]
            ])
            
            tabList.append((ivrName.capitalize(), "panelIVR%s" % ivrName))

            tabs.append(
                    tags.div(id="panelIVR%s"%ivrName, _class="tabPane")[
                        #PageHelpers.dataTable(['Number Expression','Provider','Prefix','Start Pos','Priority',''], pd, sortable=False),
                        tags.h3['Edit Menu ' + ivrName.capitalize()],
                        tags.directive('form editIVR %s' % ivrName)
                    ]
            )

        
        return ctx.tag[
            PageHelpers.TabSwitcher(tabList, id="inboundcall"),
            #tags.div(id="panelLanding", _class="tabPane")[
            #    tags.invisible(render=tags.directive('callLanding'))
            #],
            tags.div(id="panelIVR", _class="tabPane")[
                PageHelpers.dataTable([('istr', 'Menu Name'), ('istr', "Extension"), ('istr', '')], dt, sortable=True), 
                tags.h3['Add IVR'], 
                tags.directive('form addIVR')
            ],
            tabs,
            PageHelpers.LoadTabSwitcher(id="inboundcall")
        ]

    def customForm_editIVR(self, data, strData):
        ivrName = strData[0]
        def updateIVR(ctx, form, nData):
            prompt = []
            for i in range(10):
                prompt.append(nData['menuPrompt%s'%i])
            options = []
            for i in range(10):
                options.append(nData['option%s'%i])
            extensions = []
            for i in range(4):
                if nData['extNumber%s'%i]:
                    extensions.append(nData['extNumber%s'%i])

            PBX = self.sysconf.PBX
            ivr = PBX.get('ivr', {})
            print nData
            dates = []
            exDates = []
            if nData['incDates']:
                for date in nData['incDates'].split(','):
                    try:
                        d,m = date.strip().split('/')
                        d = int(d)
                        m = int(m)
                        if d >= 1 and d <= 31 and m >=1 and m <=12:
                            dates.append(date.strip())
                    except:
                        print "Invalid date format for ", str(date)
                        continue

            if nData['excDates']:
                for date in nData['excDates'].split(','):
                        try:
                            d,m = date.strip().split('/')
                            d = int(d)
                            m = int(m)
                            if d >= 1 and d <= 31 and m >=1 and m <=12:
                                exDates.append(date.strip())
                        except:
                            print "Invalid date format for ", str(date)
                            continue
                
            ivr[ivrName] = {
                'name': ivrName,
                'prompt': prompt,
                'options': options,
                'extensions': extensions,
                'timeout': nData['timeout'],
                'timeout-option': nData['timeoutoption'],
                'operating': {
                    'dow': nData['dow'],
                    'start-time': nData['startTime'] and str(nData['startTime']) or None,
                    'end-time': nData['endTime'] and str(nData['endTime']) or None,
                    'exc-dates': exDates,
                    'action': nData['timeBasedFallthrough'],
                    'dates': dates,
                    'enabled': nData['timeBasedIVR'],
                }
            }
            PBX['ivr'] = ivr
            self.sysconf.PBX = PBX
            return restartAsterisk().addCallback(returnRoot)

        ivrData = self.sysconf.PBX['ivr'][ivrName]

        form = formal.Form()
        extenWidget = formal.widgetFactory(formal.SelectChoice, options=PBXUtils.getAvaExtenNumSelect(True,ivrData.get('extensions',[]))) #provide a list of current extensions
        promptWidget = formal.widgetFactory(formal.SelectChoice, options=PBXUtils.getVoicePrompts())
        optionWidget = formal.widgetFactory(formal.SelectChoice, options=PBXUtils.getExtensionSelect())

        form.addField('menuName', formal.String(required=True),
            label = "Menu Name")
        
        form.addField('extNumber0', formal.String(required=True), extenWidget)
        form.addField('extNumber1', formal.String(required=False), extenWidget)
        form.addField('extNumber2', formal.String(required=False), extenWidget) 
        form.addField('extNumber3', formal.String(required=False), extenWidget)
        form.addField('menuPrompt0', formal.String(required=True), promptWidget, label='Welcome Prompt',
            description="This voice prompt is played before all the other voice prompts and cannot be skipped")
        form.addField('menuPrompt1', formal.String(required=True), promptWidget, label='Prompt 1')
        for i in range(2,9):
            form.addField('menuPrompt%s'%i, formal.String(), promptWidget, label='Prompt %s'%i)
        form.addField('menuPrompt9', formal.String(), promptWidget, label='Prompt 9',
            description="Select a voice prompt in the order you would like them played")
        for i in range(9):
            form.addField('option%s'%i, formal.String(), optionWidget, label='Prompt Option %s'%i)
        form.addField('option9', formal.String(), optionWidget, label='Prompt Option 9',
            description="Select an end point extension to route for each of the keypad expressions that the user may press")
        form.addField('timeout', formal.Integer(), label='Prompt Timeout',
            description="Timeout in seconds after which TimeoutOption will be selected automatically")
        form.addField('timeoutoption', formal.String(), optionWidget, label='Timeout Option')

        form.addField('timeBasedIVR', formal.Boolean(), label='Timebased IVR', description='Enable timebased IVR, enabling this will allow you to control when this IVR will be effective on and failing the time checks forward calls to Timebase fallthrough Option')
        form.addField('timeBasedFallthrough', formal.String(), optionWidget, label='Fallthrough Option', description="Option that is used when the call enters out the bounds of the times specified here")

        dowWidget = formal.widgetFactory(formal.CheckboxMultiChoice, options=[(k,i) for k,i in enumerate(PageHelpers.days)]) 
        form.addField('dow', formal.Sequence(formal.Integer()), dowWidget, label="Day of Week", description="Days of the week that this IVR is to operate")
        form.addField('startTime', formal.Time(), label="Start Time", description="Start time for each day in 24 hour format HH:MM")
        form.addField('endTime', formal.Time(), label="End Time", description="End time for each day in 24 hour format HH:MM")
        form.addField('incDates', formal.String(), label='Inc Dates', description="Specific dates to be included DD/MM, each entry seperated by a comma")
        form.addField('excDates', formal.String(), label='Except Dates', description="Dates that are treated as exceptions to all the above rules format in DD/MM, each entry seperated by a comma")

        form.data = {
            'menuName': strData,
            'timeout': ivrData['timeout'],
            'timeoutoption': ivrData['timeout-option'],
            'timeBasedIVR': ivrData['operating'].get('enabled', False),
            'dow': ivrData['operating']['dow'],
            'endTime': ivrData['operating']['end-time'],
            'timeBasedFallthrough': ivrData['operating']['action'],
            'incDates': str.join(', ',ivrData['operating'].get('dates', [])),
            'excDates': str.join(', ',ivrData['operating'].get('exc-dates', [])),
        }
        
        try:
            t = time.strptime(ivrData['operating']['start-time'], "%H:%M:%S")
            form.data['startTime'] = datetime.time(t.tm_hour, t.tm_min)
        except:
            form.data['startTime'] = None
 
        try:
            t = time.strptime(ivrData['operating']['end-time'], "%H:%M:%S")
            form.data['endTime'] = datetime.time(t.tm_hour, t.tm_min)
        except:
            form.data['endTime'] = None
            
 
 
        #Populate Extensions
        for k, ext in enumerate(ivrData['extensions']):
            form.data['extNumber%s'%k] = ext
        #Populate MenuPrompts
        for k, prompt in enumerate(ivrData['prompt']):
            form.data['menuPrompt%s'%k] = prompt
        #Populate Options
        for k, opt in enumerate(ivrData['options']):
            form.data['option%s'%k] = opt
        form.addAction(updateIVR)
        return form


    def form_addIVR(self, data):
        def addIVR(ctx, form, nData):
            PBX = self.sysconf.PBX
            ivr = PBX.get('ivr', {})
            ivr[nData['menuName']] = {
                'name': nData['menuName'],
                'prompt': [],
                'options': [],
                'extensions': [],
                'timeout': 10,
                'timeout-option': None,
                'operating': {
                    'dow': [],
                    'start-time': None,
                    'end-time': None,
                    'exc-dates': [],
                    'action': None,
                    'enabled': False,
                    'dates': [],
                }
            }
            PBX['ivr'] = ivr
            self.sysconf.PBX = PBX
        form = formal.Form()
        form.addField('menuName', formal.String(required=True), 
            label = "Menu Name")
        form.addAction(addIVR)
        return form

    def render_content(self, ctx, data):
        if not checkForAsterisk():
            return ctx.tag["Please install asterisk support"] #Auto install would be nice here

        if not PBXUtils.enabled():
            return ctx.tag[
                tags.h3[tags.img(src="/images/mailsrv.png"), " VoIP" ],
                tags.div(id="setupPBX")[
                    "Please note that the PBX functionality has not been enabled, to enable the functionality check the checkbox and click submit", 
                    tags.br,
                    tags.directive('form pbxConfig'),
                    "Note that enabling the PBX functionality will clear any asterisk configs on the box that already exists, note that a backup of the data will be placed in the /var/lib/asterisk",
                ]
            ]
        return ctx.tag[
            tags.h3[tags.img(src="/images/mailsrv.png"), " VoIP" ],
            PageHelpers.TabSwitcher((
                ("Setup",       "panelSetup"),
                ("Menus",     "panelMenus"),
                ("Providers",   "panelProviders"),
                ("CallRouting", "panelRouting"),
                ("Extensions",  "panelExtensions"),
                ("Handsets",    "panelPhones"),
                ("Hardware",    "panelHardware"),
            ), id="pbxcore"),
            tags.div(id="panelSetup", _class="tabPane")[
                tags.directive('form pbxConfig')
            ],
            tags.div(id="panelProviders", _class="tabPane")[
                tags.invisible(render=tags.directive('providers'))
            ],
            tags.div(id="panelMenus", _class="tabPane")[
                tags.invisible(render=tags.directive('menus'))
            ],
            tags.div(id="panelRouting", _class="tabPane")[
                tags.invisible(render=tags.directive('routing'))
            ],
            tags.div(id="panelExtensions", _class="tabPane")[
                tags.invisible(render=tags.directive('extensions'))
            ],
            tags.div(id="panelPhones", _class="tabPane")[
                tags.invisible(render=tags.directive('handsets'))
            ],
            tags.div(id="panelHardware", _class="tabPane")[
                tags.invisible(render=tags.directive('hardware'))
            ],
            PageHelpers.LoadTabSwitcher(id="pbxcore")
        ]

    def locateChild(self, ctx, segs):
        def returnRoot(_):
            return url.root.child(PageRoot), ()
        if len(segs) > 1:
            if segs[0] == "DelIVR":
                ivrName = segs[1]
                PBX = self.sysconf.PBX
                if ivrName in PBX.get('ivr', {}):
                    del PBX['ivr'][ivrName]
                    self.sysconf.PBX = PBX
                    return restartAsterisk().addCallback(returnRoot)
                return url.root.child(PageRoot), ()
            if segs[0] == "DelHandSet":
                handSetName = segs[1]
                PBX = self.sysconf.PBX
                if handSetName in PBX.get('phones', {}):
                    del PBX['phones'][handSetName]
                    self.sysconf.PBX = PBX
                    PBXExtensions = self.sysconf.PBXExtensions
                    for user, ext in PBXExtensions.items():
                        for k,dev in enumerate(ext.get('devices', [])):
                            if dev == handSetName:
                                del PBXExtensions['user']['devices'][k]
                    self.sysconf.PBXExtensions = PBXExtensions
                    return restartAsterisk().addCallback(returnRoot)
                return url.root.child(PageRoot), ()
            if segs[0] == "DelHardwareGroupPort":
                hardwareGroup = segs[1].replace('_','/')
                cardPort = segs[2].replace('_', '/')
                conf = self.sysconf.PBXHardware
                if hardwareGroup in conf:
                    if cardPort in conf[hardwareGroup]:
                        conf[hardwareGroup].remove(cardPort)
                self.sysconf.PBXHardware = conf
                #return restartAsterisk().addCallback(returnRoot)
                return url.root.child(PageRoot), ()
            if segs[0] == "DelHardwareGroup":
                hardwareGroup = segs[1].replace('_','/')
                conf = self.sysconf.PBXHardware
                if hardwareGroup in conf:
                    del conf[hardwareGroup]
                self.sysconf.PBXHardware = conf
                return restartAsterisk().addCallback(returnRoot)
            if segs[0] == "DelExtenGroup":
                extenGroup = segs[1]
                conf = self.sysconf.PBXRouters
                if len(segs) > 2:
                    extenItem = int(segs[2])
                    if extenGroup in conf:
                        if extenItem < len(conf[extenGroup]):
                            del conf[extenGroup][extenItem]
                else:
                    del conf[extenGroup]
                self.sysconf.PBXRouters = conf
                #return restartAsterisk().addCallback(returnRoot)
                return url.root.child(PageRoot), ()
        
        return super(Page, self).locateChild(ctx, segs)

    def childFactory(self, ctx, seg):
        if seg == "EditDevice":
            return DeviceEditPage(self.avatarId, self.db)
        return super(Page, self).childFactory(ctx,seg)
        #return PageHelpers.DefaultPage.childFactory(self, ctx, seg)
