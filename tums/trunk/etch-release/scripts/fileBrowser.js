// import Nevow.Athena

fileBrowser.PS = Nevow.Athena.Widget.subclass('fileBrowser.PS');

fileBrowser.PS.methods(
    function cutFile(self, path){
        self.callRemote('cutFile', path).addCallback(function(d){
            return true;
        });
        return false;
    },
    function copyFile(self, path){
        self.callRemote('copyFile', path).addCallback(function(d){
            return true;
        });
        return false;
    },
    function renameFile(self, path){
         self.callRemote('renameFile', path).addCallback(function(d){
            return true;
         });
         return false;
    },
    function pasteFile(self){
        self.callRemote('pasteFile').addCallback(function(d){
            return true;
        });
        return false;
    },
    function deleteFile(self){
        var l = confirm('Are you sure you wish to delete this file?');
        if (l) {
            self.callRemote('deleteFile').addCallback(function(d){
                return true;
            });
        }
        return false;
    },
    function updateDetailsPane(self, path, node){
        self.nodeById('fName').innerHTML = node;
        self.callRemote('statPath', path+'/'+node).addCallback(function(d){
            self.nodeById('fType').innerHTML = d[0];
            self.nodeById('fSize').innerHTML = d[1] + "KB";
            self.nodeById('fMod').innerHTML = d[2];
            self.nodeById('fCreate').innerHTML = d[3];

            actionBoard = self.nodeById('actionBoard');
        
            cut     = A({'href':'#', 'onclick':'return false;'}, "Cut");
            copy    = A({'href':'#', 'onclick':'return false;'}, "Copy");
            paste   = A({'href':'#', 'onclick':'return false;'}, "Paste");
            rename  = A({'href':'#', 'onclick':'return false;'}, "Rename");
            deletef = A({'href':'#', 'onclick':'return false;'}, "Delete");

            swapDOM(actionBoard, DIV({'id':'athenaid:1-actionBoard'},
                cut, BR({}),
                copy, BR({}),
                paste, BR({}),
                rename, BR({}),
                deletef, BR({})
            ));
            connect(cut,     'onclick', function(e){
                self.cutFile(path+'/'+node)
            });
            connect(copy,    'onclick', function(e){
                self.copyFile(path+'/'+node);
            });
            connect(paste,   'onclick', function(e){
                self.pasteFile();
                self.updatePane(path);
            });
            connect(rename,  'onclick', function(e){
                self.renameFile(path+'/'+node);
            });
            connect(deletef, 'onclick', function(e){
                self.deleteFile();
                self.updatePane(path);
            });
        });
        return false;
    },
    function rowSelect(self, e, path, node){
        thisRow = e.src();
        forEach(getElementsByTagAndClassName('tr', 'listRow'), function(elm){
            elm.style.background = "#ffffff";
        });
        thisRow.style.background = "#bbbbbb";
        self.updateDetailsPane(path, node);
    },
    function treeCompress(self, e, path, node){
        // Rerenders the node and clear visible subnodes
        mpath = "";
        if (path) {
            mpath = path.replace(/\//g, '');
        };
        clickable = A({'href':'#', 'onclick':'return false;'}, node);
        newNode = DIV({'id':'folder'+mpath+node, 'class':'treeBranch'}, 
            IMG({'src':'/images/treefolder.png'}),
            clickable
        );
        mySubNode = e.src().parentNode;
        swapDOM(mySubNode, newNode);
        connect(clickable, 'onclick', function(e){
            self.treeExpand(e, path, node);
        });
    },
    function treeExpand(self, e, path, node){
        // Clear the onclick event stack and connect a new event 
        disconnectAll(e.src(), 'onclick');
        connect(e.src(), 'onclick', function(ne){
            self.treeCompress(e, path, node);
            return false;
        });

        // Render my sub folders.
        if (path){
            self.renderFolders(path+'/'+node);
        }
        else {
            self.renderFolders(node);
        }
        return false;
    },
    function addEvents(self){
        var loc = getElement('location');

        connect(loc, 'onchange', function(e){
            self.nodeById('myTree').innerHTML = "";
            self.nodeById('tableNode').innerHTML = "";
            self.callRemote('changeLocation', e.src().value);
        });
    },
    function renderFolders(self, path){
        if (path) {
            c = self.callRemote('getFolders', path);
            mpath = path.replace(/\//g, '');
        } 
        else {
            c = self.callRemote('getFolders');
            path = ""
            mpath = "";
        }

        c.addCallback(function(d){
            if (path) {
                treeRoot = getElement('folder'+mpath);
            }
            else {
                treeRoot = self.nodeById('myTree');
            }
            forEach(d, function(node){
                clickable = A({'href':'#', 'onclick':'return false;'}, node);
                newNode = DIV({'id':'folder'+mpath+node, 'class':'treeBranch'}, 
                    IMG({'src':'/images/treefolder.png'}),
                    clickable
                );
                connect(clickable, 'onclick', function(e){
                    self.treeExpand(e, path, node);
                });
                treeRoot.appendChild(newNode);
            });
        });
    },
    function updatePane(self, path){
        c = self.callRemote('getFiles', path);

        c.addCallback(function(d){
            folders = d[0];
            files = d[1];
            flist = TABLE({'id':'athenaid:1-tableNode', 'class':'fileListing', 'width':'100%', 'cellspacing':'0'},
                THEAD({},
                    TR({},
                        TH({'width':'18px'}, ''),
                        TH({'align':'left'}, 'Name'),
                        TH({'align':'left'}, 'Size')
                    )
                ),
                TBODY({},
                    imap(function(item){
                        var name = item[1];
                        var size = item[2];
                        var row = TR({'class':'listRow'},
                            TD({}, IMG({'src':'/images/treefolder.png'})),
                            TD({}, name),
                            TD({}, "")
                        );
                        var createConnectMethod = function(path, name){
                            return function(e){
                                self.rowSelect(e, path, name);
                            };
                        };
                        connect(row, 'onclick', name, createConnectMethod(path, name));
                        return row;
                    }, folders),
                    imap(function(item){
                        var name = item[1];
                        var size = item[2];
                        var row = TR({'class':'listRow'},
                            TD({}, ""),
                            TD({}, name),
                            TD({}, size + "KB")
                        );
                        var createConnectMethod = function(path, name){
                            return function(e){
                                self.rowSelect(e, path, name);
                            };
                        };
                        connect(row, 'onclick', name, createConnectMethod(path, name));
                        return row;
                    }, files)
                )
            );
            tableNode = self.nodeById('tableNode');
            swapDOM(self.nodeById('tableNode'), flist);
        });
    }
);
