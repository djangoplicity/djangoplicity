# -*- coding: utf-8 -*-
#
# djangoplicity-announcements
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
from djangoplicity.announcements.models import Announcement, AnnouncementProxy
from djangoplicity.announcements.serializers import AnnouncementSerializer, \
    ICalAnnouncementSerializer, WebUpdateSerializer, ICalWebUpdateSerializer
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers import ListBrowser, \
    SerializationBrowser
from djangoplicity.archives.contrib.info import admin_edit_for_site, \
    admin_add_translation, published
from djangoplicity.archives.contrib.queries import AllPublicQuery, \
    UnpublishedQuery, YearQuery, EmbargoQuery, StagingQuery, FeaturedQuery
from djangoplicity.archives.contrib.queries.defaults import AdvancedSearchQuery
from djangoplicity.archives.contrib.search.fields import  DateSinceSearchField, \
    DateUntilSearchField, IdSearchField, TextSearchField
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from djangoplicity.archives.contrib.serialization import JSONEmitter, \
    ICalEmitter
from djangoplicity.archives.contrib.templater import DisplayTemplate
from djangoplicity.archives.utils import related_archive_items, main_visual_translated
from djangoplicity.archives.views import SerializationDetailView
from djangoplicity.media.info import object_id


# ==========================================
# Web updates
# ==========================================
class WebUpdateOptions( ArchiveOptions ):
    urlname_prefix = 'webupdates'

    admin = ()
    info = ()
    downloads = ()
    search_fields = ( 'id', 'title', 'link', 'description' )

    class Queries( object ):
        default = AllPublicQuery( browsers=( 'normal', 'json', 'ical' ), verbose_name=ugettext_noop("Web Updates"), feed_name="default" )

    class Browsers( object ):
        normal = ListBrowser( verbose_name=ugettext_noop( u'View all' ), paginate_by=100 )
        json = SerializationBrowser( serializer=WebUpdateSerializer, emitter=JSONEmitter, paginate_by=100, display=False, verbose_name=ugettext_noop( "JSON" ) )
        ical = SerializationBrowser( serializer=ICalWebUpdateSerializer, emitter=ICalEmitter, paginate_by=100, display=False, verbose_name=ugettext_noop( "iCal" ) )

    @staticmethod
    def feeds():
        from djangoplicity.announcements.feeds import WebUpdateFeed
        feed_dict = {
            '': WebUpdateFeed,
        }
        return feed_dict


