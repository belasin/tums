import LDAP, Settings
l = LDAP.createLDAPConnection(Settings.LDAPServer, 'o='+Settings.LDAPBase, Settings.LDAPManager, Settings.LDAPPass)
dc = "o=%s" % (Settings.LDAPBase)

v = LDAP.searchTree(l, dc, 'uid=*', [])

for i in v:
    path, detail = i[0]
    if "ou=People" not in path:
        continue
    dom = path.split(',o=')[0].split('ou=People,dc=')[-1].replace(',dc=', '.')
    serStruct = {
        'domain'        : dom,
        'name'          : detail['uid'][0],
        'uid'           : detail.get('uidNumber', [1000])[0],
        'gid'           : detail.get('gidNumber', [1000])[0],
        'cn'            : detail.get('cn', [''])[0],
        'sn'            : detail.get('sn', [''])[0],
        'giveName'      : detail.get('giveName', [''])[0],
        'emp'           : '+'.join(detail.get('employeeType', [])), # Can have multiple values here.
        'password'      : detail.get('userPassword', [''])[0],
        'mail'          : detail.get('mail', [''])[0],
        'active'        : detail.get('accountStatus', [''])[0],
        'pgSid'         : detail.get('sambaPrimaryGroupSID', [''])[0],
        'samSid'        : detail.get('sambaSID', [''])[0],
        'ntPass'        : detail.get('sambaNTPassword', [''])[0],
        'lmPass'        : detail.get('sambaLMPassword', [''])[0],
        'mailForward'   : '+'.join(detail.get('mailForwardingAddress', [])),
        'mailAlias'     : '+'.join(detail.get('mailAlternateAddress', []))
    }

    x = ""
    for k,v in serStruct.items():
        x += "%s:%s[" % (k,v)
    
    print x

