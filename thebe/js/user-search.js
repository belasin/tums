addLoadEvent(function() {
    var searcher = getElement('searchInput');
    connect(searcher, 'onkeyup', function(){
        var searchString = getElement('searchInput').value;
        var tableRows = getElement("TdomainTable").childNodes[1].childNodes;

        forEach(tableRows, function(tr){
            var cont = tr.firstChild.firstChild.innerHTML;
            if (cont.match(searchString)){  
                try {
                    tr.style.display = 'table-row';
                }
                catch (fuckingMicrosoftNeedToLearnHowTheFuckToProgram){
                    showElement(tr);
                }
            }
            else {
                hideElement(tr);
            }
        });
    });
});

