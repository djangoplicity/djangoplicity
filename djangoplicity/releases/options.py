# -*- coding: utf-8 -*-
#
# djangoplicity-releases
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
from django.conf import settings
from django.utils.translation import ugettext_lazy as _, ugettext_noop
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers.defaults import ListBrowser, \
    SerializationBrowser
from djangoplicity.archives.contrib.info.defaults import admin_edit_for_site, \
    admin_add_translation, published
from djangoplicity.archives.contrib.queries.defaults import AllPublicQuery, \
    EmbargoQuery, StagingQuery, YearQuery, UnpublishedQuery, AdvancedSearchQuery
from djangoplicity.archives.contrib.search.fields import SeparatorField, \
    IdSearchField, DateSinceSearchField, DateUntilSearchField, TextSearchField, \
    AVMSubjectNameSearchField, AVMSubjectCategorySearchField, \
    AVMFacilitySearchField, ManyToManySearchField
from djangoplicity.archives.contrib.serialization import ICalEmitter, \
    JSONEmitter
from djangoplicity.archives.contrib.templater import DisplayTemplate
from djangoplicity.archives.utils import related_archive_items, \
    main_visual_translated
from djangoplicity.archives.views import SerializationDetailView
from djangoplicity.releases.queries import ProgramPublicQuery
from djangoplicity.metadata.archives.info import subject_name, subject_category, \
    facility, instruments
from djangoplicity.metadata.models import Instrument
from djangoplicity.releases import views
from djangoplicity.releases.info import releaseid, oldreleaseids, telbib, principal_investigator
from djangoplicity.releases.models import ReleaseProxy, Release
from djangoplicity.releases.serializers import ReleaseSerializer, \
    ICalReleaseSerializer, MiniReleaseSerializer


__all__ = [ 'ReleaseOptions', ]


