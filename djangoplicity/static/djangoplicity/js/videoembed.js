if(sdfile){
	var config = { 	 
			file: sdfile, 
			width: 640, 
			height: 360,
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
	jwplayer("flashplayer").setup( config );	
}