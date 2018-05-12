import os

def getNIDdb(year=0, month=0, day=0):
    nids = {}
    for i in os.listdir('/usr/local/tcs/tums/rrd/'):
        if not ".nid" in i:
            continue
        if not "total" in i:
            continue

        try:
            n, iface, fdate = i.split('_')
            d, m, y, j = fdate.split('-')
        except:
            continue

        if year and int(y)!=year:
            continue
        if month and int(m)!=month:
            continue
        if day and int(d)!=day:
            continue

        if iface not in nids:
            nids[iface] = []

        nids[iface].append((i,int(y),int(m),int(d)))

    return nids

def getNIDdaySummary(year, month):
    """Returns a NID summary info, highest day and largest combined value
       for a particular month+year"""

    niddbs = getNIDdb(year, month)
    nds = {}
    maxd = 0
    maxunit = 0
    for iface, nids in niddbs.items():
        ds = {}
        dl = []
        for nid,y,m,d in nids:
            try:
                vi, vo= [float(i) for i in open('/usr/local/tcs/tums/rrd/'+nid).read().strip('\n').split(':')]
                ds[d] = (vi, vo)
                if vi+vo > maxunit:
                    maxunit = vi+vo
                dl.append(d)
                if d > maxd:
                    maxd = d
            except Exception, e:
                continue

        dl.sort()
        k = [(i,ds[i]) for i in dl]
        nds[iface] = k

    return nds, maxd, maxunit
