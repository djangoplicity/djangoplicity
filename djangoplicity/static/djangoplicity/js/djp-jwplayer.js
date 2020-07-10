function setupVideoPlayer(video_id) {
    jwplayer.key = 'EAjAk7x879BjeiN54i9pMZjIrVJMCTtZFFMcmY2yiTI=';

    // Replace '-' by '_' in video_id if any:
    config_video_id = video_id.replace(/-/g, '_', 'g');

    var config = window['config_' + config_video_id];

    // Check if we have a playlist defined:
    if (typeof playlist !== 'undefined') {
        config.playlist = playlist;

        if (typeof listbar !== 'undefined') {
            config.listbar = listbar;
        } else {
            config.listbar = {
                position: 'right',
                size: 240
            };
        }
    }

    // Set default options:
    if (!('width' in config))
        config['width'] = '100%';
    if (!('skin' in config))
        config['skin'] = 'glow';
    if (!('primary' in config))
        config['primary'] = 'html5';
    if (!('aspectratio' in config))
        config['aspectratio'] = '16:9';
    if (!('autostart' in config))
        config['autostart'] = 'false';
    if (!('ga' in config) && (typeof jwplayer_ga !== 'undefined'))
        config['ga'] = jwplayer_ga;
    if (!('html5player' in config) && (typeof jwplayer_html5player !== 'undefined'))
        config['html5player'] = jwplayer_html5player;
    if (!('flashplayer' in config) && (typeof jwplayer_flashplayer !== 'undefined'))
        config['flashplayer'] = jwplayer_flashplayer;

    jwplayer('videoplayer-' + video_id).setup(config);
}

function setupAudioPlayer(archive_id) {
    jwplayer.key = 'EAjAk7x879BjeiN54i9pMZjIrVJMCTtZFFMcmY2yiTI=';

    // Replace '-' by '_' in archive_id if any:
    config_archive_id = archive_id.replace(/-/g, '_', 'g');

    var config = window['config_' + config_archive_id];

    // Set default options:
    if (!('width' in config))
        config['width'] = '100%';
    if (!('skin' in config))
        config['skin'] = 'glow';
    if (!('primary' in config))
        config['primary'] = 'html5';
    if (!('autostart' in config))
        config['autostart'] = 'false';
    if (!('ga' in config) && (typeof jwplayer_ga !== 'undefined'))
        config['ga'] = jwplayer_ga;
    if (!('html5player' in config) && (typeof jwplayer_html5player !== 'undefined'))
        config['html5player'] = jwplayer_html5player;
    if (!('flashplayer' in config) && (typeof jwplayer_flashplayer !== 'undefined'))
        config['flashplayer'] = jwplayer_flashplayer;

    jwplayer('audioplayer-' + archive_id).setup(config);
}


// Configure popup video players
$(document).ready(function() {
    $(this).find('.popup-youtube').click(function() {
        var title = $(this).attr('data-title');
        var url = $(this).attr('data-url');
        var youtubeID = $(this).attr('data-youtube-id');

        $('#popup-youtube').find('.title').html(title);
        $('#popup-youtube').find('a').first().attr('href', url);

        setTimeout(function() {
            player.loadVideoById(youtubeID);
        }, 500);
    });

    $(this).find('.popup-jwplayer').click(function() {
        var title = $(this).attr('data-title');
        var url = $(this).attr('data-url');
        var videoID = $(this).attr('data-video-id');

        $('#popup-jwplayer').find('.title').html(title);
        $('#popup-jwplayer').find('a').first().attr('href', url);

        // Replace '-' by '_' in video_id if any:
        var config_video_id = videoID.replace(/-/g, '_', 'g');
        var config = window['config_' + config_video_id];
        jwplayer.key = 'EAjAk7x879BjeiN54i9pMZjIrVJMCTtZFFMcmY2yiTI=';

        config.height = '550px'; // We fix the height otherwise jwplayer
        // doesn't use the full height on the second
        // play
        jwplayer('videoplayer').setup(config);
        jwplayer('videoplayer').play();
    });
});
