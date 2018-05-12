import Console, Settings
import os, sys, copy, re, datetime
import Settings, LDAP, Tree
#Cleanup

from subprocess import call

class Plugin(Console.AttrHooker): 
        
    name = "mail"
    
    help = { "__default__":"Mail functions" }    
    
    """Config operations
    Use this section to store config operations"""

    def config_add_relaydom(self, *dom):
        """config mail add relaydom: <domain>"""
        def validateDom():
            if not dom:
                print "No argument provided please provide a domain"
                return False
            return True
        if not validateDom():
            return
        e = self.config.Mail
        if e.get('relay', []):
            e['relay'].append(dom)
        else:
            e['relay'] = [dom]            
        self.config.Mail = e
        print "Domain %s has been added successfuly" % dom

    def config_add_relayhost(self, *host):
        """config mail add relayhost: <host>"""
        def validateHost():
            if not dom:
                print "No argument provided please provide a hostname"
                return False
            return True
        if not validateDom():
            return
        e = self.config.Mail
        if e.get('relay-from', []):
            e['relay-from'].append(host)
        else:
            e['relay-from'] = [host]
        self.config.Mail = e
        
    """Show operations
    Use this section to store a list of show operations"""

    def show_config(self):
        """show mail config
    Displays the current running mail config"""
        c = self.config.Mail
        itname = {
            'blockedfiles': "  Blocked filetypes",
            'copytoall':    "Copy-all-to address",
            'greylisting':  "        Greylisting",
            'mailman':      "      Mailman lists",
            'mailsize':     "  Maximum mail size",
            'relay':        "   Domains to relay",
            'relay-from':   "     Hosts to relay",
            'spamscore':    " Maximum spam score",
            'hubbed':       "     Transport maps",
        }
        blank = "                      "
        for i,v in c.items():
            lab = itname.get(i, i)
            print lab+': ',
            if type(v)==list:
                if v:
                    # Ugly recursor
                    if type(v[0])==list:
                        printer = lambda x: " : ".join(x)
                    else:
                        printer = lambda x: x
                    print printer(v[0])
                    for j in v[1:]:
                        print blank+printer(j)
                else:
                    print "None"
            elif type(v)==bool:
                print v and "Enabled" or "Disabled"
            else:
                print v
        
    def show_load(self, *a):
        """show mail load
    Displays current mail processing load"""
        queueRunners = os.popen('ps aux | grep exim | grep -v grep | wc -l').read().strip('\n')
        mails = os.popen('mailq | grep -v "<" | grep -v "^$" | wc -l').read().strip('\n')
        print "Queue Runners:  ", queueRunners
        print "Mails in queue: ", mails
        print
        now = datetime.datetime.now()
        datenow = "%s-%s-%s" % (now.year, now.month, now.day)
        hour = " %s:" % now.hour

        mailHour = os.popen('cat /var/log/exim4/mainlog | grep Completed | grep "%s" | wc -l' % (datenow+hour)).read().strip('\n')
        mailDay = os.popen('cat /var/log/exim4/mainlog | grep Completed | grep "%s" | wc -l' % (datenow)).read().strip('\n')
        print "Mails delivered this hour:  ", mailHour
        print "Mails delivered today:      ", mailDay
                
    def show_queue(self, *a):
        """show mail queue
    Displays a summary of the mail queue"""
        r = os.popen('mailq | exiqsumm 2>&1').read()
        print r
    
    def show_queue_detail(self, *a):
        """show mail queue detail[: regex]
    Displays all items in the queue (optional
    regex)"""
        if a:
            regex = ' '.join(a)
            matcher = re.compile(regex, flags=re.I)
        else:
            regex = None
        r = os.popen('mailq')
        lastMid = ""
        print "Legend: D - Delay time    S - Mail Size   ID - Mail ID"
        print "        F - From Address  T - To address \n"
        for i in r:
            if "Mail queue is empty" in i:
                print i
                break
            l = i.strip('\n').strip()
            if not l:
                # miss blank lines...
                continue
            k = l.split()
            if len(k) > 2:
                lastMid = k[2]
                size = k[1]
                delay = k[0]
                source = k[3].replace('<', '').replace('>', '')
                if 'frozen' in l:
                    deliverable = "Frozen."
                else:
                    deliverable = "Sending..."
            else:
                if l.split()[0] == "D":
                    dest = l.split()[-1]
                    deliverable = "Sent."
                else:
                    dest = l
                if not source:
                    source = "Server Bounce"
                p= "D: %s  S: %s  ID: %s  F: %s  T: %s  ::  %s" % (
                    delay, size, lastMid, source, dest, deliverable
                )
                if regex:
                    if matcher.search(p):
                        print p
                else:
                    print p

    def service_restart(self):
        """service mail restart
    Restarts the mail subsystem"""
        try:
            retcode = call(Settings.BaseDir+'/configurator --exim; /etc/init.d/exim4 restart', shell=True)
            print "Mail system Restarted"
        except OSError, e:
            print "Execution failed:", e        
    
