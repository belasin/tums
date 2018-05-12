	/*
	YUI Tetris!
	Licenses:
	(c) Creative Commons 2006
	http://creativecommons.org/licenses/by-sa/2.5/
	(c) Yahoo! Inc BSD Licensing Agreement
	http://developer.yahoo.com/yui/license.txt
	
	Author: Dustin Diaz | http://www.dustindiaz.com
	Date: 2006-05-16
	*/
	
	
	// we'll need this later
	Array.prototype.inArray = function (value) {
		for (var i=0, len=this.length; i < len; ++i) {
			if (this[i] === value) {
				return true;
			}
		}
		return false;
	};
	/*
		Declare The DED Namespace!
	*/
	var DED = window.DED || {};
	DED.games = function() {};
	DED.games.tetris = function() {
		var YUD = YAHOO.util.Dom;
		var YUE = YAHOO.util.Event;
		var SQUARE, LINE, EL1, EL2, ZAG1, ZAG2, TRI;
		// Core Blocks
		var SQUARE = [[3,5],[3,6],[4,5],[4,6]]; // curShape = 0
		var LINE = [[1,5],[2,5],[3,5],[4,5]]; // curShape = 1
		// "L" Shapes
		var EL1 = [[2,5],[3,5],[4,5],[4,6]]; // curShape = 2
		var EL2 = [[2,6],[3,6],[4,6],[4,5]]; // curShape = 3
		// Zig Zag Shapes
		var ZAG1 = [[2,5],[3,5],[3,6],[4,6]]; // curShape = 4
		var ZAG2 = [[2,6],[3,6],[3,5],[4,5]]; // curShape = 5
		// Triangle Shape Pyramid
		var TRI = [[3,4],[3,5],[3,6],[4,5]]; // curShape = 6
		/*
			* colors are cordinated with the shapes for symetry in the array
			* you can access the current color of a block by colors[DED.games.tetris.curShape];
		*/
		var colors = ['blue','white','red','red2','purple','purple2','orange'];
		var oAllRows, oAllCells;
		var stats;
		// scores = 10 points for 1 line, 30 points for 2 lines, 100 points for 3 lines, and 200 points for a tetris
		var scores = [10, 30, 100, 200];
		// some very basic browser detection for the stupid keypress events		
		var ua = navigator.userAgent.toLowerCase();
		var isOpera = (ua.indexOf('opera') != -1);
		var isIE = (ua.indexOf('msie') != -1 && !isOpera); // not opera spoof
		var isSafari = (ua.indexOf("safari") != -1);
		
		return {
			oSqCords : [],
			docker : null,
			counter : 0,		// @Int The amount of lines accumulated
			shapes : [],
			curShape : 0,		// @Int (0-6) The current shape that's being animated
			nextShape : 0,		// @Int (0-6) The current shape that's being animated
			curScore : 0,		// @Int The players current score
			locked : false,		// the current shape is now locked from being allowed to move
			curState : 1,		// @Int (1-4) The shape can only be flipped on 4 different sides
			timer : 1000, 		// @Int The amount of second between each drop
			level : 0,			// @Int The current level of which we're on. Level gets +1 for every ten lines
			gOverCount : 20,	// @Int This is only called 20 times, and it happens consecutively at the end of the game
			
			init : function(e) {
				// stop our normal event from firing
				YUE.stopEvent(e);
				// set our docker for debugging
				DED.games.tetris.docker = YAHOO.util.Dom.get('docker');
				stats = YUD.get('lines');
				var grid = YUD.get('grid');
				oAllRows = grid.getElementsByTagName('tr'); // 20 rows exactly
				// set some random blocks
				/*
				var block1 = [[20,1],[20,2],[20,3],[20,4]];
				YUD.batch(DED.games.tetris.formulate(block1), DED.games.tetris.makeWhite);
				var block2 = [[17,1],[18,1],[19,1],[19,2]];
				YUD.batch(DED.games.tetris.formulate(block2), DED.games.tetris.makeRed);
				var block3 = [[20,10],[20,9],[19,10],[19,9]];
				YUD.batch(DED.games.tetris.formulate(block3), DED.games.tetris.makeBlue);
				var block4 = [[20,5],[20,6],[20,7],[19,6]];
				YUD.batch(DED.games.tetris.formulate(block4), DED.games.tetris.makeOrange);
				var block5 = [[18,2],[18,3],[19,3],[19,4]];
				YUD.batch(DED.games.tetris.formulate(block5), DED.games.tetris.makePurple);
				*/
				/*
					assign some keyboard events
					kind of lame that we have to do this, 
					but we'll be adding the keypress to the wrapper for IE
				*/
				if ( isIE ) {
					YAHOO.util.Event.on('wrapper','keypress',DED.games.tetris.press);
				}
				else {
					YAHOO.util.Event.on(window,'keypress',DED.games.tetris.press);
				}
				if ( isSafari || isOpera ) {
					// I'm assuming Opera and Safari actually get this right - but since most are on IE & Firefox, I'm doing this
					YUD.get('grid').style.position = 'relative';
					YUD.get('grid').style.top = '-40px';
				}
				// can't start this game again until we're done
				YAHOO.util.Event.removeListener('start','click',DED.games.tetris.init);
				// assign our first "next shape"
				var n = (Math.random()*7);
				var rand = Math.floor(n);
				var shuffled = ( rand > 6 ? 6 : rand );
				DED.games.tetris.nextShape = shuffled;
				
				
				DED.games.tetris.fire();
				
			},
			fire : function() {
				// unlock our system
				if ( !this.isGameOver() ) {
					DED.games.tetris.locked = false;
					// Initialize our current Block
					var allBlocks = [SQUARE, LINE, EL1, EL2, ZAG1, ZAG2, TRI]; // length is seven
					var n = (Math.random()*7);
					var rand = Math.floor(n);
					var shuffled = ( rand > 6 ? 6 : rand );
					DED.games.tetris.curShape = DED.games.tetris.nextShape;
					DED.games.tetris.oSqCords = allBlocks[DED.games.tetris.nextShape];
					DED.games.tetris.nextShape = shuffled;
					YUD.get('next-shape').innerHTML = '<img src="img/s'+((DED.games.tetris.nextShape)+1)+'.gif" />';
					/*
						* This is the testing Block for manually setting the shape
					*/
					// DED.games.tetris.curShape = 3;
					// DED.games.tetris.oSqCords = allBlocks[DED.games.tetris.curShape];
					
					/*
						* Run Line checker to see if we've eliminated since the last run through
					*/
					DED.games.tetris.lineChecker();
					/*
						add this to our stats of blocks
					*/
					switch (DED.games.tetris.curShape) {
						case(0):
							var cur = parseInt(YUD.get('square').innerHTML);
							cur++;
							YUD.get('square').innerHTML = cur;
						break;
						case(1):
							var cur = parseInt(YUD.get('line').innerHTML);
							cur++;
							YUD.get('line').innerHTML = cur;
						break;
						case(2):
							var cur = parseInt(YUD.get('el1').innerHTML);
							cur++;
							YUD.get('el1').innerHTML = cur;
						break;
						case(3):
							var cur = parseInt(YUD.get('el2').innerHTML);
							cur++;
							YUD.get('el2').innerHTML = cur;
						break;
						case(4):
							var cur = parseInt(YUD.get('zag1').innerHTML);
							cur++;
							YUD.get('zag1').innerHTML = cur;
						break;
						case(5):
							var cur = parseInt(YUD.get('zag2').innerHTML);
							cur++;
							YUD.get('zag2').innerHTML = cur;
						break;
						case(6):
							var cur = parseInt(YUD.get('tri').innerHTML);
							cur++;
							YUD.get('tri').innerHTML = cur;
						break;
					};
					// set the interval and let's begin!!!
					ID = window.setInterval("DED.games.tetris.moveDown()",DED.games.tetris.timer);
				}
				else {
					OVER_ID = window.setInterval("DED.games.tetris.gameOver()",100);
				}
			},
			gameOver : function() {
				if ( DED.games.tetris.gOverCount > 3 ) {
					var row = YUD.get('row'+DED.games.tetris.gOverCount);
					row.className = 'over';
					DED.games.tetris.gOverCount--;
					return;
				}
				window.clearInterval(OVER_ID);
			},
			/*
				@return boolean
			*/
			isGameOver : function() {
				var oRow5 = YUD.get('row5');
				var oRowCells = oRow5.getElementsByTagName('td');
				var oHasClass = YUD.hasClass(oRowCells, 'fill'); // returns array of booleans
				var bHasFill = oHasClass.inArray(true); // if there's a single instance of true
				if ( bHasFill ) {
					// DED.games.tetris.logger('GAME OVER!!!');
					// GAME OVER!!!!!
					return true;
				}
				return false;
			},
			formulate : function(cords) {
				return YAHOO.util.Dom.get(['row'+cords[0][0]+'cell'+cords[0][1], 'row'+cords[1][0]+'cell'+cords[1][1], 'row'+cords[2][0]+'cell'+cords[2][1], 'row'+cords[3][0]+'cell'+cords[3][1]]);
			},
			grabCord : function(row, col) {
				return YAHOO.util.Dom.get('row'+row+'cell'+col);
			},
			logger : function(html) {
				// Disabling logger for release!
				// DED.games.tetris.docker.innerHTML += '<p>'+html+'<hr /></p>';
				return;
			},
			press : function(e) {
				switch (YAHOO.util.Event.getCharCode(e)) {
					case(115):
						// key 's'
						DED.games.tetris.moveLeft();
					break;
					case(102):
						// key 'f'
						DED.games.tetris.moveRight();
					break;
					case(100):
						// key 'd'
						DED.games.tetris.moveDown();
					break;
					case(37):
						// key '<-'
						DED.games.tetris.rotateLeft();
					break;
					case(63234): // safari thinks this means left
						DED.games.tetris.rotateLeft();
					break;
					case(39):
						// key '->'
						DED.games.tetris.rotateRight();
					break;
					case(63235): // safari thinks this means right
						DED.games.tetris.rotateRight();
					break;
					/*
						And of course we're going to add these last two for IE
					*/
					case(44):
						// key '<-'
						DED.games.tetris.rotateLeft();
					break;
					case(46):
						// key '->'
						DED.games.tetris.rotateRight();
					break;
				}
				if ( YAHOO.util.Event.getCharCode(e) != 116 ) {
					YAHOO.util.Event.stopEvent(e);
				}
			},
			updateCounter : function(lines) {
				DED.games.tetris.counter += lines;
				stats.innerHTML = DED.games.tetris.counter;
			},
			lineChecker : function() {
				// first keep a tally of how many lines we might have nuked
				var lines = 0;
				// set aside an array (won't go past 4 in length) to get our bottom line
				var aLine = [], iLine;
				// set up a var to check if we got anylines
				var bGotLines = false;
				// move up the grid as we go
				for ( var i=19; i >3; --i ) {
					var oRowCells = oAllRows[i].getElementsByTagName('td');
					var oHasClass = YUD.hasClass(oRowCells, 'fill'); // returns array of booleans
					var bIsNotFull = oHasClass.inArray(false);
					if ( bIsNotFull ) {
						continue;
					}
					// otherwise let's nuke the row!
					YUD.batch(oRowCells, DED.games.tetris.emptyCell);
					// then add one to the tally
					lines++;
					// note that we've got this far
					bGotLines = true;
					aLine.push(i);
				}
				/* 
					If we did get any lines, we're going to move everything above the bottom line 
					down by the amount of lines we got
				*/
				if ( bGotLines ) {
					DED.games.tetris.logger('You Nuked '+lines+' lines');
					// add to our counter the amount of lines
					DED.games.tetris.updateCounter(lines);
					// get our bottom line by pulling the first in the aLine Stack
					iLine = aLine[0];
					// do a check to see how many lines we got versus the first and last
					
					// If this is a normal transaction without any funny combo stuff
					if ( (iLine-aLine[aLine.length-1])+1 == lines ) {
						for ( var k=iLine-lines; k > 4; k-- ) {
							var oRowCells = oAllRows[k].getElementsByTagName('td');
							YUD.batch(oRowCells, DED.games.tetris.moveCellDownBy, lines);
						}
					}
					else {
						// otherwise we have to do some wierd stuff
						DED.games.tetris.logger('Got a wierd combo');
						for ( var j=1; j<=lines; ++j ) {
							for ( var k=iLine-j; k > 4; --k ) {
								var oRowCells = oAllRows[k].getElementsByTagName('td');
								var oHasClass = YUD.hasClass(oRowCells, 'fill'); // returns array of booleans
								var bIsNotFull = oHasClass.inArray(false);
								YUD.batch(oRowCells, DED.games.tetris.moveCellDownBy, 1);
							}
						}
					}
					// Our Level is a division of ten. It takes at least 10 lines to get to level one
					DED.games.tetris.level = Math.floor(parseInt(DED.games.tetris.counter/10));
					var level = DED.games.tetris.level;
					// Take note that we won't be increasing the speed after level 20.
					// At this point it's just crazy
					if ( level > 0 && level < 20 ) {
						DED.games.tetris.timer = 1000 - (level*50);
						YUD.get('level').innerHTML = level;
					}
					DED.games.tetris.curScore += parseInt(scores[lines-1]);
					YUD.get('score').innerHTML = DED.games.tetris.curScore;
				}
			},
			moveCellDownBy : function(oEl, iCount) {
				var klassName = oEl.className;
				var row = parseInt( (oEl.id).split('row')[1] );
				var cell = parseInt( (oEl.id).split('cell')[1] );
				oEl.className = '';
				var targetId = 'row'+(row+iCount)+'cell'+cell;
				var targetCell = YUD.get(targetId);
				targetCell.className = klassName;
			},
			moveLeft : function() {
				if ( DED.games.tetris.locked ) {
					return;
				}
				if ( DED.games.tetris.canMoveLeft() ) {
					var cords = DED.games.tetris.oSqCords;
					YAHOO.util.Dom.batch(DED.games.tetris.formulate(cords), DED.games.tetris.nukeClasses);
					DED.games.tetris.oSqCords = [ [cords[0][0], (cords[0][1])-1], [cords[1][0], (cords[1][1])-1], [cords[2][0], (cords[2][1])-1], [cords[3][0], (cords[3][1])-1]];
					var elements = DED.games.tetris.formulate(DED.games.tetris.oSqCords);
					YAHOO.util.Dom.addClass(elements, colors[DED.games.tetris.curShape]+' fill c');
				}
			},
			moveRight : function() {
				if ( DED.games.tetris.locked ) {
					return;
				}
				if ( DED.games.tetris.canMoveRight() ) {
					var cords = DED.games.tetris.oSqCords;
					YAHOO.util.Dom.batch(DED.games.tetris.formulate(cords), DED.games.tetris.nukeClasses);
					DED.games.tetris.oSqCords = [ [cords[0][0], (cords[0][1])+1], [cords[1][0], (cords[1][1])+1], [cords[2][0], (cords[2][1])+1], [cords[3][0], (cords[3][1])+1]];
					var elements = DED.games.tetris.formulate(DED.games.tetris.oSqCords);
					YAHOO.util.Dom.addClass(elements, colors[DED.games.tetris.curShape]+' fill c');
				}
			},
			moveDown : function() {
				if ( DED.games.tetris.locked ) {
					window.clearInterval(ID);
					return;
				}
				if ( !DED.games.tetris.canMoveDown() ) {
					window.clearInterval(ID);
					DED.games.tetris.curState = 1;
					YUD.removeClass(DED.games.tetris.formulate(DED.games.tetris.oSqCords), 'c');
					DED.games.tetris.fire();
				}
				else {
					var cords = DED.games.tetris.oSqCords;
					YAHOO.util.Dom.batch(DED.games.tetris.formulate(cords), DED.games.tetris.nukeClasses);
					DED.games.tetris.oSqCords = [ [(cords[0][0])+1, cords[0][1]], [(cords[1][0])+1, cords[1][1]], [(cords[2][0])+1, cords[2][1]], [(cords[3][0])+1, cords[3][1]]];
					var elements = DED.games.tetris.formulate(DED.games.tetris.oSqCords);
					YAHOO.util.Dom.addClass(elements, colors[DED.games.tetris.curShape]+' fill c');
				}
			},
			canMoveDown : function() {
				var c = DED.games.tetris.oSqCords;
				for ( var i=0; i < 4; ++i ) {
					var current = DED.games.tetris.grabCord((c[i][0])+1, c[i][1]) || false;
					if ( !current ) {
						// must have meant we grabbed an element that doesn't exist on the grid
						DED.games.tetris.locked = true;
						return false;
					}
					if ( YAHOO.util.Dom.hasClass(current, 'fill') && !YAHOO.util.Dom.hasClass(current,'c') ) {
						// can't move down
						DED.games.tetris.locked = true;
						return false;
					}
				}
				// indeed, we keep going!
				return true;
			},
			canMoveLeft : function() {
				var c = DED.games.tetris.oSqCords;
				for ( var i=0; i < 4; ++i ) {
					var current = DED.games.tetris.grabCord(c[i][0], (c[i][1])-1) || false;
					if ( !current ) {
						// must have meant we grabbed an element that doesn't exist on the grid
						return false;
					}
					if ( YAHOO.util.Dom.hasClass(current, 'fill') && !YAHOO.util.Dom.hasClass(current,'c') ) {
						// can't move down
						return false;
					}
				}
				// indeed, we keep going!
				return true;
			},
			canMoveRight : function() {
				var c = DED.games.tetris.oSqCords;
				for ( var i=0; i < 4; ++i ) {
					var current = DED.games.tetris.grabCord(c[i][0], (c[i][1])+1) || false;
					if ( !current ) {
						// must have meant we grabbed an element that doesn't exist on the grid
						return false;
					}
					if ( YAHOO.util.Dom.hasClass(current, 'fill') && !YAHOO.util.Dom.hasClass(current,'c') ) {
						// can't move down
						return false;
					}
				}
				// indeed, we keep going!
				return true;
			},
			rotateLeft : function() {
				var c = DED.games.tetris.oSqCords;
				function remover(oEl) {
					YUD.removeClass(oEl, colors[DED.games.tetris.curShape]);
					YUD.removeClass(oEl, 'c');
					YUD.removeClass(oEl, 'fill');
				}
				function adder(oEl) {
					YUD.addClass(oEl, colors[DED.games.tetris.curShape]+' fill c');
				}
				if ( !DED.games.tetris.canRotateLeft() ) {
					// why waste time. stop the checks if it can't rotate anyway.
					return;
				}
				switch (DED.games.tetris.curShape) {
					case(0): // this is a SQUARE. No rotating here. set curState to 1 for saftey
						DED.games.tetris.curState = 1;
					break;
					case(1): // this is LINE
						if ( DED.games.tetris.curState === 1 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [(c[3][0])-2, (c[3][1])+2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [(c[3][0])+2, (c[3][1])-2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							DED.games.tetris.curState = 1;
						}
					break;
					case(2): // EL1 Shape
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 2
							DED.games.tetris.curState = 2;
						}
						else if ( DED.games.tetris.curState === 2 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [c[3][0], (c[3][1])-2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 3
							DED.games.tetris.curState = 3;
			
						}
						else if ( DED.games.tetris.curState === 3 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 4
							DED.games.tetris.curState = 4;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [c[3][0], (c[3][1])+2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
						}
					break;
					case(3): // EL2 has 4 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [c[3][0], (c[3][1])+2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 2
							DED.games.tetris.curState = 2;
						}
						else if ( DED.games.tetris.curState === 2 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 3
							DED.games.tetris.curState = 3;
			
						}
						else if ( DED.games.tetris.curState === 3 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [c[3][0], (c[3][1])-2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 4
							DED.games.tetris.curState = 4;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
						}
					break;
					case(4): // ZAG1 has 2 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 2
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
			
						}
					break;
					case(5): // ZAG2 has 2 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 2
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
			
						}
					break;
					case(6): // TRI has 4 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-1, (c[3][1])+1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 2
							DED.games.tetris.curState = 2;
						}
						else if ( DED.games.tetris.curState === 2 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [(c[3][0])-1, (c[3][1])-1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 3
							DED.games.tetris.curState = 3;
			
						}
						else if ( DED.games.tetris.curState === 3 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+1, (c[3][1])-1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 4
							DED.games.tetris.curState = 4;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [(c[3][0])+1, (c[3][1])+1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
						}
					break;
				};
			},
			rotateRight : function() {
				var c = DED.games.tetris.oSqCords;
				function remover(oEl) {
					YUD.removeClass(oEl, colors[DED.games.tetris.curShape]);
					YUD.removeClass(oEl, 'c');
					YUD.removeClass(oEl, 'fill');
				}
				function adder(oEl) {
					YUD.addClass(oEl, colors[DED.games.tetris.curShape]+' fill c');
				}
				if ( !DED.games.tetris.canRotateLeft() ) {
					// why waste time. stop the checks if it can't rotate anyway.
					return;
				}
				switch (DED.games.tetris.curShape) {
					case(0): // this is a SQUARE. No rotating here. set curState to 1 for saftey
						DED.games.tetris.curState = 1;
					break;
					case(1): // this is LINE
					/*
						This is the same exact code as per 'LINE' for rotateLeft but works for rotateRight since there's only 
						two states to worry about. Could be centralized but we can work that out later
					*/
						if ( DED.games.tetris.curState === 1 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [(c[3][0])-2, (c[3][1])+2] ];
							// run remover then adder
							YUD.batch(DED.games.tetris.formulate(c), remover);
							YUD.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [(c[3][0])+2, (c[3][1])-2] ];
							// run remover then adder
							YUD.batch(DED.games.tetris.formulate(c), remover);
							YUD.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							DED.games.tetris.curState = 1;
						}
					break;
					case(2):
						// EL1 Shape
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [c[3][0], (c[3][1])-2] ];
							// run remover then adder
							YUD.batch(DED.games.tetris.formulate(c), remover);
							YUD.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 4
							DED.games.tetris.curState = 4;
						}
						else if ( DED.games.tetris.curState === 2 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YUD.batch(DED.games.tetris.formulate(c), remover);
							YUD.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
						}
						else if ( DED.games.tetris.curState === 3 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [c[3][0], (c[3][1])+2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 2
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 3
							DED.games.tetris.curState = 3;
						}
					break;
					case(3): // EL2 has 4 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 4
							DED.games.tetris.curState = 4;
						}
						else if ( DED.games.tetris.curState === 2 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [c[3][0], (c[3][1])-2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
						}
						else if ( DED.games.tetris.curState === 3 ) {							
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 2
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [c[3][0], (c[3][1])+2] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 3
							DED.games.tetris.curState = 3;
						}
					break;
					case(4): // ZAG1 has 2 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 2
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
			
						}
					break;
					case(5): // ZAG2 has 2 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 2
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+2, c[3][1]] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
			
						}
					break;
					case(6): // TRI has 4 states
						if ( DED.games.tetris.curState === 1 ) {
							// must be original state
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])-1], [(c[3][0])-1, (c[3][1])-1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current State to 4
							DED.games.tetris.curState = 4;
						}
						else if ( DED.games.tetris.curState === 2 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])-1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])+1, (c[2][1])+1], [(c[3][0])+1, (c[3][1])-1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 1
							DED.games.tetris.curState = 1;
			
						}
						else if ( DED.games.tetris.curState === 3 ) {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])-1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])+1], [(c[3][0])+1, (c[3][1])+1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 2
							DED.games.tetris.curState = 2;
						}
						else {
							DED.games.tetris.oSqCords = [ [(c[0][0])+1, (c[0][1])+1], [c[1][0], c[1][1]], [(c[2][0])-1, (c[2][1])-1], [(c[3][0])-1, (c[3][1])+1] ];
							// run remover then adder
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(c), remover);
							YAHOO.util.Dom.batch(DED.games.tetris.formulate(DED.games.tetris.oSqCords), adder);
							// change our current state to 3
							DED.games.tetris.curState = 3;
						}
					break;
				};
			},
			/*
				@return boolean
			*/
			canRotateLeft : function() {
				var c = DED.games.tetris.oSqCords;
				switch ( DED.games.tetris.curShape ) {
					case(0): // this is a square. There's not even a need to have this here. return true for saftey
						return true;
					break;
					case(1): // this is LINE two cases					
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])-2, (c[3][1])+2) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])+2, (c[3][1])-2) || false;
							break;
						};
						if ( !c1 || !c2 || !c3 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') || YUD.hasClass(c3, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(2): // EL1 Shape
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])-2) || false;
							break;
							case(3):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;
							break;
							case(4):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])+2) || false;
							break;
						}
						if ( !c1 || !c2 || !c3 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') || YUD.hasClass(c3, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(3): // EL2 has 4 states
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])+2) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
							case(3):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])-2) || false;
							break;
							case(4):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;
							break;
						};
						if ( !c1 || !c2 || !c3 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') || YUD.hasClass(c3, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(4): // ZAG1 has 2 states
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;
							break;
						};
						if ( !c1 || !c2 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(5): // ZAG2 has 2 states
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;
							break;
						};
						if ( !c1 || !c2 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(6): // TRI has 4 states					
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])-1) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])-1) || false;
							break;
							case(3):
								var c1 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])+1) || false;
							break;
							case(4):
								var c1 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])+1) || false;
							break;
						};
						if ( !c1 || YUD.hasClass(c1, 'fill') ) {
							return false;
						}
						return true;
					break;
				};
				// indeed, let's flip it!
				return true;
			},
			/*
				@return boolean
			*/
			canRotateRight : function() {
				var c = DED.games.tetris.oSqCords;
				switch ( DED.games.tetris.curShape ) {
					case(0): // this is a square. There's not even a need to have this here return true for saftey
						return true;
					break;
					case(1): // this is LINE two cases					
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])-2, (c[3][1])+2) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])+2, (c[3][1])-2) || false;
							break;
						};
						if ( !c1 || !c2 || !c3 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') || YUD.hasClass(c3, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(2): // EL1 Shape
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])-2) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;
							break;
							case(3):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])+2) || false;
							break;
							case(4):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
						};
						if ( !c1 || !c2 || !c3 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') || YUD.hasClass(c3, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(3): // EL2 has 4 states
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])+2) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
							case(3):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])-1) || false;
								var c3 = DED.games.tetris.grabCord(c[3][0], (c[3][1])-2) || false;
							break;
							case(4):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])+1) || false;
								var c3 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;
							break;
						};
						if ( !c1 || !c2 || !c3 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') || YUD.hasClass(c3, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(4): // ZAG1 has 2 states
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[2][0])+1, (c[2][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;								
							break;
						};
						if ( !c1 || !c2 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(5): // ZAG2 has 2 states					
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[2][0])-1, (c[2][1])-1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])-2, c[3][1]) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
								var c2 = DED.games.tetris.grabCord((c[3][0])+2, c[3][1]) || false;
							break;
						};
						if ( !c1 || !c2 ) {
							// must have meant we grabbed an element that doesn't exist on the grid
							return false;
						}
						if ( YUD.hasClass(c1, 'fill') || YUD.hasClass(c2, 'fill') ) {
							// there's some other blocks there
							return false;
						}
						return true;
					break;
					case(6): // TRI has 4 states
						switch (DED.games.tetris.curState) {
							case(1):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])+1) || false;
							break;
							case(2):
								var c1 = DED.games.tetris.grabCord((c[0][0])-1, (c[0][1])-1) || false;
							break;
							case(3):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])-1) || false;
							break;
							case(4):
								var c1 = DED.games.tetris.grabCord((c[0][0])+1, (c[0][1])+1) || false;
							break;
						};
						if ( !c1 || YUD.hasClass(c1, 'fill') ) {
							return false;
						}
						return true;
					break;
				};
				// indeed, let's flip it!
				return true;
			},
			nukeClasses : function(oEl) {
				YAHOO.util.Dom.removeClass(oEl, colors[DED.games.tetris.curShape]);
				YAHOO.util.Dom.removeClass(oEl, 'fill');
				YAHOO.util.Dom.removeClass(oEl, 'c');
			},
			emptyCell : function(oEl) {
				oEl.className = '';
			},
			makeOrange : function(oEl) {
				oEl.className = '';
				YAHOO.util.Dom.addClass(oEl, 'orange fill');
			},
			makeBlue : function(oEl) {
				oEl.className = '';
				YAHOO.util.Dom.addClass(oEl, 'blue fill');
			},
			makeWhite : function(oEl) {
				oEl.className = '';
				YAHOO.util.Dom.addClass(oEl, 'white fill');
			},
			makeRed : function(oEl) {
				oEl.className = '';
				YAHOO.util.Dom.addClass(oEl, 'red fill');
			},
			makePurple : function(oEl) {
				oEl.className = '';
				YAHOO.util.Dom.addClass(oEl, 'purple fill');
			}
		};
	}();

