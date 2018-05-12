/* 
Element Toggle Script by Dustin Diaz
Date Last Modified: Aug 12, 2005
Instructions:
1) Separate your sections with div.toggleSection
2) Separate your groups (within sections) with fieldset.toggleGroup
3) Create your element enablers with input.toggleEnable
4) Add .toggleField to any element that wants to be part of the action inside your toggle groups
*/
function attachEnablers() {
var secRadio = getElementsByClass(document,'toggleEnable','input');
var secRadioLen = secRadio.length;
	for ( i=0;i<secRadioLen;i++ ) {
	addEvent(secRadio[i], 'click', toggleSections, false);
	}
}
function toggleSections() {
var sections = getElementsByClass(document,'toggleSection','div');
var sectionsLen = sections.length;
var j = 0;
	for ( j=0;j<sectionsLen;j++ ) {
	var groups = getElementsByClass(sections[j],'toggleGroup','fieldset');
	var groupsLen = groups.length;
	var k = 0;
		for ( k=0;k<groupsLen;k++ ) {
		var togEls = getElementsByClass(groups[k],'toggleEnable', 'input');
		
			if ( togEls[0].checked == true ) {
			var fields = getElementsByClass(groups[k],'toggleField', '*');
			var fieldsLen = fields.length;
			var m = 0;
				for ( m=0;m<fieldsLen;m++ )
				fields[m].disabled = false;
			// groups[k].style.color = 'black';
			groups[k].className = (groups[k].className).toString().replace(' soft','');
			groups[k].className = (groups[k].className).toString().replace(' full','');
			groups[k].className += ' full';
			}
			else {
			var n = 0;
			var fields = getElementsByClass(groups[k],'toggleField', '*');
			var fieldsLen = fields.length;
				for ( n=0;n<fieldsLen;n++ )
				fields[n].disabled = true;
			// groups[k].style.color = '#cccccc';
			groups[k].className = (groups[k].className).toString().replace(' full','');
			groups[k].className = (groups[k].className).toString().replace(' soft','');
			groups[k].className += ' soft';
			}
		}
	}
}