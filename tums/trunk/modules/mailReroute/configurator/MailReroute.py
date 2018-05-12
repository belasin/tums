"""
Vulani Configurator Mail-Reroute plugin
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
import config
from Core import Utils

class Plugin(object):
    """ Configures Exim mail rehub. """

    parameterHook = "--exim"
    parameterDescription = "Extends exim for mail rehubbing"
    parameterArgs = ""
    autoRun = True
    runLast = True
    configFiles = [
        "/etc/exim4/exim4.conf",
    ]

    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        eximConf = open('/etc/exim4/exim4.conf').read()
        hub = """\ngreys_rehubber:
    driver = manualroute
    condition = ${if match_ip{$sender_host_address}{192.168.0.0/16}{yes}{no}}
    domains = +local_domains
    route_data = ${lookup{$domain}lsearch{/etc/exim4/greys_rehubber}}
    transport = remote_smtp\n\n"""

        eximConf = Utils.insertBeforeLine(eximConf, 'catchall', hub)

        l = open('/etc/exim4/exim4.conf', 'wt')
        l.write(eximConf)
        l.close()
    ]

