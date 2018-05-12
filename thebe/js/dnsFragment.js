// import Nevow.Athena

dnsFragment.js = Nevow.Athena.Widget.subclass('dnsFragment.js');

dnsFragment.js.methods(
    function nodeInserted(self) {
        self.startup();
    },

    function addDomain(self){
        selectedDom = self.nodeById('dominput').value;

        self.domain = selectedDom;

        hideElement(self.nodeById('DomainList'));
        hideElement(self.nodeById('domautocomplete'));
        showElement(self.nodeById('lod'));

        var fnd = false;
        forEach(self.domains, function(i){
            if (i == selectedDom){
                fnd = true
            }
        });
        if (fnd) {
            alert("Domain already exists!");
        }
        else {
            self.domains.push(selectedDom);
            self.callRemote('createNewZone', selectedDom).addCallback(function(res) {
                // Refresh the view 
                self.openDomain();
            });
        }
    },
    function addRecord(self){
        self.resetDialog(false);
    },
    function addMXRecord(self){
        self.resetDialog(true);
    },
    function resetDialog(self, mx){
        if (mx) {
            dlg = "addMXRecord";
        }
        else {
            dlg = "addRecord";
        }
        // Reset the form preemptivly
        self.nodeById(dlg+'Form').reset();
        var handleSubmit = function() {
            frm = self.nodeById(dlg+'Form');

            if (frm.prio){
                data = frm.prio.value + ' ' + frm.data.value;
                type = 'MX';
            }
            else {
                data = frm.data.value;
                type = frm.type.value;
            }
            data = {
                'type': type,
                'data': data,
                'ttl':  frm.ttl.value,
                'domain': frm.dom.value,
                'primary': self.domain
            };
            frm.reset();
            self.dialog1.hide();
            // Do stuff with the form data here
            self.callRemote('storeNewRecord', data).addCallback(function(res) {
                // Refresh the view 
                self.openDomain();
            });
        };

        var handleCancel = function() {
                this.cancel();
        };

        var handleSuccess = function(o) {
                var response = o.responseText;
                response = response.split("<!")[0];
                //document.getElementById("resp").innerHTML = response;
        };

        var handleFailure = function(o) {
                alert("Submission failed: " + o.status);
        };

        // Instantiate the Dialog
        self.dialog1 = new YAHOO.widget.Dialog(self.nodeById(dlg), { 
            width : "300px",
            fixedcenter : true, 
            visible : false,
            constraintoviewport : true,
            buttons : [ 
                { text:"Submit", handler:handleSubmit, isDefault:true },
                { text:"Cancel", handler:handleCancel } 
            ]
        });

        self.dialog1.callback = { 
            success: handleSuccess,                                   
            failure: handleFailure 
        }; 

        self.dialog1.render();
        showElement(self.nodeById(dlg));
        self.dialog1.show();
    },
    function backToList(self){
        hideElement(self.nodeById('editPannel'));
        showElement(self.nodeById('domautocomplete'));
        showElement(self.nodeById('domContainer'));
        showElement(self.nodeById('DomainList'));
        hideElement(self.nodeById('lod'));
        //self.updateDomList();
    },
    function openDomain(self){
        //self.selectedDom = self.nodeById('dominput').value;
        //self.domain = self.selectedDom;
        selectedDom = self.domain;
        //self.nodeById('dominput').value = "";
        //hideElement(self.nodeById('buttonPannel'));
        hideElement(self.nodeById('domautocomplete'));

        var addRecButton = new YAHOO.widget.Button(self.nodeById("addRec")); 
        addRecButton.on("click", function(p_ev){self.addRecord()});

        var backListButton = new YAHOO.widget.Button(self.nodeById("backList")); 
        backListButton.on("click", function(p_ev){self.backToList()});

        var addMXRecButton = new YAHOO.widget.Button(self.nodeById("addMXRec")); 
        addMXRecButton.on("click", function(p_ev){self.addMXRecord()});
        
        // Set the domain name
        swapDOM(self.nodeById('domName'), H3({'id':'athenaid:1-domName'}, "Domain " + selectedDom));

        self.callRemote('getDomainDetail', selectedDom).addCallback(function (result) {
            hideElement(self.nodeById('domContainer'));
            showElement(self.nodeById('editPannel'));

            //editor:"dropdown", sortable:true, editorOptions:{dropdownOptions:['A', 'AAAA', 'CNAME', 'MX', 'NS']}},
            var myColumnDefs = [ 
                {key:"domain", sortable:true}, 
                {key:"type", sortable:true}, 
                {key:"data", editor:"textbox", sortable:true}
            ]; 

            this.myDataSource = new YAHOO.util.DataSource(result); 
            this.myDataSource.responseType = YAHOO.util.DataSource.TYPE_JSARRAY; 
            this.myDataSource.responseSchema = { 
                fields: ["domain", "type", "data"] 
            }; 
       
            this.myDataTable = new YAHOO.widget.DataTable(self.nodeById('cellediting'), myColumnDefs, this.myDataSource); 

            // Set up editing flow 
            this.highlightEditableCell = function(oArgs) { 
                var elCell = oArgs.target; 
                if(YAHOO.util.Dom.hasClass(elCell, "yui-dt-editable")) { 
                    this.highlightCell(elCell); 
                } 
            }; 

            this.onContextMenuClick = function(p_sType, p_aArgs, p_myDataTable) { 
                var task = p_aArgs[1]; 
                if(task) { 
                    // Extract which TR element triggered the context menu 
                    var elRow = this.contextEventTarget; 
                    elRow = p_myDataTable.getTrEl(elRow); 
       
                    if(elRow) { 
                        switch(task.index) { 
                            case 0:     // Delete row upon confirmation 
                                if(confirm("Are you sure you want to delete record " + 
                                    elRow.cells[0].innerHTML + " (" + 
                                    elRow.cells[2].innerHTML + ")?")) { 
                                    // Delete item.
                                    rowData = {'domain': elRow.cells[0].innerHTML, 'data': elRow.cells[2].innerHTML, 'type': elRow.cells[1].innerHTML};
                                    self.callRemote('changeDomainDetail', rowData, {}).addCallback(function(ret) {
                                        if (ret!=true){
                                            alert('Failure to update record');
                                        }
                                         
                                        //p_myDataTable.deleteRow(elRow); 
                                        swapDOM('athenaid:1-cellediting', DIV({'id':'athenaid:1-cellediting'},''));
                                        self.openDomain();

                                    });
                                } 
                        } 
                    } 
                } 
                return false;
            };

            this.myContextMenu = new YAHOO.widget.ContextMenu("mycontextmenu",
                {trigger:this.myDataTable.getTbodyEl()});
            this.myContextMenu.addItem("Delete Item");
            this.myContextMenu.render(self.nodeById('cellediting'));
            this.myContextMenu.clickEvent.subscribe(this.onContextMenuClick, this.myDataTable);

            this.myDataTable.subscribe("cellMouseoverEvent", this.highlightEditableCell); 
            this.myDataTable.subscribe("cellMouseoutEvent", this.myDataTable.onEventUnhighlightCell); 
            this.myDataTable.subscribe("cellClickEvent", this.myDataTable.onEventShowCellEditor); 
       
            // Hook into custom event to customize save-flow of "radio" editor 
            this.myDataTable.subscribe("editorUpdateEvent", function(oArgs) { 
                if(oArgs.editor.column.key === "active") { 
                    this.saveCellEditor(); 
                } 
            }); 
            this.myDataTable.subscribe("editorBlurEvent", function(oArgs) { 
                this.cancelCellEditor(); 
            }); 

            this.myDataTable.subscribe("editorShowEvent", function(oArgs) {
                // Save the current row detail
                r = oArgs.editor.record.getData();
                self.lastEditorData = {'domain':r.domain, 'data':r.data, 'type': r.type};
                // Save the current cell contents
                c = oArgs.editor.cell.textContent;
                self.firstCellData = c;
            });

            this.myDataTable.subscribe("editorSaveEvent", function(oArgs) {
                var dir = function (obj) { var keys = []; for (var key in obj) { keys.push(key); } return keys.join(', '); }
                r = oArgs.editor.record.getData();
                c = oArgs.editor.cell.textContent;

                if (self.firstCellData != c){ // Check the cell actualy changed..
                    self.callRemote('changeDomainDetail', self.lastEditorData, {
                        'domain':r.domain, 'data':r.data, 'type': r.type
                    }).addCallback(function(ret) {
                        if (ret!=true){
                            alert('Failure to update record');
                        }
                    });
                }
            });
        });

        self.callRemote('getDomainDetailMX', selectedDom).addCallback(function (result) {
            showElement(self.nodeById('editPannel'));

            //editor:"dropdown", sortable:true, editorOptions:{dropdownOptions:['A', 'AAAA', 'CNAME', 'MX', 'NS']}},
            var myColumnDefs = [ 
                {key:"domain", sortable:true}, 
                {key:"type", sortable:true}, 
                {key:"priority", editor:"textbox", sortable:true},
                {key:"host", editor:"textbox", sortable:true}
            ]; 

            this.myDataSource2 = new YAHOO.util.DataSource(result); 
            this.myDataSource2.responseType = YAHOO.util.DataSource.TYPE_JSARRAY; 
            this.myDataSource2.responseSchema = { 
                fields: ["domain", "type", "priority", "host"] 
            }; 
       
            this.myDataTable2 = new YAHOO.widget.DataTable(self.nodeById('celleditingMX'), myColumnDefs, this.myDataSource2); 

            // Set up editing flow 
            this.highlightEditableCell = function(oArgs) { 
                var elCell = oArgs.target; 
                if(YAHOO.util.Dom.hasClass(elCell, "yui-dt-editable")) { 
                    this.highlightCell(elCell); 
                } 
            }; 

            this.onContextMenuClick2 = function(p_sType, p_aArgs, p_myDataTable) { 
                var task = p_aArgs[1]; 
                if(task) { 
                    // Extract which TR element triggered the context menu 
                    var elRow = this.contextEventTarget; 
                    elRow = p_myDataTable.getTrEl(elRow); 
       
                    if(elRow) { 
                        switch(task.index) { 
                            case 0:     // Delete row upon confirmation 
                                if(confirm("Are you sure you want to delete record " + 
                                    elRow.cells[0].innerHTML + " (" + 
                                    elRow.cells[3].innerHTML + ")?")) 
                                { 

                                    rowData = {
                                        'domain': elRow.cells[0].innerHTML, 
                                        'host': elRow.cells[3].innerHTML, 
                                        'type': elRow.cells[1].innerHTML,
                                        'priority': elRow.cells[2].innerHTML
                                    };
                                    self.callRemote('changeDomainDetail', rowData, {}).addCallback(function(ret) {
                                        if (ret!=true){
                                            alert('Failure to update record');
                                        }
                                    });
 
                                    p_myDataTable.deleteRow(elRow); 
                                    //self.
                                } 
                        } 
                    } 
                } 
            };

            this.myContextMenu2 = new YAHOO.widget.ContextMenu("mycontextmenu2",
                {trigger:this.myDataTable2.getTbodyEl()});
            this.myContextMenu2.addItem("Delete Item");
            this.myContextMenu2.render(self.nodeById('celleditingMX'));
            this.myContextMenu2.clickEvent.subscribe(this.onContextMenuClick2, this.myDataTable2);

            this.myDataTable2.subscribe("cellMouseoverEvent", this.highlightEditableCell); 
            this.myDataTable2.subscribe("cellMouseoutEvent", this.myDataTable.onEventUnhighlightCell); 
            this.myDataTable2.subscribe("cellClickEvent", this.myDataTable.onEventShowCellEditor); 
       
            // Hook into custom event to customize save-flow of "radio" editor 
            this.myDataTable2.subscribe("editorUpdateEvent", function(oArgs) { 
                if(oArgs.editor.column.key === "active") { 
                    this.saveCellEditor(); 
                } 
            }); 
            this.myDataTable2.subscribe("editorBlurEvent", function(oArgs) { 
                this.cancelCellEditor(); 
            }); 

            this.myDataTable2.subscribe("editorShowEvent", function(oArgs) {
                // Save the current row detail
                r = oArgs.editor.record.getData();
                self.lastEditorData = {'domain':r.domain, 'priority':r.priority, 'host':r.host, 'type': r.type};
                // Save the current cell contents
                c = oArgs.editor.cell.textContent;
                self.firstCellData = c;
            });

            this.myDataTable2.subscribe("editorSaveEvent", function(oArgs) {
                r = oArgs.editor.record.getData();
                c = oArgs.editor.cell.textContent;

                if (self.firstCellData != c){ // Check the cell actualy changed..
                    self.callRemote('changeDomainDetail', self.lastEditorData, {
                        'domain':r.domain, 'priority':r.priority, 'host':r.host, 'type': r.type
                    }).addCallback(function(ret) {
                        if (ret!=true){
                            alert('Failure to update record');
                        }
                    });
                }
            });
        });
    },
    function updateDomList(self){
        swapDOM(self.nodeById('DomainList'), 
            DIV({'id':'athenaid:1-DomainList'}, 
                TABLE({'id':'TdomainTable', 'class':'sortable', 'cellspacing':'0'}, 
                    THEAD({'background':"/images/gradMB.png"},
                        TR({},
                            TH({'colformat':'istr'}, 'Domain'),
                            TH({}, '')
                        )
                    ),                        
                    TBODY({}, 
                        map(function(i){
                            var thisA = A({'href':'#'}, i);
                            connect(thisA, 'onclick', function(){
                                self.domain = i;
                                self.openDomain();
                                hideElement(self.nodeById('DomainList'));
                                showElement(self.nodeById('lod'));
                                return null;
                            });

                            var thisDel = A({'href':'#'}, 'Delete');
                            connect(thisDel, 'onclick', function(){
                                self.domain = i;

                                hideElement(self.nodeById('DomainList'));
                                hideElement(self.nodeById('domautocomplete'));
                                showElement(self.nodeById('lod'));

                                self.callRemote('deleteRecord', i).addCallback(function(r){
                                    self.showDomains();
                                });
                                return null;
                            });

                            return TR({}, TD({}, thisA), TD({}, thisDel));

                        }, self.sdomains)
                    )
                )
            )
        );

        /*var sorter = new TableSorter();
        sorter.init(getElement('TdomainTable'));*/
    },
    function showDomains(self){
        hideElement(self.nodeById('lod'));
        //showElement(self.nodeById('buttonPannel'));
        showElement(self.nodeById('domautocomplete'));

        self.sdomains = self.domains;
        self.updateDomList();

        /*
        var addButton = new YAHOO.widget.Button(self.nodeById("addButton")); 
        var openButton = new YAHOO.widget.Button(self.nodeById("openButton")); 

        addButton.on("click", function(p_ev){self.addDomain()});
        openButton.on("click", function(p_ev){self.openDomain()});

        YAHOO.example.ACJSArray = new function() { 
            // Instantiate first JS Array DataSource
            this.oACDS = new YAHOO.widget.DS_JSArray(self.domains);

            // Instantiate first AutoComplete
            this.oAutoComp = new YAHOO.widget.AutoComplete(self.nodeById('dominput'),self.nodeById('domcontainer'), this.oACDS);
            this.oAutoComp.prehighlightClassName = "yui-ac-prehighlight";
            this.oAutoComp.typeAhead = true;
            this.oAutoComp.useShadow = true;
            this.oAutoComp.minQueryLength = 0;
            this.oAutoComp.textboxFocusEvent.subscribe(function(){
                var sInputValue = self.nodeById('dominput').value;
                if(sInputValue.length === 0) {
                    var oSelf = this;
                    setTimeout(function(){oSelf.sendQuery(sInputValue);},0);
                }
            });
        }
        */

        var addButton = new YAHOO.widget.Button(self.nodeById("addDomain")); 
        addButton.on("click", function(p_ev){self.addDomain()});
        hideElement(self.nodeById('addContainer'));

        var searcher = self.nodeById('dominput');
        connect(searcher, 'onkeyup', function(){
            searchString = self.nodeById('dominput').value;
            // Update our search list
            self.sdomains = [];
            ms = 0;
            forEach(self.domains, function(el){
                if (el.match(searchString)){
                    self.sdomains.push(el);
                    ms++;
                }
            });
            if ((ms == 0) && searchString!=''){
                // No matches so allow adding new domain
                showElement(self.nodeById('addContainer'));
            }
            else {
                showElement(self.nodeById('addContainer'));
            }
            self.updateDomList();
        });
    },
    function startup(self) {
        self.callRemote('getDomains').addCallback(function (result) {
            self.domains = result
            self.showDomains();
        });
    }
)
