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
    'AACAudioType',
    'Mp3AudioType',
    'WaveAudioType',
    'M4AAudioType',
)


class AACAudioType( FileType ):
    verbose_name = ugettext_noop(u'AAC Audio File')
    exts = ['aac', 'm4a']
    bitrate = 192


class Mp3AudioType( FileType ):
    verbose_name = ugettext_noop(u'MP3 Audio File')
    exts = ['mp3']


class M4AAudioType( FileType ):
    verbose_name = ugettext_noop(u'M4A Audio File')
    exts = ['m4a']


class WaveAudioType( FileType ):
    verbose_name = ugettext_noop(u'WAV Audio File')
    exts = ['wav']
