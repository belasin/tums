# Generates a special graph
import os, sys

asCache = {}

try:
    l = file('ascache').read()
    exec l
except:
    asCache = {}

def getAddress(host):
    l = os.popen('host %s | grep address' % host)
    for n in l:
        if 'address' in n:
            p = n.split()[-1]
            return p
    try:
        int(host.split('.')[0])
        return host
    except:
        return None

j = os.popen('/home/thebe/thebe2/test.py getServers')
hosts = {}

for i in j:
    l = eval(i.strip('\n'))
    name, ip = (l[1], l[-1])
    id = int(l[0])
    if not ip:
        continue
    class_c = '.'.join(ip.split('.')[:3])
    if class_c in asCache.keys():
        if asCache[class_c][0] not in hosts:
            hosts[asCache[class_c][0]] = []
        hosts[asCache[class_c][0]].append((name, id))

        print asCache[class_c][0], ip
    else:
        n = os.popen('whois -h whois.cymru.com %s' % ip).read()
        print n, ip, name
        AS = n.split('|')[2].strip().split()[-1]
        N = n.split('|')[-1].strip()
        asCache[class_c] = (AS, N)
        hosts[AS] = [(name, id)]

nodes = []
relations = []

asns = {}
for k,v in asCache.items():
    asns[v[0]] = v[1]

print hosts 

for AS, host in hosts.items():
    N = asns[AS].split()[0]
    nodes.append(
        '  AS_%s [label="%s"];' % (AS, N)
    )
    for h, id in host:
        nodes.append(
            '  "%s" [label="%s", color=lightblue2, style=filled, href="/Servers/Manage/%s"];' % (h, h, id)
        )
        relations.append('  AS_%s -- "%s";' % (AS, h))

l = hosts.keys()
# Create circular reference
relations.append('  AS_%s -- AS_%s;' % (l[-1], l[0]))
lastAS = l[0]
for AS in l[1:]:
    relations.append('  AS_%s -- AS_%s;' % (lastAS, AS))
    lastAS = AS

graph = """graph G {
  graph[rankdir="LR"];
  node[shape=rect,fontsize=5, height=0.1];
  ranksep=2;
  ratio=auto;
  edge[len=1.3];
  %s
  %s
}\n""" % ('\n'.join(relations), '\n'.join(nodes))

l = file('test.dot', 'wt')
l.write(graph)

l.close()

l = file('ascache', 'wt')
l.write('asCache = %s' % repr(asCache))

l.close()
