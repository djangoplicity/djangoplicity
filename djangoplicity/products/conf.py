# -*- coding: utf-8 -*-
#
# djangoplicity-products
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
#

"""
Configuration of root paths for all product archives.
"""

from django.conf import settings

ARCHIVE_ROOT = settings.ARCHIVE_ROOT if hasattr( settings, 'ARCHIVE_ROOT' ) else 'archives/'

if len( ARCHIVE_ROOT ) > 0 and ARCHIVE_ROOT[-1] != '/':
    ARCHIVE_ROOT = ARCHIVE_ROOT + '/'


class archive_settings:
    APPLICATION_ROOT = ARCHIVE_ROOT + 'applications'
    MEDIA_ROOT = ARCHIVE_ROOT + 'media'
    PRINTEDPOSTER_ROOT = ARCHIVE_ROOT + 'print_posters'
    CONFERENCEPOSTER_ROOT = ARCHIVE_ROOT + 'conf_posters'
    ELECTRONICPOSTER_ROOT = ARCHIVE_ROOT + 'elec_posters'
    CONFERENCE_POSTER_ROOT = ARCHIVE_ROOT + 'conference_posters'
    LOGO_ROOT = ARCHIVE_ROOT + 'logos'
    BOOK_ROOT = ARCHIVE_ROOT + 'books'
    BROCHURE_ROOT = ARCHIVE_ROOT + 'brochures'
    FLYER_ROOT = ARCHIVE_ROOT + 'flyers'
    STATIONERY_ROOT = ARCHIVE_ROOT + 'stationery'
    MAP_ROOT = ARCHIVE_ROOT + 'maps'
    CALENDAR_ROOT = ARCHIVE_ROOT + 'calendars'
    PRESSKIT_ROOT = ARCHIVE_ROOT + 'presskits'
    STICKER_ROOT = ARCHIVE_ROOT + 'stickers'
    TECHDOC_ROOT = ARCHIVE_ROOT + 'techdocs'
    MERCHANDISE_ROOT = ARCHIVE_ROOT + 'merchandise'
    APPAREL_ROOT = ARCHIVE_ROOT + 'apparel'
    ELECTRONICCARD_ROOT = ARCHIVE_ROOT + 'electroniccards'
    STECFNEWSLETTER_ROOT = ARCHIVE_ROOT + 'stecfnewsletters'
    CAPJOURNAL_ROOT = ARCHIVE_ROOT + 'capjournals'
    MESSENGER_ROOT = ARCHIVE_ROOT + 'messengers'
    SCIENCEINSCHOOL_ROOT = ARCHIVE_ROOT + 'schools'
    BULLETIN_ROOT = ARCHIVE_ROOT + 'bulletins'
    FITS_IMAGE_ROOT = ARCHIVE_ROOT + 'fitsimages'
    KIDS_DRAWING_ROOT = ARCHIVE_ROOT + 'drawings'
    EDUMATERIAL_ROOT = ARCHIVE_ROOT + 'education'
    ONLINE_ART_ROOT = ARCHIVE_ROOT + 'art'
    ONLINE_ART_AUTHOR_ROOT = ARCHIVE_ROOT + 'artists'
    POSTCARD_ROOT = ARCHIVE_ROOT + 'postcards'
    EXHIBITION_ROOT = ARCHIVE_ROOT + 'exhibitions'
    USER_VIDEO_ROOT = ARCHIVE_ROOT + 'uservideos'
    PRESENTATION_ROOT = ARCHIVE_ROOT + 'presentations'
    PRINT_LAYOUT_ROOT = ARCHIVE_ROOT + 'printlayouts'
    ANNUAL_REPORT_ROOT = ARCHIVE_ROOT + 'annualreports'
    REPORT_ROOT = ARCHIVE_ROOT + 'reports'
    HANDOUT_ROOT = ARCHIVE_ROOT + 'handouts'
    MINISITE_ROOT = ARCHIVE_ROOT + 'minisites'
    PAPER_MODEL_ROOT = ARCHIVE_ROOT + 'papermodels'
    PLANETARIUM_SHOW_ROOT = ARCHIVE_ROOT + 'planetariumshows'
    IMAX_FILM_ROOT = ARCHIVE_ROOT + 'imaxfilms'
    MODEL3D_FILM_ROOT = ARCHIVE_ROOT + 'models3d'
    EPUBLICATION_ROOT = ARCHIVE_ROOT + 'epublications'
    VIRTUAL_TOUR_ROOT = ARCHIVE_ROOT + 'virtualtours'
    MOUNTED_IMAGE_ROOT = ARCHIVE_ROOT + 'mountedimages'
    CONFERENCEITEM_ROOT = ARCHIVE_ROOT + 'conferenceitems'
    VISIT_ROOT = ARCHIVE_ROOT + 'visits'
    DONATION_ROOT = ARCHIVE_ROOT + 'donations'
    SUPERNOVA_ACTIVITY_ROOT = ARCHIVE_ROOT + 'supernovaactivities'
    MUSIC_ROOT = ARCHIVE_ROOT + 'music'
