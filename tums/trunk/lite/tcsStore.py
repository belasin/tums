# A simple data store for TCS update completion 
import Settings

class TCSStore:
    store = Settings.BaseDir + "/tcsstore.dat"
    def getUpdates(self):
        """ Returns availiable updates """
        installed = self.getInstalled()
        fi = open(self.store)
        updates = []
        for i in fi:
            if i[0]=='U':
                update = i[1:]
                if not update in installed:
                    updates.append(update.strip('\n'))
        fi.close()
        return updates
        
    def getInstalled(self):
        """ Returns installed updates """
        fi = open(self.store)
        installed = []
        for i in fi:
            if i[0]=='I':
                installed.append(i[1:].strip('\n'))
        fi.close()
        return installed

    def getCurrentVersion(self):
        """ Returns the current TCS version """
        fi = open(self.store)
        for i in fi:
            if i[0]=='V':
                fi.close()
                return i[1:].strip('\n')
        fi.close()
        return None

    def updateVersion(self, newVersion):
        installed = self.getInstalled()
        updates = self.getUpdates()
        fi = open(self.store)
        fi.write('V%s\n' % newVersion)
        for i in installed:
            fi.write('I%s\n' % i)
        fi.flush()
        for u in updates:
            fi.write('U%s\n' % u)
        fi.flush()
        fi.close()

    def addInstalled(self, name):
        """ Add an installed update """
        fi = open(self.store, 'at')
        fi.write('I%s\n' % (name,))
        fi.close()

    def updateUpdates(self, names):
        """ Rewrites the whole file with only the current availiable updates"""
        current = self.getInstalled()
        ver = self.getCurrentVersion()
        
        fi = open(self.store, 'wt') 
        fi.write('V%s\n' % (ver,))
        
        for i in names:
            fi.write('U%s\n' % (i,))
            fi.flush()

        for i in current:
            fi.write('I%s\n' % (i,))
            fi.flush()
        fi.close()

