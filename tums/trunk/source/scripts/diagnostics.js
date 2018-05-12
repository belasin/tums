// import Nevow.Athena

diagnostics.PS = Nevow.Athena.Widget.subclass('diagnostics.PS');

diagnostics.PS.methods(
    function nodeInserted(self){
        self.pingTest();
        self.lanTest();
        var ld = self.callRemote('bandwidthTest');
        ld.addCallback(function(r){
            // Test is done;
        });
        ld.addErrback(function(r){});
    },
    function lanTest(self){
        var ld = self.callRemote('lanTest');
        ld.addCallback(function(res){
            var tabBod = map(function(d){
                return TR({'style':'text-align:center'}, TD({}, d[0]), TD({}, d[1]), TD({}, d[2]), TD({}, d[3]));
            }, res);
            swapDOM(self.nodeById("localComp"), TABLE({'cellspacing':'0'}, 
                THEAD({},
                    TR({},
                        TH({}, "IP"),
                        TH({}, "Hostname"),
                        TH({}, "MAC"),
                        TH({}, "Brand name")
                    )
                ),
                TBODY({},
                    tabBod
                )
            ));
            hideElement(self.nodeById('Loading'));
        });
        ld.addErrback(function(r){});
    },
    function localSpeed(self, speed){
        swapDOM(self.nodeById('localSpeed'), DIV({}, speed));
    },
    function intlSpeed(self, speed){
        swapDOM(self.nodeById('intlSpeed'), DIV({}, speed));
    },
           
    function pingTest(self){
        var ld = self.callRemote('pingTest');
        ld.addCallback(function(res){
            var intlLatency = res[0];
            var intlPl = res[1];
            var localLatency = res[2];
            var localPl = res[3];
            swapDOM(self.nodeById('localLatency'), DIV({}, localLatency, "ms"));
            swapDOM(self.nodeById('localPl'), DIV({}, localPl, "%"));
            swapDOM(self.nodeById('intlLatency'), DIV({}, intlLatency, "ms"));
            swapDOM(self.nodeById('intlPl'), DIV({}, intlPl, "%"));
        });
        ld.addErrback(function(r){});
    }
);
