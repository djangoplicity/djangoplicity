document.addEventListener('DOMContentLoaded', function() {
	compass_init();
}, false);


// Compas widget
// Expects one compass_canvas canvas:
//    <canvas id="compass_canvas" width="240" height="140"></canvas>
// Expects two variables set in page:
//    spatial_rotation: spatial rotation in degrees
//    compass_src: path to the compass image file

function compass_init()
{
	// Set variables
	angle = 0;
	speed = 5;
	max_speed = 20;
	min_speed = 5;
	canvas = document.getElementById('compass_canvas');
	if (!canvas)
		return;

	ctx = canvas.getContext('2d');
	if (!ctx) {
		// Canvas not supported
		canvas.style.display = 'none';
		return;
	}

	compass = new Image();
	compass.src = compass_src;
	compass.onload = compass_loaded;
	if (spatial_rotation < 0)
		direction = 'ccw';
	else
		direction = 'cw';
}

function compass_loaded()
{
	compass_interval_id = setInterval(compass_draw, 50);
}

function compass_draw()
{
	ctx.clearRect( 0, 0, canvas.width, canvas.height );
	ctx.save();
	ctx.translate( canvas.width/2 , canvas.height/2 );
	if (angle == spatial_rotation) {
		clearInterval(compass_interval_id);
	}
	if (direction == 'cw') {
		if (angle + speed > spatial_rotation)
			angle = spatial_rotation;
		else
			angle += speed;
		if (spatial_rotation / 2 > angle) {
			// increase speed
			if (speed < max_speed)
				speed += 1;
		}
		else if (spatial_rotation / 2 < angle) {
			// decrease speed
			if (speed > min_speed)
				speed -= 1;
		}
	} else {
		if (angle - speed < spatial_rotation)
			angle = spatial_rotation;
		else
			angle -= speed;
		if (spatial_rotation / 2 < angle) {
			// increase speed
			if (speed < max_speed)
				speed += 1;
		}
		else if (spatial_rotation / 2 < angle) {
			// decrease speed
			if (speed > min_speed)
				speed -= 1;
		}
	}
	// we rotate by -angle as the compas turns, not the image
	ctx.rotate( -angle*Math.PI/180 );
	ctx.drawImage( compass, -compass.width/2, -compass.height/2 );
	ctx.restore();
}
