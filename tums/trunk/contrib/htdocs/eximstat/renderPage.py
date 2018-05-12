#!/usr/bin/python
import os, datetime

header = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
   <title>Mail Statistics</title>
   <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
   <script src="./js/mochi/MochiKit.js" type="text/javascript"></script>
   <script src="./js/plotkit/excanvas.js" type="text/javascript"></script>

   <script src="./js/plotkit/Base.js" type="text/javascript"></script>
   <script src="./js/plotkit/Layout.js" type="text/javascript"></script>
   <script src="./js/plotkit/Canvas.js" type="text/javascript"></script>
   <script src="./js/plotkit/SweetCanvas.js" type="text/javascript"></script>
   <style type="text/css">
   body {
        margin: 1em;
        padding: 0;
        background-color: #ffffff;
        color: #333;
        
        font-family: "Lucida Grande", "Tahoma", "Verdana", "Sans", "sans-serif";
        font-size: 0.9em;
        line-height: 1.5em;
    }
    </style>
</head>
<body>
    <h2><img align="absmiddle" src="images/directory.png"/> &nbsp;Mail Statistics</h2>
"""

footer = """
</body></html>
"""
dbs = os.popen('ls ./statdb/*rs.db').read().strip('\n').split('\n')
months = []
days = {}
for i in dbs:
    tm = i.split('/')[-1]
    if "20" in i and tm[:6] not in months:
        days[tm[:6]] =[]
        months.append(tm[:6])

    if "20" in i:
        days[tm[:6]].append(i) 

    ## Last Month
for month in months:
    MonthData = {}
    topDomains = {}
    topSendDomains = {}
    localSenders = {}
    localRecip = {}
    localDest = {}
    remoteSenders = {}

    statargs = [
        [topDomains, 'receive_domains'], 
        [topSendDomains, 'send_domains'], 
        [localSenders, 'local_senders'],
        [localRecip,   'destinations'], 
        [remoteSenders, 'remote_senders'],
        [localDest,     'recipients']
    ]
    for i in days[month]:
        if i.split('/')[-1][:6] == month:
            lp = open(i).read()
            mp = open(i.replace('rs','ms')).read()
            stat = eval(lp)
            mstat = eval(mp)
            
            day = int(i.split('/')[-1][6:8])

            MonthData[day] = stat
            
            for target, source in statargs:

                for key,val in mstat[source].items():
                    if key in target:
                        target[key] += val
                    else:
                        target[key] = val
    # URGH!

    def listify(adict):
        trd = [ [i,k] for k,i in adict.items()]
        trd.sort()
        return [k for k in reversed(trd[-10:])]

    topDomains = listify(topDomains)
    topSendDomains = listify(topSendDomains)
    localSenders = listify(localSenders)
    localRecip = listify(localRecip)
    remoteSenders = listify(remoteSenders)
    localDest = listify(localDest)

    ### Spam graph
    xTicks = ['{label: "%s", v: %s}' % (i,i) for i in  range(1,32)]

    spam = []
    blacklist = []
    total = []
    grey = []

    for i in range(1,32):
        try:
            stats = MonthData[i]
        except:
            stats = {'blacklist':0, 'spam':0, 'other':0, 'grey':0}
        
        spam.append([i, int(stats['spam'])])
        blacklist.append([i, int(stats['blacklist'])])
        total.append([i, int(stats['other'])])
        try:
            grey.append([i, int(stats['grey'])])
        except:
            print "No greylist data for the %sth" % i

    greyCanvas = """\n
    <h3>Spam Statistics</h3>
    <p>Greylisted mails for this month</p>
    <div><canvas id="grey%s" width="600" height="300"></canvas></div>
    <script type="text/javascript">
        var xTicks = [%s];
        var options = PlotKit.Base.officeOrange();
        options['shouldStroke'] = true;
        var layout = new Layout("bar", {"xTicks": xTicks}, options);
        layout.addDataset("greylisted", %s);

        layout.evaluate();

        var chart = new SweetCanvasRenderer($("grey%s"), layout, options);
        chart.render();
    </script>
    <br/>
    """ % (month, ','.join(xTicks), repr(grey), month)

    spamCanvas = """\n
    <p>Spam and other mail blocked for this month</p>
    <table>
        <tr>
            <td>
                <div><canvas id="chart%s" width="600" height="300"></canvas></div>
                <script type="text/javascript">
                    var xTicks = [%s];
                    var options = PlotKit.Base.officeOrange();
                    options['shouldStroke'] = true;
                    var layout = new Layout("bar", {"xTicks": xTicks}, options);
                    layout.addDataset("total", %s);
                    layout.addDataset("blacklist", %s);
                    layout.addDataset("spam", %s);

                    layout.evaluate();

                    var chart = new SweetCanvasRenderer($("chart%s"), layout, options);
                    chart.render();
                </script>
            </td>
            <td>
                <img src="images/spam.png" alt = "Spam"/>&nbsp;&nbsp;Spam blocked<br/>
                <img src="images/blacklist.png" alt = "Blacklist"/>&nbsp;&nbsp;Mail from blacklisted domain<br/>
                <img src="images/total.png" alt = "Other"/>&nbsp;&nbsp;Viruses, forged mail and greylisting<br/>
            </td>
        </tr>
    </table>
    """ % (month, ','.join(xTicks), repr(total), repr(blacklist), repr(spam), month)



    def pieCharts(tile, descrip, values):
        pie = """
        <h3>%s</h3>
        <p>%s</p>
        <table>
            <tr>
                <td>
                    <div><canvas id="recdom%s" width="300" height="300" style="background:#fff"></canvas></div>\n
                    <script type="text/javascript">
                       var options = PlotKit.Base.officeOrange();
                       options['backgroundColor'] = MochiKit.Color.Color.whiteColor()
                       var layout = new PlotKit.Layout("pie", options);
                       layout.addDataset("sqrt", %s);
                       layout.evaluate();
                       var plotter = new PlotKit.SweetCanvasRenderer($("recdom%s"), layout, options);
                       plotter.render();   
                    </script>
                </td>
                <td>
                    <table cellspacing=0>
                        %s
                    </table>
                </td>
            </tr>
        <table>
        """ % (
            tile, 
            descrip, 
            tile.replace(' ',''), [[k[0],k[0]] for i,k in enumerate(values)],  tile.replace(' ',''), 
            "\n".join(["                <tr><td style=\"padding-left:2em;\">%s</td><td style=\"padding-left:1.4em;\">%s</td></tr>" % (
                k[0], k[1]) for i,k in enumerate(values) ]
            )
        )
        return pie

    l = open('%s.html' % month, 'wt') 
    l.write(header)
    l.write(greyCanvas)
    l.write(spamCanvas)
    l.write(pieCharts("Top sender domains", "Top 10 domains which deliver mail to this site", topDomains))
    l.write(pieCharts("Top recipient domains", "Top 10 domains to which mail is delivered from this site", topSendDomains))
    l.write(pieCharts("Top local sender addresses", "Top 10 email addresses from which mail was delivered", localSenders))
    l.write(pieCharts("Top local recipient addresses", "Top 10 email addresses to which mail was delivered at this site", localDest))
    l.write(pieCharts("Top recipient addresses", "Top 10 email addresses to which mail was delivered from this site", localRecip))
    l.write(pieCharts("Top sender addresses", "Top 10 email addresses from which mail was received by this site", remoteSenders))

    l.write(footer)
    l.close()

l = open('index.html', 'wt')
l.write(header)
l.write("<h3>Mail Statistics</h3>")
months.sort()
for i in reversed(months):
    date = datetime.datetime(int(i[:4]),int(i[4:6]),01).ctime().split()
    l.write('<a href="%s.html">%s %s</a><br/>' % (i, date[1], date[4]))
