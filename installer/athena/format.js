format.E = Nevow.Athena.Widget.subclass('format.E');

format.E.methods(
    function nodeInserted(self) {
        self.format();
    },

    function updateProgress(self, percent){
        // Update the progress percentage
        self.pb.set(percent);
    },

    function updateTicker(self, text){
        // Update the description text on the progress bar
        self.nodeById('statusText').innerHTML = text
    }, 

    function nextPage(self, url){
        // Redirect to next page
        window.location=url;
    },

    function format(self){
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
        self.callRemote('startup').addCallback(function (e) {
            self.nextPage('/Install/')
        });
    }
);

