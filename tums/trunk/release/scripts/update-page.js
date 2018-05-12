// import Nevow.Athena

updates.PS = Nevow.Athena.Widget.subclass('updates.PS');

updates.PS.methods(
    function nodeInserted(self){
        self.installBar();
        hideElement(self.nodeById("updateConfirm"));
        hideElement(self.nodeById("noUpdates"));

    },

    function noUpdates(self){
        hideElement(self.nodeById('progressSection'));
        showElement(self.nodeById("noUpdates"));
    },

    function newUpdates(self, size){
        hideElement(self.nodeById('progressSection'));
        showElement(self.nodeById("updateConfirm"));
        swapDOM(self.nodeById("updateConfSize"), SPAN({}, size));

        connect(self.nodeById("doUpdateBtn"), 'onclick', function() {
            hideElement(self.nodeById("updateConfirm"));
            showElement(self.nodeById('progressSection'));
            self.callRemote('doDownload');
            return false;
        });
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

    function installBar(self){
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
        self.callRemote('doUpdate');
    }
);
