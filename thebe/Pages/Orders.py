from enamel import authentication, deployment, pages, servers, storage, deferreds, tags, url
from enamel import sql, form
import enamel, sha, md5

from datetime import datetime, date

from custom import Widgets
from twisted.internet import utils, defer

from nevow import inevow

from lib import PageBase, web

PayGateKey = "secret"
PayGateID = "10011013800"

PayGateLogoStuff = tags.div(_class="paygateLogos")[
                    tags.p(style="margin-top:30px;")[
                        tags.a(href="http://www.paygate.co.za", target="_blank")[
                            tags.img(src="http://www.thusa.co.za/images/paygate.png", border="0")]]]

def genPayGateReqCHK(formDict):
    vars = [
        formDict["PAYGATE_ID"],
        formDict["REFERENCE"],
        formDict["AMOUNT"],
        formDict["CURRENCY"],
        formDict["RETURN_URL"],
        formDict["TRANSACTION_DATE"],
        formDict["EMAIL"]
    ]
    if "SUB_START_DATE" in formDict:
        vars.extend([
            formDict["SUB_START_DATE"],
            formDict["SUB_END_DATE"],
            formDict["SUB_FREQUENCY"],
            formDict["PROCESS_NOW"],
            formDict["PROCESS_NOW_AMOUNT"],
        ])
    vars.append(str(PayGateKey))
    return md5.new(str.join('|',vars)).hexdigest()
    

class ItemPreCheckout(PageBase.Page):
    # List invoice and direct to VCS
    arbitraryArguments = True 

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Vulani Order"]]

    def render_content(self, ctx, data):
        iid = int(self.arguments[0])

        def retrOrder(row, userRow):
            print row

            email = userRow[4]


            descr = row[5]
            if row[5] == "Vulani License":
                if row[6] in ['standard', 'silver', 'gold', 'platinum']:
                    descr = "Vulani License + First month of %s support" % (row[6].capitalize())
                else:
                    descr = "Standard Vulani License with no support"

            costMapper = {
                'gold':     (3000, 700, "Gold support (recurring monthly)"), 
                'platinum': (2000, 1000, "Platinum support (recurring monthly)")
            }

            costTup = costMapper.get(row[6].lower(), (5000, 0, None))

            costBase = costTup[0] + costTup[1]

            costRecur = costTup[1]
            
            transactionDate = datetime.now().strftime("%Y-%m-%d %H:%M")

            formDict = {
                "PAYGATE_ID":       PayGateID,
                "REFERENCE":        str(row[0]),
                "AMOUNT":           str(costBase*100),
                "CURRENCY":         "ZAR",
                "RETURN_URL":       "https://portal.vulani.net/Orders/PayGateReturn/",
                "TRANSACTION_DATE": transactionDate,
                "EMAIL":            email,
            }

            sup = ""
            if costRecur:
                today = date.today()
                nextYear = date(today.year + 1, today.month, today.day)
                formDict["VERSION"]         = "21"
                formDict["SUBS_START_DATE"] = today.strftime("%Y-%m-%d")
                formDict["SUBS_END_DATE"]   = nextYear.strftime("%Y-%m-%d")
                formDict["PROCESS_NOW"]     = "YES"
                formDict["PROCESS_NOW_AMOUNT"] = str(costBase*100)
                formDict["AMOUNT"]          = str(costRecur*100)
            
                sup = tags.tr[
                    tags.td["1 x %s" % costTup[2]], 
                    tags.td["R%s.00" % costRecur]
                ]

            formDict["CHECKSUM"] =  genPayGateReqCHK(formDict)
            print formDict

            return ctx.tag[
                tags.table[
                    tags.tr[    
                        tags.td[
                            "1 x Vulani license"
                        ], 
                        tags.td[
                            "R%s.00" % costTup[0]
                        ]
                    ], 
                    sup,
                    tags.tr[
                        tags.td[
                            "Order Total"
                        ], 
                        tags.td[
                            "R%s.00" % costBase
                        ]
                    ]
                ],
                tags.div(_class="billingNotice")["Please note: Purchases will be billed and processed by THUSA BUSINESS SUPPORT (PTY) LTD"],
                PayGateLogoStuff,
                tags.form(method="POST", action="https://www.paygate.co.za/paywebv2/process.trans")[
                #tags.form(method="POST", action="https://www.vcs.co.za/vvonline/ccform.asp")[
                    [ tags.input(type="hidden", name=k, value=v) for k,v in formDict.items() ], 
                    tags.input(type="submit", value="Pay by Credit Card")
                ]
            ]

        def gotUser(row):
            return self.enamel.storage.getOrder(iid).addBoth(retrOrder, row)
        return self.enamel.storage.getUser(self.avatarId.uid).addBoth(gotUser)

