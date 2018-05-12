// import Nevow.Athena

mailbox.PS = Nevow.Athena.Widget.subclass('mailbox.PS');

mailbox.PS.methods(
    function nodeInserted(self){
        var loc = document.location.toString();
        if (loc.search(/##/) > 0) {
            self.folder = loc.split('##')[1]; // Always start on inbox
        }
        else {
            self.folder = "INBOX"; // Always start on inbox
        }
        self.pageNum = 1;
    
        self.loadMailbox();
        self.connectTree();

        connect('athenaid:1-prev', 'onclick', function(e){
            self.pageNum--;
            self.loadMailbox();
        });
        connect('athenaid:1-next', 'onclick', function(e){
            self.pageNum++;
            self.loadMailbox();
        });

        connect('deletesel', 'onclick', function(e){
            var forDelete =[];
            forEach(self.idns, function(idn){
                var realId = idn.split('-')[1];
                var chk = getElement(idn).checked; 
                if(chk){
                    forDelete.push(realId);
                }
            });

            self.callRemote('deleteMail', self.folder, forDelete).addCallback(function(r){
                self.loadMailbox();
            });
        });
    }, 
    function loadMailbox(self){
        self.callRemote('getMail', self.folder, self.pageNum).addCallback(function(res){
            var mails = res[1];
            var cnt = res[0];

            var mstart = ((self.pageNum-1)*25) +1;
            var mend = mstart + 24; 
            
            getElement('athenaid:1-next').style.display="inline";
            getElement('athenaid:1-prev').style.display="inline";

            if (mend >= cnt) {
                mend = cnt;
                hideElement('athenaid:1-next');
            }

            swapDOM('athenaid:1-count', SPAN({'id':'athenaid:1-count'}, ' ' + mstart + ' - ' + mend + ' of ' + cnt + ' '));

            var pane = self.nodeById('mailWindow');
            var paneId = pane.id;

            self.idns = [];

            swapDOM(pane, DIV({'id':paneId},    
                TABLE({'id': 'mailListTable', 'cellspacing':'0', 'cellpadding':'0'}, 
                    THEAD({}, 
                        TR({},
                            TH({}, ""),
                            TH({}, "From"),
                            TH({}, "Subject"),
                            TH({}, "Date")
                        )
                    ),
                    TBODY({}, 
                        map(function(mail){
                            var rowclass = "readMail";
                            if (mail[4]){
                                rowclass = "unreadMail";
                            }

                            var idn = "c-"+mail[0].toString();

                            self.idns.push(idn);
                            var sub = TD({'class':'mailSubjectCol'}, mail[2]);

                            var row = TR({'class':rowclass, 'style':'cursor: pointer'},
                                TD({'style':'width:0em'}, INPUT({'type':"checkbox", 'name':idn, 'id':idn})),
                                TD({}, mail[1]), 
                                sub,
                                TD({}, mail[3])
                            );

                            connect(sub, 'onclick', function(e){
                                window.location="/mail/View/"+self.folder+"/"+mail[0].toString()+"/";
                            });

                            return row;
                        }, mails)
                    )
                )
            ));
        });
    },
    function switchFolder(self, folder){
        self.folder = folder;
        self.loadMailbox();
    },
    function connectTree(self){
        // Connects our tree up to some useful listeners
        
        var nodes = getElementsByTagAndClassName('a', 'treeNode');
        forEach(nodes, function(node){
            var nodeFolder = node.className.split(' ')[1];
            connect(node, 'onclick', function(q){
                self.switchFolder(nodeFolder)
            });
        });
    }
);
