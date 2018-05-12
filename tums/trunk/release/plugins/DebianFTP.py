import config, os
from Core import Utils

class Plugin(object):
    """ Configures everything needed for Debian FTP. """
    parameterHook = "--ftp"
    parameterDescription = "Reconfigure FTP on Debian"
    parameterArgs = ""
    autoRun = True
    required = "debian"
    configFiles = [ 
        "/etc/vsftpd.conf",
        "/etc/vsftpd.chroot_list", 
    ]

    def reloadServices(self):
        os.system('/etc/init.d/vsftpd restart')

    def writeConfig(self, *a):
        vsconfig = """#listen=YES
listen_ipv6=YES
anonymous_enable=NO

local_enable=YES
write_enable=YES
dirmessage_enable=YES
xferlog_enable=YES
connect_from_port_20=YES
xferlog_file=/var/log/vsftpd.log

ftpd_banner=Thusa ftpd v1.5.30 at %s

chroot_local_user=YES
chroot_list_enable=YES
file_open_mode=0660
local_umask=000

# Users *not* to chroot
chroot_list_file=/etc/vsftpd.chroot_list

secure_chroot_dir=/var/run/vsftpd
pam_service_name=vsftpd
rsa_cert_file=/etc/ssl/certs/vsftpd.pem\n""" % (config.CompanyName)

        l = open('/etc/vsftpd.conf', 'wt')
        l.write(vsconfig)
        l.close()

        l = open('/etc/vsftpd.chroot_list', 'wt')
        if config.FTP.get('globals', None):
            for i in config.FTP['globals']:
                l.write(i+'\n')
        l.close()