class PayGateReturn(PageBase.Page):
    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))
    
    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Vulani Order"]]

    def genChecksum(self, rDict):
        vars = [
            rDict["PAYGATE_ID"],
            rDict["REFERENCE"],
            rDict["TRANSACTION_STATUS"],
            rDict["RESULT_CODE"],
            rDict["AUTH_CODE"],
            rDict["AMOUNT"],
            rDict["RESULT_DESC"],
            rDict["TRANSACTION_ID"],
            rDict["RISK_INDICATOR"],
        ]
        vars.append(str(PayGateKey))
        return md5.new(str.join('|',vars)).hexdigest()


    def render_content(self, ctx, data):
        def approveOrder():
            def rend(su):
                return ctx.tag[
                    "Your order has been successfully completed. Please allow 24 hours for your license key to be allocated", tags.br, 
                    "Reason: %s (%s)" % (responseDict["RESULT_DESC"], responseDict["RESULT_CODE"])
                ]

            def confirmStatus(tr):
                return self.enamel.storage.updateStatus(orderId, "Payment Confirmed.").addBoth(rend)

            return self.enamel.storage.logTransaction(orderId, 'Authorized', rlogBulk).addBoth(confirmStatus)

        def declineOrder():
            def rend(su):
                return ctx.tag[
                    "Your credit card transaction has failed. Please place a new order to retry.", tags.br, 
                    "Reason: %s (%s)" % (responseDict["RESULT_DESC"], responseDict["RESULT_CODE"])
                ]

            def confirmStatus(tr):
                return self.enamel.storage.purgeOrder(orderId).addBoth(rend)

            return self.enamel.storage.logTransaction(orderId, 'Declined', rlogBulk).addBoth(confirmStatus)

        ir = inevow.IRequest(ctx)
        # Sanitise our response dict
        responseDict = {}

        fields = [
            'PAYGATE_ID',
            'REFERENCE',
            'TRANSACTION_STATUS',
            'RESULT_CODE',
            'AUTH_CODE',
            'AMOUNT',
            'RESULT_DESC',
            'TRANSACTION_ID',
            'RISK_INDICATOR',
            'CHECKSUM',
        ]

        for k in fields:
            v = ir.args.get(k, [''])[0]
            responseDict[k] = v 

        orderId = int(responseDict['REFERENCE'])

        trCode = responseDict['TRANSACTION_ID']

        print responseDict, orderId, trCode

        if self.genChecksum(responseDict) == responseDict["CHECKSUM"]:
            print "Checksum Passed for Gateway Response"

        validResp = [
            "990017", #Auth Done
            #"990030", #Subscribed Payment Done
        ]

            
        rlogBulk = '&'.join(["%s=%s" % (k,v[0]) for k,v in ir.args.items()])

        print rlogBulk

        if responseDict["RESULT_CODE"] == "990017":
            return approveOrder()
        else:
            return declineOrder()

class ItemDeclined(PageBase.Page):
    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Vulani Order"]]

    def render_content(self, ctx, data):
        ir = inevow.IRequest(ctx)
        # Sanitise our response dict
        responseDict = {}

        fields = [
            'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12',
            'm_1', 'm_2', 'm_3',
            'CardHolderIpAddr', 
            'MaskedCardNumber', 
            'TransactionType'
        ]

        for k in fields:
            v = ir.args.get(k, [''])[0]
            responseDict[k] = v 

        orderId = int(responseDict['m_3'])

        trCode = responseDict['p3']

        print responseDict, orderId, trCode


        rlogBulk = '&'.join(["%s=%s" % (k,v[0]) for k,v in ir.args.items()])

        print rlogBulk

        def rend(su):
            return ctx.tag[
                "Your credit card transaction has failed. Please place a new order to retry.", tags.br, 
            ]

        def confirmStatus(tr):
            return self.enamel.storage.purgeOrder(orderId).addBoth(rend)

        return self.enamel.storage.logTransaction(orderId, 'Authorized', rlogBulk).addBoth(confirmStatus)

