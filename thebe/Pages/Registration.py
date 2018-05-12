from enamel import authentication, deployment, pages, servers, storage, deferreds, tags, form
from enamel import sql
import enamel, os, sha

from nevow import inevow, rend, static, compression, loaders, url, guard

from twisted.internet import utils

from Pages import Users, Thebe, Dashboard, Servers, Commands, DNS, DynDNS, Updates, Account, Orders, Tickets
import Settings
from lib import system, web

class Index(pages.Standard):
    childPages = {}

    arbitraryArguments = True

    def __init__(self, *a, **kw):
        pages.Standard.__init__(self, *a, **kw)

    def document(self):
        baseDir = self.enamel.Settings.BaseDir
        theme = self.enamel.Settings.theme
        # Images, javascript and CSS locations
        # derived from base directory and theme 
        self.child_css = static.File('%s/themes/%s/css/' % (baseDir, theme))
        self.child_js  = compression.CompressingResourceWrapper(static.File(baseDir + '/js/'))
        self.child_images = compression.CompressingResourceWrapper(static.File('%s/themes/%s/images/' % (baseDir, theme)))
        return pages.template('registration.xml', templateDir='%s/themes/%s/templates/' % (baseDir, theme))

    def form_regform(self, ctx):
        f = form.Form()
        f.addField('fullname', form.String(required=True), label = "Name")
       
        f.addField('company', form.String(required=True), label = "Company")
        f.addField('email', form.String(required=True), label = "EMail")
        f.addField('phone', form.String(required=True), label = "Phone number")
        
        f.addField('address0', form.String(required=True), label = "Address")
        f.addField('address1', form.String(), label = "Address")
        f.addField('address2', form.String(), label = "Address")
        f.addField('address3', form.String(), label = "Address")

        f.addField('country', form.String(required=True), label = "Country")

        #f.addField('zaId', form.String(), label = "SA ID", description = 
        #    ["If you are a South African citizen please enter your ID number (", 
        #    tags.a(href="/Help/why_id")["Why?"], ")"]
        #), 
        
        f.addField('password', form.String(required=True), form.CheckedPassword, label = "Password")
        
        f.addAction(self.registerUser)

        return f

    def registerUser(self, ctx, form, data):
        mailhash = sha.sha(data['email'].encode('ascii', 'replace')).hexdigest()
        namehash = sha.sha(data['fullname'].encode('ascii', 'replace')).hexdigest()
        confhash = ''.join([i+j for i,j in zip(mailhash, namehash)])

        def added(_):
            # Send a mail to us so we know when people register
            maildata = """Fullname: %(fullname)s
Company: %(company)s
Email: %(email)s
Phone: %(phone)s
Address: %(address0)s
         %(address1)s
         %(address2)s
         %(address3)s
Country: %(country)s\n""" % data

            web.sendMail(
                "Registrations <support@thusa.co.za>", 
                ["support@vulani.net"], 
                "New Vulani Portal Registration - %s" % data['email'].encode('ascii', 'replace'), 
                maildata.encode('ascii', 'replace')
            )

            maildata2 = """Thank you for registering with the Vulani Portal.

Vulani Portal allows you to place orders for Vulani products, as well as manage your existing products from one central location.

Please note your username is the email address you have registered with: %s

To confirm your registration please click the following link:
   http://reg.portal.vulani.net/Confirm/%s/
   
If you did not request this account, please delete this email.\n\n""" % (
                data['email'].encode('ascii', 'replace'), 
                confhash
            )

            web.sendMail(
                "Vulani <support@vulani.net>", 
                [data['email'].encode('ascii', 'replace')], 
                "Vulani Portal account confirmation", 
                maildata2
            )

            return url.root.child('RegistrationComplete')
            
        # Create user entity 
        return self.enamel.storage.addUserFull(
            data['fullname'].encode('ascii', 'replace'),
            data['company'].encode('ascii', 'replace'),
            data['email'].encode('ascii', 'replace'),
            data['phone'].encode('ascii', 'replace'),
            data['address0'].encode('ascii', 'replace'),
            (data['address1'] or u"").encode('ascii', 'replace'),
            (data['address2'] or u"").encode('ascii', 'replace'),
            (data['address3'] or u"").encode('ascii', 'replace'),
            data['country'].encode('ascii', 'replace'),
            data['password'].encode('ascii', 'replace'), 
            confhash
        ).addBoth(added)

    def renderConfirmed(self, _, ctx):
        return ctx.tag[
            tags.h3["Registration confirmed!"], 
            "Your registration has been successfully confirmed. You may now log in by clicking here: " , 
            tags.a(href="https://portal.vulani.net/")["https://portal.vulani.net/"]
        ]

    def confirmUser(self, result, ctx):
        if not result:
            return ctx.tag[
                "Your confirmation string is not valid. Please email support@vulani.net for assistance"
            ]

        web.sendMail(
            "Registrations <support@thusa.co.za>", 
            ["colin@thusa.co.za"], 
            "Vulani portal confirmation - %s" % result[4], 
            """%s confirmed their Vulani Portal registration successfully""" % result[5]
        )

        return self.enamel.storage.confirmUser(result[0]).addBoth(self.renderConfirmed, ctx)

    def render_regform(self, ctx, data):
        if len(self.arguments) > 0:
            if self.arguments[0] == "RegistrationComplete":
                return ctx.tag[
                    tags.strong["Thank you for registering!"], 
                    tags.br, tags.br,
                    "An email has been sent to your address with instructions on completing your registration.", 
                    tags.br, tags.br,
                    "If you do not receive an email after 2 hours please contact support@vulani.net"
                ]

            if self.arguments[0] == "Confirm":
                return self.enamel.storage.getUserByHash(self.arguments[1]).addBoth(self.confirmUser, ctx)

        return ctx.tag[
            "Welcome to the Vulani Portal registration", tags.br, tags.br, 

            "The Vulani Portal allows you to place orders for Vulani products as well as manage those products and Vulani servers (with Silver, Gold and Platinum support options) from a central location.", tags.br, tags.br,

            "After completing this form you will be emailed a confirmation URL. Your email address will be your username. If you require additional accounts linked to your company, please ask them to register here then log a service request for those users to be added to your customer group by emailing support@vulani.net", tags.br, tags.br,

            tags.directive('form regform')
        ]


    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["Registration"]]

