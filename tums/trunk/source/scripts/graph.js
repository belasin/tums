var Graph = function(canvas, prefix, mode){
    this.canvas = getElement(canvas);
    this.dataSets = [];
    this.prefix = prefix;
    this.mode = mode;
    // Add a set
    this.addSet = function(valueAr){
        var index = this.dataSets.length;
        this.dataSets[index] = valueAr;
    };

    // Renders the whole graph
    this.render = function(){
        this.renderSet();
    };

    // Clean up all our rendering
    this.clean = function(){
        removeElement(this.prefix+'-axis');
        var i=0;
        var j=0;
        for (j=0; j<this.dataSets.length; j++){
            for (i=0; i<this.dataSets[j].length; i++){
                removeElement(this.prefix+'-ln'+i+'-'+j);
            }
        }
    };
    // Render a single set
    this.renderSet = function(){
        var i=0;
        var canvas = this.canvas;
        var height = this.canvas.offsetHeight;
        var width = this.canvas.offsetWidth;
        var prefix = this.prefix;
        var mode = this.mode;
        var leftOffset = 20 + this.canvas.offsetLeft;

        // Get the max and minimum over the entire series
        var max = this.dataSets[0][0];
        var min = max;
        for (i=0; i<this.dataSets.length; i++){
            forEach(this.dataSets[i], function(val){
                if (val>max){
                    max = val;
                }
                if (val<min){
                    min = val;
                }
            });
        }
        // Determine the scaling and axis.
        scale = Math.abs(min) + max;
        scaleFactor = (height-20)/scale;
        if (min<0){
            axisPos = (height)-(Math.abs(min)*scaleFactor) + this.canvas.offsetTop;
        }
        else {
            axisPos = (height + this.canvas.offsetTop)
        }
        var topOffset = 0;
        axWid = this.dataSets[0].length * 4;
        // Draw the axis
        axis = DIV({'id':prefix+'-axis', 'style':'position:absolute; height:0px; width:'+axWid+'px;border-bottom:1px solid black; top:'+axisPos+'px'}, "");
        appendChildNodes(this.canvas, axis);
        // Draw the data
        var numSets = this.dataSets.length;
        for (var j=0; j<this.dataSets.length; j++){
            var thisSet = this.dataSets[j];
            var n=0;
            var lasti = 0;
            var grad = 0;
            for (var i=0; i<thisSet.length; i++){
                setval = thisSet[i];
                var val = setval * scaleFactor;
                // Workout the gradient
                if (mode == 0){
                    if (lasti) {
                        grad = Math.abs(setval-lasti)*5;
                    }
                    var lineLen = 10+grad; //Math.abs(val)-(Math.abs(val)/2);
                    if (val < 0){
                        val = Math.abs(val);
                        topOffset = (axisPos + val + (lineLen/2));
                    }
                    else {
                        topOffset = (axisPos - val + (lineLen/2));
                    }
                }
                else{
                    var lineLen = val;
                    if (val < 0){
                        val = Math.abs(val);
                        lineLen = val
                        topOffset = axisPos+val;
                    }
                    else {
                        topOffset = axisPos;
                    }
 
                }
                // Create the graph line node and append it
                line = DIV({'id':prefix+'-ln'+i+'-'+j, 'class':'set'+j,
                    'style':'height:'+lineLen+'px; top:'+(topOffset-lineLen)+'px;'+
                    'width:2px; position:absolute; left:'+(leftOffset+(i*(numSets+1))+j)+'px;'}," ");
                appendChildNodes(canvas, line);
                lasti = setval;
            }
        }
    };
};

