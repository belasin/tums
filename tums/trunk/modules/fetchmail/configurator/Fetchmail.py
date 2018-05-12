"""
Vulani Configurator Fetchmail plugin
Copyright (c) 2009, Thusa Business Support (Pty) Ltd.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Thusa Business Support (Pty) Ltd. nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY Thusa Business Support (Pty) Ltd. ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL Thusa Business Support (Pty) Ltd. BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import config, os

from Core import Utils

class Plugin(object):
    """ Configures everything needed for Fetchmail """
    parameterHook = "--fetchmail"
    parameterDescription = "Reconfigure fetchmail"
    parameterArgs = ""
    autoRun = True   # Run this plugin automaticaly 

    # Configuration files we change
    configFiles = [
        "/etc/default/fetchmail",
        "/etc/fetchmailrc"
    ]

    def reloadServices(self):
        """Reload all our services"""
        if config.Mail.get('fetchmail'):
            os.system('/etc/init.d/fetchmail restart')

    def writeConfig(self, *a):
        # Build our configuration file
        conf = """set daemon 300
set postmaster "postmaster@%(domain)s"

""" %   {'domain': config.Domain}
        
        # Iterate through configuration 
        for server, domain, username, password, destination in config.Mail.get('fetchmail', []):
            conf += "poll %s proto POP3 localdomains %s\n" % (server, domain)
            conf += "  envelope \"Envelope-to\"\n"
            conf += "  envelope \"Delivered-To\"\n"
            conf += "    user \"%s\" with pass \"%s\" to %s here\n\n" % (username, password, destination)

        fetchmailrc = open('/etc/fetchmailrc', 'wt')
        fetchmailrc.write(conf)
        fetchmailrc.close()

        # If unconfigured, leave now. 
        if not config.Mail.get('fetchmail'):
            # Make sure it is not set to start at bootup
            os.system('update-rc.d -f fetchmail remove > /dev/null 2>&1')
            os.system('/etc/init.d/fetchmail stop')
            return 

        # Check if fetchmail is installed
        if not Utils.isPackageInstalled('fetchmail'):
            print "Installing fetchmail..."
            os.system('DEBIAN_FRONTEND="noninteractive" apt-get -y -q --force-yes install fetchmail')
            # Check if it installed now. 
            if not Utils.isPackageInstalled('fetchmail'):
                print "ERROR: Failed to install fetchmail."
                return 
        
        # Make sure it is set to start
        os.system('update-rc.d fetchmail defaults > /dev/null 2>&1')

        os.system("sed 's/START_DAEMON=no/START_DAEMON=yes/' -i /etc/default/fetchmail")
        
