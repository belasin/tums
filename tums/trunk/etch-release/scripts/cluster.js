// import Nevow.Athena

cluster.PS = Nevow.Athena.Widget.subclass('cluster.PS');

cluster.PS.methods(
    function nodeInserted(self){
        self.updateTable([['Searching...', '', '', '']]);

        self.callRemote('initialTable').addCallback(function(res){
            self.updateTable(res);
        });
            
        self.lanTest();
    },
    function updateTable(self, res){
        newres = map(function(el){
            if (el[0] == "Searching...") return el
            return [el[0], el[1], el[2], A({'href': 'Configure/'+el[3]+'/'}, 'Edit')];
        }, res);

        swapDOM(self.nodeById('servers'), createTable(['Server', 'Topology', 'Status', ''], newres, 'athenaid:1-servers'))
    },
    function lanTest(self){
        var ld = self.callRemote('lanTest');
        ld.addCallback(function(res){
            hideElement(self.nodeById('Loading'));

            self.updateTable(res);
        });
    }
);
