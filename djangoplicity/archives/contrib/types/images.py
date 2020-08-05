# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.utils.translation import ugettext_noop as _
from djangoplicity.archives.resources import ImageFileType, FileType


class OriginalImageType(ImageFileType):
    verbose_name = _(u'Fullsize Original')
    exts = ['tif', 'jpg', 'gif', 'png', 'tga', 'psb']
    content_type = 'image/*'


class TiffType(ImageFileType):
    content_type = 'image/tiff'
    compression_type = 'LZW'
    exts = ['tif']


class SvgType(ImageFileType):
    verbose_name = _(u'Scalable Vector Graphics (SVG)')
    exts = ['svg']
    content_type = 'image/svg+xml'


class PublicationTiff40KType(TiffType):
    verbose_name = _(u'Publication TIFF 40K')
    size = 40000
    required = False


class PublicationTiff25KType(TiffType):
    verbose_name = _(u'Publication TIFF 25K')
    size = 25000
    required = False


class PublicationTiff10KType(TiffType):
    verbose_name = _(u'Publication TIFF 10K')
    size = 10000
    required = False


class PublicationTiffType(TiffType):
    verbose_name = _(u'Publication TIFF 4K')
    size = 4000
    required = False


class ZoomableType(ImageFileType):
    verbose_name = _(u'Zoomable')
    exts = []


class PngType(ImageFileType):
    verbose_name = _('PNG')
    exts = ['png']
    content_type = 'image/png'


class BmpType(ImageFileType):
    verbose_name = _('BMP')
    exts = ['bmp']
    content_type = 'image/bmp'


class JpegType(ImageFileType):
    verbose_name = _('JPEG')
    exts = ['jpg']
    compression_quality = 90
    content_type = 'image/jpeg'


class LargeJpegType(ImageFileType):
    verbose_name = _('Large JPEG')
    exts = ['jpg']
    compression_quality = 90
    content_type = 'image/jpeg'


class PublicationJpegType(JpegType):
    verbose_name = _(u'Publication JPEG')
    compression_quality = 90
    size = 4000
    required = False


class ScreensizeJpegType(JpegType):
    verbose_name = _(u'Screensize JPEG')
    compression_quality = 85
    width = 1280
    unsharp = 25
    upscale = True


class Screen640Type(JpegType):
    verbose_name = _(u'Screen 640')
    compression_quality = 85
    width = 640
    height = 360
    unsharp = 25
    upscale = True


class MediumJpegType(JpegType):
    verbose_name = _('Medium JPEG')
    compression_quality = 90
    unsharp = 70
    width = 320
    upscale = True


class NewsJpegType(JpegType):
    verbose_name = _('News JPEG')
    compression_quality = 90
    unsharp = 80
    width = 180


class ThumbnailJpegType(JpegType):
    verbose_name = _('Thumbnail')
    compression_quality = 90
    unsharp = 80
    width = 122


class WallpaperThumbnailType(JpegType):
    verbose_name = _(u'Wallpaper Thumbnail')
    compression_quality = 90
    width = 122
    height = 92
    unsharp = 80


class NewsMiniJpegType(JpegType):
    verbose_name = _('News Mini JPEG')
    compression_quality = 90
    unsharp = 80
    width = 60


class NewsFeatureType(JpegType):
    verbose_name = _('News Feature JPEG')
    compression_quality = 85
    width = 733
    height = 300
    unsharp = 25
    upscale = True


class WallpaperSmallType(JpegType):
    verbose_name = _(u'1024x768')
    width = 1024
    height = 768


class Wallpaper1Type(JpegType):
    verbose_name = _(u'1024x768')
    width = 1024
    height = 768
    unsharp = 25
    upscale = True
    required = False


class Wallpaper2Type(JpegType):
    verbose_name = _(u'1280x1024')
    width = 1280
    height = 1024
    unsharp = 25
    upscale = True
    required = False


class Wallpaper3Type(JpegType):
    verbose_name = _(u'1600x1200')
    width = 1600
    height = 1200
    unsharp = 25
    upscale = True
    required = False


class Wallpaper4Type(JpegType):
    verbose_name = _(u'1920x1200')
    width = 1920
    height = 1200
    unsharp = 25
    upscale = True
    required = False


class Wallpaper5Type(JpegType):
    verbose_name = _(u'2048x1536')
    width = 2048
    height = 1536
    unsharp = 25
    upscale = True
    required = False


class WallpaperMediumType(JpegType):
    verbose_name = _(u'1280x1024')
    width = 1280
    height = 1024


class WallpaperLargeType(JpegType):
    verbose_name = _(u'1600x1200')
    width = 1600
    height = 1200


class VirtualTourType(FileType):
    verbose_name = _(u'Virtual Tour')
    exts = []


class POTWMediumThumbnailJpegType(JpegType):
    verbose_name = _(u'POTW Medium')
    compression_quality = 85
    width = 220
    height = 140
    unsharp = 25


class Thumb150yType(JpegType):
    verbose_name = _(u'Thumbnail 300y')
    compression_quality = 85
    height = 150
    unsharp = 70


class Thumb300yType(JpegType):
    verbose_name = _(u'Thumbnail 300y')
    compression_quality = 85
    height = 300
    unsharp = 70
    upscale = True


class Thumb300xPNGType(PngType):
    verbose_name = _(u'Thumbnail 300x PNG')
    compression_quality = 85
    width = 300
    unsharp = 70


class Thumb700xType(JpegType):
    verbose_name = _(u'Thumbnail 700x')
    compression_quality = 85
    width = 700
    unsharp = 25
    upscale = True


class Thumb350xType(JpegType):
    verbose_name = _(u'Thumbnail 350x')
    compression_quality = 85
    width = 350
    height = 223
    unsharp = 25
    upscale = True


class Banner1920Type(JpegType):
    verbose_name = _('Banner 1920x900')
    compression_quality = 80
    width = 1920
    height = 900
    unsharp = 25
    upscale = True


class VideoFrameType(JpegType):
    verbose_name = _('Video Frame')
    compression_quality = 85
    width = 640
    unsharp = 25


class Portrait1080Type(JpegType):
    verbose_name = _(u'Portrait 1080')
    compression_quality = 85
    width = 960
    height = 1080
    unsharp = 25
    upscale = True


class Poster400yType(JpegType):
    verbose_name = _(u'Poster 400y')
    compression_quality = 85
    width = 282
    height = 400
    unsharp = 25
    upscale = True
