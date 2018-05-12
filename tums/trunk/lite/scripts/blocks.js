function Get_Cookie(name) {
   var start = document.cookie.indexOf(name+"=");
   var len = start+name.length+1;
   if ((!start) && (name != document.cookie.substring(0,name.length))) return null;
   if (start == -1) return null;
   var end = document.cookie.indexOf(";",len);
   if (end == -1) end = document.cookie.length;
   return unescape(document.cookie.substring(len,end));
}

function Set_Cookie(name,value,expires,path) {
    expires = expires * 60*60*24*1000;
    var today = new Date();
    var expires_date = new Date( today.getTime() + (expires) );
    var cookieString = name + "=" +escape(value) +
       ( (expires) ? ";expires=" + expires_date.toGMTString() : "") +
       ( (path) ? ";path=" + path : "");
    document.cookie = cookieString;
}


function rollEvent(eve){
    var block = eve.parentNode.parentNode.parentNode; // We know this...
    var title = block.childNodes[1].childNodes[0].childNodes[1].data; 
    var node = block.childNodes[2]; // we know this as well...
    hideElement(node);
    swapDOM(eve, IMG({'src':'/images/maximise.png', 'onclick':'unrollEvent(this);'}));
    Set_Cookie(title, "rolled", 500);
}

function unrollEvent(eve){
    var block = eve.parentNode.parentNode.parentNode; // We know this...
    var title = block.childNodes[1].childNodes[0].childNodes[1].data;
    var node = block.childNodes[2]; // we know this as well.
    node.style.display="block";
    swapDOM(eve, IMG({'src':'/images/minimise.png', 'onclick':'rollEvent(this);'}));
    Set_Cookie(title, "unrolled", 500);
}

addLoadEvent(function() {
    blocks = getElementsByTagAndClassName('div', 'roundedBlock');
    forEach(blocks, function(block){
        /* Fetch the paragraph content */
        var title = block.childNodes[0];
        hideElement(title);
        var titleText = title.innerHTML;
        var para = block.childNodes[1];
        var newPara = DIV({},"");
        newPara.innerHTML = para.innerHTML;

        var roller = IMG({'src':'/images/minimise.png', 'onclick':'rollEvent(this);'})

        /* Define our top and bottom */
        var topRow = DIV({'class':'blockTop'},
            DIV({'class':'hardLeft'},
                IMG({'src':'/images/topleft.png'}),
                titleText
            ),
            DIV({'class':'hardRight'},
                roller,
                IMG({'src':'/images/topright.png'})
            )
        );
        var bottomRow = DIV({'class': 'blockBottom'},
            DIV({'class':'hardLeft'},
                IMG({'src':'/images/bottomleft.png'})
            ),
            DIV({'class':'hardRight'},
                IMG({'src':'/images/bottomright.png'})
            )
        );

        /* Reconstruct the block */
        block.insertBefore(topRow, para);
        appendChildNodes(block, bottomRow);

        /* Replace the paragraph with a table nesting it */
        var newDom = TABLE({'cellspacing':'100', 'cellpadding':'0', 'width':'100%', 'border':'1'},
            TBODY({},
                TR({}, 
                    TD({'class':'blockLeft'} ),
                    TD({'class':'blockContent'}, newPara),
                    TD({'class':'blockRight'})
                )
            )
        );
        var newnew = "<table cellspacing=\"0\" cellpadding=\"0\" width=\"100%\" border=\"0\"><tr>";
        newnew += "<td width=\"5px\" class=\"blockLeft\"><img src=\"/images/left.png\"/></td>";
        newnew += "<td class=\"blockContent\">"+newPara.innerHTML+"</td>";
        newnew += "<td width=\"5px\" class=\"blockRight\"><img src=\"/images/right.png\"/></td>";
        newnew += "</tr></table>";
        para.innerHTML = newnew;
        
        // Check cookies
        if (Get_Cookie(title.firstChild.data) == "rolled"){
            // Roll up this block
            rollEvent(roller);
        }
    });

});

