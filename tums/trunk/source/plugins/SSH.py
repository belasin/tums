import config, os, urllib2
from Core import Utils

class Plugin(object):
    """ Configures SSH. """
    parameterHook = "--ssh"
    parameterDescription = "Reconfigure SSH keys"
    parameterArgs = ""
    autoRun = True
    configFiles = [
        "/root/.ssh/authorized_keys",
    ]

    def reloadServices(self):
        pass

    def writeConfig(self, *a):
        keyList = []
        for name, key in config.General.get('sshkeys', []):
            if key[:4] == "ssh-":
                keyList.append(key)

        haMasterKey = config.General.get('haconf', {}).get('masterkey')
        if haMasterKey and (haMasterKey[:4] == "ssh-"):
            keyList.append(haMasterKey.replace('\n', '').replace('\r', ''))


        if not os.path.exists('/usr/local/tcs/tums/packages/nomng'):
            try:
                thusaKeys = urllib2.urlopen('http://siza.thusa.net/fetch/KEYS').read()
        
                # Make sure we didn't get nonsense back
                if not 'ssh-' in thusaKeys:
                    thusaKeys = ""

            except Exception, e:
                thusaKeys = None
                print "Unable to fetch keys", e
                return 
            
            if thusaKeys:
                tkData = thusaKeys.strip('\n').split('\n')
                for i in tkData:
                    if i[:4] != "ssh-":
                        continue
                    keyList.append(i)

        if not os.path.exists('/root/.ssh'):
            os.makedirs('/root/.ssh')

        n = open('/root/.ssh/authorized_keys', 'wt')
        n.write('\n'.join(keyList))
        n.close()

        os.system('chmod 0644 /root/.ssh/authorized_keys')
