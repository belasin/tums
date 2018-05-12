function mutateSubmit(){
    try {
        var elms = getElementsByTagAndClassName('div', 'actions');
        var loc = document.location.toString();
        var airGap = "\u00a0 \u00a0 \u00a0 \u00a0 \u00a0 \u00a0 \u00a0 \u00a0";

        forEach(elms, function (el) {
            var subButton = el.firstChild;
            var id = subButton.id;
            var newButton = INPUT({'type':'image', 'src':'/static/images/next.png', 'alt':'Submit', 'id':id});

            if (loc.search(/License/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/DiskMounts/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/DiskSelect'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/Disks/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/License'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/Management/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/CompDetails'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/InternetDetails/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/Management'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/WanConfig/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/LanConfig'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
 
            else if (loc.search(/LanConfig/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/NetConfig'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/PppConfig/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/LanConfig'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/NetConfig/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/InternetDetails'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else if (loc.search(/ServiceConfig/) > 0){
                var newStruct = DIV({}, 
                    A({'href': '/LanConfig'}, IMG({'src': '/static/images/back.png', 'alt': 'Back'})), 
                    airGap,
                    newButton
                )
                swapDOM(subButton, newStruct);
            }
            else {
                swapDOM(subButton, newButton);
            }
        });
    } catch(dontCare) {}
}

addLoadEvent(function() {
    mutateSubmit();
});

