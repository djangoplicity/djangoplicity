# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.utils.translation import ugettext_noop
from djangoplicity.archives.resources import FileType

__all__ = (
    'EPUBType',
    'PDFType',
    'PostScriptType',
    'ZipType',
    'PowerpointPresentationType',
    'PowerpointSlideshowType',
    'DocType',
    'TxtType',
    'IllustratorType',
    'InDesignType',
    'EpsType',
    'DirType',
    'PPTType',
    'PPSType',
    'Model3dObjType',
    'Model3dC4DType'
)


class DirType ( FileType ):
    verbose_name = ugettext_noop(u'Directory')
    exts = []


class InDesignType ( FileType ):
    verbose_name = ugettext_noop(u'InDesign Document File')
    exts = ['indd']


class PowerpointPresentationType( FileType ):
    verbose_name = ugettext_noop(u'Powerpoint Presentation')
    exts = ['ppt', 'pptx']


class PowerpointSlideshowType( FileType ):
    verbose_name = ugettext_noop(u'Powerpoint Slideshow')
    exts = ['pps']


class PDFType( FileType ):
    verbose_name = ugettext_noop(u'PDF File')
    exts = ['pdf']


class EPUBType( FileType ):
    verbose_name = ugettext_noop(u'EPUB File')
    exts = ['epub']


class PostScriptType( FileType ):
    verbose_name = ugettext_noop(u'PostScript File')
    exts = ['gz']


class ZipType( FileType ):
    verbose_name = ugettext_noop(u'ZIP File')
    exts = ['zip']


class DocType( FileType ):
    verbose_name = ugettext_noop(u'Word File')
    exts = ['doc']


class PPTType( FileType ):
    verbose_name = ugettext_noop(u'Powerpoint Presentation')
    exts = ['ppt']


class PPSType( FileType ):
    verbose_name = ugettext_noop(u'Powerpoint Slideshow')
    exts = ['pps']


class TxtType( FileType ):
    verbose_name = ugettext_noop(u'Text File')
    exts = ['txt']


class IllustratorType( FileType ):
    verbose_name = ugettext_noop('Illustrator File')
    exts = ['ai']


class EpsType( FileType ):
    verbose_name = ugettext_noop('EPS File')
    exts = ['eps']


class Model3dObjType( FileType ):
    verbose_name = ugettext_noop( u'Wavefront (.obj)' )
    exts = ['obj', 'zip']


class Model3dC4DType( FileType ):
    verbose_name = ugettext_noop( u'Maxon Cinema 4D (.c4d)' )
    exts = ['c4d', 'zip']
