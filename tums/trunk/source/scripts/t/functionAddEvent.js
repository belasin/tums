function addEvent(elm, evType, fn, useCapture) {
	if (elm.addEventListener) { 
	elm.addEventListener(evType, fn, useCapture); 
	return true; 
	}
	else if (elm.attachEvent) { 
	var r = elm.attachEvent('on' + evType, fn); 
	return r; 
	}
	else {
	elm['on' + evType] = fn;
	}
}
function getEventSrc(e) {
	if (!e) e = window.event;

	if (e.originalTarget)
	return e.originalTarget;
	else if (e.srcElement)
	return e.srcElement;
}
function addLoadEvent(func) {
var oldonload = window.onload;
	if (typeof window.onload != 'function') {
	window.onload = func;
	} else {
	window.onload = 
		function() {
		oldonload();
		func();
		}
	}
}