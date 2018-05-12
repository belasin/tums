from twisted.internet.defer import deferredGenerator, waitForDeferred as wait
from twisted.mail import smtp
from Core import confparse

import os

@deferredGenerator
def system(e):
    from twisted.internet import utils
    #def procResult(e):
    #    return e

    mq = utils.getProcessOutput('/bin/sh', ['-c', e], errortoo=1)
    #.addCallbacks(procResult, procResult)
    res = wait(mq) 
    yield res
    yield res.getResult()

def serialiseUser(detail, dom):
    vacation = ""
    vacEnable = False
    user, domain = detail['uid'][0], dom
    try:
        vac = open("/var/spool/mail/vacation/%s@%s.txt" % (user, domain), 'r')
        vacation = vac.read()
        vacEnable = True
    except:
        pass # No vacation note

    try:
        vac = open("/var/spool/mail/vacation/DISABLED%s@%s.txt" % (user, domain), 'r')
        vacation = vac.read()
    except:
        pass # No disabled note either.
    serStruct = {
        'domain'        : dom,
        'name'          : detail['uid'][0],
        'uid'           : detail.get('uidNumber', [1000])[0],
        'gid'           : detail.get('gidNumber', [1000])[0],
        'cn'            : detail.get('cn', [''])[0],
        'sn'            : detail.get('sn', [''])[0],
        'giveName'      : detail.get('givenName', [''])[0],
        'emp'           : '+'.join(detail.get('employeeType', [])), # Can have multiple values here.
        'password'      : detail.get('userPassword', [''])[0],
        'mail'          : detail.get('mail', [''])[0],
        'active'        : detail.get('accountStatus', [''])[0],
        'pgSid'         : detail.get('sambaPrimaryGroupSID', [''])[0],
        'samSid'        : detail.get('sambaSID', [''])[0],
        'ntPass'        : detail.get('sambaNTPassword', [''])[0],
        'lmPass'        : detail.get('sambaLMPassword', [''])[0],
        'mailForward'   : '+'.join(detail.get('mailForwardingAddress', [])),
        'mailAlias'     : '+'.join(detail.get('mailAlternateAddress', [])),
        'vacation'      : vacation,
        'vacEnable'     : vacEnable
    }

    # Construct our flags.
    flags = []
    # Order is important from here on
    thisFlag = False
    for i in os.listdir('/etc/openvpn/keys/'):
        if "%s.%s" % (serStruct['name'], dom) in i and "key" in i:
            thisFlag = True
    flags.append(thisFlag)

    # FTP Enabled
    thisFlag = False
    if detail.get('loginShell'):
        if '/bin/bash' in detail['loginShell'][0]:
            thisFlag = True
    flags.append(thisFlag)

    # We need a config parser
    sysconf = confparse.Config()
    thisFlag = False
    # FTP Global
    if  sysconf.FTP.get('globals'):
        if serStruct['name'] in sysconf.FTP['globals']:
            thisFlag = True
    flags.append(thisFlag)

    address = "%s@%s" % (serStruct['name'], dom)
    copyto = ""
    if sysconf.Mail.get('copys', []):
        for addr, dest in sysconf.Mail['copys']:
            if addr == address:
                copyto = dest
    flagSer = ""
    for i in flags:
        flagSer += i and '-' or '_'
    flagSer += "+" + copyto

    serStruct['flags'] = flagSer
    
    x = ""
    for k,v in serStruct.items():
        x += "%s:%s`" % (k,v)
    
    return x
