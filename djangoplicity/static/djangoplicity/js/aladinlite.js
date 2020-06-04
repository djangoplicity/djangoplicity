$(document).ready(function() {
	if ($('div#aladin-lite-div').length) {
		
		var aladin = A.aladin('#aladin-lite-div', aladin_params);
		aladin.displayJPG(aladin_jpg_url);
	}
});