# ==========================================
# Announcements
# ==========================================
class AnnouncementOptions( ArchiveOptions ):
    description_template = 'archives/announcement/object_description.html'

    urlname_prefix = 'announcements'

    admin = (
        (
            ugettext_noop(u'Admin'), {
                'links': (
                    admin_edit_for_site('admin_site', translation_proxy=AnnouncementProxy),
                    admin_add_translation('admin_site', translation_proxy=AnnouncementProxy)
                ),
                'fields': ( published, 'release_date', 'last_modified', 'created' ),
            }
        ),
    )

    info = (
        ( ugettext_noop(u'About the Announcement'), { 'fields': ( object_id,)  } ),
    )

    downloads = (
        ( ugettext_noop(u'Images'), {'resources': ( 'original', 'large', 'screen'  ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'  } } ),
        ( ugettext_noop(u'Downloads'), {'resources': ( 'pdf', 'pdfsm', 'sciencepaper' ), 'icons': { 'pdf': 'doc', 'pdfsm': 'doc', 'sciencepaper': 'doc' } } ),

    )

    detail_views = (
        { 'url_pattern': 'api/(?P<serializer>json)/', 'view': SerializationDetailView( serializer=AnnouncementSerializer, emitters=[JSONEmitter] ), 'urlname_suffix': 'serialization', },
    )

    search_fields = ( 'id', 'title', 'description', 'contacts', 'links', )

    class Queries( object ):
        default = AllPublicQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Announcements"), feed_name="default" )
        featured = FeaturedQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Featured Announcements"), feed_name="default", include_in_urlpatterns=False )
        embargo = EmbargoQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Embargoed Announcements") )
        staging = StagingQuery( browsers=( 'normal', 'viewall', 'json', 'ical' ), verbose_name=ugettext_noop("Announcements (Staging)") )
        year = YearQuery( browsers=( 'normal', 'viewall' ), verbose_name=ugettext_noop("Announcements %d"), feed_name="default" )
        search = AdvancedSearchQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Advanced Announcement Search"), searchable=False )

    class Browsers( object ):
        normal = ListBrowser()
        viewall = ListBrowser( verbose_name=ugettext_noop( u'View all' ), paginate_by=100 )
        json = SerializationBrowser( serializer=AnnouncementSerializer, emitter=JSONEmitter, paginate_by=20, display=False, verbose_name=ugettext_noop( "JSON" ) )
        ical = SerializationBrowser( serializer=ICalAnnouncementSerializer, emitter=ICalEmitter, paginate_by=100, display=False, verbose_name=ugettext_noop( "iCal" ) )

    class ResourceProtection ( object ):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )

    class Display():
        multiple_announcements = DisplayTemplate( 'template', '{{obj.title}}<br/><a href="{{site_url_prefix}}{{obj.get_absolute_url}}">{{site_url_prefix}}{{obj.get_absolute_url}}</a>', name='Multiple Announcements list' )
        multiple_announcements_text = DisplayTemplate( 'template', '{{obj.title}}<br/>{{site_url_prefix}}{{obj.get_absolute_url}}', name='Multiple Announcements list (plaintext)' )
        targeted_email_from = DisplayTemplate( 'file', 'archives/announcement/email/from.txt', name='Targeted email from' )
        targeted_email_subject = DisplayTemplate( 'file', 'archives/announcement/email/subject.txt', name='Targeted email subject' )
        targeted_email = DisplayTemplate( 'file', 'archives/announcement/email/html.html', name='Targeted email' )
        translation_available_announcement = DisplayTemplate( 'file', 'archives/announcement/email/translations_available_announcement.html', name='Announcement available for translation' )

    @staticmethod
    def feeds():
        from djangoplicity.announcements.feeds import AnnouncementFeed, AnnouncementFeaturedFeed
        return {
            '': AnnouncementFeed,
            'featured': AnnouncementFeaturedFeed,
        }

    @staticmethod
    def process_object_list( object_list ):
        """
        Preprocess a list of Announcements to fetch the main images for all of them.
        """
        Announcement.store_main_visuals( object_list )

    @staticmethod
    def extra_context( obj, lang=None ):
        images = related_archive_items( Announcement.related_images, obj )
        videos = related_archive_items( Announcement.related_videos, obj, has_main_visual=False )
        comparisons = related_archive_items( Announcement.related_comparisons, obj, has_main_visual=False )
        main_visual = main_visual_translated(obj.main_visual, images + videos)
        main_image_comparison = main_visual_translated(obj.main_image_comparison, comparisons)

        # # main_visual =
        # from djangoplicity.media.models.images import Image
        # main_visual = Image.objects.language(obj.lang).get(source=obj.main_visual)
        return {
            'main_visual': main_visual,
            'main_image_comparison': main_image_comparison,
            'images': images,
            'videos': videos,
            'comparisons': comparisons,
            'translations': obj.get_translations(),
        }

    class AdvancedSearch(object):
        id = IdSearchField( label=_('Announcement ID') )
        published_since = DateSinceSearchField( label=_( "Published since" ), model_field='release_date' )
        published_until = DateUntilSearchField( label=_( "Published until" ), model_field='release_date' )
        title = TextSearchField( label=_( "Title" ), model_field='title' )
        description = TextSearchField( label=_( "Description" ), model_field='description' )

        class Meta:
            verbose_name = ugettext_noop("Advanced Announcement Search")
