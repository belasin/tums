try {
    container = getElement('editForm-tumsUser-field');
    swapDOM(container.firstChild, A({'id':'addDom','href':"#"}, "Add domain rights"));
    hideElement(container.childNodes[1]);
}
catch (dontCare) {}

try {
    container = getElement('addForm-tumsUser-field');
    swapDOM(container.firstChild, A({'id':'addDom','href':"#"}, "Add domain rights"));
    hideElement(container.childNodes[1]);
}
catch (dontCare) {}

mutateSubmit();
atatchEvents();
enableTooltips();
startBlocks();
sortTables();

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
    var expires = expires * 60*60*24*1000;
    var today = new Date();
    var expires_date = new Date( today.getTime() + (expires) );
    var cookieString = name + "=" +escape(value) +
       ( (expires) ? ";expires=" + expires_date.toGMTString() : "") +
       ( (path) ? ";path=" + path : "");
    document.cookie = cookieString;
}

// On the DNS Edit page, make sure submitting a new record
// redirects the user to the Records tab

var loc = document.location.toString();
if (loc.search(/DNS/) > 0) {
    connect('addRecord', 'onsubmit', function(){
        tabSwitcherA('panelDNSRecs');
        return true;
    });
}

// Assert mutual exclusivity on certain firewall inputs

if (loc.search(/Firewall/) > 0 && !(loc.search(/Ajax/) > 0)){
    connect('allowRange-sport', 'onkeyup', function(){
        var dport = getElement('allowRange-dport-field').childNodes[2];
        var dportin = getElement('allowRange-dport');
        var origText = "Destination port OR other protocol subtype (Blank for any)";
        if (getElement('allowRange-sport').value == ""){
            dportin.disabled = false;
            dport.innerHTML = origText;
        }
        else {
            dportin.disabled = true;
            dportin.value = "";
            dport.innerHTML = "<strong>Disabled</strong>. You may not specify both a source and destination port at the same time. Since source ports are usualy random for a known destination, your attempted rule will make no sense";
        }
    });

    connect('allowRange-dport', 'onkeyup', function(){
        var sport = getElement('allowRange-sport-field').childNodes[2];
        var sportin = getElement('allowRange-sport');
        var origText = "Source port (Blank for Any)";
        if (getElement('allowRange-dport').value == ""){
            sportin.disabled = false;
            sport.innerHTML = origText;
        }
        else {
            sportin.disabled = true;
            sportin.value = "";
            sport.innerHTML = "<strong>Disabled</strong>. You may not specify both a source and destination port at the same time. Since source ports are usualy random for a known destination port, your attempted rule will would make no sense.";
        }
    });

    //Define that Source IP's must not have an all option in the dropdown box for szone
    connect('allowRange-sip', 'onkeyup', function() {
        var szone = getElement('allowRange-szone');
        if(getElement('allowRange-sip').value != "") {
            //Disable the 'all' option for szone
            for (i=0;i<szone.length;i++)
            {
                if(szone.options[i].value == 'all') {
                    szone.options[i].disabled = true;
                    if(szone.options[i].selected) {
                        szone.selectedIndex = 0;
                    }
                }
            }
        } else {
            for (i=0;i<szone.length;i++)
            {
                if(szone.options[i].value == 'all') {
                    szone.options[i].disabled = false;
                }
            }
        }
    });
    
    //Define that Dest IP's must not have an all option in the dropdown box for dzone
    connect('allowRange-dip', 'onkeyup', function() {
        var dzone = getElement('allowRange-dzone');
        if(getElement('allowRange-dip').value != "") {
            //Disable the 'all' option for dzone
            for (i=0;i<dzone.length;i++)
            {
                if(dzone.options[i].value == 'all') {
                    dzone.options[i].disabled = true;
                    if(dzone.options[i].selected) {
                        dzone.selectedIndex = 0;
                    }
                }
            }
        } else {
            for (i=0;i<dzone.length;i++)
            {
                if(dzone.options[i].value == 'all') {
                    dzone.options[i].disabled = false;
                }
            }
        }
    });

}

