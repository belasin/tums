// import Nevow.Athena

mailbox.PS = Nevow.Athena.Widget.subclass('mailbox.PS');

mailbox.PS.methods(
    function nodeInserted(self){
        var loc = document.location.toString();
        
        self.attachments = []

        self.callRemote('getUsername').addCallback(function(user){
            self.fileLoc = '/mail/mdata/'+user+'/'
        });

        if (loc.search(/##/) > 0) {
            var mail = loc.split('##')[1];

            self.callRemote('getIMail', mail).addCallback(function(mresp){
                var sub = mresp[0];
                var mail = mresp[1];
                var ckDocument = CKEDITOR.instances.mailcomp;
                ckDocument.setData(mail);
                getElement('subject').value = sub;
                // Update attachments as well for inline images
            });
        }

        CKEDITOR.replace('mailcomp', {
            customConfig : '/scripts/editor_config.js'
        });
        connect('sendBtn', 'onclick', function(e){
            var ckDocument = CKEDITOR.instances.mailcomp;
            var to = getElement('to').value;
            var subject = getElement('subject').value;
            
            self.callRemote('sendMail', to, subject, ckDocument.getData()).addCallback(function(r){
                alert(r);
            });
            return false;
        });

        connect('fileFile', 'onchange', function(e){
            var fileField = getElement('fileFile');
            self.fileFile = fileField.value;
            if (self.fileFile.search(/\\/) > 0) {
                var ar = self.fileFile.split('\\');
                self.fileFile = ar[ar.length-1];
            }
            showElement('uploading');
            hideElement('fileUpload');
            document.fileUpload.submit();
        });

        connect('fileFrame', 'onload', function(e){
            var iframe = getElement('fileFrame').contentWindow.document;
            var code = iframe.getElementById('rcode').innerHTML;
            hideElement('uploading');
            showElement('fileUpload');

            if (code != "Complete"){
                alert(code);
                return false;
            }

            var hashKey = getElement('hashKey').value;
            self.fileName = self.fileLoc+hashKey+self.fileFile;

            self.attachments.push([self.fileName, self.fileFile]);

            self.callRemote('updateAttachments', hashKey+self.fileFile, self.fileFile);

            showElement("attachList");
            swapDOM("attachList", DIV({'id':'attachList'},
                map(function(elm) {
                    return [elm[1], BR()];
                }, self.attachments)
            ));

            if (getElement('inline').checked){
                var ckDocument = CKEDITOR.instances.mailcomp;
                ckDocument.insertHtml('<img src="'+self.fileName+'" alt="'+self.fileFile+'"/>');
            }

            getElement('inline').checked = false;
        });

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
