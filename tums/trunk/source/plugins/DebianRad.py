import config, os
from Core import Utils

class Plugin(object):
    """ Configures everything needed for Debian RADIUS. """
    parameterHook = "--radius"
    parameterDescription = "Reconfigure RADIUS on Debian"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = [ 
        "/etc/raddb/users",
        "/etc/raddb/users.ext",
        "/etc/raddb/clients",
    ]

    def reloadServices(self):
        os.system('/etc/init.d/xtradius restart')

    def writeConfig(self, *a):
        
        usersexec = """
# Our script calls
DEFAULT Auth-Type = External
    Exec-Program-Wait = "/usr/local/tcs/tums/tums --radauth %u %w",
    Fall-Through = 0
"""
        users = """
$INCLUDE users.exec

DEFAULT Auth-Type = System
        Fall-Through = 1

# Defaults for all framed connections.
#
DEFAULT Service-Type = Framed-User
        Framed-IP-Address = 255.255.255.254,
        Framed-MTU = 576,
        Service-Type = Framed-User,
        Fall-Through = Yes

DEFAULT Framed-Protocol = PPP
        Framed-Protocol = PPP,
        Framed-Compression = Van-Jacobson-TCP-IP

#
# Default for CSLIP: dynamic IP address, SLIP mode, VJ-compression.
#
DEFAULT Hint = "CSLIP"
        Framed-Protocol = SLIP,
        Framed-Compression = Van-Jacobson-TCP-IP

#
# Default for SLIP: dynamic IP address, SLIP mode.
#
DEFAULT Hint = "SLIP"
        Framed-Protocol = SLIP
"""

        l = open('/etc/raddb/users', 'wt')
        l.write(users)
        l.close()

        l = open('/etc/raddb/clients', 'wt')
        l.write("localhost               2saraddb")
        # XXX - support configurable client list here
        l.close()

        l = open('/etc/raddb/users.exec', 'wt')
        l.write(usersexec)
        l.close()
