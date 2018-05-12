/**************** FUNCTIONS **************/

jQuery.animateMenu = function(l, p, s) {
	$(l).stop().animate({'top' : p}, s);
}

jQuery.changeBackColor = function(l, hx) {
	$(l).css({'backgroundColor' : hx})
}


/**************** EVENTS **************/

$(document).ready(function() {
						   
/**************** Animate the menu *******************/

$('#FeaturesLink').hover(function(){$.animateMenu(this,'-60px',250)},function(){$.animateMenu(this,'-70px',500)});
$('#CaseLink').hover(function(){$.animateMenu(this,'-60px',250)},function(){$.animateMenu(this,'-70px',500)});
$('#SupportLink').hover(function(){$.animateMenu(this,'-60px',250)},function(){$.animateMenu(this,'-70px',500)});
$('#ContactLink').hover(function(){$.animateMenu(this,'-60px',250)},function(){$.animateMenu(this,'-70px',500)});

/**************** change the background colours *******************/

$('#right .views-row-even').hover(
						   function(){$.changeBackColor(this, '#eee')},
						   function(){$.changeBackColor(this, '#fff')}
						   );

$('#right .views-row-odd').hover(
						   function(){$.changeBackColor(this, '#eee')},
						   function(){$.changeBackColor(this, '#fff')}
						   );

$('#right .views-row-first').hover(
						   function(){$.changeBackColor(this, '#eee')},
						   function(){$.changeBackColor(this, '#fff')}
						   );

$('#main .feed-item').hover(
						   function(){$.changeBackColor(this, '#eee')},
						   function(){$.changeBackColor(this, '#fff')}
						   );

$('#main .views-row-odd').hover(
						   function(){$.changeBackColor(this, '#eee')},
						   function(){$.changeBackColor(this, '#fff')}
						   );

$('#main .views-row-even').hover(
						   function(){$.changeBackColor(this, '#eee')},
						   function(){$.changeBackColor(this, '#fff')}
						   );

/**************** Run the slideshow *******************/

$(window).bind("load", function() { 
										
	
	var imageTitle = $('#stripTransmitter0 a.current').attr("name");
	var imageText = $('#stripTransmitter0 a.current').attr("title");
		
	HTMLString = "<h3>"+imageTitle+"</h3>"
	HTMLString += "<p>"+imageText+"</p>"
	$('#pictitles').html(HTMLString);
	
	$('#pictitles').fadeIn(500);
	
	$('#stripTransmitter0 a').click(function() {
			imageTitle = $(this).attr("name");
			imageText = $(this).attr("title");
		
		$('#pictitles').fadeOut(250, function() {
		
			HTMLString = "<h3>"+imageTitle+"</h3>"
			HTMLString += "<p>"+imageText+"</p>"
		
			$('#pictitles').html(HTMLString);
		
		});
		
		$('#pictitles').fadeIn(500);
	});
}); 

/**************** change field focus highlight ******************

$('#Contact input').focus(function() {
								   $(this).toggleClass('focusedField');
								   })
					.blur(function() {
								   $(this).toggleClass('blurredField');
								   });*/
					
/***************   Tabs    *****************/					
					
					
});
