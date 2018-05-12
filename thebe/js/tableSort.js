/*
    TableSorter
    Copyright (C) Thusa Business Support 2008

    A sorted table implementation. 
*/

TableSorter = function () {
    this.thead = null;
    this.tbody = null;
    this.columns = [];
    this.rows = [];
    this.sortState = {};
    this.sortkey = 0;
};

mouseOverFunc = function () {
    addElementClass(this, "over");
};

mouseOutFunc = function () {
    removeElementClass(this, "over");
};

ignoreEvent = function (ev) {
    if (ev && ev.preventDefault) {
        ev.preventDefault();
        ev.stopPropagation();
    } else if (typeof(event) != 'undefined') {
        event.cancelBubble = false;
        event.returnValue = false;
    }
};


update(TableSorter.prototype, {

    "init": function (table) {
        this.thead = table.getElementsByTagName('thead')[0];
        var cols = this.thead.getElementsByTagName('th');
        for (var i = 0; i < cols.length; i++) {
            var node = cols[i];
            var attr = null;
            try {
                attr = node.getAttribute("colformat");
            } catch (err) {
                // pass
            }
            var o = node.childNodes;
            this.columns.push({
                "format": attr,
                "element": node,
                "proto": node.cloneNode(true)
            });
        }
        this.tbody = table.getElementsByTagName('tbody')[0];
        var rows = this.tbody.getElementsByTagName('tr');
        for (var i = 0; i < rows.length; i++) {
            // every cell
            var row = rows[i];
            var cols = row.getElementsByTagName('td');
            var rowData = [];
            for (var j = 0; j < cols.length; j++) {
                var cell = cols[j];
                var obj = scrapeText(cell);
                switch (this.columns[j].format) {
                    case 'isodate':
                        obj = isoDate(obj);
                        break;
                    case 'cdate':
                        bits = obj.split(' ');
                        month = {
                            'Jan':'01', 'Feb':'02', 'Mar':'03', 'Apr':'04',
                            'May':'05', 'Jun':'06', 'Jul':'07', 'Aug':'08',
                            'Sep':'09', 'Oct':'10', 'Nov':'11', 'Dec':'12'
                        }
                        if (bits.length == 2) {
                            // is just month/year

                            tdate = bits[1] + '-' + month[bits[0]] + '-01';
                            obj = isoDate(tdate);
                            break;
                        }
                        if (bits.length == 3) {
                            // is day, month and year
                            tdate = bits[2] + '-' + month[bits[1]] + '-' + bits[0];
                            obj = isoDate(tdate);
                            break;
                        }
                        obj= isoDate(obj);
                        break;
                    case 'str':
                        break;
                    case 'istr':
                        obj = obj.toLowerCase();
                        break;
                    case 'int':
                        mul = 1
                        if (obj.search(/M/)>0) {
                            mul = 1024*1024;
                        }
                        if (obj.search(/K/)>0) {
                            mul = 1024;
                        }
                        if (obj.search(/G/)>0) {
                            mul = 1024*1024*1024;
                        }
                        obj = parseFloat(obj) * mul;
                        break;
                    // cases for numbers, etc. could be here
                    default:
                        break;
                }
                rowData.push(obj);
            }
            rowData.row = row.cloneNode(true);
            this.rows.push(rowData);
        }
        this.drawSortedRows(this.sortkey, true, false);

    },

    "onSortClick": function (name) {
        return method(this, function () {
            var order = this.sortState[name];
            if (order == null) {
                order = true;
            } else if (name == this.sortkey) {
                order = !order;
            }
            this.drawSortedRows(name, order, true);
        });
    },

    "drawSortedRows": function (key, forward, clicked) {
        this.sortkey = key;
        var cmp = (forward ? keyComparator : reverseKeyComparator);
        this.rows.sort(cmp(key));
        this.sortState[key] = forward;
        var newBody = TBODY(null, map(itemgetter("row"), this.rows));
        this.tbody = swapDOM(this.tbody, newBody);
        for (var i = 0; i < this.columns.length; i++) {
            var col = this.columns[i];
            var node = col.proto.cloneNode(true);
            col.element.onclick = null;
            col.element.onmousedown = null;
            col.element.onmouseover = null;
            col.element.onmouseout = null;
            node.onclick = this.onSortClick(i);
            node.onmousedown = ignoreEvent;
            node.onmouseover = mouseOverFunc;
            node.onmouseout = mouseOutFunc;
            if (key == i) {
                // \u2193 is down arrow, \u2191 is up arrow
                // forward sorts mean the rows get bigger going down
                var arrow = (forward ? "\u2193" : "\u2191");
                // add the character to the column header
                node.appendChild(SPAN(null, arrow));
                if (clicked) {
                    node.onmouseover();
                }
            }
 
            // swap in the new th
            col.element = swapDOM(col.element, node);
        }
    }
});

addLoadEvent(function() {
    blocks = getElementsByTagAndClassName('TABLE', 'sortable');
    forEach(blocks, function(block){
        var sorter = new TableSorter();
        sorter.init(block);
    });
});
