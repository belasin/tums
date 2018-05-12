StatView = function(name, table, graph, prefilters, postfilters, groupfilters, style) {
    this.base = "http://stats.liquidx.net/data/";
    this.name = name;
    this.prefilters = prefilters ? prefilters : [];
    this.postfilters = postfilters ? postfilters : [];
    this.groupfilters = groupfilters ? groupfilters : [];

    this.table = table;

    this.graph = graph;
    this.style = style ? style : "bar";
    this.opts = {
        padding: {top: 0, left: 0, right: 0, bottom: 0},
        drawYAxis: false,
        drawXAxis: false,
        enableEvents: false,
        IECanvasHTC: "/js/plotkit/iecanvas.htc"
    };
    this.layout = null;
    this.renderer = null;
};

StatView.prototype.updateForDate = function(date) {
    var url = this.base + this.name + "/" + date;
    var ajax = doSimpleXMLHttpRequest(url);
    ajax.addCallbacks(bind(this.updateTableAndGraph, this),
                      bind(this.error, this));
};

StatView.prototype.updateForAll = function() {
    var url = this.base + this.name + "/all";
    var ajax = doSimpleXMLHttpRequest(url);
    ajax.addCallbacks(bind(this.updateTableAndGraph, this),
                      bind(this.error, this));
};

StatView.prototype.updateTableAndGraph = function(request) {
    var dataset = this.evalTextResponse(request.responseText);
    
    var newRows = new Array();


    // draw values into table

    for (var i = 0; i < this.prefilters.length; i++) {
        dataset = map(this.prefilters[i], dataset);
    }

    for (var i = 0; i < this.groupfilters.length; i++) {
        dataset = this.groupfilters[i](dataset);
    }

    if (this.table) {
        var rowCount = dataset.length;
        
        for (var i = 0; i < rowCount; i++) {
            var rowdata = dataset[i];
            var count = rowdata[0];
            var desc = rowdata[1];
            var children = rowdata[2];
            var row = null;
            var childClass = StatFilters.slugify(desc);
            //var childClass = desc;
            
            if (!children) { // no children
                var columns = rowdata;
                for (var j = 0; j < this.postfilters.length; j++) {
                    columns = this.postfilters[j](columns);
                }

                row = TR({}, [TD({'class':'count'}, columns[0]), 
                              TD({'class':'label'}, columns[1])]);
                newRows.push(row);            
            }
            else if (children.length == 1) { // only one child
                var columns = rowdata[2][0];
                for (var j = 0; j < this.postfilters.length; j++) {
                    columns = this.postfilters[j](columns);
                }            
                row = TR({}, [TD({'class':'count'}, columns[0]), 
                              TD({'class':'label'}, columns[1])]);
                newRows.push(row);
            }
            else {
                var columns = rowdata;
                
                for (var j = 0; j < this.postfilters.length; j++) {
                    columns = this.postfilters[j](columns);
                }
                log(desc, childClass);
                
                // add the count to the start
                if (columns[1].nodeName == 'A') {
                    updateNodeAttributes(columns[1],
                    {"href": "#", "onclick": "toggleChildren('" +  childClass + "'); return false;"});
                }
                else {
                    columns[1] = A({onclick:"toggleChildren('" +  childClass + "'); return false;",  href:"#"}, columns[1]);
                };
                
                row = TR({'class':"tree"}, 
                         [TD({'class':'count'}, columns[0]), 
                          TD({'class':'label'}, columns[1])]);
                newRows.push(row);
                
                for (var j = 0; j < children.length; j++) {
                    var child = children[j];
                    for (var k = 0; k < this.postfilters.length; k++) {
                        child = this.postfilters[k](child);
                    }
                    
                    row = TR({'class':'child ' + childClass, style:{"display": "none"}}, 
                             [TD({'class':'count'}, child[0]), 
                              TD({'class':'label'}, child[1])]);
                    newRows.push(row);
                }
            }
        }

        var tableBody = this.table.tBodies[0];    
        swapDOM(tableBody, TBODY({}, newRows));
    }

    if (this.graph) {
        // draw graph
        var graphdata = items(map(itemgetter(0), dataset));
        graphdata.sort(function(a,b) {return parseInt(a[0])-parseInt(b[0])}, 
                       graphdata);
        //for (var i = 0; i < graphdata.length; i++) {
        //    log (i, graphdata[i][0], graphdata[i][1]);
        // }

        this.layout = new PlotKit.Layout(this.style, this.opts);
        this.layout.addDataset("data", graphdata);
        this.layout.evaluate();
        this.renderer = new PlotKit.SweetCanvasRenderer(this.graph, 
                                                        this.layout,
                                                        this.opts);
        this.renderer.render();
    }

};

StatView.prototype.error = function(request) {
    alert("failed response");
};


StatView.prototype.evalTextResponse = function(text) {
    var table = new Array();
    var lines = text.split('\n');
    for (var i = 0; i < lines.length; i++) {
        var stripped = strip(lines[i]);
        if ((stripped.length > 1) && (stripped.charAt(0) != '#')) {
            table.push(stripped.split(' '));
        }
    }
    return table;
};

var stats = new Array();

function statview_init() {
    var linkify = function(rowdata) {
        var count = rowdata[0];
        var desc = rowdata[1];
        var f = StatFilters;
        desc = f.makelink(desc, f.ellipsis(f.stripProtocol(desc)));
        return [count, desc];
    };

    stats["referrers"] = new StatView("referrers", 
                                      $('referrerstable'),
                                      $('referrerscanvas'),
                                      null,
                                      [linkify],
                                      [StatFilters.groupByDomain,
                                       partial(StatFilters.limitRows, 10)],
                                      "pie");
    stats["referrers"].updateForDate("2006.04");

    stats["albumart"] = new StatView("albumart_dl",
                                     $('albumarttable'),
                                     $('albumartcanvas'),
                                     null,
                                     null,
                                     [StatFilters.groupByMonth]);

    stats["albumart"].opts["xOriginIsZero"] = false;
    stats["albumart"].updateForAll();

    stats["usage_graph"] = new StatView("albumart_usage",
                                        null,
                                        $('usagecanvas'),
                                        null,
                                        null,
                                        [StatFilters.toInt],
                                        "line");

    stats["usage_graph"].opts["xOriginIsZero"] = false;

    stats["usage_table"] = new StatView("albumart_usage",
                                        $('usagetable'),
                                        null,
                                        null,
                                        [StatFilters.averagePerMonth],
                                        [StatFilters.groupByMonth]);

    stats["usage_graph"].updateForAll();
    stats["usage_table"].updateForAll();
}

addLoadEvent(statview_init);

function toggleChildren(className) {
    var elements = getElementsByTagAndClassName(null, className);
    var newDisplay = "none";
    if (elements && (elements.length > 0)) {
        var displayed = computedStyle(elements[0], "display");
        log("displayed:", displayed);
        if (displayed == "none" || isUndefinedOrNull(displayed))
            newDisplay = "";
        for (var i = 0; i < elements.length; i++) {
            elements[i].style.display = newDisplay;
        }
    }
}

