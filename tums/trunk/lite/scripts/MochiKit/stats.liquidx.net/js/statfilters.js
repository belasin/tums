StatFilters = {};

StatFilters.makelink = function(url, label, title) {
    if (!label)
        label = url.substring(0, url.length);
    if (!title)
        title = url.substring(0, url.length);

    return A({'href':url, 'title':title}, label);
};

StatFilters.stripProtocol = function(url) {
    return url.replace(/[a-z]*\:\/\//, '');
};

StatFilters.ellipsis = function(text, maxlen/*=16*/) {
    if (!maxlen)
        maxlen = 16;

    if (text.length > maxlen)
        return text.substring(0, maxlen) + '...';
    else
        return text;
};

StatFilters.swap = function(table) {
    return map(function (x) { return [x[1], x[0]] }, table);
};

StatFilters.slugify = function(s, maxlen) {
    // copied from django
    s = s.replace(/[^-A-Z0-9\s]/gi, '');  // remove unneeded chars
    s = s.replace(/^\s+|\s+$/g, ''); // trim leading/trailing spaces
    s = s.replace(/\s+/g, '-');      // convert spaces to hyphens
    s = s.toLowerCase();             // convert to lowercase
    return s.substring(0, maxlen ? maxlen : 30);
};

StatFilters.groupByDomain = function(table) {
    // [count, domain, [children]]
    var groups = new Array();
    var rowCount = table.length;
    var domain_re = /http\:\/\/([^\/]+)\//;
    for (var i = 0; i < rowCount; i++) {
        var row = table[i];
        var domain = domain_re.exec(row[1]);
        if (domain) {
            domain = domain[1].replace(/^www\./,'');
            if (groups[domain]) {
                groups[domain][0] += parseInt(row[0]);
                groups[domain][2].push([parseInt(row[0]), row[1]]);
            }
            else {
                groups[domain] = [parseInt(row[0]), domain, [[parseInt(row[0]), row[1]]]];
            }
        }
    }

    var newTable = map(itemgetter(1), items(groups));
    newTable.sort(function (a, b) { return b[0] -  a[0] });
    return newTable;
};

StatFilters.groupByMonth = function(table) {
    var groups = new Array();
    var rowCount = table.length;
    for (var i = 0; i < rowCount; i++) {
        var dateString = parseInt(table[i][1].substring(0, 6));
        if (groups[dateString])
            groups[dateString] += parseInt(table[i][0]);
        else
            groups[dateString] = parseInt(table[i][0]);
    }
    
    var newTable = items(groups);
    newTable.sort(function(a, b) { return compare(a[0], b[0]) });
    newTable = StatFilters.swap(newTable);
    return newTable;
};

StatFilters.toInt = function(table) {
    var newTable =  map(function(row){return [parseInt(row[0]), parseInt(row[1])]}, table);
    newTable.sort(function(a,b) { return compare(a[1], b[1]) });
    return newTable;
};


StatFilters.greaterCountThan = function(min, table) {
    var newTable = new Array();
    for (var i = 0; i < table.length; i++) {
        if (table[i][0] > min) {
            newTable.push(table[i]);
        }
    }
    return newTable;
};

StatFilters.limitRows = function(max, table) {
    return table.slice(0, max);
}

StatFilters.daysInMonth = {
    1: 31, 2: 28, 3: 31, 4: 30,
    5: 31, 6: 30, 7: 31, 8: 31,
    9: 30, 10: 31, 11: 30, 12: 31
};

StatFilters.averagePerMonth = function(rowdata) {
    var month = "" + rowdata[1];
    if (month.charAt(4) == '0') {
        month = parseInt(month.charAt(5));
    }
    else {
        month = parseInt(month.substring(4, 6));
    }
    //log(rowdata[1], month);
    return [twoDigitFloat(rowdata[0]/StatFilters.daysInMonth[month]), rowdata[1]];
};
