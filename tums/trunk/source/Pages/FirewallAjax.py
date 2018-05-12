from nevow import rend, loaders, tags, athena, flat
from twisted.internet import reactor
from Core import PageHelpers, Shorewall, confparse, Utils, WebUtils
from Pages import Tools

import re, os
import formal 

import Settings

class FirewallFragment(formal.ResourceMixin, athena.LiveFragment):
    jsClass = u'firewall.PS'

    protocols = [
                 ('-',   'Any'),
                 ('tcp', 'TCP'),
                 ('udp', 'UDP'),
                 ('47', 'PPTP'),
                 ('icmp', 'ICMP')
                ]

    #Masq Rules collected during init
    masqRules = []

    parseFirewallResultRE = re.compile('ERROR:\s+((.*)(.:.(.*).\((line.(.*))\)))|ERROR:\s+(.*)', re.I)

    securityViolation = False

    docFactory = loaders.xmlfile('firewall-fragment.xml', templateDir = Settings.BaseDir + '/templates')

    def __init__(self, *a, **kw):
        super(FirewallFragment, self).__init__(*a, **kw)
        #On instantiation lets make sure the rules are upgraded
        Shorewall.upgradeRules()

        # Initialize config db object
        self.sysconf = confparse.Config()

        self.masqRules = self.getMasqRules()


    def parseFirewallResult(self, result = None, completeMessage = None):
        errors = []
        def parseErrorLines(lines):
            for i in lines:
                i = i.strip().strip('\n')
                match = self.parseFirewallResultRE.search(i)
                if match:
                    #There is an error, build tuple
                    if match.group(1):
                        errors.append([match.group(1),[match.group(4), match.group(6)]])
                    else:
                        errors.append([match.group(7),[]])
        if result:
            parseErrorLines(result.split('\n'))
        elif os.path.exists('/usr/local/tcs/tums/shorewallBroken'):
            l = open('/usr/local/tcs/tums/shorewallBroken', 'r')
            parseErrorLines(l.readlines())
            l.close

        if errors:
            messageHTML = flat.flatten([tags.h1["Firewall Rules Error"],tags.p["There was an error processing the firewall rules, %s" % errors[0][0]]])
            self.callRemote('setMessage', unicode(messageHTML), u'firewallStatus', u'error')
        else:
            if(completeMessage):
                self.callRemote('setMessage',unicode(completeMessage), u'firewallStatus', u'notice', u'10000');
            else:
                self.callRemote('clearMessage', u'firewallStatus');

        if(result):
            """Only write to the shorewallBroken file when we have a result to update it with otherwise we read it"""
            if not errors:
                # Delete any potential error outputs
                WebUtils.system('rm /usr/local/tcs/tums/shorewallBroken > /dev/null 2>&1 ')
            else:
                l = open('/usr/local/tcs/tums/shorewallBroken', 'wt')
                l.write(result)
                l.close
    athena.expose(parseFirewallResult)
        
    def testRules(self):
        Utils.log.msg('%s tested firewall configuration' % (self.avatarId.username))
        self.callRemote('setMessage', u'Testing the Firewall', u'firewallStatus', u'notice')
        return WebUtils.system('/usr/local/tcs/tums/configurator --shorewall; shorewall check').addCallback(self.parseFirewallResult, "Firewall Test Completed with no errors")
    athena.expose(testRules)

    def applyRules(self):
        Utils.log.msg('%s caused shorewall restart' % (self.avatarId.username))
        self.callRemote('setMessage', u'Restarting the Firewall', u'firewallStatus', u'notice')
        WebUtils.system(Settings.BaseDir+'/configurator --shorewall; shorewall save; shorewall restart').addCallback(self.parseFirewallResult, "Firewall rules have been applied with no errors")
    athena.expose(applyRules)

    def constructRule(self, data):
        rule = ""
        rule += data['action'].encode("ascii", "replace") + "   "
        rule += data['szone'].encode("ascii", "replace")
        if data['sip']:
            rule += ":"+data['sip'].encode("ascii", "replace")
        rule += "    %s" % (data['dzone'].encode("ascii", "replace") or '')
        if data['dip']:
            rule+= ":"+data['dip'].encode("ascii", "replace")

        rule += "        "
        
        rule += data['proto'].encode("ascii", "replace") + "    "

        rule += data['dport'].encode("ascii", "replace") or "-"
        rule += "    "
        rule+= data['sport'].encode("ascii", "replace") or "-"
        return rule
        
    def checkRuleSecurity(self):
        """Checks the firewall rules and returns a list of rules that evil"""
        rules = self.rules.read()
        out = []
        for n, rule in enumerate(rules['AIP']):
            if rule[7] in ["22", "9682"]:
                if (rule[2] == "Any") and ((rule[1] in ["net", "Any", "dsl", "ppp", "wan", "net2"]) or (rule[4] == "fw")):
                    out.append(u"fwrule_%s" % n)
        return out
    athena.expose(checkRuleSecurity)

    def parseID(self, idText):
        """Strips the first part and produces an integer used to isolate the rule number"""
        (text, id_txt) = idText.split('_')
        try:
            return (int(id_txt),text)
        except Exception, _e:
            self.raiseError("parseID, idText invalid (%s)" % _e)

    def raiseError(self, errorText):
        self.callRemote('setMessage', unicode(errorText), u'raiseError', u'error')
        print "ERROR: %s" % errorText

    def raiseNotice(self, noticeText, seconds = 10):
        self.callRemote('setMessage', unicode(noticeText), u'raiseNotice', u'notice', u'%s' % str(seconds * 1000))
        print "NOTICE: %s" % noticeText

    def delFirewallRule(self, ruleIDText):
        """Deletes a firewall rule"""
        rdet = self.parseID(ruleIDText)
        if not rdet:
            self.raiseError("Unable to delete rule due to invalid ID")
            return
        fwRules = self.sysconf.Shorewall["rules"]
        del fwRules[rdet[0]]
        shw = self.sysconf.Shorewall
        shw["rules"] = fwRules
        self.sysconf.Shorewall = shw
        self.raiseNotice('Rule was deleted successfully')
        #self.callRemote('resetIDS', u'firewallRules', u'fwrule') Chicken and egg story
        return

    athena.expose(delFirewallRule)

    def applyFirewallRuleOrder(self, ruleOrder):
        """Applies the firewall rule order as defined by the user"""
        fwRules = self.sysconf.Shorewall["rules"]
        newRules = []
        for rdet in ruleOrder:
            rdet = self.parseID(rdet)
            if not rdet:
                self.raiseError("Unable to apply rule ordering due to invalid ID")
                return
            newRules.append(fwRules[rdet[0]])

        if len(newRules) > 0 and len(newRules) == len(self.sysconf.Shorewall["rules"]):
            #Make sure we are not destroying the current rulesets
            shw = self.sysconf.Shorewall
            shw["rules"] = newRules
            self.sysconf.Shorewall = shw
            self.callRemote('resetIDS', u'firewallRules', u'fwrule')
            self.raiseNotice('Updated firewall rule order successfully')
        else:
            self.raiseError("Error, unable to reorder the rules due to an inconsistency, please reload")
    athena.expose(applyFirewallRuleOrder)

    def renderRule(self, rule):
        """
        Generate tags for a rule
        """
        ruleClass = rule[0].upper() != "ACCEPT" and "noaccept" or "accept"
        return tags.table[
            tags.tr[
                tags.td(rowspan=2, _class="fwcol move")[""],
                tags.td(rowspan=2, _class="rule fwcol "+ruleClass)[rule[0]],
                tags.td(_class="srclabel fwcol")['Source'],
                tags.td(_class="srczone fwcol")[rule[1]],
                tags.td(_class="srcport fwcol")[rule[3].replace('-', 'Any')],
                tags.td(_class="srcip fwcol")[rule[2]],
                tags.td(rowspan=2, _class="protocol fwcol")[rule[6].replace('-', 'Any')],
                tags.td(rowspan=2, _class="edit fwcol")[""],
                tags.td(rowspan=2, _class="delete fwcol")[""],
                ],
            tags.tr[
                tags.td(_class="dstlabel fwcol")['Destination'],
                tags.td(_class="dstzone fwcol")[rule[4]],
                tags.td(_class="dstport fwcol")[rule[7].replace('-','Any')],
                tags.td(_class="dstip fwcol")[rule[5]],
            ]]

    def render_firewallRules(self, ctx, data):
        """
        Generate the initial Ruleset
        """
        rules = self.rules.read()

        outRules = [tags.li(id="fwrule_%s" % n,
                    _class= (n % 2 == 0) and "odd dynRow" or "even dynRow")[
                        self.renderRule(rule)
                    ] 
                    for n, rule in enumerate(rules['AIP'])]
        return tags.div(id="firewallRulesTab", _class="tabPane")[
            tags.h3["Firewall Rules"], 
            tags.p(_class="addRulePlacer")[tags.a(name="addRule", id="fwAddRuleButton")['Add Rule']],
            tags.table(id="firewallRulesHeader", background="/images/gradMB.png")[
                tags.tr[
                    tags.th(_class="headMove")[''],
                    tags.th(_class="headRule")['Rule'],
                    tags.th(_class="headLabel")[''],
                    tags.th(_class="headZone")['Zone'],
                    tags.th(_class="headPort")['Port'],
                    tags.th(_class="headIP")['IP'], 
                    tags.th(_class="headProt")['Protocol'],
                    tags.th(_class="headEdit")[''],
                    tags.th(_class="headDel")[''],
                ],
            ],
 
            tags.ul(id="firewallRules")[outRules],
            tags.div(id="firewallRulesFormDialog", _class="dialogwin", style="width:450px;height:auto;display:none")[
                tags.div(id="firewallRulesFormTitle", _class="dialogtopbar")[""],
                tags.div(_class="dialogcontent")[
                    tags.directive("form firewallRulesForm")
                ]
            ]
        ]

    def form_firewallRulesForm(self, data):
        form = formal.Form()

        form.addField('action', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, 
            options = [
                ("ACCEPT", "Accept"),
                ("REJECT", "Reject")
            ]), label = "Action")

        # Source
        form.addField('sip', formal.String(), label = "Source IP", 
            description = "Source IP address of connecting host or network (Blank for Any)")

        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)

        form.addField('szone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Source Zone")

        form.addField('sport', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Source Port",
            description = "Source port (Blank for Any)")

        # Destination
        form.addField('dip', formal.String(), label = "Destination IP", 
            description = "Destination IP address or network (Leave blank for ANY)")

        form.addField('dzone', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, 
            options = self.getZones()), label = "Destination Zone")

        form.addField('dport', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Destination Port/Type",
            description = "Destination port OR other protocol subtype (Blank for any)")

        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, 
            options = self.protocols), label = "Protocol")

        form.data['szone']="all"
        form.data['dzone']="all"
        form.data['proto']="-"

        form.addAction(self.submitFirewallRule)
        form.addAction('cancel', 'cancel', validate=False)

        return form

    def submitFirewallRule(self, data):
        """
        Apply data submitted from ajax for rule creation and updating
        """
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false

        rule = self.constructRule(data) #Build a rule
        shw = self.sysconf.Shorewall

        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None
 
        if(txt_ruleID):#Apply the new rule either insert or replace
            shw["rules"][rid] = [1, unicode(rule)]
            actionText = "Updated"
        else:
            shw["rules"].append([1, unicode(rule)])
            rid = len(shw["rules"]) - 1
            actionText = "Added"
        
        self.sysconf.Shorewall = shw
        rule_data = self.rules.read()["AIP"][rid]
        
        htmlOut = flat.flatten(self.renderRule(rule_data)) #Get the new html of the rule

        self.callRemote('insertListHTML', u'firewallRules', txt_ruleID, unicode(htmlOut), u'fwrule')
        self.callRemote('initFirewallRulesInterface');
        self.raiseNotice("Rule was successfully %s" % actionText);

    athena.expose(submitFirewallRule)

    def getRuleFormData(self, ruleID = None):
        data = {
            u'action':u'',
            u'sip':u'',
            u'szone':u'all',
            u'sport':u'',
            u'dip':u'',
            u'dzone':u'all',
            u'dport':u'',
            u'proto':u'Any',
        }
        if ruleID:
            rid = self.parseID(ruleID)[0]
            ruledata = self.rules.read()["AIP"][rid]
            data = {
                u'action':unicode(ruledata[0]),
                u'sip':unicode(ruledata[2].lower().replace('any','')),
                u'szone':unicode(ruledata[1].replace('Any', 'all')),
                u'sport':unicode(ruledata[3].replace('-','').lower().replace('any', '')),
                u'dip':unicode(ruledata[5].replace('-','').lower().replace('any','')),
                u'dzone':unicode(ruledata[4].replace('Any', 'all')),
                u'dport':unicode(ruledata[7].replace('-','').lower().replace('any', '')),
                u'proto':unicode(ruledata[6].replace('-', 'Any')),
            }
        return data
    athena.expose(getRuleFormData)

    def unicodeArray(self, ar):
        return [ unicode(i) for i in ar ]

    def renderLIRule(self, data, colClasses):
        """
        Renders the content with the provided classes for each column
        """
        tableData = []
        for k, item in enumerate(data):
            className = ""
            if len(colClasses) > k:
                className = colClasses[k]
            className = className + " col_%s" % k
            tableData.append(tags.td(_class=className)[item])
        #return tags.table[tags.tr[tableData]]
        return tableData

    def renderDataTable(self, id, rulePrefix, data, columns, colClasses):
        """
        Renders the data into a table
        """
        rulesTags = [tags.tr(id="%s_%s" % (rulePrefix, n),
                    _class= "rulesListItem " + ((n % 2 == 0) and "odd" or "even"))[
                        self.renderLIRule(rule, colClasses)
                    ] 
                    for n, rule in enumerate(data)]

        tableData = []
        for k, item in enumerate(columns):
            className = ""
            if len(colClasses) > k:
                className = colClasses[k]+"_head"
            className = className + " head_%s" % k
            tableData.append(tags.th(_class=className)[str(item)])

        return [ 
            tags.table(id=id+'_table', _class='dataTable',cellPadding=10,cellSpacing=0)[
                tags.thead[tags.tr(id=id+"_header", _class="tableHeaderRow")[tableData]],
                tags.tbody(id=id, _class="rulesList")[rulesTags]
            ],
            #tags.ul(id=id, _class="rulesList")[rulesTags]
        ]

    def render_firewallNatRules(self, ctx, data):
        """
        Generate the initial NatRuleset
        """
        #Dnat / Forwarding rules
        fwdRulesColNames = ['Source Zone', 'Source IP', 'Forward To', 'Destination Zone', 'Protocol', 'Port', 'Destination IP', '', '']
        fwdRulesColClasses = ['srczone', 'srcip', 'fwdip', 'dstzone', 'protocol', 'port', 'dstip', 'edit', 'delete']
        fwdTableTags = self.renderDataTable("firewallForwardRules", 'forwardRule' , self.getForwardRules(), fwdRulesColNames, fwdRulesColClasses)
        #Redirect rules / Transparent Proxy 
        redirectRulesColNames = ['Source Zone', 'Source Network', 'Destination Port', 'Source Port', 'Protocol', 'Destination Network', '', ''];
        redirectRulesColClasses = ['srczone', 'srcnet', 'dstport', 'srcport', 'protocol', 'dstnet', 'edit', 'delete'];
        redirectTableTags = self.renderDataTable("firewallRedirectRules", 'redirectRule' , self.getRedirectRules(), redirectRulesColNames, redirectRulesColClasses)
        #Masquerading 
        masqRulesColNames = ['Destination Interface', 'Destination Network', 'Source Interface', 'Source Network', 'NAT IP', 'Protocol', 'Port', '', '']
        masqRulesColClasses = ['dstint', 'dstnet', 'srcint', 'srcnet', 'natip', 'protocol', 'port', 'edit', 'delete']
        masqTableTags = self.renderDataTable("firewallMasqRules", 'masqRule' , self.masqRules, masqRulesColNames, masqRulesColClasses)
        #SourceNat
        snatRulesColNames = ['Source IP', 'External Interface', 'Internal IP', 'Any Interface', 'Use Internal', '', '']
        snatRulesColClasses = ['srcip', 'extint', 'intint', 'anyint', 'useint', 'edit', 'delete']
        snatTableTags = self.renderDataTable("firewallSNATRules", 'snatRule', self.getSNATRules(), snatRulesColNames, snatRulesColClasses)

        return tags.div(id="firewallNatRulesTab", _class="tabPane")[
                    PageHelpers.TabSwitcher((
                        ('Forwarding',  'panelForwardPort'), 
                        ('Redirection', 'panelTransparentProxy'), 
                        ('NAT',         'panelNAT'), 
                        ('Source NAT',  'panelSNAT')
                    ), id ="firewallNAT"),
                    tags.div(id="panelForwardPort", _class="tabPane")[
                        tags.h3["Port Forwarding"], 
                        tags.p(_class="addRulePlacer")[tags.a(name="addFwdRule", id="fwAddFwdRuleButton", _class="addRuleBtn")['Add Forwarding Rule']],
                        fwdTableTags,
                        tags.div(id="firewallFwdRulesFormDialog", _class="dialogwin", style="width:450px;height:auto;display:none")[
                            tags.div(id="firewallFwdRulesFormTitle", _class="dialogtopbar")[""],
                            tags.div(_class="dialogcontent")[
                                tags.directive("form firewallForwardPortForm")
                            ]
                        ]
                    ],
                    tags.div(id="panelTransparentProxy", _class="tabPane")[
                        tags.h3["Port Redirection (Transparent Proxy)"], 
                        tags.p(_class="addRulePlacer")[tags.a(name="addRedirectRule", id="fwAddRedirectRuleButton", _class="addRuleBtn")['Add Redirection Rule']],
                        redirectTableTags,
                        tags.div(id="firewallRedirectRulesFormDialog", _class="dialogwin", style="width:450px;height:auto;display:none")[
                            tags.div(id="firewallRedirectRulesFormTitle", _class="dialogtopbar")[""],
                            tags.div(_class="dialogcontent")[
                                tags.directive("form firewallRedirectForm")
                            ]
                        ]
                    ],
                    tags.div(id="panelNAT", _class="tabPane")[
                        tags.h3["Nework Address Translation (Masquerading)"],
                        tags.p(_class="addRulePlacer")[tags.a(name="addMasqRule", id="fwAddMasqRuleButton", _class="addRuleBtn")['Add NAT Rule']],
                        masqTableTags,
                        tags.div(id="firewallMasqRulesFormDialog", _class="dialogwin", style="width:450px;height:auto;display:none")[
                            tags.div(id="firewallMasqRulesFormTitle", _class="dialogtopbar")[""],
                            tags.div(_class="dialogcontent")[
                                tags.directive("form firewallMasqForm")
                            ]
                        ]
                    ],
                    tags.div(id="panelSNAT", _class="tabPane")[
                        tags.h3["Source Nat"],
                        tags.p(_class="addRulePlacer")[tags.a(name="addSNATRule", id="fwAddSNATRuleButton", _class="addRuleBtn")['Add Source Nat Rule']],
                        snatTableTags,
                        tags.div(id="firewallSNATRulesFormDialog", _class="dialogwin", style="width:450px;height:auto;display:none")[
                            tags.div(id="firewallSNATRulesFormTitle", _class="dialogtopbar")[""],
                            tags.div(_class="dialogcontent")[
                                tags.directive("form firewallSNATForm")
                            ]
                        ]
                    ],
                    PageHelpers.LoadTabSwitcher(id="firewallNAT")
                ]

    def getForwardRules(self):
        rules = []
        for en, ru in self.sysconf.Shorewall.get('dnat',[]):
            ru = ru.split();
            destz = ru[1].split(':',1)[0]
            if ':' in ru[1]:
                source = ru[1].split(':',1)[-1]
            else:
                source = "Any"
            tzone = ru[2].split(':',1)[0]
            destip = ru[2].split(':',1)[-1]
            proto = ru[3]
            port = ru[4].strip('-') or "ANY"
            if len(ru)>6:
                sourceip = ru[6]
            else:
                sourceip = ""
            rules.append([destz, source, destip, tzone, proto, port, sourceip, '', ''])
        return rules
    
    def form_firewallForwardPortForm(self, data):
        form = formal.Form()
        form.addField('szone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Source Zone", description = "Source zone from which this rule will catch packets. ")

        form.addField('dzone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Destination Zone",
            description = "Destination Zone to which this rule will forward packets.")
        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)

        form.addField('port', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Port", description = "TCP/UDP port to forward. Blank for protocol forward (like PPTP). Use separate ranges with a colon.")
        form.addField('fwdip', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "Forward To", description = "Destination IP address to forward to")
        form.addField('dport', formal.String(strip=True, validators=[PageHelpers.PortValidator()]), label = "Forward To:Port", description = "TCP/UDP port to forward to. Blank for the same port.")
        form.addField('extip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Destination IP", description = "External IP to forward from")
        form.addField('sip', formal.String(strip=True, validators=[PageHelpers.IPValidator()]), label = "Source IP", description = "External IP to accept connections from")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.addAction(self.submitForwardPort)
        form.addAction('cancel', 'cancel', validate=False)
        return form
    
    def getForwardFormData(self, ruleID = None):
        """gets data that is used to populate the firewall forward form"""
        data = {
            u'szone':u'net',
            u'dzone':u'loc',
            u'port':u'',
            u'fwdip':u'',
            u'dport':u'',
            u'sip':u'',
            u'extip':u'',
            u'proto':u'tcp',
        }
        if ruleID:
            rid = self.parseID(ruleID)[0]
            
            ruleData = self.getForwardRules()[rid]
            dport = ':' in ruleData[2] and ruleData[2].split(':',2)[1] or ""
            data = {
                # XXX Needs some tweaking
                u'szone':unicode(ruleData[0].replace('Any', 'all')),
                u'dzone':unicode(ruleData[3].replace('Any', 'all')),
                u'port':unicode(ruleData[5].lower().replace('-','').replace('any', '')),
                u'fwdip':unicode(ruleData[2].split(':',2)[0]),
                u'dport':unicode(dport),
                u'sip':unicode(ruleData[1].replace('Any','')),
                u'extip':unicode(ruleData[6]),
                u'proto':unicode(ruleData[4]),
            }
        return data
    athena.expose(getForwardFormData)

    def submitForwardPort(self, data):
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false
        shw = self.sysconf.Shorewall
        
        if data['dport'].strip():
            dstport = ":%s" % data['dport'].strip()
        else:
            dstport = ""

        if data['sip'].strip():
            source = ":%s" % data['sip'].strip()
        else:
            source = ""

        rule = "DNAT    %s%s    %s:%s    %s      %s    -           %s" % (
            data['szone'], 
            source,
            data['dzone'],
            data['fwdip'] + dstport,
            data['proto'], 
            data['port'] or "-",
            data['extip'] or " ",
        )

        
        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None
 
        if(txt_ruleID):#Apply the new rule either insert or replace
            shw["dnat"][rid] = [1, unicode(rule)]
            actionText = "Updated"
        else:
            shw["dnat"].append([1, unicode(rule)])
            rid = len(shw["dnat"]) - 1
            actionText = "Added"
        
        self.sysconf.Shorewall = shw
        rule_data = self.getForwardRules()[rid]
        #htmlOut = flat.flatten(self.renderLIRule(rule_data, ['srczone', 'srcip', 'fwdip', 'dstzone', 'protocol', 'port', 'dstip', 'edit', 'delete'])) #Get the new html of the rule

        self.callRemote('insertTR', u'firewallForwardRules', txt_ruleID, self.unicodeArray(rule_data), [u'srczone', u'srcip', u'fwdip', u'dstzone', u'protocol', u'port', u'dstip', u'edit', u'delete'], u'forwardRule')
        self.callRemote('initForwardListEvents');
        self.raiseNotice("Port Forward was successfully %s" % actionText);
        Utils.log.msg('%s added a new firewall port forward %s' % (self.avatarId.username, repr(data)))
    athena.expose(submitForwardPort)

    def delForwardPort(self, ruleID):
        """
        Removes the Forward Port entry at ruleID
        """
        rdet = self.parseID(ruleID)
        if not rdet:
            self.raiseError("Unable to delete PortForward due to invalid ID")
            return
        dnatRules = self.sysconf.Shorewall["dnat"]
        del dnatRules[rdet[0]]
        shw = self.sysconf.Shorewall
        shw["dnat"] = dnatRules
        self.sysconf.Shorewall = shw
        self.raiseNotice('Port Forward was deleted successfully')
    athena.expose(delForwardPort)

    def form_firewallRedirectForm(self, data):
        form = formal.Form()
        
        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)

        form.addField('srczone', formal.String(required=True), 
            formal.widgetFactory(formal.SelectChoice, options = self.getZones()), 
            label = "Source Zone", description = "Source zone from which this rule will catch traffic")

        form.addField('srcnet', formal.String(), label = "Source IP", description=["Source IP address of connecting host or network (Leave blank for ANY)."
        " This is usually a source host or network you want to exclude."])

        form.addField('dstnet', formal.String(), label = "Destination IP", description = ["Destination IP address or network (Leave blank for ANY). ", 
        "This is usually the opposite (!) of your local network.", "This is NOT the server you'd like to proxy to."])
        form.addField('srcport', formal.String(required=True, strip=True, validators=[PageHelpers.PortValidator()]), label = "Source port", description = "TCP/UDP port to catch.")
        form.addField('dstport', formal.String(required=True, strip=True, validators=[PageHelpers.PortValidator()]), label = "Destination port", description = "TCP/UDP port to forward to.")
        form.addField('protocol', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = self.protocols), label = "Protocol")
        form.addAction(self.submitRedirectRule)
        form.addAction('cancel', 'cancel', validate=False)
        return form

    def getRedirectRules(self):
        rules = []
        for en, ru in self.sysconf.Shorewall.get('redirect', []):
            ru = ru.split();
            if ":" in ru[1]:
                source = ru[1].split(':')[-1]
                zone = ru[1].split(':')[0]
            else:
                source = ""
                zone = ru[1]

            srcport = ru[4]
            dstport = ru[2]
            proto = ru[3]
            if len(ru) > 6:
                dest = ru[6]
            else:
                dest = "-"
            rules.append([zone, source, srcport, dstport, proto, dest, '', ''])
        return rules

    def getRedirectFormData(self, ruleID = None):
        """
        Gets the rule data for the specified ruleID
        """
        data = {
            u'srczone':u'loc',
            u'srcnet':u'',
            u'dstport':u'',
            u'srcport':u'',
            u'protocol':u'tcp',
            u'dstnet':u'',
        }
        if ruleID:
            rid = self.parseID(ruleID)[0]
            ruleData = self.getRedirectRules()[rid]
            print ruleData #Analyze and map accordingly
 
            data = {
                u'srczone':unicode(ruleData[0]),
                u'srcnet':unicode(ruleData[1]),
                u'dstport':unicode(ruleData[2]),
                u'srcport':unicode(ruleData[3]),
                u'protocol':unicode(ruleData[4]),
                u'dstnet':unicode(ruleData[5].replace('-','')),
            }
        return data
    athena.expose(getRedirectFormData)

    def submitRedirectRule(self, data):
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false
        shw = self.sysconf.Shorewall
        if data['srcnet']:
            data['srcnet'] = ":%s" % data['srcnet']
        else:
            data['srcnet'] = ""       
        rule = "REDIRECT  %(srczone)s%(srcnet)s   %(srcport)s    %(protocol)s    %(dstport)s    -   %(dstnet)s" % data
        print rule
        
        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None
 
        if(txt_ruleID):#Apply the new rule either insert or replace
            shw["redirect"][rid] = [1, unicode(rule)]
            actionText = "Updated"
        else:
            shw["redirect"].append([1, unicode(rule)])
            rid = len(shw["redirect"]) - 1
            actionText = "Added"
        
        self.sysconf.Shorewall = shw
        rule_data = self.getRedirectRules()[rid]
        #htmlOut = flat.flatten(self.renderLIRule(rule_data, ['srczone', 'srcnet', 'dstport', 'srcport', 'protocol', 'dstnet', 'edit', 'delete'])) #Get the new html of the rule

        self.callRemote('insertTR', u'firewallRedirectRules', txt_ruleID, self.unicodeArray(rule_data), [u'srczone', u'srcnet', u'dstport', u'srcport', u'protocol', u'dstnet', u'edit', u'delete'], u'redirectRule')
        self.callRemote('initRedirectListEvents');
        self.raiseNotice("Redirect Rule was successfully %s" % actionText);
        Utils.log.msg('%s added a new firewall transparent proxy %s' % (self.avatarId.username, repr(data)))

    athena.expose(submitRedirectRule)

    def delRedirectRule(self, ruleID):
        """
        Removes a redirect rule
        """
        rdet = self.parseID(ruleID)
        if not rdet:
            self.raiseError("Unable to delete Redirect due to invalid ID")
            return
        redirectRules = self.sysconf.Shorewall["redirect"]
        del redirectRules[rdet[0]]
        shw = self.sysconf.Shorewall
        shw["redirect"] = redirectRules
        self.sysconf.Shorewall = shw
        self.raiseNotice('Redirect Rule was deleted successfully')

    athena.expose(delRedirectRule)

    def form_firewallMasqForm(self, data):
        form = formal.Form()

        ifs = [(i,i) for i in Utils.getInterfaces()]
        
        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)

        form.addField('dstint', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "External Interface",
            description = "The interface to which this traffic will be NATed.")

        form.addField('srcint', formal.String(), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "Source Interface",
            description = "The interface which will have NAT applied to it")

        form.addField('dstnet', formal.String(), label = "Destination IP", description = ["Destination IP or network (Leave blank for ANY). ", 
        "This is the destination network you would like to NAT to"])

        form.addField('srcnet', formal.String(), label = "Source IP", description = ["Source IP or network (Leave blank for ANY). ", 
        "This is the source network you would like to NAT from."])

        form.addField('natip', formal.String(), label = "NAT IP", description = ["The IP address that you would like to NAT the connections as.",
            "Leave this blank to let the firewall decide based on the interface configuration."])

        form.addField('protocol', formal.String(), formal.widgetFactory(formal.SelectChoice, options = self.protocols), 
            label = "Protocol", description = "Protocol to NAT")
        form.addField('port', formal.String(strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Source port", description = "TCP/UDP port to NAT.")

        form.addAction(self.submitMasqRule)
        form.addAction('cancel', 'cancel', validate=False)

        return form
    
    def getMasqRules(self):
        rules = []
        for interface, masq in self.sysconf.Shorewall.get('masq', {}).items():
            for v in masq:
                if type(v) == list:
                    l = [interface]
                    l.extend([i.replace('-', 'Any') for i in v])
                    l.extend(['',''])
                    rules.append(l)
                else:
                    rules.append([interface, 'Any', v, 'Any', 'Any', 'Any', 'Any','',''])
        return rules

    def commitMasqRules(self):
        """
        Take the rules stored in self.masqRules and repopulate the config with the data
        """
        newRules = {}

        for ruleData in self.masqRules:
            data = {
                'dstint':ruleData[0].encode("ascii", "replace"),
                'dstnet':ruleData[1].replace('Any','').encode("ascii", "replace"),
                'srcint':ruleData[2].encode("ascii", "replace"),
                'srcnet':ruleData[3].replace('Any','').encode("ascii", "replace"),
                'natip':ruleData[4].replace('Any','').encode("ascii", "replace"),
                'protocol':ruleData[5].replace('Any','').encode("ascii", "replace"),
                'port':ruleData[6].replace('Any','').encode("ascii", "replace"),
            }
            if data['srcint'] and not ( data['dstnet'] or data['srcnet'] or data['natip'] or data['protocol'] or data['port'] ):
                rule = data['srcint']
            else:
                rule = [data['dstnet'] or '-']
                rule.append(data['srcint'] or '-')
                rule.append(data['srcnet'] or '-')
                rule.append(data['natip'] or '-')
                rule.append(data['protocol'] or '-')
                rule.append(data['port'] or '-')
            dest = data['dstint']

            if dest not in newRules:
                newRules[dest] = [rule]
            else:
                newRules[dest].append(rule)
        
        shw = self.sysconf.Shorewall
        shw["masq"] = newRules
        self.sysconf.Shorewall = shw

    def getMasqFormData(self, ruleID = None):
        data = {
            u"dstint":u"",
            u"dstnet":u"",
            u"srcint":u"",
            u"srcnet":u"",
            u"natip":u"",
            u"protocol":u"",
            u"port":u"",
        }
        if ruleID:
            rid = self.parseID(ruleID)[0]
            ruleData = self.masqRules[rid]
            print ruleData #Analyze and map accordingly
 
            data = {
                u'dstint':unicode(ruleData[0]),
                u'dstnet':unicode(ruleData[1].replace('Any','')),
                u'srcint':unicode(ruleData[2]),
                u'srcnet':unicode(ruleData[3].replace('Any','')),
                u'natip':unicode(ruleData[4].replace('Any','')),
                u'protocol':unicode(ruleData[5].replace('Any','')),
                u'port':unicode(ruleData[6].replace('Any','')),
            }

        return data
    athena.expose(getMasqFormData)

    def submitMasqRule(self, data):
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false
        #Build Rule
        masqRulesColClasses = ['dstint', 'dstnet', 'srcint', 'srcnet', 'natip', 'protocol', 'port', 'edit', 'delete']
        rule = [ 
            data['dstint'],
            data['dstnet'] and data['dstnet'] or 'Any',
            data['srcint'],
            data['srcnet'] and data['srcnet'] or 'Any',
            data['natip'] and data['natip'] or 'Any',
            data['protocol'] and data['protocol'] or 'Any',
            data['port'] and data['port'] or 'Any'
        ]
        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None

        if txt_ruleID:
            actionText = "Updated"
            self.masqRules[rid] = rule
        else:
            actionText = "Added"
            self.masqRules.append(rule)

        rule.extend(["",""]) #Make sure edit and delete are here

        self.commitMasqRules()
        #htmlOut = flat.flatten(self.renderLIRule(rule, masqRulesColClasses)) #Get the new html of the rule

        self.callRemote('insertTR', u'firewallMasqRules', txt_ruleID, self.unicodeArray(rule), self.unicodeArray(masqRulesColClasses), u'masqRule')
        self.callRemote('initMasqListEvents');
        self.raiseNotice("Nat Rule was successfully %s" % actionText);

        Utils.log.msg('%s added a new firewall nat rule %s' % (self.avatarId.username, repr(data)))

    athena.expose(submitMasqRule)

    def delMasqRule(self, ruleID):
        """
        Removes the Masq entry at ruleID
        """
        rdet = self.parseID(ruleID)
        if not rdet:
            self.raiseError("Unable to delete NAT rule due to invalid ID")
            return
        del self.masqRules[rdet[0]]
        self.commitMasqRules()
        self.raiseNotice('NAT rule was deleted successfully')
 
    athena.expose(delMasqRule)

    def form_firewallSNATForm(self, data):
        form = formal.Form()

        ifs = []
        for i in Utils.getInterfaces():
            if 'eth' in i or 'tap' in i or 'vlan' in i: # Only allow tap and eth binds...
                ifs.append((i, i))
        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)

        form.addField('dstif', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifs), label = "External Interface",
            description = "The interface to which this traffic will be NATed. (Generaly the outside/internet interface)")

        form.addField('dstip', formal.String(required=True, validators=[PageHelpers.IPValidator()]), label = "External IP",
            description = "The IP to which this traffic will be NATed")

        form.addField('srcip', formal.String(required=True, strip=True, validators=[PageHelpers.IPValidator()]), label = "Source IP", description = ["The source IP you would like to NAT to and from."])

        form.addField('all', formal.Boolean(), label = "Any Interface", 
            description = "Tick this if the rule should apply to all interfaces and not just the External Interface.")

        form.addField('local', formal.Boolean(), label = "Use Internal", description = "Apply this NAT rule to this servers traffic as well.")

        form.addAction(self.submitSNATRule)
        form.addAction('cancel', 'cancel', validate=False)

        return form
        
    def getSNATFormData(self, ruleID = None):
        """
        Gets the rule data for the specified ruleID
        """
        data = {
            u'dstip':u'',
            u'dstif':u'',
            u'srcip':u'',
            u'all': False,
            u'local': False,
        }
        
        if ruleID:
            rid = self.parseID(ruleID)[0]
            ruleData = self.getSNATRules()[rid]
            data = {
                u'dstip':unicode(ruleData[0]),
                u'dstif':unicode(ruleData[1]),
                u'srcip':unicode(ruleData[2]),
                u'all':ruleData[3] == "yes",
                u'local':ruleData[4] == "yes",
            }
        return data
    athena.expose(getSNATFormData)

    def getSNATRules(self):
        rules = []
        for ru in self.sysconf.Shorewall.get('snat', []):
            ru = ru.split()
            ru.extend([' ',' '])
            rules.append(ru)
        return rules

    def submitSNATRule(self, data, ruleID = None):
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false
        shw = self.sysconf.Shorewall

        ru = "%s    %s            %s      %s          %s" % (
            data['dstip'].encode("ascii", "replace"),
            data['dstif'].encode("ascii", "replace"),
            data['srcip'].encode("ascii", "replace"),
            data['all'] and "yes" or "no",
            data['local'] and "yes" or "no",
        )
        
        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None
 
        if(txt_ruleID):#Apply the new rule either insert or replace
            shw["snat"][rid] = unicode(ru)
            actionText = "Updated"
        else:
            if shw.get('snat',False):
                shw['snat'].append(ru)
            else:
                shw['snat'] = [ru]

            rid = len(shw["snat"]) - 1
            actionText = "Added"
        
        self.sysconf.Shorewall = shw
        rule_data = self.getSNATRules()[rid]
        snatRulesColClasses = ['srcip', 'extint', 'intint', 'anyint', 'useint', 'edit', 'delete']
        #htmlOut = flat.flatten(self.renderLIRule(rule_data, snatRulesColClasses)) #Get the new html of the rule

        self.callRemote('insertTR', u'firewallSNATRules', txt_ruleID, self.unicodeArray(rule_data), self.unicodeArray(snatRulesColClasses), u'snatRule')
        self.callRemote('initSNATListEvents');
        self.raiseNotice("SNAT Rule was successfully %s" % actionText);

        Utils.log.msg('%s added a new firewall SNAT rule %s' % (self.avatarId.username, repr(data)))


        #self.sysconf.Shorewall = e
    athena.expose(submitSNATRule)

    def delSNATRule(self, ruleID = None):
        """
        Removes a snat rule
        """
        rdet = self.parseID(ruleID)
        if not rdet:
            self.raiseError("Unable to delete SNAT due to invalid ID")
            return
        snatRules = self.sysconf.Shorewall["snat"]
        del snatRules[rdet[0]]
        shw = self.sysconf.Shorewall
        shw["snat"] = snatRules
        self.sysconf.Shorewall = shw
        self.raiseNotice('SNAT Rule was deleted successfully')
    athena.expose(delSNATRule)

    def getQosRules(self):
        toss = {
            '16':'Minimize Delay',
            '8':'Maximize Throughput',
            '4':'Maximize Reliability',
            '2':'Minimize Cost',
            '0':'Normal Service'
        }
        qosRules = []
        l = 0
        for port, proto, tos in self.sysconf.Shorewall.get('qos', []):
            qosRules.append([
                port,
                proto,
                toss[tos],
                '',''
            ])
        return qosRules

    def render_firewallQOS(self, ctx, data):

        qosRulesColNames = ['Port', 'Protocol', 'Type of service', '', ''];
        qosRulesColClasses = ['port', 'proto', 'qos', 'edit', 'delete'];
        qosTableTags = self.renderDataTable("firewallQosRules", 'qosRule' , self.getQosRules(), qosRulesColNames, qosRulesColClasses)

        return tags.div(id="firewallQOSTab", _class="tabPane")[
            tags.h3["QOS"],
            tags.p(_class="addQosRulePlacer")[tags.a(name="addQosRule", id="fwAddQosRuleButton", _class="addRuleBtn")['Add Qos Rule']],
            qosTableTags,
            tags.div(id="firewallQosRulesFormDialog", _class="dialogwin", style="width:450px;height:auto;display:none")[
                tags.div(id="firewallQosRulesFormTitle", _class="dialogtopbar")[""],
                tags.div(_class="dialogcontent")[
                    tags.directive('form firewallQosForm') 
                ]
            ]
        ]
    
    def form_firewallQosForm(self, data):
        tos = [
            ('16', 'Minimize Delay'),
            ('8',  'Maximize Throughput'),
            ('4',  'Maximize Reliability'),
            ('2',  'Minimize Cost'),
            ('0',  'Normal Service')
        ]
        form = formal.Form()
        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)
        protocols = [('tcp', 'TCP'),
                     ('udp', 'UDP'),
                     ('47', 'PPTP')]
        form.addField('port', formal.String(required=True, strip=True, validators=[PageHelpers.PortRangeValidator()]), label = "Port")
        form.addField('proto', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = protocols), label = "Protocol")
        form.addField('qos', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = tos), label = "Type of service")
        form.addAction(self.submitQosRule)
        form.addAction('cancel', 'cancel', validate=False)

        return form

    def getQosFormData(self, ruleID=None):
        data = {
            u'port' : u'',
            u'proto': u'',
            u'qos': u''
        }
        if(ruleID):
            rid = self.parseID(ruleID)[0]
            ruledata = self.sysconf.Shorewall.get('qos', [])[rid]
            print ruledata
            data = {
                u'port' : unicode(ruledata[0]),
                u'proto': unicode(ruledata[1]),
                u'qos': unicode(ruledata[2])
            }
        return data
    athena.expose(getQosFormData)

    def submitQosRule(self, data):
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false
        shw = self.sysconf.Shorewall

        rule = (data['port'].encode("ascii", "replace"),
                data['proto'].encode("ascii", "replace"), 
                data['qos'].encode("ascii", "replace"))
        print rule
        
        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None
 
        if(txt_ruleID):#Apply the new rule either insert or replace
            shw["qos"][rid] = rule
            actionText = "Updated"
        else:
            if not shw.get('qos', None):
                shw['qos'] = []
            shw["qos"].append(rule)
            rid = len(shw["qos"]) - 1
            actionText = "Added"

        self.sysconf.Shorewall = shw

        qosRulesColClasses = ['port', 'proto', 'qos', 'edit', 'delete'];
        #htmlOut = flat.flatten(self.renderLIRule(self.getQosRules()[rid], qosRulesColClasses)) #Get the new html of the rule

        self.callRemote('insertTR', u'firewallQosRules', txt_ruleID, self.unicodeArray(self.getQosRules()[rid]), self.unicodeArray(qosRulesColClasses), u'qosRule')
        self.callRemote('initQosListEvents');
        self.raiseNotice("Qos Rule was successfully %s" % actionText);

        Utils.log.msg('%s %s a new firewall qos rule %s' % (self.avatarId.username, actionText, repr(data)))


    athena.expose(submitQosRule)

    def delQosRule(self, ruleID):
        """
        Removes a qos rule
        """
        rdet = self.parseID(ruleID)
        if not rdet:
            self.raiseError("Unable to delete Qos Rule due to invalid ID")
            return
        qosRules = self.sysconf.Shorewall["qos"]
        del qosRules[rdet[0]]
        shw = self.sysconf.Shorewall
        shw["qos"] = qosRules
        self.sysconf.Shorewall = shw
        self.raiseNotice('Qos Rule was deleted successfully')

    athena.expose(delQosRule)

    def render_firewallPolicy(self, ctx, data):
        return tags.div(id="firewallPolicyTab", _class="tabPane")[
            tags.div(id="panelPolicy", _class="tabPane")[
                    tags.h3["General firewall policy"],
                    tags.directive('form firewallPolicyForm') 
            ]]

    def form_firewallPolicyForm(self, data):
        form = formal.Form()
        if os.path.exists('/lib/iptables/libipt_ipp2p.so'):
            form.addField('blockp2p', formal.Boolean(), label = "Block P2P")

        form.addField('transProxy', formal.Boolean(), label = "Web transparent proxy",
            description = "Transparently proxy all web traffic")
        form.addField('blockAll', formal.Boolean(), label = "Block LAN -> Internet",
            description = "Block the LAN from accessing the internet directly. Web proxy access will still be permitted, as well as SMTP")

        try:
            lanpolicy = self.sysconf.Shorewall['zones']['loc']['policy']
            if lanpolicy != "ACCEPT":
                form.data['blockAll'] = True
        except:
            form.data['blockAll'] = False

        if self.testProxy():
            form.data['transProxy'] = True

        if self.sysconf.Shorewall.get('blockp2p', False):
            form.data['blockp2p'] = True

        return form

    def testProxy(self):
        transwww = self.sysconf.Shorewall['redirect']

        for en, ru in transwww:
            if "REDIRECT" in ru and "tcp" in ru and "80" in ru:
                return True


    def setTransProxy(self, state=False):
        transwww = self.sysconf.Shorewall
        if state:
            # XXX We should have support for multiple LANPrimary interfaces here.
            net = [i for j,i in Utils.getLanNetworks(self.sysconf).items()][0]
            transwww['redirect'].append([
                1, "REDIRECT loc      8080     tcp     80      -     !%s" % (net)
            ])
        else:
            newRules = []
            for k, ru in enumerate(transwww['redirect']):
                if "REDIRECT" in ru[1] and "tcp" in ru[1] and "80" in ru[1] and "8080" in ru[1]:
                    print "clipping"
                    self.callRemote('removeListEntry', u'redirectRule_%s' % k)
                else:
                    newRules.append(ru)

            transwww['redirect'] = newRules

        self.sysconf.Shorewall = transwww

        if(state):
            #rid = len(self.getRedirectRules()) - 1
            #txt_ruleID = u'redirectRule_%s' % rid
            #rule_data = self.getRedirectRules()[rid]
            rule_data = self.getRedirectRules()[-1]
            #htmlOut = flat.flatten(self.renderLIRule(rule_data, ['srczone', 'srcnet', 'dstport', 'srcport', 'protocol', 'dstnet', 'edit', 'delete'])) #Get the new html of the rule

            self.callRemote('insertTR', u'firewallRedirectRules', None, self.unicodeArray(rule_data), [u'srczone', u'srcnet', u'dstport', u'srcport', u'protocol', u'dstnet', u'edit', u'delete'], u'redirectRule')
        self.callRemote('initRedirectListEvents');
        actionTXT = state and "Enabled" or "Disabled"
        self.raiseNotice("Transparent Proxy %s" % actionTXT);
        Utils.log.msg('%s %s the transparent proxy' % (self.avatarId.username, actionTXT))
    athena.expose(setTransProxy)

    def setBlockAllLAN(self, state = False):
        shorewall = self.sysconf.Shorewall
        try:
            if state:
                lanpolicy = shorewall['zones']['loc']['policy'] = "DROP"
            else:
                lanpolicy = shorewall['zones']['loc']['policy'] = "ACCEPT"
        except:
            print "Failed to change loc zone"

        self.sysconf.Shorewall = shorewall

        actionTXT = state and "DROP" or "ACCEPT"
        #XXX XXX Once zones have been added will need to put update the loc zone on the interface
        self.raiseNotice("Set the policy for local zone to %s" % actionTXT);
        Utils.log.msg('%s set the policy for loc to %s' % (self.avatarId.username, actionTXT))
    athena.expose(setBlockAllLAN)
    
    def setBlockP2P(self, state = False):
        shorewall = self.sysconf.Shorewall

        if state:
            shorewall['blockp2p'] = state
        else:
            shorewall['blockp2p'] = False

        self.sysconf.Shorewall = shorewall

        actionTXT = state and "Enabled" or "Disabled"
        self.raiseNotice("P2P Blocking %s" % actionTXT);
        Utils.log.msg('%s %s P2P Blocking' % (self.avatarId.username, actionTXT))
    athena.expose(setBlockP2P)


    def render_firewallZones(self, ctx, data):
        zoneColNames = ['Zone Name', 'Policy', 'Log target', 'Interfaces', '', ''];
        zoneColClasses = ['name', 'policy', 'log', 'interface', 'edit', 'delete'];
        zoneTableTags = self.renderDataTable("firewallZones", 'zoneRule' , self.getZoneData(), zoneColNames, zoneColClasses)

        return tags.div(id="firewallZonesTab", _class="tabPane")[
            tags.h3["Zones"],
            tags.p(_class="addZonePlacer")[tags.a(name="addZones", id="fwAddZoneButton", _class="addRuleBtn")['Add Zone']],
            tags.div(id="firewallZoneTable")[zoneTableTags],
            tags.div(id="firewallZoneFormDialog", _class="dialogwin", style="width:550px;height:auto;display:none")[
                tags.div(id="firewallZoneFormTitle", _class="dialogtopbar")[""],
                tags.p(_class="addMemPlacer")[tags.a(name="addMem", id="fwAddMemButton", _class="addRuleBtn")['Add Member']],
                tags.div(id='zoneMemberTable') [
                    self.genFirewallZoneMembersTable()
                ], 
                tags.directive('form firewallZoneForm'),
            ],
            tags.div(id="zoneMemFormDialog", _class="dialogwin", style="width:450px;height:auto;display:none")[
                tags.div(id="zoneMemFormTitle", _class="dialogtopbar")[""],
                tags.directive('form firewallZoneMember')
            ]
        ]

    def getZones(self):
        """
        gets a list of zones that can be used for dropdown lists
        """
        zones = self.sysconf.Shorewall.get('zones', {})
        baseZones = [
            (u"all", u"Any"), 
            (u'fw', u"Firewall")
        ]
        if self.sysconf.ProxyConfig.get('captive'):
            for zo in Utils.getLanZones(self.sysconf):
                baseZones.append((u"c%s" % zo, u"Authenticted %s" % zo))
        return baseZones + [(unicode(zo),unicode(zo)) for zo in zones.keys()] # Build something we can se for drop downs
    athena.expose(getZones)

    def getZoneMemberData(self, zone):
        data = []
        ifaces = self.sysconf.Shorewall['zones'].get(zone, {}).get('interfaces', [])
        
        for i in ifaces:
            tline = [i.split()[0]]
            if 'dhcp' in i:
                tline.append('yes') 
            else:
                tline.append('no')

            if 'routeback' in i:
                tline.append('yes')
            else:
                tline.append('no')

            tline.extend(['',''])

            data.append(tline)
        return data

    def getZoneData(self):
        """
        getZoneData collects all the information that is used to generate a list of zones for editing
        """
        return [[ zone, zd['policy'], zd['log'], [[i, tags.br] for i in zd['interfaces']],
                  "","" #Edit ,Delete
                ] 
               for zone, zd in self.sysconf.Shorewall.get('zones', {}).items()]

    def form_firewallZoneForm(self, data):
        form = formal.Form()

        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)

        form.addField('zone', formal.String(required=True), label = "Zone name", description = "The name of this zone")

        form.addField('policy', formal.String(required=True),  formal.widgetFactory(formal.SelectChoice, options = [
                ('ACCEPT', 'ACCEPT'),
                ('DROP', 'DROP')
            ]), label = "Policy", 
            description = "The default action to take on traffic not matching any rule")

        form.addField('log', formal.String(), label = "Log", description = "Advanced: Logging target for dropped packets. Usualy $log if policy is ACCEPT")

        #form.addField('interfaces', formal.String(), label = "Interface members", description = "Advanced: Comma separated list of interface defenitions.")
       
        form.addAction(self.submitZone)
        form.addAction('cancel', 'cancel', validate=False)

        return form


    def getZoneFormData(self, ruleID = None):
        """
        Get Zone details for zone adding / editing forms
        """
        data = {
            u"zone": u"",
            u"policy": u"",
            u"log": u""
        }
        
        if ruleID:
            rid = self.parseID(ruleID)[0]
            ruleData = self.getZoneData()[rid]
            data = {
                u"zone": unicode(ruleData[0]),
                u"policy": unicode(ruleData[1]),
                u"log": unicode(ruleData[2])
            }
        return data
    athena.expose(getZoneFormData)

    def form_firewallZoneMember(self, data):
        form = formal.Form()
        ifaces = [(i,i) for i in Utils.getInterfaces()]

        form.addField('ruleID', formal.String(), widgetFactory=formal.Hidden)
        form.addField('iface', formal.String(required=True), formal.widgetFactory(formal.SelectChoice, options = ifaces), label = "Interface")
        form.addField('dhcp', formal.Boolean(), label = "DHCP", description="Check this if DHCP is performed on this interface")
        form.addField('routeback', formal.Boolean(), label = "Route-back", description = "Check this if route reflection is allowed on this interface")

        form.data['iface'] = ifaces[0][0]
        form.addAction(self.submitZoneMember)
        form.addAction('cancel', 'cancel', validate=False)

        return form
    
    def genFirewallZoneMembersTable(self, data=[]):
        zoneMemberColNames = ['Interface', 'Dhcp', 'Route-back', '', '']
        zoneMemberClasses = ['iface', 'dhcp', 'routeback', 'edit', 'delete']
        zoneMemberTableTags = self.renderDataTable(
            "zoneMembers",
            'zoneMember',
            data,
            zoneMemberColNames,
            zoneMemberClasses)
        return zoneMemberTableTags

    def genZoneMembersHTML(self, ruleID):
        #Firstly resolve the ruleID
        if ruleID:
            rdet = self.parseID(ruleID)
            rid = self.parseID(ruleID)[0]
            self.currentZoneData = self.getZoneData()[rid]
            self.currentZoneMemData = self.getZoneMemberData(self.currentZoneData[0])
        else:
            self.currentZoneData = None
            self.currentZoneMemData = []
        return unicode(flat.flatten(self.genFirewallZoneMembersTable(self.currentZoneMemData)))
    athena.expose(genZoneMembersHTML)

    def getZoneMemberFormData(self, ruleID):
        data = {
            u'iface': u'',
            u'dhcp': False,
            u'routeback': False,
        }
        if not ruleID:
            #If we should return an empty entry
            return data
        rid = self.parseID(ruleID)[0]
        if len(self.currentZoneMemData) > rid:
            data = {
                #u'ruleID': ruleID,
                u'iface': unicode(self.currentZoneMemData[rid][0]),
                u'dhcp': 'yes' in self.currentZoneMemData[rid][1] and True or False,
                u'routeback': 'yes' in self.currentZoneMemData[rid][2] and True or False,
            }
        return data
    athena.expose(getZoneMemberFormData)

    def submitZoneMember(self, data):
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false

        ln = [data['iface'].encode("ascii","replace"), data['dhcp'] and "yes" or "no", data['routeback'] and "yes" or "no", '', '']

        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None
            
        if(txt_ruleID):#Apply the new rule either insert or replace
            self.currentZoneMemData[rid] = ln
            actionText = "Updated"
        else:
            self.currentZoneMemData.append(ln)
            rid = len(self.currentZoneMemData) - 1
            actionText = "Added"

        zoneMemberClasses = ['iface', 'dhcp', 'routeback', 'edit', 'delete']
        #htmlOut = flat.flatten(self.renderLIRule(ln, zoneMemberClasses)) #Get the new html of the rule
        self.callRemote('insertTR', u'zoneMembers', txt_ruleID, self.unicodeArray(ln), self.unicodeArray(zoneMemberClasses), u'zoneMember')
        self.callRemote('initZoneMemEvents');

        if self.currentZoneData:
            zoneName = self.currentZoneData[0]
        else:
            zoneName = "New Zone"

        Utils.log.msg('%s (Q) %s of interface to zone %s => %s' % (self.avatarId.username, actionText, zoneName, repr(data)))

    athena.expose(submitZoneMember)

    def delZoneMember(self, ruleID = None):
        try:
            rid = self.parseID(ruleID)[0]
        except:
            rid = None
        if not ruleID:
            return
        print rid
        val = self.currentZoneMemData[rid]
        del self.currentZoneMemData[rid]
        if self.currentZoneData:
            zoneName = self.currentZoneData[0]
        else:
            zoneName = "New Zone"

        Utils.log.msg('%s (Q) Removed interface zone %s => %s' % (self.avatarId.username, zoneName, val[0]))
    athena.expose(delZoneMember)

    def submitZone(self, data):
        if(not '__nevow_form__' in data):
            """Not a nevow form"""
            return false

        interfaces = []
        for zoneMem in self.currentZoneMemData:
            options = []
            if "yes" in zoneMem[1]:
                options.append('dhcp')
            if "yes" in zoneMem[2]:
                options.append('routeback')
            interfaces.append("%s detect %s" % (zoneMem[0].encode("ascii","replace"), ','.join(options)))
        k = self.sysconf.Shorewall

        zoneName = data['zone'].encode("ascii", "replace")
        if self.currentZoneData:
            del k['zones'][self.currentZoneData[0]]
        k['zones'][zoneName] = {}
        k['zones'][zoneName]['interfaces'] = interfaces
        k['zones'][zoneName]['policy'] = data['policy'].encode("ascii", "replace")
        k['zones'][zoneName]['log'] = data['log'] or ''
        try:
            rid = self.parseID(data["ruleID"])[0]
            txt_ruleID = data["ruleID"]
        except:
            rid = None
            txt_ruleID = None
            
        if(txt_ruleID):
            actionText = "Updated"
            isNew = False
        else:
            rid = len(k['zones']) - 1
            actionText = "Added"
            isNew = True

        self.sysconf.Shorewall = k
        
        zoneColNames = ['Zone Name', 'Policy', 'Log target', 'Interfaces', '', ''];
        zoneColClasses = ['name', 'policy', 'log', 'interface', 'edit', 'delete'];
        htmlOut = flat.flatten(self.renderDataTable("firewallZones", 'zoneRule' , self.getZoneData(), zoneColNames, zoneColClasses))
        self.callRemote('popZones', unicode(zoneName), isNew, unicode(htmlOut))
        self.callRemote('updateZones', [unicode(zone) for zone in k['zones'].keys()])

        Utils.log.msg('%s modified firewall zone %s' % (self.avatarId.username, zoneName))

    athena.expose(submitZone)

    def delZone(self, ruleID = None):
        k = self.sysconf.Shorewall
        try:
            rid = self.parseID(ruleID)[0]
        except:
            rid = None

        if not ruleID:
            return

        zoneName = k['zones'].keys()[rid]
        del k['zones'][zoneName]

        self.sysconf.Shorewall = k

        self.callRemote('updateZones', [unicode(zone) for zone in k['zones'].keys()])

        Utils.log.msg('%s deleted firewall zone %s' % (self.avatarId.username, zoneName))
    athena.expose(delZone)

    def updateConnections(self):
        """Updates the user connection table"""
        # Grab netstat
        l = WebUtils.system('netstat -n --ip | grep -E ".?[0-9]?[0-9]?[0-9]\." | awk \'{print $4 " " $5}\'| uniq | sort')

        # build a matcher
        regex = re.compile("(.*):(.*) (.*):(.*)")

        def renderFragment(ret, error=False):
            if error:
                print ret
                print "ERROR"
                return

            connections = []
            connList = []
            for con in ret.split('\n'):
                m = regex.match(con)
                if m:
                    tup = m.groups()
                    if tup[0] == tup[2]:
                        # boring
                        continue
                    connections.append(list(tup)+[
                        tags.div(_class="addRulePlacerInLine")[tags.a(name="addConnectionRule", id="fwAddConnRuleButton", _class="addRuleBtnTR")['Add Block']]
                    ])
                    connList.append(tup)

            self.connList = connList
            connectColClasses = ['dstip', 'dstport', 'srcip', 'srcport', 'addrule'];
            connectColNames = ["Destination IP", "Destination Port", "Source IP", "Source Port", ""];
            htmlOut = flat.flatten(self.renderDataTable("firewallConnections", 'connectionRule' , connections, connectColNames, connectColClasses))
            self.callRemote('populateTableHTML', u'firewallConnectionsTab', unicode(htmlOut), u'firewallConnections', u'connectionRule')
            self.callRemote('initFirewallConnectionsTable');

        return l.addCallback(renderFragment).addErrback(renderFragment, True)
    athena.expose(updateConnections)
    
    def addConnectionRule(self, ruleID = None):
        """Adds a connection based on the ruleID provided by the users click event"""
        if not ruleID:
            return
        try:
            rid = self.parseID(ruleID)[0]
            conn = self.connList[rid]
        except:
            rid = None
            conn = None

        if not conn:
            print "Could not determine the connection"
            return


        try:
            sport = int(conn[3])
        except:
            sport = 0

        try:
            dport = int(conn[1])
        except:
            dport = 0

        if sport > dport and dport > 0:
            sport = ""
            dport = str(dport)
        elif dport > sport and sport > 0:
            dport = ""
            sport = str(sport)
        else:
            sport = ""
            dport = ""

        zones = self.sysconf.Shorewall.get('zones', {})
        def resolveZone(iface):
            """Resolves an interface's Zone"""
            for zone, zdata in zones.items():
                for ifaceDet in zdata.get('interfaces', []):
                    if ifaceDet.split(' ')[0] == iface:
                        return zone

        def calculateZones(ret, error=False):
            if error:
                print "ERROR: " + str(ret)
            else:
                intBinds = ret.split('\n')
                szone = "all"
                dzone = "net"
                for intB in intBinds:
                    intB = intB.strip()
                    if len(intB) < 5:
                        continue
                    intB = intB.split(' ')
                    print intB
                    if intB[0] == "inet6":
                        continue
                    ip = intB[1].split('/')[0]
                    iface = intB[-1]
                    print ip, iface
                    if ip == conn[2]:
                        dzone = resolveZone(iface)
                        szone = "net"
                    if ip == conn[0]:
                        szone = resolveZone(iface)
                        dzone = "net"
                data = {
                    '__nevow_form__': True, #Trick it into thinking this is a valid form
                    'ruleID': None, #Add a rule
                    'action':'REJECT',
                    'sip':conn[2],
                    'szone':szone,
                    'sport':sport,
                    'dip':conn[0],
                    'dzone':dzone,
                    'dport':dport,
                    'proto':'TCP',
                }
                self.submitFirewallRule(data)

        #Determine Zone that this rule belongs
        l = WebUtils.system('ip addr | grep inet')
        return l.addCallback(calculateZones).addErrback(calculateZones, True)
            
        
 
    athena.expose(addConnectionRule)

    def render_firewallConnections(self, ctx, data):
        #connectColNames = ["Destination IP", "Destination Port", "Source IP", "Source Port", ""];
        #connectColClasses = ['dstip', 'dstport', 'srcip', 'srcport', 'addrule'];
        #connectTableTags = self.renderDataTable("firewallConnections", 'connectionRule' , [], connectColNames, connectColClasses)

        return tags.div(id="firewallConnectionsTab", _class="tabPane")["Loading ... "]

