// import Nevow.Athena

statusGraphs.PS = Nevow.Athena.Widget.subclass('statusGraphs.PS');

statusGraphs.PS.methods(
    function nodeInserted(self){
        self.renderTables();
        self.renderGraphs();
    },
    function renderTables(self){
        var loopingCall = function(){
            var sys = self.callRemote('getSystemDetails');
            sys.addCallback(function(res){
                var makeTable = function(h, contents){
                    var body = map(function(el){
                        return TR({}, map(function(inel){
                            return TD({}, inel);
                        }, el));
                    },contents);

                    var head = map(function(el){
                        return TH({}, el);
                    },h);

                    return TABLE({'cellspacing':'0','class':'listing'}, 
                        THEAD({'background':'/images/gradMB.png'},
                            TR({},
                                head
                            )
                        ),
                        TBODY({}, 
                            body
                        )
                    );
                };
                // Read data...
                var mq          = res[0];
                var procstatus  = res[1];
                var filesystem  = res[2];
                var raidstat    = res[3];
                var shares      = res[4];
                var sessions    = res[5];
                var time        = res[6];
                var up          = res[7];
                var users       = res[8];
                
                var swapValue = function(id, value){
                    swapDOM(self.nodeById(id), DIV({'id':'athenaid:1-'+id}, value));
                }

                swapValue('sysEmails', mq[0]);
                swapValue('sysQueue', mq[1]);
                swapValue('sysTime', time);
                swapValue('sysUsers', users);
                swapValue('sysUptime', up);

                swapValue('processTable', TABLE({'cellspacing':0,'cellpadding':'0px','class':'servicetable'},
                    TBODY({},
                        map(function(row){
                            if (row[3] == 0){
                                var bg = "#eee";
                                var tcol = "#006b33";
                                /*var tcol = "#1b7b49";*/
                            }
                            else{
                                var bg = "#fff";
                            }
                            if (row[3]==1){
                                var tcol = "#bf0000";
                            }
                            if (row[3]==2){
                                var tcol = "#ff7f00";
                            }
                            return TR({}, 
                                TD({'style':'background:'+ bg}, IMG({'src':row[0]})),
                                TD({'style':'background:'+ bg}, row[1]),
                                TD({'style':'background:'+ bg +'; font-family:arial,verdana,helvetica,sans-serif; color:'+tcol},
                                    row[2][2]
                                ),
                                TD({'style':'background:'+ bg}, 
                                    A({'href':'/auth/Proc/'+row[2][1]+'/start/', 'title':row[2][0], 
                                       'onclick':"return confirm('Are you sure you want to restart the "+row[1]+" service?');"}, 
                                        IMG({'src': '/images/service-start.png'})
                                    ),
                                    A({'href':'/auth/Proc/'+row[2][1]+'/stop/', 'title':row[2][0], 
                                       'onclick':"return confirm('Are you sure you want to stop the "+row[1]+" service?');"}, 
                                        IMG({'src': '/images/service-stop.png'})
                                    )
                                )
                            );
                        }, procstatus)
                    )
                ));

                swapDOM(self.nodeById('sysSessions'), DIV({'id':'athenaid:1-sysSessions'}, TABLE({'cellspacing':'0px','class':'listing'},
                    THEAD({'background':'/images/gradMB.png'},
                        TR({},
                            TH({},"Username"), TH({},"Group"), TH({},"Workstation"), TH({},"Open Shares")
                        )
                    ),
                    TBODY({},
                        map(function(row){
                            return TR({},
                                TD({}, row[0]),
                                TD({}, row[1]),
                                TD({}, row[2]),
                                TD({}, map(function(ses){return [ses, BR()];},row[3]))
                            );
                        },sessions)
                    )
                )));
                swapDOM(self.nodeById('sysFS'), DIV({'id':'athenaid:1-sysFS'},
                    makeTable(["Disk", "Size", "Available", "Usage", "Location"], filesystem)
                ));

                swapDOM(self.nodeById('sysRAID'), DIV({'id':'athenaid:1-sysRAID'}, TABLE({'cellspacing':'0','class':'listing'},
                    THEAD({'background':'/images/gradMB.png'},
                        TR({},
                            TH({}, "Device"), TH({},"Type"), TH({},"Status"), TH({}, '')//, TH({},"Disks")
                        )
                    ),
                    TBODY({},
                        map(function(row){
                            var ln = row[3].length + 1;
                            return TR({},
                                TD({}, row[0]),
                                TD({}, row[1]),
                                TD({}, row[2]),
                                TD({}, DIV({'style':'width:'+ln+'em'}, map(function(img){
                                    return IMG({'src':'/images/'+img, 'class':'raidInline'});
                                }, row[3])))
                                //,TD({}, map(function(ses){return [ses, BR()];},row[4]))
                            );
                        },raidstat)
                    )
                )));
            });
            callLater(10, loopingCall);
        };
        loopingCall();
    },
    function renderGraphs(self){
        var thusaGraph = function(){
            var r = {
                "colorScheme": PlotKit.Base.palette(PlotKit.Base.baseColors()[5]),
                "backgroundColor": PlotKit.Base.baseColors()[2].lighterColorWithLevel(0.5),
                "xTicks":[
                    {v:1, label:"38s"},
                    {v:3, label:"34s"},
                    {v:5, label:"30s"},
                    {v:7, label:"26s"},
                    {v:9, label:"22s"},
                    {v:11, label:"18s"},
                    {v:13, label:"14s"},
                    {v:15, label:"10s"},
                    {v:17, label:"6s"},
                    {v:19, label:"2s"},
                    {v:20, label:"0s"}
                ]
            };
            MochiKit.Base.update(r, PlotKit.Base.officeBaseStyle);
            return r;
        };
        var loopingCall = function(){
            var ld = self.callRemote('getLoadAve');
            ld.addCallback(function(res){
                var options = new thusaGraph();
                var layout = new Layout("line", options);
                var j=0;
                var statsNow = res[1];
                var statsKeys = res[2];
                var lays = {};
                var cans = {};
                var plots = {};
                var opts = {};

                canvas = getElement('graphload');

                forEach(res[0], function(i){
                    j++;
                    layout.addDataset("set"+j, i);
                });

                try {
                    forEach(statsKeys, function(thiskey){
                        var key = thiskey;
                        var j=0;

                        opts[key] = new thusaGraph();
                        cans[key] = getElement("graph"+key);
                        lays[key] = new Layout("line", opts[key]);

                        forEach(statsNow[key], function(i){
                            j++;
                            lays[key].addDataset("set"+j, i);
                        });

                        // Clean up around the canvas container
                        forEach(cans[key].parentNode.childNodes, function(el){
                            if (el.localName!="CANVAS") {
                                cans[key].parentNode.removeChild(el);
                            }
                        });
                    });

                    // Clean up around the canvas container
                    forEach(canvas.parentNode.childNodes, function(el){
                        if (el.localName!="CANVAS") {
                            canvas.parentNode.removeChild(el);
                        }
                    });

                    forEach(statsKeys, function(key){
                        lays[key].evaluate();
                        ctx = cans[key].getContext('2d');
                        ctx.clearRect(0,0,384,192);
                        plots[key] = new PlotKit.SweetCanvasRenderer(cans[key], lays[key], opts[key]);
                        plots[key].render();
                    });

                    layout.evaluate();

                    ctx = canvas.getContext('2d');
                    ctx.clearRect(0,0,384,192);
                    var plotter = new PlotKit.SweetCanvasRenderer(canvas, layout, options);
                    plotter.render();
                }
                catch(e){
                    n = 1;
                }
            });
            callLater(2, loopingCall);
        };
        loopingCall();
    }
);
