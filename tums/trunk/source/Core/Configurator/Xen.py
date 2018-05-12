from Core import WebUtils, Utils, confparse
from twisted.internet import utils, defer
import os, sys
import Settings

# Disk sizes always in GB

def xen_create_linux(sysconf, data):
    if data['ip']:
        net = '--ip=%s' % data['ip'].encode()
    else:
        net = '--dhcp'

    size = data['disk']
    mem = data['memory']

    name = data['name'].encode()

    exScript = """#!/usr/bin/perl

use Expect;

my $Command             = "/tmp/create-im-%s";
my @Parameters          = ();
my $timeout             = 9999999;
my $expect_string       = "ssword:";
my $send_data           = "%s";

my $exp = new Expect;

$exp->spawn($Command, @Parameter)
        or die "Cannot Spawn $Command: $!\n";

$exp->expect($timeout,
    [ $expect_string, \&send_response,],
    [ $expect_string, \&send_response,],
);

$exp->soft_close();

sub send_response {
        $exp->send($send_data."\n");
        exp_continue;
}\n""" % (name, data['password'].encode())


    l = open('/tmp/ex-%s' % name, 'wt')
    l.write(exScript)
    l.close()

    l = open('/tmp/create-im-%s' % name, 'wt')
    l.write('#!/bin/bash\nxen-create-image --debootstrap --hostname=%s %s --dist=%s --size=%sGb --memory=%sMb --swap=%sMb\n' % (
        name,
        net,
        data['distribution'],
        size,
        mem,
        mem,
    ))
    l.close()

    os.chmod('/tmp/create-im-%s' % name, 0777)
    os.chmod('/tmp/ex-%s' % name, 0777)

    return WebUtils.system('/tmp/ex-%s' % (name))

def createImage(host, size):
    return WebUtils.system('dd if=/dev/zero of=/storage/virtual_machines/%s-disk.img bs=1M count=%s' % size*1024)

def createSwap(host, size):
    return WebUtils.system('dd if=/dev/zero of=/storage/virtual_machines/%s-swap.img bs=1M count=%s' % size)

def reconfigure_xen(sysconf, name, rename=""):
    """ Reconfigure the memory or IP setting of a domain """
    conf = open('/etc/xen/%s.cfg' % name)
    
    if rename:
        data = sysconf.General['xen']['images'].get(rename, {})
    else:
        data = sysconf.General['xen']['images'].get(name, {})

    newconf = ""
    for l in conf:
        if l[:4] == "name" and rename:
            newconf += "name    = '%s'\n" % rename
            continue
            
        if l[:6] == "memory":
            newconf += "memory  = '%s'\n" % data['memory'] 
            continue 

        # Skip these for now...
        if l[:4] == "dhcp":
            continue 
        if l[:3] == "vif":
            continue 

        newconf += l 
    
    newconf += "\n"
    if data.get('ip'):
        newconf += "vif  = ['', 'ip=%s']\n" % data['ip']
    else:
        newconf += "dhcp = 'dhcp'\nvif  = ['']\n"

    conf.close()
    if rename:
        conf = open('/etc/xen/%s.cfg' % rename, 'wt')
        os.remove('/etc/xen/%s.cfg' % name)
    else:
        conf = open('/etc/xen/%s.cfg' % name, 'wt')

    conf.write(newconf)
    conf.close()


def xen_create_hvm(sysconf, data):
    host = data['name'].encode(),
    size = data['disk']
    mem = data['memory']
    iso = data['bootiso']

    def HVMConfig(_):
        hvmconf = """#Vulani config for HVM %(host)s
kernel = "/usr/lib/xen-3.0.3-1/boot/hvmloader"
apic = 0
acpi = 0
builder = 'hvm'
memory = %(mem)s
name = "%(host)s"
vcpus = 1
vif = [ 'type=ioemu, bridge=xenbr1' ]
disk = [ 'phy:/storage/virtual_machines/%(host)s-disk.img,ioemu:hda,w' ]
device_model = '/usr/lib/xen-3.0.3-1/bin/qemu-dm'
boot='c'
sdl=0
vnc=1
vncviewer=1
vncunused=0\n""" % {
            'mem': mem,
            'host': host, 
        }

        l = open('/etc/xen/%s.cfg' % host, 'wt')
        l.write(hvmconf)
        l.close()

    def swap(_):
        return createSwap(host, mem).addBoth(HVMConfig)
    return createImage(host, size).addBoth(swap)
