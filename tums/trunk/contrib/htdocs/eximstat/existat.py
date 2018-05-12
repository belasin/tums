#!/usr/bin/python
import os

def mainLog():
    main = open('/var/log/exim/exim_main.log')
    completeIds = []
    mstats = {}
    stats = {}
    for l in main:
        line = l.strip('\n').strip()
        lsegs = line.split()
        date = lsegs[0]

        if not date in stats:
            mstats[date] = {
                'send_domains':{},
                'receive_domains':{},
                'recipients':{},
                'destinations': {},
                'remote_senders':{},
                'local_senders': {},
                'send_hosts':{},
                'receive_hosts':{},
            }
            stats[date] = {}

        time = lsegs[1]
        message =  ' '.join(lsegs[2:])

        if "=>" in message or "<=" in message and "<>" not in lsegs[4]: 
            messageId = lsegs[2]

            if messageId not in stats[date]:
                stats[date][messageId] = {}

            if "<=" in message:
                stats[date][messageId]['from'] = lsegs[4]
                if 'H=' in lsegs[5]:
                    if "(" in lsegs[5]:
                        ip = message.split('[')[-1].split(']')[0]
                        #dom = os.popen('host %s | grep arpa | awk \'{print $5}\'' % ip).read().strip('\n').strip('.')
                        dom = ip
                        if "." in dom and not "SERVFAIL" in dom:
                            stats[date][messageId]['from_domain'] = dom
                        else:
                            stats[date][messageId]['from_domain'] = ip
                    else:
                        stats[date][messageId]['from_domain'] = lsegs[5].replace('H=','')
                else:
                    stats[date][messageId]['from_domain'] = "Server Local"
                stats[date][messageId]['from_ip'] = message.split('[')[-1].split(']')[0]
                if "P=smtp" in message: 
                    # Remote relay
                    stats[date][messageId]['relay'] = 'remote'
                else:
                    stats[date][messageId]['relay'] = 'local' # or other... who cares...

            elif "=>" in message:
                if stats[date][messageId] ==  {}: # Mail is trash, there has to be a <= line before this is hit
                    pass
                else:
                    stats[date][messageId]['to'] = lsegs[4]
                    mailfrom = stats[date][messageId]['from']
                    rdom = mailfrom.split('@')[-1]
                    host = stats[date][messageId]['from_domain']
                    mailto = stats[date][messageId]['to']

                    if ("R=hubbed_hosts" in message or "R=ldap_user" in message) or stats[date][messageId]['relay'] == 'remote':
                        stats[date][messageId]['direction'] = 'in'

                        if rdom in mstats[date]['receive_domains']:
                            mstats[date]['receive_domains'][rdom] += 1
                        else:
                            mstats[date]['receive_domains'][rdom] = 1

                        if host in mstats[date]['receive_hosts']:
                            mstats[date]['receive_hosts'][host] += 1
                        else:
                            mstats[date]['receive_hosts'][host] = 1

                        if mailfrom in mstats[date]['remote_senders']:
                            mstats[date]['remote_senders'][mailfrom] += 1
                        else:
                            mstats[date]['remote_senders'][mailfrom] = 1

                        if mailto in mstats[date]['recipients']:
                            mstats[date]['recipients'][mailto] += 1
                        else:
                            mstats[date]['recipients'][mailto] = 1

                    elif ("R=dnslookup" in message) and stats[date][messageId]['relay'] == 'local':
                        stats[date][messageId]['direction'] = 'out'

                        mailfrom = stats[date][messageId]['from']

                        if mailto in mstats[date]['destinations']:
                            mstats[date]['destinations'][mailto] += 1
                        else:
                            mstats[date]['destinations'][mailto] = 1

                        if rdom in mstats[date]['send_domains']:
                            mstats[date]['send_domains'][rdom] += 1
                        else:
                            mstats[date]['send_domains'][rdom] = 1

                        if host in mstats[date]['send_hosts']:
                            mstats[date]['send_hosts'][host] += 1
                        else:
                            mstats[date]['send_hosts'][host] = 1

                        if mailfrom in mstats[date]['local_senders']:
                            mstats[date]['local_senders'][mailfrom] += 1
                        else:
                            mstats[date]['local_senders'][mailfrom] = 1
    return mstats

def rejectLog():
    rejects = {}

    reject = open('/var/log/exim/exim_reject.log')

    for l in reject:
        line = l.strip('\n').strip()
        lsegs = line.split()
        if "H=" in line:
            try:
                date = lsegs[0]
                time = lsegs[1]
                if date not in rejects:
                    rejects[date] = {'spam':0, 'blacklist':0, 'other':0, 'grey':0}

                message = ' '.join(lsegs[2:])
                
                if "spam points" in message:
                    rejects[date]['spam'] += 1

                elif "blacklist" in message:
                    rejects[date]['blacklist'] += 1
                elif "greylist" in message:
                    rejects[date]['grey'] += 1
                
                else:
                    rejects[date]['other'] += 1
            except:
                pass

    return rejects

rejects = rejectLog()
delivers = mainLog()

for date in rejects:
    fn = date.replace('-', '')+"rs.db"

    fdrs = open('statdb/%s' % fn, 'wt')

    fdrs.write(repr(rejects[date]))
    fdrs.close()

for date in delivers:
    fn = date.replace('-', '')+"ms.db"

    fdms = open('statdb/%s' % fn, 'wt')

    fdms.write(repr(delivers[date]))
    fdms.close()

