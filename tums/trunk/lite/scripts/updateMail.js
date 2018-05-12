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

addLoadEvent(function() {
    rollForwards();
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
});

