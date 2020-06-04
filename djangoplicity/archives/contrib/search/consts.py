# -*- coding: utf-8 -*-
#
# djangoplicity-archives
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext_noop

ADV_SEARCH_START_YEAR = getattr( settings, 'ADV_SEARCH_START_YEAR', 1984 )

VALID_OPERATORS = ['gte', 'gt', 'lt', 'lte', 'exact', 'icontains']

LOGIC_REPR = {
  'icontains': ugettext_noop( 'containing' ),
  'gte': ugettext_noop( 'greater than or equal to' ),
  'gt': ugettext_noop( 'greater than' ),
  'lte': ugettext_noop( 'less than or equal to' ),
  'lt': ugettext_noop( 'less than' ),
  'exact': ugettext_noop( 'matching' ),
}

IMAGE_SIZES = (
    ( 0, 'Select...' ),
    ( 1, "400x300" ),
    ( 2, "640x480" ),
    ( 3, "800x600" ),
    ( 4, "1024x768" ),
    ( 5, "2 MP (1600x1200)" ),
    ( 6, "4 MP (2272x1704)" ),
    ( 7, "6 MP (2816x2212)" ),
    ( 8, "8 MP (3264x2448)" ),
    ( 9, "10 MP (3648x2736)" ),
    ( 10, "12 MP (3648x2736)" ),
    ( 11, "15 MP (4480x3360)" ),
    ( 12, "20 MP (5120x3840)" ),
    ( 13, "40 MP (7216x5412)" ),
    ( 14, "70 MP (9600x7200)" ),
    ( 15, "100 MP (11544x8658)" ),
    ( 16, "250 MP (18256x13692)" ),
    ( 17, "500 MP (25816x19362)" ),
    ( 18, "1000 MP (36512x27384)" ),
)

FOV_CHOICES = (
    (0, _(u'Select...')),
    (4, _(u'180-270° width')),  # These were added after hence the different
    (5, _(u'270-360° width')),  # sequence number
    (1, _(u'360° width')),
    (2, _(u'360° width, 180° height')),
    (3, _(u'360° width, >= 90° height')),
)

IMAGE_DIMS = {
    "0": ( None, None, None ),
    "1": ( 400, 300, 120000 ),
    "2": ( 640, 480, 307200 ),
    "3": ( 1024, 768, 786432 ),
    "4": ( 800, 600, 480000 ),
    "5": ( 1600, 1200, 1920000 ),
    "6": ( 2272, 1704, 3871488 ),
    "7": ( 2816, 2212, 6228992 ),
    "8": ( 3264, 2448, 8871552 ),
    "9": ( 3648, 2736, 9980928 ),
    "10": ( 4096, 3072, 12582912 ),
    "11": ( 4480, 3360, 15052800 ),
    "12": ( 5120, 3840, 19660800 ),
    "13": ( 7216, 5412, 39052992 ),
    "14": ( 9600, 7200, 69120000 ),
    "15": ( 11544, 8658, 100000000 ),
    "16": ( 18256, 13692, 250000000 ),
    "17": ( 25816, 19362, 500000000 ),
    "18": ( 36512, 27384, 1000000000 ),
}

VIDEO_SIZES = (
    ( 0, 'Select...' ),
    ( 1, "320x180" ),
    ( 2, "640x360" ),
    ( 3, "720x406" ),
    ( 4, "HD (1280x720)" ),
    ( 5, "Full HD (1920x1080)" ),
    ( 6, "4K UHD (3840x2160)" ),
    ( 7, "Fulldome (4096x4096)" ),
)

VIDEO_DIMS = {
    "0": ( None, None ),
    "1": ( 320, 180 ),
    "2": ( 640, 360 ),
    "3": ( 720, 406 ),
    "4": ( 1280, 720 ),
    "5": ( 1920, 1080 ),
    "6": ( 3840, 2160 ),
    "7": ( 4096, 4096 ),
}

PRIO_CHOICES = (
    ( 0, _( 'All' ) ),
    ( 80, _( 'Highest only' ) ),
    ( 70, _( 'Good or better' ) ),
    ( 40, _( 'Average or better' ) ),
    ( 20, _( 'Fair or better' ) ),
)