class Page(PageHelpers.DefaultAthena):
    moduleName = 'firewall'

    moduleScript = 'firewall-page.js'

    docFactory = loaders.xmlfile('firewall-page.xml', templateDir = Settings.BaseDir + '/templates')

    addSlash = True

    def render_firewallFragment(self, ctx, data):
        """Renders rulesFragment instance"""
        f = FirewallFragment()
        f.rules = Shorewall.Rules() 
        f.setFragmentParent(self)
        f.avatarId = self.avatarId
        return ctx.tag[f]
    
    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2[tags.img(src='/images/tools-lg.png'), " Tools"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[Tools.Page.sideMenu(Tools.Page(None, self.db), ctx, data)]

    def render_content(self, ctx, data):
        """Render firewall content page"""
        Utils.log.msg('%s opened Tools/Firewall' % (self.avatarId.username))
        return ctx.tag[
            tags.h3[tags.img(src="/images/firewall.png"), "  Firewall"],
            tags.div(id="securityNotice", style="display:none") [
                tags.h1["Security Violation!"],
                tags.p["Inbound SSH and/or Vulani administrative access should not be unrestricted! " +
                "Your system security has been seriously compromised. Please remove this " +
                "rule and restrict the source IP or make use of the VPN to administer the server remotely"],
            ],
            tags.div(id="messageBox")[''],
            tags.div(id="settingsLinks")[
                tags.a(
                    id="testFirewall",
                    title="Test the firewall. (This may take some time!)"
                )["Test Settings"],
                tags.a(
                    id="applyFirewall",
                    title="Restart the firewall and apply the changes. Changes are only activated after this is clicked."
                )["Apply Changes"]],
            PageHelpers.TabSwitcher((
                    ('Rules',           'firewallRulesTab'),
                    ('NAT',             'firewallNatRulesTab'),
                    ('QoS',             'firewallQOSTab'),
                    ('Policy',          'firewallPolicyTab'),
                    ('Zones',           'firewallZonesTab'),
                    ('Connections',     'firewallConnectionsTab'),
                ), id = "firewall"),
            tags.div[
                tags.invisible(render=tags.directive('firewallFragment'))
            ],
            PageHelpers.LoadTabSwitcher(id="firewall")
        ]

