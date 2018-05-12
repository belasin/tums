function checkAdvancedRouting(){
    var advElms = ['tabpanelParp', 'tabpanelBGP'];

    var cookie = Get_Cookie('routing');

    if (cookie != 'advanced') {
        forEach(advElms, function(i){
            hideElement(i);
        });
    }
    else {
        var newA = A({'href':"#", "onclick": "setAdvanced('routing', false);", 'id': 'advBtn'}, 'Simple');
        swapDOM('advBtn', newA);
    }
}

function enableAdvancedRouting(io){
    var advElms = ['tabpanelParp', 'tabpanelBGP'];

    forEach(advElms, function(i){
        if (io){
            showElement(i);
        }
        else {
            hideElement(i);
        }
    });

    if (io){
        Set_Cookie('routing', 'advanced', 500);
    }
    else {
        Set_Cookie('routing', 'simple', 500);
    }
        
}


function setAdvanced(type, io){
    if (io){
        var newA = A({'href':"#", "onclick": "setAdvanced('"+type+"', false);", 'id': 'advBtn'}, 'Simple');
        swapDOM('advBtn', newA);
    }
    else {
        var newA = A({'href':"#", "onclick": "setAdvanced('"+type+"', true);", 'id': 'advBtn'}, 'Advanced');
        swapDOM('advBtn', newA);
    }
 
    if (type=="routing"){
        enableAdvancedRouting(io);
    }
    return false;
}

function checkAdvanced(){
    checkAdvancedRouting();
}
