partEditor.E = Nevow.Athena.Widget.subclass('partEditor.E');

partEditor.E.methods(
    function nodeInserted(self) {
        self.updatePartitions();
    },
    function deletePartition(self, device, partnum){
        var newTab = DIV({'id':'athenaid:1-partTable'}, "Loading...");
        swapDOM(self.nodeById('partTable'), newTab);

        self.callRemote('deletePartition', device, partnum).addCallback(function(res){
            self.updatePartitions();
        });
    },
    function addForm(self, disk, partnum, sec_start, sec_end, size){
        var pane = DIV({'id':'athenaid:1-partTable'}, "")

        var form = FORM({'id': 'addForm'},
            TABLE({},
                THEAD({}),
                TBODY({},
                    TR({},
                        TD({}, "Partition size (MB)"),
                        TD({}, INPUT({'id': 'psize', 'name': 'size', 'type':'text', 'value':Math.round(size)}))
                    ),
                    TR({}, 
                        TD({}, "Partition type"), 
                        TD({}, SELECT({'id': 'ptype', 'name': 'type'}, 
                            OPTION({}, 'Swap'), 
                            OPTION({'selected':'selected'}, 'Vulani'),
                            OPTION({}, 'Vulani RAID')
                        ))
                    )
                )
            )
        );
         
        pane.appendChild(form);
        
        var cancel = INPUT({'name': 'cancel', 'type': 'button', 'value': 'cancel'});

        var create = INPUT({'name': 'create', 'type': 'button', 'value': 'create'});

        connect(cancel, 'onclick', function(e){
            self.updatePartitions()
        });

        connect(create, 'onclick', function(e){

            var nsize = getElement('psize').value;
            if (nsize == size){
                var nsize = 0;
            } else {
                var nsize = nsize;
            }

            var type = getElement('ptype').value;

            var pnum = self.partList[disk]; 

            if ((pnum == 0) || (pnum > 2)){
                var num = 0;
            }
            else {
                var num = partnum;
            }
            
            var newTab = DIV({'id':'athenaid:1-partTable'}, "Loading...");
            swapDOM(self.nodeById('partTable'), newTab);
            self.callRemote('createPartition', disk, partnum+1, nsize, type).addCallback(function(res){
                self.updatePartitions();
            });
        });

        pane.appendChild(DIV({}, 
            create,
            cancel
        ));

        // Stick it in the DOM somewhere...
        swapDOM(self.nodeById('partTable'), pane);
        hideElement('nextButton');
        return null;
    },
    function autoPart(self, disk){
        return self.callRemote('autoPart', disk).addCallback(function(res){
            // Refresh the window
            var sURL = unescape(window.location.pathname);
            window.location.href = sURL;
            return false;
        });
    },
    function updatePartitions(self){
        self.partList = {};
        showElement('nextButton');
        self.callRemote('getPartitions').addCallback(function(result){
            // Initialise new partition table block
            var newTab = DIV({'id':'athenaid:1-partTable'}, "");
            swapDOM(self.nodeById('partTable'), newTab);
            var table = self.nodeById('partTable');

            // break out some of our results
            var drives = result[1];
            var parts = result[0];

            var barColours = {
                '-1': '#ccffc8',
                '82': '#ffbaec',  // Linux swap
                '83': '#ffc400',  // Linux
                '7' : '#87baff',  // NTFS
                'c' : '#00ccff',  // Fat32
            };
            
            var cnt = 0;
            forEach(parts, function(diskElm){
                cnt++; 
                var disk = diskElm[0];
                var diskParts = diskElm[1];

                self.partList[disk] = 0;

                var diskTable = TABLE({'cellspacing':'0','width':'90%'}, 
                    THEAD({}),
                    TBODY({}, 
                        TR({'id':'bar'+cnt}, "")
                    )
                );
                table.appendChild(diskTable);
                
                var diskBar = getElement('bar'+cnt);
                var size = drives[disk][0]/1000

                diskBar.appendChild(
                    TD({}, DIV({'style':'width:5em'},
                        STRONG({},'Drive '+cnt), BR({}), 
                        disk, BR({}),
                        size.toFixed(2), "GB"
                    ))
                );

                forEach(diskParts, function(partElm){
                    // Delete partition
                    var deleteButton = A({'href': '#', 'style':'font-family:arial,verdana,helvetica,sans-serif;'}, " Delete");
                    connect(deleteButton, 'onclick', function(ev){  
                        return self.deletePartition(disk, partElm[6]);
                    });
                    
                    if (partElm[3] == "-1"){
                        // Create button for freespace
                        var createButton = A({'href': '#', 'style': 'font-family:arial,verdana,helvetica,sans-serif;'}, " Create");
                        connect(createButton, 'onclick', function(ev){
                            return self.addForm(disk, partElm[6], partElm[1], partElm[2], partElm[0]);
                        });
                    } 
                    else {
                        self.partList[disk] += 1;
                        var createButton = "";
                    }
                    
                    // Construct partition cell
                    var w = (partElm[0] / drives[disk][0])*100;
                    var d = DIV({'style':'width:10em; height:6.5em;'},
                        partElm[5]," - ", deleteButton,
                        DIV({'style': 'margin-left: 10px'},
                            "Size: "+ partElm[0].toFixed(2)+ "MB",
                            BR({}),
                            "Type: "+ partElm[4]
                        ),
                        createButton
                    );

                    // Find the colour assigned to this partition type
                    if (barColours[partElm[3]]){
                        var colour = barColours[partElm[3]];
                    }
                    else {
                        var colour = "#FF0000";
                    }

                    diskBar.appendChild(
                        TD({'style':'background:'+colour, 'width': w+'%', 'valign':'top'}, d)
                    );
                });
                
                var defaultPartitioning =  A({'href':'#', 'style':'font-family:arial,verdana,helvetica,sans-serif;'}, "Default Partitioning");

                connect(defaultPartitioning, 'onclick', function(ev){
                    var conf = confirm('Are you sure you want to auto-partition this disk? This will permenantly remove any partitions on the drive');
                    if (conf) {
                        var newTab = DIV({'id':'athenaid:1-partTable'}, "Loading...");
                        swapDOM(self.nodeById('partTable'), newTab);
                        return self.autoPart(disk);
                    }
                    return false;
                });
                diskBar.appendChild(
                    TD({'valign': 'middle'}, defaultPartitioning)
                );

           });
        });
    }
);

