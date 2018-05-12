// import Nevow.Athena

calendar.PS = Nevow.Athena.Widget.subclass('calendar.PS');

calendar.PS.methods(
    function nodeInserted(self){
        var loc = document.location.toString();

        self.now   = new Date();
       

        self.months = [
            "January",      "February", "March",        "April",
            "May",          "June",     "July",         "August",
            "September",    "October",  "November",     "December"
        ];

        // Days in each month
        self.mdays = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

        self.days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        self.daysSmall = ["S", "M", "T", "W", "T", "F", "S"];

        self.day   = self.now.getDate();
        self.month = self.now.getMonth();
        self.year  = self.now.getYear()+1900;

        self.renderMonth(self.year, self.month, self.day);

        self.selTab('monthView');

        window.onresize = function(re){
            self.selTab(self.currentTab);
        };

        forEach(['weekView', 'monthView'], function(tag){
            connect(self.nodeById(tag), 'onclick', function(ek){
                self.selTab(tag);
            });
        });
    },
    function selTab(self, tabId){
        hideElement(self.nodeById('weekViewPane'));
        hideElement(self.nodeById('monthViewPane'));

        self.currentTab = tabId; 
        forEach(['weekView', 'monthView'], function(id) {
            self.nodeById(id).firstChild.style.background = '#ffcf6c';
            self.nodeById(id).firstChild.style.fontWeight = 'normal';
        });
 
        self.nodeById(tabId).firstChild.style.background = '#ffac00';
        self.nodeById(tabId).firstChild.style.fontWeight = 'bold';

        if (tabId == "weekView"){
            self.openWeekView(self.year, self.month, self.day);
        }
        if (tabId == "monthView"){
            self.openMonthView(self.year, self.month, self.day);
        }
    },
    function createEvPopup(self, bl, year, month, day, timeSt) {
        if (self.popup){
            removeElement(self.popup);
            delete self.popup; 
            self.popped=null; 
        }

        self.popped = bl;

        var ok     = INPUT({'type': 'button', 'name': 'Create', 'value':'Create'});
        var cancel = INPUT({'type': 'button', 'name': 'Cancel', 'value':'Cancel'});

        timeOptions =[];
        
        for(var r=0; r < 48; r++){
            var tString = r%2 ? r/2-0.5 +':30' : r/2 + ':00'; 
            timeOptions.push( tString);
        }

        self.popup = DIV({'class': 'mkCalEnt'}, 
            STRONG({}, "Create Entry"), 
            BR(), BR(), 

            DIV({'style': 'margin-left: 1em'}, 
                TABLE({}, TBODY({}, 
                    TR({}, 
                        TD({}, "Description: "),
                        TD({}, INPUT({'type': 'text', 'id': 'caldescr', 'name':'description'}))
                    ),
                    TR({}, 
                        TD({}, "Start: "), 
                        TD({}, SELECT({'name':'st', 'id':'stTime'}, map(function(ts){return OPTION({'value': ts}, ts)}, timeOptions)))
                    ),
                    TR({}, 
                        TD({}, "End: "), 
                        TD({}, SELECT({'name':'end', 'id':'edTime'}, map(function(ts){return OPTION({'value': ts}, ts)}, timeOptions)))
                    ),
                    TR({},
                        TD({}, BR(), ok),
                        TD({}, BR(), cancel)
                    )
                ))
            )
        );

        var cpos = elementPosition(bl);
        var scrollOffset = self.nodeById("weekViewScrollArea").scrollTop;
        cpos.y += scrollOffset;
        setElementPosition(self.popup, cpos);

        self.nodeById('popupModal').appendChild(self.popup);
        // Select defaults
        getElement('stTime').selectedIndex = timeSt[0]; 
        getElement('edTime').selectedIndex = timeSt[0]+1; 
 
        connect(ok, 'onclick', function(e){
            self.callRemote('addEntry', 
                getElement('caldescr').value, 
                year, month, day, 
                getElement('stTime').value, 
                getElement('edTime').value
        ).addCallback(function(e){
                removeElement(self.popup);
                self.popped = null;
                delete self.popup; 
                self.selTab(self.currentTab);
                return null;
            });
        });

        connect(cancel, 'onclick', function(e){
            removeElement(self.popup);
            self.popped = null;
            delete self.popup; 
            return null;
        });
    },
    function openMonthView(self, year, mont, day){
        showElement(self.nodeById('monthViewPane'));

        var trows = []

        forEach(self.monthFlow, function(r){
            var trow = []

            forEach(r, function(e){
                trow.push(TD({'valign':'top', 'height': '100px'}, 
                    DIV({'class': 'mvTdTop'}, e[1] + ' '+ self.months[e[0]]), 
                    DIV({'id':e[0]+'-'+e[1]}, " ")
                ));
            });
            trows.push(TR({}, trow));
        });

        var nID = self.nodeById('monthTable'); 

        // Construct dom
        swapDOM(nID, DIV({'id':nID.id}, 
            TABLE({'width': '100%'}, TBODY({}, 
                TR({}, 
                    map(function(day){
                        return TD({'align':'center'}, day)
                    }, self.days)
                ), 
                trows
            ))
        ));
    }, 
    function openWeekView(self, year, month, day){
        showElement(self.nodeById('weekViewPane'));
        var rows = [];
        var rows2 = [];

        var nodeId = self.nodeById('weekViewCont').id;

        var cells = [TD({'width': '60px', 'style': 'padding-right: 10px;'}, ' ')];

        var cellWidth = Math.floor((getElement(nodeId).offsetWidth - 120) / 7) + 'px';


        var dayCnt = 0;
        forEach(self.weekFlow, function(seg){
            var d = seg[1];
            var m = seg[0];
            cells.push(
                TD( {
                        'width': cellWidth, 
                        'style': 'border: 1px solid #ffcf6c; background:#ffcf6c;', 
                        'align':'center'
                    }, 
                    self.days[dayCnt] + ' ' + d + '/' + (m+1)
                )
            );

            dayCnt++;
        });


        rows.push(TR({}, cells));

        // Construct our day columns 


        for(var r=0; r < 48; r++){
            var drow = [TD({'width': '60px', 'align':'right', 'style': 'padding-right: 10px;'},
                r%2 ? r/2-0.5+':30' : r/2+':00'
            )];

            forEach(self.weekFlow, function(seg){
                var bl = TD({'width': cellWidth, 'height': '20px', 'style': 'border:1px solid #ffcf6c;', 'id': r+'-'+seg[0]+'-'+seg[1]}, '');
                connect(bl, 'onclick', function(e){
                    var parts = bl.id.split('-');
                    var tDelta = parseInt(parts[0]);
                    // Make a time tupple for this cell
                    var time = tDelta%2 ? [tDelta, tDelta/2-0.5, 30] : [tDelta, tDelta/2, 0];
                    var m = parts[1];
                    var d = parts[2];
                    self.createEvPopup(bl, year, m, d, time);
                });
                drow.push(bl);
            });

            rows2.push(TR({}, drow));
        };

        var drId = self.nodeById('dayRow').id;
        swapDOM(drId, DIV({'id': drId},
            TABLE({'cellspacing':'0'},
                TBODY({}, rows)
            )
        ));

        var wvcId = self.nodeById('weekViewCont').id;
        swapDOM(wvcId, DIV({'id': wvcId},
            TABLE({'cellspacing': '0'},
                TBODY({}, rows2)
            )
        ));

        var sa = self.nodeById("weekViewScrollArea");
        var blInc = sa.scrollHeight/48
        // Current time
        var now = new Date();
        sa.scrollTop = now.getHours() *2 * blInc;

        // Get records
        var calEntries = [];
        self.callRemote('getEntries', year, self.weekFlow).addCallback(function(results){
            var scrollOffset = self.nodeById("weekViewScrollArea").scrollTop;
            forEach(results, function(entry){
                var blS = entry[3] + '-' + entry[2] + '-' + entry[1];
                var blE = entry[4] + '-' + entry[2] + '-' + entry[1];
                var tc = getElement(blS); 
                var te = getElement(blE);

                var cpos = elementPosition(tc);
                cpos.y += scrollOffset;
                var epos = elementPosition(te);
                epos.y += scrollOffset;
 
                var width = tc.offsetWidth -10; 
                var height = (epos.y - cpos.y) +tc.offsetHeight - 10; 
                
                var node = DIV({'class': 'calEnt', 'style': 'height: '+height+'px; width:'+width+'px', 'id': entry[5]},  
                    entry[0], BR(), "From " +entry[6] +" to "+entry[7]
                );

                connect(node, 'onclick', function(ev){
                    var e = ev.event();
                    if (!e) var e = window.event;

                    e.cancelBubble = true;

                    if (e.stopPropagation) e.stopPropagation();

                    return false;
                });
                
                appendChildNodes(tc, DIV({'class':'calWrap'}, node));
            });
        });

    },
    function renderMonth(self, year, month, day){
        var construct = [
            TR({},
                map(function(e){return TD({}, e);}, self.daysSmall)
            )
        ];

        var first = self.getWeekday(year, month, 1);
        var mo = self.getDays(year, month);
        var previousMonth = (month>0) ? month-1 : 11;
        var moprev = self.getDays(year, previousMonth);

        var buffer = 0;
        if (first > 0) {
            // buffer
            buffer = moprev - first;
        }

        var tcnt = 0;
        var inMonth = 0;
        var mFinish = false;

        self.monthFlow = []; // Stores how this month looks for month view 

        for(var dstep=0; dstep<6; dstep++){
            var cs = [];
            var weekFlow = []; // Stores how this week looks in day-month pairs - read by later view systems

            if (inMonth>1){
                mFinish = true;
            }
            
            var hasToday = false;

            for (var wd=0; wd<7; wd++){
                var bgcol = '#fff';
                if (wd==0 ||wd==6) {
                    bgcol = '#eee';
                }

                if ((buffer>0) && (buffer<moprev)){
                    buffer++; 
                    var val = buffer;
                }
                else {  
                    if (inMonth<1){
                        inMonth=1;
                    }
                    tcnt++;
                    if (tcnt > mo) {
                        inMonth=2;
                        tcnt = 1;
                    }
                    var val = tcnt;
                }

                if (inMonth==1){
                    if (day && (tcnt == day)) {
                        hasToday = true;
                        bgcol = '#ffcf6c';
                        cs.push(TD({'style':'background:'+bgcol}, STRONG({}, val)));
                    }
                    else {
                        cs.push(TD({'style':'background:'+bgcol}, STRONG({}, val)));
                    };
                    var thisMonth = month;
                }
                else{
                    cs.push(TD({'style':'background:'+bgcol}, val));

                    var thisMonth = (inMonth==0) ? previousMonth : ((month==11) ? 0 : month+1);
                };

                weekFlow.push([thisMonth, val]);
            };
            if (!mFinish) {
                self.monthFlow.push(weekFlow);
                construct.push(TR({'class':'calMinRow'}, cs));
            };
            if (hasToday){
                self.weekFlow = weekFlow;
            };
        };

        swapDOM('sideCalDate', DIV({}, STRONG({}, self.months[month] + " " + year)));

        swapDOM('sideCal', TABLE({'cellspacing':'0','cellpadding':'2px', 'id':'sideCal'}, 
            TBODY({}, 
                construct
            )
        ));

    },
    function getWeekday(self, year, month, day){
        var myDate = new Date();
        myDate.setFullYear(year, month, day); 
        return myDate.getDay();
    },
    function getDays(self, year, month){
        var myDate = new Date();
        myDate.setFullYear(year, month, 1);
        var days = self.mdays[month];
        // February
        if (month == 1) {
            if (((year%4 == 0) && (year%100 != 0)) || (year%400==0)) { 
                // Leap year
                days++;
            }
        }
        return days
    }
);