hideVpnTunOpt = function () {
    // Add setting triggers to Tunnel configuration page
    if (loc.search(/VPN/) > 0) {
        hideElement('addTun-username-field');
        hideElement('addTun-password-field');

        hideElement('addTun-proto-field');
        hideElement('addTun-CA-field');
        hideElement('addTun-crt-field');
        hideElement('addTun-key-field');
    }
}

// Add setting triggers to Tunnel configuration page
if (loc.search(/VPN/) > 0) {
    hideVpnTunOpt();
    showElement('addTun-proto-field');
    showElement('addTun-CA-field');
    showElement('addTun-crt-field');
    showElement('addTun-key-field');

    connect('addTun-type', 'onchange', function(){
        hideVpnTunOpt();
        var val = getElement('addTun-type').value;
        if ((val == "l2tp") || (val == "pptp")) {
            showElement('addTun-username-field');
            showElement('addTun-password-field');
        }
        else if (val == "openvpn") {
            showElement('addTun-proto-field');
            showElement('addTun-CA-field');
            showElement('addTun-crt-field');
            showElement('addTun-key-field');
        }            
    });
}

hideBackupOpt = function () {  
    // Add setting triggers to Backup configuration page
    if (loc.search(/Backup/) > 0) {
        hideElement('addSet-usbDev-field');
        hideElement('addSet-smbHost-field');
        hideElement('addSet-smbShare-field');
        hideElement('addSet-smbUser-field');
        hideElement('addSet-smbPass-field');
        hideElement('addSet-pathPath-field');
    }
};

showBackupOpt = function () {
    var val = getElement('addSet-type').value;
    if (val == "usb") {
        showElement('addSet-usbDev-field');
    }
    else if (val == "smb") {
        showElement('addSet-smbHost-field');
        showElement('addSet-smbShare-field');
        showElement('addSet-smbUser-field');
        showElement('addSet-smbPass-field');
    }
    else if (val == "path") {
        showElement('addSet-pathPath-field');
    }
};

// Add setting triggers to Backup configuration page
if (loc.search(/Backup/) > 0) {
    hideBackupOpt();
    showBackupOpt();
    connect('addSet-type', 'onchange', function(){
        hideBackupOpt();
        showBackupOpt();
    });
}

hideSnomOpt = function () {
    // Hide snom options 
    for (var i=0; i<=12; i++){
        hideElement('addHandset-Snom320fkeys'+i+'-field');
    }

    hideElement('addHandset-Snom320MAC-field');
}

showSnomOpt = function () {
    // Hide snom options 
    for (var i=0; i<=12; i++){
        showElement('addHandset-Snom320fkeys'+i+'-field');
    }

    showElement('addHandset-Snom320MAC-field');
}

// Add JS for Asterisk VoIP page
if (loc.search(/VoIP/) > 0) {
    hideSnomOpt();
    connect('addHandset-phonetype', 'onchange', function(){
        var val = getElement('addHandset-phonetype').value;
        hideSnomOpt();

        if (val == "Snom 320"){
            showSnomOpt();
        }
    });
}

// Assert time distance on proxy pages
if (loc.search(/Squid/) > 0) {
    checkProxyTimeValues = function(){
        var sport = getElement('addTime-to-field').childNodes[2];
        var cont = getElement('addTime-to').value.split(':');
        var cont2 = getElement('addTime-from').value.split(':');

        // Make a big number from what we expect to be a time in the fields
        // and make sure they are correct.
        try {
            var v1 = ((parseFloat(cont[0])*100)+parseFloat(cont[1]));
            var v2 = ((parseFloat(cont2[0])*100)+parseFloat(cont2[1]));
            if (v1 < v2){
                // User is being crazy
                sport.innerHTML = "Ending time (24 hour format), <span style=\"font-size:1.5em;color:#f00\"><strong>must be later than the starting time</strong></span> and must not overlap midnight";
                hideElement('addTime-action-submit');
            }
            else {
                // All is well. 
                sport.innerHTML = "Ending time (24 hour format), must be later than the starting time and must not overlap midnight";
                showElement('addTime-action-submit');
            }
        }
        catch (dontCare) {}
    }
    connect('addTime-to', 'onkeyup', checkProxyTimeValues);
    connect('addTime-from', 'onkeyup', checkProxyTimeValues);
}

