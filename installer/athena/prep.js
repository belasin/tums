prep.E = Nevow.Athena.Widget.subclass('prep.E');

prep.E.methods(
    function nodeInserted(self) {
        self.prep();
    },

    function updateProgress(self, percent){
        // Update the progress percentage
        self.pb.set(percent);
    },

    function updateTicker(self, text){
        // Update the description text on the progress bar
        self.nodeById('statusText').innerHTML = text
    }, 

    function installComplete(self){
        // Redirect to next page
        self.callRemote('grubInstall').addCallback(function (r) {
            window.location="/CompDetails/";
        });
    },

    function prep(self){
        // Initialise the widget thing
        //
        self.pb = new dwProgressBar({
            container:          self.nodeById('progressBar'), 
            startPercentage:    0,
            speed:              1000, 
            boxID:              'progbox', 
            percentageID:       'progmain', 
            displayID:          'progtext', 
            displayText:        true, 
        });
        self.callRemote('startConfig');
    }
);

