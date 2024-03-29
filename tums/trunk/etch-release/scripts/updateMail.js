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

function activationClick(){
    hideElement('enterNewLicense');
    showElement('ActivateCode');
}

function newLicenseClick(){
    hideElement('enterNewLicense');
    showElement('NewLicense');
}

createTable = function(headings, rows, id){
    var tab = TABLE({'id': id, 'cellspacing':'0', 'class':'listing'},
        THEAD({},
            TR({},
                map(function(elm){
                    return TH({}, elm)
                }, headings)
            )
        ),
        TBODY({},
            map(function(row){
                return TR({}, map(function(col){
                    return TD({}, col);
                }, row))
            }, rows)
        )
    );
    return tab;
}

updateMail = function () {
    try {
        var myIn = getElement('editForm-userSettings-uid').value;
    }
    catch (dc) {
        var myIn = getElement('addForm-userSettings-uid').value;
    }   
    cont = getElement('emailAd').firstChild.data;
    dom = cont.split('@')[1];
    getElement('emailAd').firstChild.data = myIn +'@'+ dom;
};

showDomains = function() {
    try {
        showElement(getElement('editForm-tumsUser-field').childNodes[1]);
    } catch(dc){}

    try {
        showElement(getElement('addForm-tumsUser-field').childNodes[1]);
    } catch(dc){}
}

waitForSubmit = function() {
    swapDOM('addUser-action-submit', DIV({'style':'text-size:1.2em; color:#222;'}, STRONG({}, "Please wait while the key is generated")));
}

populateRule = function(dst, dstport, src, srcport) {
    getElement('allowRange-sip').value = src;
    getElement('allowRange-sport').value = srcport;
    getElement('allowRange-dip').value = dst;
    getElement('allowRange-dport').value = dstport;
    // Switch to add rule page
    tabSwitcher('panelRules');
}

function mutateSubmit(){
    try {
        var elms = getElementsByTagAndClassName('div', 'actions');
        forEach(elms, function (el) {
            var subButton = el.firstChild;
            var id = subButton.id;
            if (id.indexOf('wizard')==0) {
                var newButton = INPUT({'type':'image', 'src':'/images/next.png', 'alt':'Submit', 'id':id});
                try {
                    // Insert a Back button or fail silently 
                    var prev = parseInt(id[6]) - 1;
                    if (prev < 1) {
                        // If this is the first page take us to the server root.
                        var newLoc="/"
                    } else {
                        var newLoc ="/Wizard/" + prev + "/"
                    }
                    el.insertBefore(INPUT({'type':'image', 'action':'back', 
                        'src':'/images/back.png', 'alt':'Submit', 'onclick':'location="'+newLoc+'"; return false;'}), subButton);
                } catch(dontCare) {}
            }
            else {
                var newButton = INPUT({'type':'image', 'src':'/images/sub-up.png', 'alt':'Submit', 'id':id});
            }
            swapDOM(subButton, newButton);
        });
    } catch(dontCare) {}

    try {
        var id = "selectProfile-action-submit";
        //swapDOM(id, INPUT({'type':'image', 'src':'/images/button-switch.png', 'alt':'Submit', 'id':id}));
    }
    catch (dc) {}
}

var displayedForwards = 10;
var displayedAliases = 10;

function rollForwards(){
    var i = 0;
    var name="";
    for (i=1; i<10; i++){
        try {
            name = 'addForm-mailSettings-mailForwardingAddress'+i+'-field';
            p = getElement(name);
            hideElement(name);
            if (p) {
                displayedForwards--;
            }
        } catch(d) {alert("not add");}

        try {
            name = 'editForm-mailSettings-mailForwardingAddress'+i+'-field';
            thisone = getElement(name);
            if (thisone.childNodes[1].firstChild.value==""){
                hideElement(name);
                displayedForwards--;
            }
        } catch(d) {}
    }
    for (i=1; i<10; i++){
        try{
            name = 'addForm-mailSettings-mailAlternateAddress'+i+'-field';
            p = getElement(name);
            hideElement(getElement(name));
            if (p) {
                displayedAliases--;
            }
        } catch(d) {}
        try {
            name = 'editForm-mailSettings-mailAlternateAddress'+i+'-field';
            thisone = getElement(name);
            if (thisone.childNodes[1].firstChild.value==""){
                hideElement(name);
                displayedAliases--;
            }
        } catch(d) {}
    }
}

function addForward(){
    if (displayedForwards < 10){
        displayedForwards++;
        try {
            name = 'addForm-mailSettings-mailForwardingAddress'+displayedForwards+'-field';
            showElement(name);
        } catch (d){}
        try {
            name = 'editForm-mailSettings-mailForwardingAddress'+displayedForwards+'-field';
            showElement(name);
        } catch (d){}
    }
}

function addAlias(){
    if (displayedAliases < 10){
        displayedAliases++;
        try {
        name = 'addForm-mailSettings-mailAlternateAddress'+displayedAliases+'-field';
        showElement(name);
        } catch (d){}
        try {
            name = 'editForm-mailSettings-mailAlternateAddress'+displayedAliases+'-field';
            showElement(name);
        } catch (d){}
    }
}

function checkAdmin(){
    try {
        if (getElement('editForm-tumsAdmin').checked){
            hideElement('editForm-tumsUser-field');
            hideElement('addDom');
        } 
        else {
            showElement('editForm-tumsUser-field');
            showElement('addDom');
        }
    } catch(dc) {}

    try {
        if (getElement('addForm-tumsAdmin').checked){
            hideElement('addForm-tumsUser-field');
            hideElement('addDom');
        }
        else {
            showElement('addForm-tumsUser-field');
            showElement('addDom');
        }
    } catch(dc) {}
}

atatchEvents = function() {
    try {
        connect('editForm-userSettings-uid', 'onkeyup', updateMail);
        connect
    }
    catch(dontCare) { }

    try {
        connect('addForm-userSettings-uid', 'onkeyup', updateMail);
    }
    catch(dontCare) { }

    try {
        connect('addDom', 'onclick', showDomains);
    }
    catch(dontCare) { }

    try { 
        connect('addUser', 'onsubmit', waitForSubmit);
    }
    catch(dontCare) { }

    try {
        connect('editForm-tumsAdmin', 'onclick', checkAdmin);
    }
    catch(dontCare) {}

    try {
        connect('addForm-tumsAdmin', 'onclick', checkAdmin);
    }
    catch(dontCare) {}
};

loadJs = function(scriptsrc) {
    var head= document.getElementsByTagName('head')[0];
    var script= document.createElement('script');
    script.type= 'text/javascript';
    script.src= scriptsrc;
    head.appendChild(script);
};

loadMochikit = function(){
    loadJs('/scripts/MochiKit/MochiKit.js');
};

loadPlotkit = function() {
    loadJs('/scripts/plotkit/excanvas.js');
    loadJs('/scripts/plotkit/Base.js');
    loadJs('/scripts/plotkit/Layout.js');
    loadJs('/scripts/plotkit/Canvas.js');
    loadJs('/scripts/plotkit/SweetCanvas.js');
};

addLoadEvent(function() {
    rollForwards();
    loadJs('/scripts/blocks.js');
    loadJs('/scripts/BaloonTooltips.js');
    loadJs('/scripts/tableSort.js');
    var loc = document.location.toString();
    if (loc.search(/Status/) > 0) {
        loadPlotkit();
    };
    loadJs('/scripts/pageBootstrap.js');
});