// PPP stuff

function recheckPPP(){
    var ppplist = getElementsByTagAndClassName("tbody", null, parent=getElement('pageContent'));

    forEach(ppplist[0].childNodes, function (elm){
        var segs = elm.childNodes;
        var unit = segs[1].firstChild.textContent;
        var cStatus = segs[0];
        doSimpleXMLHttpRequest("/auth/PPP/Status/"+unit).addCallback(function (cStatus, unit, nstat){
            var result = nstat.responseText.replace('\n', '').replace('\r', '');
            if (result=='running') {
                var runIco = TD({}, 
                    A({'href':"/auth/PPP/Disconnect/"+unit, 'onclick':"return confirm('Are you sure you want to disconnect this interface?');",
                        'title':"Connected: Click to disconnect."}, 
                        IMG({'src':"/images/connect.png"})
                    ),
                    A({'href':"/auth/PPP/Reset/"+unit, 'onclick':"return confirm('Are you sure you wish to reconnect this interface?');",
                        'title':"Reconnect this interface"},
                        IMG({'src':"/images/refresh.png"})
                    )
                );
                swapDOM(cStatus, runIco);
            }
            else {
                var stopIco = TD({},
                    A({'href':"/auth/PPP/Connect/"+unit, 'title':"Disconnected: Click to connect."},
                        IMG({'src':"/images/noconnect.png"})
                    )
                );
                swapDOM(cStatus, stopIco);
            }
        }, cStatus, unit);

    });

    callLater(5.0, recheckPPP);
}

if (loc.search(/PPP/) > 0){
    recheckPPP();
}

//
// Menu system 
//


var lastNode = null;

function unrollSideMenu(node){
    var expander = getElementsByTagAndClassName('div', 'sideMenuSubExpander', node); 
    var haveElms = false; 
    forEach(expander, function(elm){
        showElement(elm); 
        haveElms = true;
    });

    if (haveElms){
        var nlable = node.firstChild;
        connect(nlable, 'onclick', function (el) {
            if (lastNode){
                lastNode.style.background="#fff";
            }
            lastNode = nlable;
            nlable.style.background="#eee"
            rollSideMenu(node);
            Set_Cookie(nlable.innerHTML, 'false', 1, '/')
            return false;
        });
    }
}

function rollSideMenu(node){
    var expander = getElementsByTagAndClassName('div', 'sideMenuSubExpander', node); 
    var haveElms = false; 
    forEach(expander, function(elm){
        hideElement(elm); 
        haveElms = true;
    });
    
    if (haveElms){
        var nlable = node.firstChild;
        connect(nlable, 'onclick', function (el) {
            if (lastNode){
                lastNode.style.background="#fff";
            }
            lastNode = nlable;
            nlable.style.background="#eee"
            unrollSideMenu(node);
            Set_Cookie(nlable.innerHTML, 'true', 1, '/')
            return false;
        });
    }
}

function rollSideMenus(){
    var nodes = getElementsByTagAndClassName('div', 'sideMenuPrimary');

    forEach(nodes, function(node){
        var expander = getElementsByTagAndClassName('div', 'sideMenuSubExpander', node);
        var haveElms = false; 
        forEach(expander, function(elm){
            haveElms = true;
        });
        if (haveElms) { 
            c = Get_Cookie(node.firstChild.innerHTML);
            if (c != 'true'){
                rollSideMenu(node);
            }
            else {
                unrollSideMenu(node);
            }
        }
    });
}

rollSideMenus();
