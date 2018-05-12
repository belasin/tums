tableWidget = Nevow.Athena.Widget.subclass('tableWidget');

tableWidget.methods(
    function nodeInserted(self){
        self.callRemote('getTableName').addCallback(function(tname){
            self.tableName = tname;
            self.renderTable();
        });
    }, 

    function renderTable(self){
        self.callRemote('getData').addCallback(function(tdata){
    
            var thStruct = THEAD({}, 
                TR({}, 
                    map(function(c){ return TH({}, c);}, tdata[1])
                )
            );

            var rows = [];

            // Reconstruct our table rows including id numbers
            var i = 0;

            forEach(tdata[0], function(row){
                bg = "#ddd";
                if (i%2){
                    bg = "#eee";
                } 

                rows.push(
                    TR({'style': 'background:'+bg, 'id': self.tableName + 'Row-' + (i+1)}, 
                        map(function(cell){
                            cellObject =  TD({}, "");
                            cellObject.innerHTML = cell;
                            return cellObject;
                        }, row)
                    )
                );
                i++;
            });


            var tbStruct = TBODY({}, rows);

            swapDOM(self.tableName, TABLE({'class': 'listing', 'id': self.tableName}, 
                thStruct,
                tbStruct
            ));

            $(getElement(self.tableName)).tableDnD({
                onDragClass: "tableRowDrag",
                onDrop: function(table, row) {
                    var rows = table.tBodies[0].rows;
                    var rowOrder = [];
                    for (var i=0; i<rows.length; i++) {
                        rowOrder.push(parseInt(rows[i].id.replace(self.tableName + 'Row-', ''))-1);
                    }
                    self.callRemote('tableChanged', rowOrder)
                }
            });
        });
    }
);
