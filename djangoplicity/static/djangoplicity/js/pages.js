function livePageEdit() {
	var editable = $('div#editable-content');

	if (editable.length === 0) {
		console.log('No div#editable-content found');
		return;
	}

	// Get the CSRF Token from the cookies and setup ajax calls
	var csrftoken = getCookie('csrftoken');

	$.ajaxSetup({
		beforeSend: function(xhr, settings) {
			if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
				xhr.setRequestHeader('X-CSRFToken', csrftoken);
			}
		}
	});

	// Turn on live edit
	editable.attr('contentEditable', 'true');

	// Display save button
	$('.admin_bar #save-button').css('display', 'block');

	// Hide edit button
	$('.admin_bar #edit-button').hide();
}

function livePageSave() {
	$('.admin_bar #save-button').button('loading');

	var data = {
		content: $('div#editable-content').html()
	};

	$.ajax({
		url: api_url,
		type: 'patch',
		data: data,
		success: function(){
			if ($('#edit-info-block #page-edit-success').length)
				$('#edit-info-block #page-edit-success').css('display', 'block');
		},
		error: function(XMLHttpRequest, textStatus, errorThrown) {
			if ($('#edit-info-block #page-edit-failure').length)
				$('#edit-info-block #page-edit-failure').css('display', 'block');
		},
		complete: function(){
			// Display edit button
			$('.admin_bar #edit-button').show();

			// Reset and hide save button
			$('.admin_bar #save-button').button('reset');
			$('.admin_bar #save-button').css('display', 'none');

			// Turn off live edit
			$('div#editable-content').attr('contentEditable', 'false');
		}
	});
}


// Function to get the CSRF token, see https://docs.djangoproject.com/en/dev/ref/csrf/#ajax
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