class ItemApproved(PageBase.Page):

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Vulani Order"]]

    def render_content(self, ctx, data):
        ir = inevow.IRequest(ctx)
        # Sanitise our response dict
        responseDict = {}

        fields = [
            'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8', 'p9', 'p10', 'p11', 'p12',
            'm_1', 'm_2', 'm_3',
            'CardHolderIpAddr', 
            'MaskedCardNumber', 
            'TransactionType', 'pam'
        ]

        for k in fields:
            v = ir.args.get(k, [''])[0]
            responseDict[k] = v 

        orderId = int(responseDict['m_3'])

        trCode = responseDict['p3']

        print responseDict, orderId, trCode

        rlogBulk = '&'.join(["%s=%s" % (k,v[0]) for k,v in ir.args.items()])

        print rlogBulk

        def rend(su):
            return ctx.tag[
                "Your order has been successfully completed. Please allow 24 hours for your license key to be allocated"
            ]

        def confirmStatus(tr):
            return self.enamel.storage.updateStatus(orderId, "Payment Confirmed.").addBoth(rend)

        return self.enamel.storage.logTransaction(orderId, 'Authorized', rlogBulk).addBoth(confirmStatus)

class ServerLicense(PageBase.Page):

    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Vulani Order"]]


    def form_vlic(self, data):
        vlics = form.Form()
        vlics.addField('name', form.String(required=True), label = "Client Name", description="Where this server will be installed")
        vlics.addField('host', form.String(), label = "Hostname", description="The external hostname this server will be reachable on")

        vlics.addField('support', form.String(required=True), 
            form.widgetFactory(form.SelectChoice, options = (
                ('none', 'No support'),
                ('standard', 'Standard update protection'),
                ('silver',   'Silver SLA'),
                ('gold',   'Gold SLA'),
                ('platinum', 'Platinum SLA'),
            )), description = "Select a support option")

        vlics.addField('terms', form.Boolean(required=True), label = "Accept Terms and Conditions", description=["Please read and accept the ", 
            tags.a(href="http://www.vulani.net/sites/default/files/downloads/T&C.pdf")["Terms and Conditions"]])

        vlics.addAction(self.vlicOrder)
        return vlics

    def vlicOrder(self, ctx, form, data):
        if not data['terms']:
            return url.root.child('Orders').child("Vulani")

        name = (data['name'] or u"").encode('ascii')
        host = (data['host'] or u"").encode('ascii')
        support = (data['support'] or u"none").encode('ascii')

        def goBack(_):
            def sendMail(row, order):
                orderText = """Vulani order #%s
   End user name : %s
   Hostname      : %s
   Support SLA   : %s
   Requested by  : %s at company %s\n
   Contact Number: %s
   Email address : %s """ % (
                    40215 + order[0], 
                    name, 
                    host, 
                    support, 
                    row[3], 
                    row[5], 
                    row[10], 
                    row[4])

                web.sendMail("%s <%s>" % (row[3], row[4]), ["support@vulani.net"], "[#%s] New Vulani Order" % (40215 + order[0]), orderText)

                return url.root.child('Orders').child('Checkout').child(order[0])

            def gotOrderBack(order):
                
                return self.enamel.storage.getUser(self.avatarId.uid).addBoth(sendMail, order)

            return self.enamel.storage.findOrder(self.avatarId.gids[0], name, host, support, 'Vulani License').addBoth(gotOrderBack)
    
        return self.enamel.storage.createOrder(self.avatarId.gids[0], name, host, support, 'Vulani License').addBoth(goBack)


    def render_content(self, ctx, data):
        return ctx.tag[
            tags.directive('form vlic'),
            tags.div(_class="billingNotice")["Please note: Purchases will be billed and processed by THUSA BUSINESS SUPPORT (PTY) LTD"],
            PayGateLogoStuff
        ]

