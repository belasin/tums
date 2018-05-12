// import Nevow.Athena

diagnostics.PS = Nevow.Athena.Widget.subclass('diagnostics.PS');

diagnostics.PS.methods(
    function nodeInserted(self){
        connect(self.nodeById("mailTest-action-submit"), 'onclick', function (el) {
            var formCont = self.nodeById('mailTest-address').value;
            var ld = self.callRemote('testAddress', formCont); 
            ld.addCallback(function(r){
                var res = self.nodeById('mailTest-results');
                swapDOM(res, DIV({'id':'athenaid:1-mailTest-results'}, H3({}, 'Test Results'), PRE({}, r)));
                
            });
            return false;
        });
    }
);
