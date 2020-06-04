if(sdfile){
	var config = { 	 
			file: sdfile, 
			width: width, 
			height: height,
			autostart: false,
			players : [
				{ type : "flash", src: flashsrc },
				{ type : "html5" }
			],
			backcolor : "0x000000",
			frontcolor: "0xCCCCCC",
			lightcolor : "0x005ba0"
	};
	if( imagefile ) {
		config.image = imagefile;
	}
	if( jwplayer.utils.hasFlash() ) {
		config.plugins = {
				sharing : { link : sharelink , code : sharecode },
				gapro: { accountid: gaid }
			};
		if( hdfile ) {
			config.plugins.hd = { file: hdfile }
		}
	} else {
		var isiPad = navigator.userAgent.match(/iPad/i) != null;
		
		if( isiPad ) {
			config.file = ipadfile;
		} else {
			config.file = mobilefile;		
		}
	}
	if (subs.length == 1)
	{
		config.plugins['captions-2'] = {
		           'file': subs[0]
		    }
	
	} 
	if (subs.length > 1) {
		config.plugins['captions-2'] = {
		           'files': subs.join(","),
		           'labels': labels.join(",")
		    }
	
	}
	jwplayer("flashplayer").setup( config );	
}