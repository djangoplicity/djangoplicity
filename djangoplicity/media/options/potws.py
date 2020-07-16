# -*- coding: utf-8 -*-
#
# djangoplicity-media
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

from builtins import object
from django.utils.translation import ugettext_noop
from djangoplicity.archives.contrib.browsers import ListBrowser, \
    SerializationBrowser
from djangoplicity.archives.contrib.queries import EmbargoQuery, \
    StagingQuery, YearQuery
from djangoplicity.archives.contrib.serialization.serializers import JSONEmitter, \
    ICalEmitter
from djangoplicity.archives.contrib.templater import DisplayTemplate
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.views import SerializationDetailView
from djangoplicity.media.queries import PotwAllPublicQuery
from djangoplicity.media.serializers import PictureOfTheWeekSerializer, \
    ICalPictureOfTheWeekSerializer


class PictureOfTheWeekOptions( ArchiveOptions ):
    urlname_prefix = "potw"

    detail_views = (
        { 'url_pattern': 'api/(?P<serializer>json)/', 'view': SerializationDetailView( serializer=PictureOfTheWeekSerializer, emitters=[JSONEmitter] ), 'urlname_suffix': 'serialization', },
    )

    search_fields = (
        'image__id', 'image__title', 'image__headline', 'image__description', 'image__subject_name__name', 'image__subject_name__alias', 'image__credit', 'image__type',
        'video__id', 'video__title', 'video__headline', 'video__description', 'video__subject_name__name', 'video__subject_name__alias', 'video__facility__name', 'video__credit', 'video__type',
    )

    class Queries( object ):
        default = PotwAllPublicQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Picture of the Week"), feed_name="default" )
        embargo = EmbargoQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Picture of the Week (embargoed)") )
        staging = StagingQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Picture of the Week (staging)") )
        year = YearQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Picture of the Week %d"), feed_name="default" )

    class Browsers( object ):
        normal = ListBrowser( paginate_by=20 )
        viewall = ListBrowser( paginate_by=100 )
        json = SerializationBrowser( serializer=PictureOfTheWeekSerializer, emitter=JSONEmitter, paginate_by=20, display=False, verbose_name=ugettext_noop( "JSON" ) )
        ical = SerializationBrowser( serializer=ICalPictureOfTheWeekSerializer, emitter=ICalEmitter, paginate_by=100, display=False, verbose_name=ugettext_noop( "iCal" ) )

    class Display( object ):
        multiple_potw = DisplayTemplate( 'template', '{%block org_prefix %}ESO{% endblock %} Picture of the Week: {{obj.image.title}}<br/><a href="{{site_url_prefix}}{{obj.get_absolute_url}}">{{site_url_prefix}}{{obj.get_absolute_url}}</a>', name='Multiple POTW list' )
        multiple_potw_text = DisplayTemplate( 'template', '{%block org_prefix %}ESO{% endblock %} Picture of the Week: {{obj.image.title}}<br/>{{site_url_prefix}}{{obj.get_absolute_url}}', name='Multiple POTW list (plaintext)' )
        potw_available_announcement = DisplayTemplate( 'file', 'archives/pictureoftheweek/email/translations_available_potw.html', name='Picture of the week available for translation' )

    @staticmethod
    def feeds():
        from djangoplicity.media.feeds import PictureOfTheWeekFeed
        feeds = {
            '': PictureOfTheWeekFeed,
        }
        return feeds
