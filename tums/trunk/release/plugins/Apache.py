import config, os, time, sys
from Core import Utils

class Plugin(object):
    parameterHook = "--apache"
    parameterDescription = "Reconfigure Apache"
    parameterArgs = ""
    autoRun = True
    configFiles = [ 
    ]
    
    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        dir = "sites-enabled"

        os.system('ln -s /etc/apache2/mods-available/php5.load /etc/apache2/mods-enabled/php5.load >/dev/null 2>&1')
        os.system('ln -s /etc/apache2/mods-available/php5.conf /etc/apache2/mods-enabled/php5.conf >/dev/null 2>&1')

            
        if not config.General.get('http'):
            # Bail.
            return
        conf = config.General['http']
        
        def createVhost(dom, dct, c=1):
            """ A horror which was inspired by listening to Avril Lavigne """
            vhostDef = []
            for k, v in dct.items():
                if isinstance(v, dict):
                    vhostDef.append(' '*(c*4) + '<%s>' % k)
                    vhostDef.extend(createVhost(dom, v, c+1))
                    vhostDef.append(' '*(c*4) + '</%s>' % k.split()[0])
                elif isinstance(v, list):
                    for l in v:
                        vhostDef.append(' '*(c*4) + '%s %s'%(k,l))
                else:
                    vhostDef.append(' '*(c*4) + '%s %s'%(k,v))
            
            return vhostDef
        
        if conf.get('defaults'):
            v = createVhost(config.Domain, conf['defaults'])
            
            l = open('/etc/apache2/%s/%s' % (dir, "000-default"), 'wt')
            
            l.write('NameVirtualHost *\n')
            l.write('<VirtualHost *>\n')
            l.write('\n'.join(v))
            l.write('\n</VirtualHost>\n')
            l.close()
        
        if conf.get('vhosts'):
            for domain, defn in conf['vhosts'].items():
                m = createVhost(config.Domain, defn)
                l = open('/etc/apache2/%s/%s' % (dir, domain), 'wt')
                l.write('<VirtualHost *>\n')
                l.write('    ServerName %s\n' % domain)
                l.write('\n'.join(v))
                # Make sure there is logging
                if not "ErrorLog" in defn.keys():
                    l.write('    ErrorLog /var/log/apache2/mail.%s-error.log' % config.Domain)
                if not "CustomLog" in defn.keys():
                    l.write('    CustomLog /var/log/apache2/mail.%s-access.log combined' % config.Domain)
                l.write('\n</VirtualHost>\n')
                l.close()
        
        if 'mail.%s' % config.Domain not in conf['vhosts'].keys():
            mailVhost = """<VirtualHost *:80>
        DocumentRoot /var/www/localhost/htdocs/mail
        Alias /roundcube /var/www/localhost/htdocs/mail
        ServerName mail.%(dom)s
        ErrorLog /var/log/apache2/mail.%(dom)s-error.log
        CustomLog /var/log/apache2/mail.%(dom)s-access.log combined
</VirtualHost>\n""" % { 'dom': config.Domain }
            
            l = open('/etc/apache2/%s/01_default_mail.conf' % dir, 'wt')
            l.write(mailVhost)
            l.close()
        else:
            # We already wrote a vhost for mail.${domain} so delete our default
            os.system('rm /etc/apache2/%s/01_default_mail.conf' % dir)
            