#
# Release archive configuration
#
class ReleaseOptions( ArchiveOptions ):

    description_template = 'archives/release/object_description.html'

    title = ugettext_noop("Press Releases")

    urlname_prefix = "releases"

    downloads = ( ( ugettext_noop( 'Text' ), {'resources': ( 'pdf', 'text', 'doc', ), 'icons': { 'pdf': 'pdf', 'text': 'txt', 'doc': 'word' } } ), )

    info = (
        ( ugettext_noop( 'About the Release' ), { 'fields': ( releaseid, oldreleaseids, subject_name, subject_category, facility, instruments, telbib, principal_investigator ) } ),
    )

    admin = (
        ( ugettext_noop( 'Admin' ), { 'links': (
            admin_edit_for_site( 'admin_site', translation_proxy=ReleaseProxy ),
            admin_add_translation( 'admin_site', translation_proxy=ReleaseProxy ),
            ), 'fields': ( published, 'last_modified', 'created', 'meltwater_keywords', ), } ),
    )

    detail_views = (
        { 'url_pattern': 'api/(?P<serializer>json)/', 'view': SerializationDetailView( serializer=ReleaseSerializer, emitters=[JSONEmitter] ), 'urlname_suffix': 'serialization', },
        { 'url_pattern': 'kids/', 'view': views.KidsDetailView(), 'urlname_suffix': 'kids' },
    )

    search_fields = (
        'id', 'old_ids', 'release_type__name', 'title', 'release_city', 'headline',
        'description', 'notes', 'more_information', 'links', 'subject_name__name', 'subject_name__alias', 'facility__name',
        'releasecontact__name'
    )
    # Warning: prefetching releasecontact_set makes them disappear from the
    # archive_detail view and translations. Prefetch probably doesn't
    # work as it uses the translation contacts (which is empty) instead of the
    # source ones
    prefetch_related = (
        'facility', 'subject_name', 'publications',
        'subject_category', 'related_images', 'related_videos',
    )

    class Queries( object ):
        default = AllPublicQuery( browsers=( 'normal', 'viewall', 'json', 'minijson', 'ical' ), verbose_name=ugettext_noop("Press Releases"), feed_name="default", select_related='release_type' )
        program = ProgramPublicQuery(relation_field='programs',
                                     browsers=('normal', 'json', 'minijson' ),
                                     verbose_name=ugettext_noop("Press Releases: %(title)s"),
                                     extra_templates=[],
                                     category_type='Releases', feed_name='programs')
        embargo = EmbargoQuery( browsers=( 'normal', 'viewall', 'json', 'minijson', 'ical'  ), verbose_name=ugettext_noop("Embargoed Press Releases"), select_related='release_type' )
        staging = StagingQuery( browsers=( 'normal', 'viewall', 'json', 'minijson', 'ical'  ), verbose_name=ugettext_noop("Press Releases (staging)"), select_related='release_type' )
        year = YearQuery( browsers=( 'normal', 'viewall', 'json', 'minijson', 'ical' ), verbose_name=ugettext_noop("Press Releases %d"), feed_name="default", select_related='release_type' )
        search = AdvancedSearchQuery( browsers=( 'normal', 'viewall', 'json' ), verbose_name=ugettext_noop("Advanced press release search"), searchable=False )

    class Browsers( object ):
        normal = ListBrowser()
        viewall = ListBrowser( verbose_name=ugettext_noop('View all'), paginate_by=100 )
        json = SerializationBrowser( serializer=ReleaseSerializer, emitter=JSONEmitter, paginate_by=20, display=False, verbose_name=_( "JSON" ) )
        minijson = SerializationBrowser( serializer=MiniReleaseSerializer, emitter=JSONEmitter, paginate_by=10, display=False, verbose_name=_( "JSON" ) )
        ical = SerializationBrowser( serializer=ICalReleaseSerializer, emitter=ICalEmitter, paginate_by=100, display=False, verbose_name=_( "iCal" ) )

    class ResourceProtection( object ):
        unpublished = ( UnpublishedQuery, security.UNPUBLISHED_PERMS )
        staging = ( StagingQuery, security.STAGING_PERMS )
        embargo = ( EmbargoQuery, security.EMBARGO )

    class Display():
        #default = DisplayTemplate('template','{{obj}} - {{obj.id}}',name='ID')
        #sender = DisplayTemplate( 'template', settings.ARCHIVE_EMAIL_SENDER if hasattr( settings, 'ARCHIVE_EMAIL_SENDER' ) else '', name = 'From' )
        #subject = DisplayTemplate( 'file', 'archives/release/email/subject.txt', name = 'Subject' )
        #subject_embargo = DisplayTemplate('file','archives/release/email/subject.txt',name='Subject (Embargo)',embargo=True)
        esonews_from = DisplayTemplate( 'file', 'archives/release/email/from.txt', name='esonews or hubblenews or iaunews/eaae-list/all-users from' )
        esonews_subject = DisplayTemplate( 'file', 'archives/release/email/subject.txt', name='esonews or hubblenews or iaunews/eaae-list/all-users subject' )
        esonews = DisplayTemplate( 'file', 'archives/release/email/html_eso.html', name='esonews or hubblenews or iaunews/eaae-list/all-users' )
        epodpress_sender = DisplayTemplate( 'file', 'archives/release/email/from.txt', name='epodpress from' )
        epodpress_subject_embargo = DisplayTemplate( 'file', 'archives/release/email/subject.txt', name='epodpress subject (embargo)', embargo=True )
        epodpress_embargo = DisplayTemplate( 'file', 'archives/release/email/html.html', name='epodpress (embargo)', embargo=True )
        epodpress_subject = DisplayTemplate( 'file', 'archives/release/email/subject.txt', name='epodpress subject (immediate release)' )
        epodpress_immediate = DisplayTemplate( 'file', 'archives/release/email/html.html', name='epodpress (immediate release)' )
        #epodpress_embargo_plaintext = DisplayTemplate( 'file', 'archives/release/email/plaintext.txt', name = "epodpress (embargo txt)", embargo = True )
        #epodpress_immediate_plaintext = DisplayTemplate( 'file', 'archives/release/email/plaintext.txt', name = "epodpress (embargo txt)" )
        aas_from = DisplayTemplate('template', '{{request.user.get_full_name}} <{{request.user.email}}>', name='press-release@aas.org from')
        aas_subject_embargo = DisplayTemplate( 'file', 'archives/release/email/subject.txt', name='press-release@aas.org subject (embargo)', embargo=True )
        aas_embargo = DisplayTemplate( 'file', 'archives/release/email/aas.txt', name='press-release@aas.org (embargo)', embargo=True )
        aas_subject = DisplayTemplate( 'file', 'archives/release/email/subject.txt', name='press-release@aas.org subject')
        aas = DisplayTemplate( 'file', 'archives/release/email/aas.txt', name='press-release@aas.org', )
        if settings.USE_I18N:
            translations_embargo_subject = DisplayTemplate( 'file', 'archives/release/email/translations_subject_embargo.html', name='Translations availability subject (before embargo)' )
            translations_embargo = DisplayTemplate( 'file', 'archives/release/email/translations_embargo.html', name='Translations availability (before embargo)' )
            translations_release_subject = DisplayTemplate( 'file', 'archives/release/email/translations_subject_base.html', name='Translations availability subject (before release)' )
            translations_release = DisplayTemplate( 'file', 'archives/release/email/translations_release.html', name='Translations availability (before release)' )
            translation_available_release = DisplayTemplate( 'file', 'archives/release/email/translations_available_release.html', name='Release available for translation' )
        meltwater = DisplayTemplate( 'file', 'archives/release/email/meltwater.html', name='Meltwater Keywords' )

    class AdvancedSearch (object):
        facility = AVMFacilitySearchField( label=_( "Facility used" ) )
        instruments = ManyToManySearchField( label=_( "Instruments" ), model_field='instruments__id', choices_func=lambda: [( i.id, _( i.name ) ) for i in Instrument.objects.all() ] )
        additional_search_items = SeparatorField( label=_("Additional search terms") )
        id = IdSearchField( label=_('Release ID') )
        published_since = DateSinceSearchField( label=_( "Published since" ), model_field='release_date' )
        published_until = DateUntilSearchField( label=_( "Published until" ), model_field='release_date' )
        title = TextSearchField( label=_( "Title" ), model_field='title' )
        subject_name = AVMSubjectNameSearchField( label=_( "Subject name" ) )
        category = AVMSubjectCategorySearchField( label=_( "Category" ), )
        description = TextSearchField( label=_( "Description" ), model_field='description' )

        class Meta:
            verbose_name = ugettext_noop("Advanced press release search")

    @staticmethod
    def feeds():
        """
        Feeds for press releases archive
        """
        from djangoplicity.releases.feeds import ReleaseFeed
        return {
            '': ReleaseFeed,
        }

    @staticmethod
    def process_object_list( object_list ):
        """
        Preprocess a list of releases to fetch the main images for all of them.
        """
        Release.store_main_visuals( object_list )

    @staticmethod
    def extra_context( obj, lang=None ):
        """
        Extra context variables for detail view
        """
        #
        # Visuals
        #
        images = related_archive_items( Release.related_images, obj )
        videos = related_archive_items( Release.related_videos, obj, has_main_visual=False )
        comparisons = related_archive_items( Release.related_comparisons, obj, has_main_visual=False )
        stock_images = related_archive_items( Release.stock_images, obj, has_main_visual=False )

        # Get main_visual
        main_image = main_visual_translated(obj.main_image, images)
        main_video = main_visual_translated(obj.main_video, videos)
        main_image_comparison = main_visual_translated(obj.main_image_comparison, comparisons)

        #
        # Translations
        #
        return {
            'main_image': main_image,
            'main_video': main_video,
            'main_image_comparison': main_image_comparison,
            'images': images,
            'videos': videos,
            'comparisons': comparisons,
            'stock_images': stock_images,
            'translations': obj.get_translations(),
        }
