from Core import WebUtils, Utils, confparse
from twisted.internet import utils, defer
import os, sys
import Settings

def create_lease(sysconf, data):
    """ Create a static lease
    @param sysconf: A C{Config} instance
    @param data: C{dict} of configuration options containing
        'ip': The IP address for the lease
        'hostname': The computers hostname
        'mac': The mac address of the computers network card
    """

    leases = sysconf.DHCP

    if leases.get('leases', None):
        leases['leases'][data['ip'].encode('ascii', 'replace')] = [data['hostname'].encode('ascii', 'replace'), data['mac'].encode('ascii', 'replace')]
    else:
        leases['leases']  = {
            data['ip'].encode('ascii', 'replace'):[data['hostname'].encode('ascii', 'replace'), data['mac'].encode('ascii', 'replace')]
        }

    sysconf.DHCP = leases

    #return WebUtils.restartService('dhcp')

def get_dhcp_config(sysconf, iface):
    
    # Catch interfaces that are DHCP themselves
    if sysconf.EthernetDevices[iface].get('type', None) == 'dhcp':
        return {}

    config = sysconf.DHCP.get(iface, {})
    
    # Determine myIp
    try:
        myIp = sysconf.EthernetDevices[iface]['ip'].split('/')[0]
        myNetmask = Utils.cidr2netmask(sysconf.EthernetDevices[iface]['ip'].split('/')[1])
    except KeyError:
        myIp = ''
        myNetmask = ''

    data = {
        'rangeStart'  : config.get('rangeStart', "100"),
        'rangeEnd'    : config.get('rangeEnd', "220"),
        'netmask'     : config.get('netmask', myNetmask),
        'netbios'     : config.get('netbios', myIp),
        'nameserver'  : config.get('nameserver', myIp),
        'gateway'     : config.get('gateway', myIp),
        'domain'     : config.get('domain', sysconf.Domain),
        'autoProv'   : config.get('autoProv', True),
        'snomStart'  : config.get('snomStart', '60'),
        'snomEnd'    : config.get('snomEnd', '80'),
        'snomConfigAddr': config.get('snomConfigAddr', myIp + ':9682'),
        'network'     : config.get('network', '.'.join(myIp.split('.')[:3]) + ".0")
    }

    return data

def set_dhcp_config(sysconf, data, iface):
    config = sysconf.DHCP 

    nc = {}
    for i,v in data.items():
        nc[i] = v

    config[iface] = nc

    sysconf.DHCP = config

    return WebUtils.restartService('dhcp')

