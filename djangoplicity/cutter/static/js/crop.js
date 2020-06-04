$( document ).ready(
	function() {
		$('.offset').change(
			function(e) {
				// Update crop areas
				console.log('Changed', e.target, e.target.value);
				var crop = $(e.target).closest('.crop');

				// Get initial value
				var initial = parseInt(crop.find('.crop-area').attr('data-initial'));
				var value = parseInt(e.target.value);

				crop.find('.crop-area-top').css(
					'height', initial + value
				);

				crop.find('.crop-area-bottom').css(
					'height', initial - value
				);

				crop.find('.crop-area-left').css(
					'width', initial + value
				);

				crop.find('.crop-area-right').css(
					'width', initial - value
				);
			}
		);
	}
);
