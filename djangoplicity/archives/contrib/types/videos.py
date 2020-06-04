# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>


from django.utils.translation import ugettext_noop
from djangoplicity.archives.resources import FileType


class LegacyVideo(FileType):
    verbose_name = ugettext_noop(u'Legacy Video')
    exts = ['m4v', 'flv', 'mov', 'avi', 'mpeg', 'mp4', 'mpg', 'mp2', 'gif' ]
    content_type = 'video/*'


class VodcastType(FileType):
    verbose_name = ugettext_noop(u'Video Podcast')
    exts = ['m4v', 'm4v']


class FlvType(FileType):
    verbose_name = ugettext_noop(u'Flash Video')
    exts = ['flv']


class SwfType(FileType):
    verbose_name = ugettext_noop(u'Flash')
    exts = ['swf']


class HD720PType(FileType):
    verbose_name = ugettext_noop(u'HD 720p')
    exts = ['m4v', 'mp4']


class HD1080PType(FileType):
    verbose_name = ugettext_noop(u'HD 1080p')
    exts = ['mp4', 'm4v']


class H264Type(FileType):
    verbose_name = ugettext_noop(u'H.264 MPEG-4')
    exts = ['mp4', 'm4v']


class M4VType(FileType):
    verbose_name = ugettext_noop(u'M4V')
    exts = ['m4v']


class MP4Type(FileType):
    verbose_name = ugettext_noop(u'MP4')
    exts = ['mp4']


class MpegType(FileType):
    verbose_name = ugettext_noop(u'MPEG')
    exts = ['mpg', 'mpeg']


class MovType(FileType):
    verbose_name = ugettext_noop(u'Quicktime')
    exts = ['mov']


class BroadcastType(FileType):
    verbose_name = ugettext_noop('Broadcast')
    exts = ['avi', 'mxf', 'm2t']


class HDAndAppleType(M4VType):
    width = 1280
    height = 720


class DomeMovType(FileType):
    verbose_name = ugettext_noop(u'Fulldome 1.5k mov')
    exts = ['mov', 'mp4']
    width = 1536
    height = 1536


class Dome2kMasterType(FileType):
    verbose_name = ugettext_noop(u'Fulldome 2k Master')
    exts = ['avi', 'zip']
    width = 2048
    height = 2048


class Dome4kMasterType(FileType):
    verbose_name = ugettext_noop(u'Fulldome 4k Master')
    exts = ['avi', 'zip']
    width = 4096
    height = 4096


class Dome8kMasterType(FileType):
    verbose_name = ugettext_noop(u'Fulldome 8k Master')
    exts = ['avi', 'zip']
    width = 8192
    height = 8192


class MediumPodcastType(FileType):
    verbose_name = ugettext_noop(u'Video Podcast')
    exts = ['m4v', 'mp4']


class DomePreviewType(FileType):
    verbose_name = ugettext_noop(u'Fulldome Preview')
    exts = ['mp4']
    width = 1024
    height = 1024


class VR8kType(FileType):
    verbose_name = ugettext_noop(u'8k VR')
    exts = ['mp4']
    width = 4096
    height = 2048


class VR4kType(FileType):
    verbose_name = ugettext_noop(u'4k VR')
    exts = ['mp4']
    width = 8192
    height = 4096


class CylindricalPreviewType(FileType):
    verbose_name = ugettext_noop(u'Cylindrical VR Preview')
    exts = ['mp4']


class Cylindrical4kMasterType(FileType):
    verbose_name = ugettext_noop(u'4k Cylindrical VR Master')
    exts = ['zip']


class Cylindrical8kMasterType(FileType):
    verbose_name = ugettext_noop(u'8k Cylindrical VR Master')
    exts = ['zip']


class Cylindrical16kMasterType(FileType):
    verbose_name = ugettext_noop(u'16k Cylindrical VR Master')
    exts = ['zip']


class UltraHDType(FileType):
    verbose_name = ugettext_noop(u'Ultra HD (4k/2160p)')
    exts = ['mp4']
    width = 3840
    height = 2160


class FullHDPreview1080p(MP4Type):
    width = 1920
    height = 1080


class UltraHDH265Type(FileType):
    verbose_name = ugettext_noop(u'Ultra HD (4k/2160p)')
    exts = ['mkv', 'mp4']


class UltraHDBroadcastType(FileType):
    verbose_name = ugettext_noop(u'Ultra HD Broadcast (4k/2160p)')
    exts = ['avi']


class BroadcastSDType(FileType):
    verbose_name = ugettext_noop(u'Brodcast SD')
    exts = ['mxf', 'avi', 'mov']  # mov to be removed


class SubtitleType (FileType):
    verbose_name = ugettext_noop(u'Subtitle')
    exts = ['srt']


class AudioTrackType (FileType):
    verbose_name = ugettext_noop(u'Audio Track')
    exts = ['zip', 'wav']
