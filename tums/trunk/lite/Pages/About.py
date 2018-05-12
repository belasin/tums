from nevow import rend, loaders, tags
from twisted.application import service, internet, strports
from twisted.web import server, static
from twisted.python import failure
from nevow import inevow, rend, appserver, static, guard, url, loaders, stan
from nevow.taglibrary import tabbedPane

import Tree, Settings, os, LDAP
from Core import PageHelpers, AuthApacheProxy
from Pages import Tools
import formal
import _mysql

class Page(PageHelpers.DefaultPage):
    addSlash = True

    def render_pageName(self, ctx, data):
        return ctx.tag[tags.h2["About"]]

    def render_sideMenu(self, ctx, data):
        return ctx.tag[""]

    def render_content(self, ctx, data):
        credits = [
            (tags.h3["Credits"], ""),
            ("Colin Alston",    "Chief Architect"),
            ("Warwick Chapman", "Project Manager"),
            ("Jarrod Meyer",    "Development Engineer"),
            ("Sean Preston",    "Consulting Architect"),
            ("Junaid Loonat",   "Consulting Developer"),
            ("Tristan Coetzee", "Consulting Developer"),
            ("Gerard Roberts",  "Testing"),
            ("Dane Lepens",     "Testing"),
        ]
        credits2 = [
            ("Donovan Preston", "Nevow", "Matt Goodall",    "Nevow and Formal"),
            ("James Y. Knight", "Nevow", "Glyph Lefkowitz", "Nevow and Twisted"),
            ("JP Calderone",    "Nevow and Twisted", "Allen Short",     "Nevow"),
            ("Alex Levy",       "Nevow", "Justin Johnson",  "Nevow"),
            ("Christopher Armstrong", "Nevow", "Jonathan Simms",  "Nevow"),
            ("Phil Frost",      "Nevow", "Tommi Virtanen",      "Nevow"),
            ("Michal Pasternak",    "Nevow", "Valentino Volonghi",  "Nevow"),
            ("Duane Wessels",   "Squid Proxy", "Michael Stroeder","LDAP EXOP decoding"),
            ("Benjamin Kuit",   "NTLM Hashing")

        ]
        return ctx.tag[
            tags.h2["Thusa Unified Management System"],
            "TUMS Version ", PageHelpers.VERSION, ' "%s" release.' % PageHelpers.CODENAME,
            tags.table[
                [
                    tags.tr[
                        [tags.td[i] for i in j]
                    ]
                for j in credits]
            ],
            tags.h3["Thanks"],
            "Without the tireless work and assistance of many people around the globe, TUMS in it's ",
            "current form would almost certainly not be possible. This is a brief list of some of the people who we have to thank.",
            tags.br, tags.br,
            tags.table[
                [
                    tags.tr[
                        [tags.td[i] for i in j]
                    ]
                for j in credits2]
            ]
        ]

