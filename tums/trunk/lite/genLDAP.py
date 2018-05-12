#!/usr/bin/python

import config

l = open('template.ldif', 'wt')

l.write("""dn: o=%s
description: %s
objectclass: organization
objectclass: top
o: %s\n\n""" % (config.LDAPBase, config.CompanyName, config.LDAPBase))

l.write("""dn: cn=Manager,o=%s
objectclass: organizationalRole
cn: Manager\n\n""" % config.LDAPBase)

l.flush()

last = []
for i in reversed(config.Domain.split('.')):
    last = [i]+last
    l.write("""dn: %s,o=%s
dc: %s
objectclass: dcObject
objectclass: domain
o: %s\n\n""" % (','.join(['dc=%s' % k for k in last]), config.LDAPBase, i, config.LDAPBase))
    l.flush()
l.write("""dn: ou=People,%s,o=%s
ou: People
objectclass: organizationalUnit\n\n\n""" % (','.join(['dc=%s' % k for k in last]), config.LDAPBase))
l.close()
