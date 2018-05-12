addLoadEvent(function() {
    var nodes = getElementsByTagAndClassName('a', 'treeNode');
    forEach(nodes, function(node){
        var nodeFolder = node.className.split(' ')[1];
        connect(node, 'onclick', function(q){
            window.location = '/mail/Mail/##' + nodeFolder;
        });
    });
});
