from enamel import pages, deferreds, tags, form, url

from pages import * 

import utils

class Format(pages.AthenaFragment):

    def document(self):
        return pages.template('format_fragment.xml', templateDir = '/home/installer/templates')

    @pages.exposeAthena
    def progressUpdate(self, n):
        # Figure out the percentage
        self.callRemote('updateProgress', n)

    @pages.exposeAthena
    def startup(self):
        commands = self.enamel.setup['formatcoms']
        print commands

        self.chainSize = len(commands)
        self.chainCounter = 0

        def logOutput(_):
            print _

        
        def runCommand(previous, cmd):
            print previous
            self.chainCounter += 1
            self.progressUpdate( int((self.chainCounter/float(self.chainSize)) * 100))
            return utils.system(cmd).addBoth(logOutput)

        def done(_):
            print _
            return True
            
        def doMounts(_):
            # Mount our target filesystem
            return utils.system(';'.join(self.enamel.setup['runmounts'])).addBoth(done)

        deferChain = runCommand(None, commands[0])
        for command in commands[1:]:
            print command
            deferChain.addBoth(runCommand, command)
        
        return deferChain.addBoth(doMounts)

class Page(pages.Athena):
    elements = {'format': (Format, 'format.E', '/home/installer/athena/format.js')} 

    def document(self):
        return pages.template('format.xml', templateDir = '/home/installer/templates')

