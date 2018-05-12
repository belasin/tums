var yHx = {
	/* 
	yHx ColorPicker (c) 2005
	Written by Dustin Diaz
	Developed for Yahoo! Inc.
	
	Script Dependencies: findPosXY.js, functionAddEvent.js, getElementsByClass.js
	Be Sure you get a Copy of these libraries before running this script
	Implementation:
	1) include the appropriate css & js files
	2) append class attributes with value 'yHxColorPicker' to any input[type='text'] elements
	
	Library Params:
	incrementer: A running value of how many times the colorPicker is being appended to the document. Indicie beginning at Zero. 
	hexOpen: Bool indicating if any colorPicker is open
	currentPicker: Indicates which colorPicker is currently open
	isDisabled: Indicates the state of which the colorPickers can be used or not
	*/
	incrementer : 0,
	hexOpen : false,
	currentPicker : null,
	isDisabled : false,
	shim : 'yHxPickerShim',
	isIE : false,
	hexPallete : function(e) {
	var pickers = getElementsByClass(document,'yHxColorPicker','input');
		for ( i=0;i<pickers.length;i++ ) { 
			if ( pickers[i].getAttribute('hexParent') == this.incrementer ) {
			var pickerElement = pickers[i];
			break;
			}
		}
	var hexTable = '<table class="pickerTable" id="pickerTable'+this.incrementer+'"><thead id="hexSection'+this.incrementer+'">';
	hexTable += '<tr>';
	hexTable += '<td hx="ff0000"></td><td hx="ffff00"></td><td hx="00ff00"></td><td hx="00ffff"></td>';
	hexTable += '<td hx="0000ff"></td><td hx="ff00ff"></td><td hx="ffffff"></td><td hx="ebebeb"></td>';
	hexTable += '<td hx="e1e1e1"></td><td hx="d7d7d7"></td><td hx="cccccc"></td><td hx="c2c2c2"></td>';
	hexTable += '<td hx="acacac"></td><td hx="a0a0a0"></td><td hx="959595"></td><td hx="b7b7b7"></td>';
	hexTable += '</tr>';
	
	hexTable += '<tr>';
	hexTable += '<td hx="ee1d24"></td><td hx="fff100"></td><td hx="00a650"></td><td hx="00aeef"></td>';
	hexTable += '<td hx="2f3192"></td><td hx="ed008c"></td><td hx="898989"></td><td hx="7d7d7d"></td>';
	hexTable += '<td hx="707070"></td><td hx="626262"></td><td hx="555555"></td><td hx="464646"></td>';
	hexTable += '<td hx="363636"></td><td hx="262626"></td><td hx="111111"></td><td hx="000000"></td>';
	hexTable += '</tr>';

	hexTable += '<tr>';
	hexTable += '<td hx="f7977a"></td><td hx="fbad82"></td><td hx="fdc68c"></td><td hx="fff799"></td>';
	hexTable += '<td hx="c6df9c"></td><td hx="a4d49d"></td><td hx="81ca9d"></td><td hx="7bcdc9"></td>';
	hexTable += '<td hx="6ccff7"></td><td hx="7ca6d8"></td><td hx="8293ca"></td><td hx="8881be"></td>';
	hexTable += '<td hx="a286bd"></td><td hx="bc8cbf"></td><td hx="f49bc1"></td><td hx="f5999d"></td>';
	hexTable += '</tr>';

	hexTable += '<tr>';
	hexTable += '<td hx="f16c4d"></td><td hx="f68e54"></td><td hx="fbaf5a"></td><td hx="fff467"></td>';
	hexTable += '<td hx="acd372"></td><td hx="7dc473"></td><td hx="39b778"></td><td hx="16bcb4"></td>';
	hexTable += '<td hx="00bff3"></td><td hx="438ccb"></td><td hx="5573b7"></td><td hx="5e5ca7"></td>';
	hexTable += '<td hx="855fa8"></td><td hx="a763a9"></td><td hx="ef6ea8"></td><td hx="f16d7e"></td>';
	hexTable += '</tr>';

	hexTable += '<tr>';
	hexTable += '<td hx="ee1d24"></td><td hx="f16522"></td><td hx="f7941d"></td><td hx="fff100"></td>';
	hexTable += '<td hx="8fc63d"></td><td hx="37b44a"></td><td hx="00a650"></td><td hx="00a99e"></td>';
	hexTable += '<td hx="00aeef"></td><td hx="0072bc"></td><td hx="0054a5"></td><td hx="2f3192"></td>';
	hexTable += '<td hx="652c91"></td><td hx="91278f"></td><td hx="ed008c"></td><td hx="ee105a"></td>';
	hexTable += '</tr>';

	hexTable += '<tr>';
	hexTable += '<td hx="9d0a0f"></td><td hx="a1410d"></td><td hx="a36209"></td><td hx="aba000"></td>';
	hexTable += '<td hx="588528"></td><td hx="197b30"></td><td hx="007236"></td><td hx="00736a"></td>';
	hexTable += '<td hx="0076a4"></td><td hx="004a80"></td><td hx="003370"></td><td hx="1d1363"></td>';
	hexTable += '<td hx="450e61"></td><td hx="62055f"></td><td hx="9e005c"></td><td hx="9d0039"></td>';
	hexTable += '</tr>';

	hexTable += '<tr>';
	hexTable += '<td hx="790000"></td><td hx="7b3000"></td><td hx="7c4900"></td><td hx="827a00"></td>';
	hexTable += '<td hx="3e6617"></td><td hx="045f20"></td><td hx="005824"></td><td hx="005951"></td>';
	hexTable += '<td hx="005b7e"></td><td hx="003562"></td><td hx="002056"></td><td hx="0c004b"></td>';
	hexTable += '<td hx="30004a"></td><td hx="4b0048"></td><td hx="7a0045"></td><td hx="7a0026"></td>';
	hexTable += '</tr></thead>';

	hexTable += '<tbody><tr><td style="cursor:default;height:60px;border:1px solid #000;background:#fff;" colspan="16">';
	
	hexTable += '<form class="hexRGB"><p>';
	hexTable += '<input onkeyup="yHx.updateSwatch('+this.incrementer+');" value="'+pickerElement.value.substr(0,2)+'" maxlength="2" type="text" size="2" class="hxR" id="hxR'+yHx.incrementer+'" />';
	hexTable += '<input onkeyup="yHx.updateSwatch('+this.incrementer+');" value="'+pickerElement.value.substr(2,2)+'" maxlength="2" type="text" size="2" class="hxG" id="hxG'+yHx.incrementer+'" />';
	hexTable += '<input onkeyup="yHx.updateSwatch('+this.incrementer+');" value="'+pickerElement.value.substr(4,2)+'" maxlength="2" type="text" size="2" class="hxB" id="hxB'+yHx.incrementer+'" /></p>';
	hexTable += '<p class="c"><input onclick="yHx.updateHex('+this.incrementer+');" class="submit" type="button" value="OK" style="position:absolute;bottom:1px;right:75px;" />';
	hexTable += '<input style="position:absolute;bottom:1px;right:2px;" class="submit" type="button" value="CANCEL" onclick="yHx.closeHexPicker('+this.incrementer+');" />';
	hexTable += '</p></form></td></tr></tbody></table>';
	hexTable += '<span id="ySwatch'+yHx.incrementer+'" style="display:block;position:absolute;top:90px;left:5px;margin:5px;width:35px;height:35px;border:1px solid #000;background-color:#'+pickerElement.value+';"></span>';
	this.incrementer = this.incrementer + 1;
	return hexTable;
	},
	
	showVal : function(e) {
	var cell = getEventSrc(e);
	var hexVal1 = document.getElementById('hxR'+yHx.currentPicker);
	var hexVal2 = document.getElementById('hxG'+yHx.currentPicker);
	var hexVal3 = document.getElementById('hxB'+yHx.currentPicker);
	var ySwatch = document.getElementById('ySwatch'+yHx.currentPicker);
	hexVal1.value = cell.getAttribute('hx').substr(0,2);
	hexVal2.value = cell.getAttribute('hx').substr(2,2);
	hexVal3.value = cell.getAttribute('hx').substr(4,2);
	ySwatch.style.backgroundColor = '#'+hexVal1.value+hexVal2.value+hexVal3.value;
	},
	
	initCellColors : function() {
	var hxs = getElementsByClass(document,'pickerTable','table');
		for ( i=0;i<hxs.length;i++ ) {
		var tbl = document.getElementById('hexSection'+i);
		var tblChilds = tbl.childNodes;
			for ( j=0;j<tblChilds.length;j++ ) {
			var tblCells = tblChilds[j].childNodes;
				for ( k=0;k<tblCells.length;k++ ) {
				addEvent(tblChilds[j].childNodes[k],'click',yHx.showVal,false);
				tblChilds[j].childNodes[k].style.backgroundColor = '#'+tblChilds[j].childNodes[k].getAttribute('hx');
				}
			}
		}
	},
	
	appendHexTable : function(obj,ref,tp,lft) {
	var hexTable = document.createElement('div');
	document.body.appendChild(hexTable);
	hexTable.id = 'hexTable'+ref;
	hexTable.className = 'pickerBox';
	hexTable.style.position = 'absolute';
	hexTable.style.zIndex = '1000';
	hexTable.style.top = tp+'px';
	hexTable.style.left = eval(lft+30)+'px';
	hexTable.style.display = 'none';
	hexTable.innerHTML = yHx.hexPallete();
	},

	updateSwatch : function(ref) {
	var hexVal1 = document.getElementById('hxR'+yHx.currentPicker);
	var hexVal2 = document.getElementById('hxG'+yHx.currentPicker);
	var hexVal3 = document.getElementById('hxB'+yHx.currentPicker);
	var swatch = document.getElementById('ySwatch'+ref);
	var offSet = 0;
	var zeroStr = "";
	var hexiDec = hexVal1.value.toString()+hexVal2.value.toString()+hexVal3.value.toString();
		if ( hexiDec.length < 6 )
		offSet = (6 - parseInt(hexiDec.length));
		for ( i=0;i<offSet;i++ )
		zeroStr += "0";
	swatch.style.backgroundColor = '#'+zeroStr+hexiDec;
	},
	
	updateHex : function(ref) {
	var pickerBox = document.getElementById('hexTable'+ref);
	var pickerInputs = getElementsByClass(document,'yHxColorPicker','input');
	var hexVal1 = document.getElementById('hxR'+yHx.currentPicker);
	var hexVal2 = document.getElementById('hxG'+yHx.currentPicker);
	var hexVal3 = document.getElementById('hxB'+yHx.currentPicker);
	var swatch = document.getElementById('swatch'+ref);
	yHx.hideShim();
		for ( i=0;i<pickerInputs.length;i++ ) {
			if ( pickerInputs[i].getAttribute('hexParent') == ref ) {
			var pickerInput = pickerInputs[i];
			break;
			}
		}
	pickerInput.value = hexVal1.value+hexVal2.value+hexVal3.value;
	swatch.style.backgroundColor = '#'+pickerInput.value;
	pickerBox.style.display = 'none';
	yHx.hexOpen = false;
	},
	
	closeHexPicker : function(ref) {
	var pickerBox = document.getElementById('hexTable'+ref);
	yHx.hideShim();
	pickerBox.style.display = 'none';
	yHx.hexOpen = false;
	},
	
	openHexPicker : function(e) {
		if ( yHx.isDisabled == true ) return;
	var obj = getEventSrc(e);
	var num = obj.getAttribute('hexChooser');
	var hexTable = document.getElementById('hexTable'+num);
	var hexTables = getElementsByClass(document,'pickerBox','div');
	yHx.hideShim();
		for ( i=0;i<hexTables.length;i++ )
		hexTables[i].style.display = 'none';
		if ( yHx.hexOpen == false ) {
		yHx.hexOpen = true;
		hexTable.style.display = 'block';
		yHx.moveShim(hexTable);		
		}
		else {
			if ( yHx.currentPicker == num ) {
			yHx.hexOpen = false;
			}
			else {
			hexTable.style.display = 'block';
			yHx.moveShim(hexTable);
			}
		}
	yHx.currentPicker = num;
	},
	
	moveShim : function(hexTable) {
		if ( yHx.isIE == true ) {
		var shim = document.getElementById(yHx.shim);
		shim.style.display = 'block';
		shim.style.width = hexTable.offsetWidth+'px';
		shim.style.height = hexTable.offsetHeight+'px';
		shim.style.left = findPosX(hexTable)+'px';
		shim.style.top = findPosY(hexTable)+'px';
		}
	},
	
	hideShim : function() {
		if ( yHx.isIE == true ) {
		var shim = document.getElementById(yHx.shim);
		shim.style.display = 'none';
		}
	},
	
	appendShim : function() {
		if ( yHx.isIE == true ) {
		var shim = document.createElement('iframe');
		document.body.appendChild(shim);
		shim.style.display = 'none';
		shim.style.zIndex = '999';
		shim.style.position = 'absolute';
		shim.style.border = 'none';
		shim.id = 'yHxPickerShim';
		}
	},
	
	appendChoosers : function() {
	var pickers = getElementsByClass(document,'yHxColorPicker','input');
	var offSet = 10;
	yHx.appendShim();
		for ( i=0;i<pickers.length;i++ ) { 
		var span = document.createElement('span');
		var par = pickers[i].parentNode;
		par.appendChild(span);
		pickers[i].setAttribute('hexParent',i);
		span.setAttribute('hexChooser',i);
		span.className = 'picker';
		span.id = 'swatch'+i;
		span.style.position = 'absolute';
		var topPos = eval(findPosY(pickers[i])+((pickers[i].offsetHeight/2) - offSet));
		var leftPos = eval(findPosX(pickers[i])+pickers[i].offsetWidth+offSet);
		span.style.top = topPos+'px';
		span.style.left = leftPos+'px';
		span.style.backgroundColor = '#'+pickers[i].defaultValue;
		yHx.appendHexTable(span,i,topPos,leftPos)
		addEvent(span,'click',yHx.openHexPicker,false);
			if ( yHx.isDisabled == true ) {
			span.style.opacity = '.5';
			span.style.filter = "alpha(opacity=50)";
			}
		}
	},
	initColorPicker : function() {
		if ( !document.getElementById || !document.getElementsByTagName || !document.createElement ) {
		alert('The use of the Color Picker on this page requires a modern browser to operate correctly. Please upgrade appropriately or just use the given input fields to type in the value of your choice');
		return;
		}
		if ( navigator.appName == 'Microsoft Internet Explorer' )
		yHx.isIE = true;
	yHx.appendChoosers();
	yHx.initCellColors();
	}
};