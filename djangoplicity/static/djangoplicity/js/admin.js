// Djangoplicity
// Copyright 2008-2009
//
// Authors:
//   Lars Holm Nielsen <lnielsen@eso.org>
//   Luis Clara Gomes <lcgomes@eso.org>
//


//
// Firefox spellcheck on single-line input fields (not automatically enabled).
//
$(document).ready( function() {
	$(".vTextField").attr("spellcheck", true );
} );

//
// Priority slider for archives
//
$(document).ready(function(){
	var selector = '.vPrioritySlider';
	if ($(selector).length) {
		$(selector).slider( {
			min: 0,
			max: 100,
			step: 1,
			slide: function( event, ui ) {
						valuediv = '#' + event.target.id + "_val";
						valueinput = '#' + event.target.id.replace(/_slider$/g,"");
						$( valuediv  ).text( ui.value + ' %' );
						$( valueinput ).val( ui.value )			;
				}
		});


		$(".vPrioritySlider").map( function(){
			valuediv = '#' + this.id + "_val";
			valueinput = '#' + this.id.replace(/_slider$/g,"");

			val =  $( valueinput ).val() ;
			$(this).slider( 'value', val );
			$( valuediv  ).text( val + ' %' );
		});
	}
});