class EditOrder(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Vulani Order"]]

    def form_vlic(self, data):
        vlics = form.Form()
        def gotServerGroups(server):
            servers = [ (i[0], i[1]) for i in server ]
            vlics.addField('sidlink', form.Integer(required=True), form.widgetFactory(form.SelectChoice, options = servers),
                label = "SID Link", description="The entry we have created - this will bond the server to the ordering group")

            vlics.addField('completed', form.Boolean(), label = "Complete", description="Tick to complete the order. ")

            vlics.addAction(self.vlicOrder)
            return vlics

        return self.enamel.storage.getServers().addBoth(gotServerGroups)

    def vlicOrder(self, ctx, form, data):
        def returnRoot(_):
            return url.root.child('Orders')

        def sendMail(row, order):
            orderText = """Vulani order #%s completed by %s <%s> for %s""" % (
                order[0] + 40215, 
                row[3],
                row[4], 
                order[3]
            )

            web.sendMail("%s <%s>" % (row[3], row[4]), ["support@vulani.net"], "[#%s] Completed Vulani Order" % (order[0] + 40215), orderText)
            return returnRoot(None)

        def getAdmin(_, order):
            return self.enamel.storage.getUser(self.avatarId.uid).addBoth(sendMail, order)
 
        def updateOrder(_, order):
            # If the order is not complete, don't send any emails 
            if data['completed']:
                return self.enamel.storage.updateOrder(int(self.arguments[0]), data['sidlink'], 'Completed').addBoth(getAdmin, order)
            else:
                return self.enamel.storage.updateOrder(int(self.arguments[0]), data['sidlink'], None).addBoth(returnRoot)
        
        def gotOrder(order):
            return self.enamel.storage.addServerMembership(order[1], data['sidlink']).addBoth(updateOrder, order)

        return self.enamel.storage.getOrder(int(self.arguments[0])).addBoth(gotOrder)

    def render_content(self, ctx, data):
        if not 1 in self.avatarId.gids:
            # Don't display if we aren't Thusa
            return ctx.tag[""]

        return ctx.tag[
            tags.directive('form vlic')
        ]



class ViewOrder(PageBase.Page):
    arbitraryArguments = True # Enable REST style arguments to the page

    def document(self):
        return pages.template('defaultc.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Vulani Order"]]


class Page(PageBase.Page):
    childPages = {
        "Vulani":   ServerLicense,
        "EditOrder": EditOrder, 
        "ViewOrder": ViewOrder, 
        "Checkout": ItemPreCheckout, 
        "Declined": ItemDeclined,
        "Cancel":   ItemDeclined,
        "Approved": ItemApproved,
        "PayGateReturn": PayGateReturn,
    }

    def document(self):
        return pages.template('orders.xml', templateDir='%s/themes/%s/templates/' % (self.enamel.Settings.BaseDir, self.enamel.Settings.theme))

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Dashboard"]]

    def render_admin(self, ctx, d):
        if not 1 in self.avatarId.gids:
            # Don't display if we aren't Thusa
            return ctx.tag[""]

        def renderTable(rows):
            orderTable = []

            for i in rows:
                if i[5] == "Vulani License":
                    descr = "Vulani License + %s support for %s" % (i[6].capitalize(), i[3])
                else:
                    descr = ""
                orderTable.append([i[10], i[3], i[5], descr, i[8].ctime(), i[9].ctime(), i[7] or u"Pending", tags.a(href="/Orders/EditOrder/%s/" % i[0])["Manage"]])

            return ctx.tag[
                tags.div(_class="tabBlock")[
                    tags.div(_class="tabHeader")[tags.div(_class="tabText")["Pending Orders"]],
                    tags.div(_class="tabContent")[
                        self.dataTable(["Requester", "Company", "Type", "Detail", "Created", "Changed", "Status", ""], orderTable, width="100%")
                    ]
                ]
            ]
        return self.enamel.storage.listPendingOrders().addBoth(renderTable)

    def render_orders(self, ctx, d):
        def renderTable(rows):
            orderTable = []

            for i in rows:
                if i[5] == "Vulani License":
                    descr = "Vulani License + %s support for %s" % (i[6].capitalize(), i[3])
                else:
                    descr = ""
                orderTable.append([i[5], descr, i[8].ctime(), i[9].ctime(), i[7] or u"Pending"])

            return ctx.tag[
                self.dataTable(["Type", "Detail", "Created", "Changed", "Status"], orderTable, width="100%")
            ]

        return self.enamel.storage.getOrders(self.avatarId.gids[0]).addBoth(renderTable)

    def render_content(self, ctx, d):
        return ctx.tag[
            tags.a(href="/Orders/Vulani")["Vulani licenses"], 
            tags.br, 
            #tags.a(href="/Orders/DNS")["DNS hosting"], 
        ]   
