# -*- coding: utf-8 -*-
#
# djangoplicity-releases
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#   * Neither the name of the European Southern Observatory nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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
from django.contrib import admin
from django.forms import ModelForm
from django.utils.safestring import mark_safe
from djangoplicity.archives.contrib.admin.defaults import DisplaysAdmin, ArchiveAdmin, \
    RenameAdmin, SyncTranslationAdmin, TranslationDuplicateAdmin, view_link
from djangoplicity.contrib.admin import CleanHTMLAdmin, DjangoplicityModelAdmin
from djangoplicity.releases.models import Release, KidsRelease, ReleaseProxy, \
    ReleaseType, ReleaseContact, ReleaseTranslationContact, ReleaseImage, \
    ReleaseVideo, Country, ReleaseImageComparison, \
    ReleaseStockImage


class ReleaseProxyInlineForm( ModelForm ):
    class Meta:
        model = ReleaseProxy
        fields = ( 'id', 'published', 'translation_ready', 'lang', )


class ReleaseProxyInlineAdmin( admin.TabularInline ):
    model = ReleaseProxy
    extra = 0
    form = ReleaseProxyInlineForm
    #readonly_fields = ('id', 'lang', )


class ReleaseContactInlineForm( ModelForm ):
    class Meta:
        model = ReleaseContact
        # Decision 26 Oct: Show only the following elements.
        fields = ( 'name', 'affiliation', 'city', 'country', 'telephone', 'cellular', 'email' )


class ReleaseTranslationContactInlineForm( ModelForm ):
    class Meta:
        model = ReleaseTranslationContact
        # Decision 26 Oct: Show only the following elements.
        fields = ( 'name', 'affiliation', 'city', 'country', 'telephone', 'cellular', 'email' )


class ReleaseContactInlineAdmin( admin.StackedInline ):
    model = ReleaseContact
    extra = 3
    form = ReleaseContactInlineForm


class ReleaseTranslationContactInlineAdmin( admin.StackedInline ):
    model = ReleaseTranslationContact
    extra = 1
    form = ReleaseTranslationContactInlineForm


# DEPRECATED
#class ReleaseTranslationInlineForm( ModelForm ):
#   class Meta:
#       model = ReleaseTranslation
#       fields = ('country','url_suffix')
#
#class ReleaseTranslationInlineAdmin( admin.TabularInline ):
#   model = ReleaseTranslation
#   form = ReleaseTranslationInlineForm
#   extra = 0
#   #raw_id_fields = ('country',)

#
# Related Releases Inline Admin
#
def archiveitem_inlineadmin( modelclass ):
    """
    Factory function for creating InlineAdmin for subclasses of
    RelatedRelease abstract model.

    InlineAdmin to be included in related archive model admin.
    """
    class InlineForm( ModelForm ):
        class Meta:
            model = modelclass
            fields = ('release', )

    class InlineAdmin( admin.TabularInline ):
        model = modelclass
        form = InlineForm
        extra = 1
        raw_id_fields = ('release', )

    return InlineAdmin


def release_inlineadmin( modelclass, exclude=None ):
    """
    Factory function for creating InlineAdmin for subclasses of
    RelatedRelease abstract model.

    InlineAdmin to be included in release model admin.
    """
    if exclude is None:
        exclude = []

    all_fields = ['archive_item', 'override_id', 'order', 'main_visual', 'archive_item', 'zoomable']

    flds = [x for x in all_fields if x not in exclude]

    class InlineForm( ModelForm ):
        class Meta:
            model = modelclass
            fields = flds

    class InlineAdmin( admin.TabularInline ):
        model = modelclass
        extra = 3
        form = InlineForm
        ordering = ('order', 'archive_item__pk')
        raw_id_fields = ('archive_item',)

    return InlineAdmin


def releaseinlineadmin( modeladmin, modelname ):
    """
    Add inline admin for
    """
    if modelname == 'ReleaseImage':
        modeladmin.inlines.append( archiveitem_inlineadmin( ReleaseImage ) )
    elif modelname == 'ReleaseVideo':
        modeladmin.inlines.append( archiveitem_inlineadmin( ReleaseVideo ) )
    elif modelname == 'ReleaseImageComparison':
        modeladmin.inlines.append( archiveitem_inlineadmin( ReleaseImageComparison ) )
    elif modelname == 'ReleaseStockImage':
        modeladmin.inlines.append( archiveitem_inlineadmin( ReleaseStockImage ) )


ReleaseImageInlineAdmin = release_inlineadmin( ReleaseImage )
ReleaseVideoInlineAdmin = release_inlineadmin( ReleaseVideo, exclude=['zoomable'] )
ReleaseImageComparisonInlineAdmin = release_inlineadmin( ReleaseImageComparison, exclude=['main_visual', 'zoomable'] )
ReleaseStockImageInlineAdmin = release_inlineadmin( ReleaseStockImage, exclude=['override_id', 'main_visual', 'zoomable'] )


class CountryAdmin( DjangoplicityModelAdmin ):
    list_display = ( 'isocode', 'name', 'url_prefix', 'flag_url' )
    list_editable = ( 'name', 'url_prefix', 'flag_url' )
    ordering = ( 'name', )
    search_fields = ( 'isocode', 'name', 'url_prefix', 'flag_url' )
    fieldsets = (
        ( None, {'fields': ( 'isocode', 'name', 'url_prefix', 'flag_url', ) } ),
    )
    richtext_fields = ('contact', 'footer', )


class ReleaseTypeAdmin( admin.ModelAdmin ):
    list_display = ( 'name', )
    ordering = ( 'name', )
    search_fields = ( 'name', )
    fieldsets = (
        ( None, {'fields': ( 'name', ) } ),
    )


#hack: Injecting Release Options into DisplaysAdmin
class ReleaseDisplaysAdmin(DisplaysAdmin):
    from djangoplicity.releases.options import ReleaseOptions
    options = ReleaseOptions


class ReleaseAdmin( DjangoplicityModelAdmin, CleanHTMLAdmin, ReleaseDisplaysAdmin, RenameAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'release_type', 'title', 'published', 'release_date', 'embargo_date', view_link('releases') )
    list_filter = ( 'release_type', 'published', 'last_modified', 'created', 'release_date', 'embargo_date', 'principal_investigator' )
    list_editable = ( 'release_type', 'title', 'published', )
    search_fields = ( 'id', 'old_ids', 'release_type__name', 'title', 'release_city', 'headline',
                    'description', 'notes', 'more_information', 'links', 'subject_name__name', 'facility__name', 'disclaimer', 'meltwater_keywords', 'publications__bibcode', 'kids_title', 'kids_description' )
    date_hierarchy = 'release_date'
    fieldsets = (
                    ( None, {'fields': ( 'id', ('release_type'), 'release_city' ) } ),
                    ( 'Language', {'fields': ( 'lang', ) } ),
                    ( 'Publishing', {'fields': ( 'published', ('release_date', 'embargo_date', ),), } ),
                    ( 'Release', {'fields': ( 'title', 'subtitle', 'headline', 'description', 'notes', 'more_information', 'links', 'disclaimer' ), } ),
                    ( 'Classification', {'fields': ( 'subject_category', 'subject_name', 'facility', 'instruments', 'publications' ), 'description': mark_safe("<strong>Typical subject category:</strong><ol><li>Solar System: Planet, Interplanetary Body, Star, Sky Phenomenon, Technology</li><li>Milky Way: Planet, Interplanetary Body, Star, Nebula</li><li>Local Universe (z&lt;=0.1): Star, Nebula, Galaxy</li><li>Early Universe (z&gt;0.1): Galaxy, Cosmology</li><li>Unspecified: any (non-astronomical in nature - e.g. artwork and photographic)</li><li>Local use only: Mission Graphics</li><ol>") } ),
                    ( 'Kids', {'fields': ( 'kids_title', 'kids_description', 'kids_image') } ),
                    ( 'Compatibility', {'fields': ('old_ids', 'meltwater_keywords' ), }),
                    ( 'Investigator', {'fields': ( 'principal_investigator', ) } ),
                    #( 'Social Networks', {'fields': ( ('facebook_post','facebook_is_posted'),('tweet','tweet_is_posted'),) } ),

                )
    ordering = ('-release_date', '-id', )
    richtext_fields = ('description', 'more_information', 'links', 'notes', 'disclaimer', 'kids_description', )
    actions = ['action_mutiple_item_displays', 'action_toggle_published', ]
    inlines = [
                #ReleaseSubjectNameInlineAdmin, ReleaseFacilityInlineAdmin,
                ReleaseContactInlineAdmin, ReleaseImageInlineAdmin, ReleaseVideoInlineAdmin, ReleaseImageComparisonInlineAdmin, ReleaseStockImageInlineAdmin] + ([ReleaseProxyInlineAdmin] if settings.USE_I18N else [])
    #radio_fields = {"release_type": admin.VERTICAL }
    filter_horizontal = ('subject_category', 'subject_name', 'facility', 'instruments', 'publications' )
    raw_id_fields = ('kids_image',)

    def get_queryset( self, request ):
        qs = super( ReleaseAdmin, self ).get_queryset( request )
        return ArchiveAdmin.limit_access( self, request, qs )

    def formfield_for_dbfield(self, db_field, **kwargs):
        '''
        Cache the release_type choices to speed up admin list view
        '''
        request = kwargs['request']
        formfield = super(ReleaseAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in ('release_type', ):
            choices_cache = getattr(request, '%s_choices_cache' % db_field.name, None)
            if choices_cache is not None:
                formfield.choices = choices_cache
            else:
                setattr(request, '%s_choices_cache' % db_field.name, formfield.choices)
        return formfield

    class Media:
        css = { 'all': (settings.MEDIA_URL + settings.SUBJECT_CATEGORY_CSS,) }  # Extra widget for subject category field


class KidsReleaseAdmin( DjangoplicityModelAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'release_type', 'kids_title', 'published', 'release_date', 'embargo_date', view_link('releases') )
    list_filter = ReleaseAdmin.list_filter
    list_editable = ('kids_title',)
    search_fields = ReleaseAdmin.search_fields
    date_hierarchy = ReleaseAdmin.date_hierarchy
    ordering = ReleaseAdmin.ordering
    richtext_fields = ReleaseAdmin.richtext_fields
    fieldsets = (
                ( None, {'fields': ( 'id', 'release_type', 'published', 'release_date', 'embargo_date' ) } ),
                ( 'Kids', {'fields': ( 'kids_title', 'kids_description', 'kids_image') } ),
            )
    readonly_fields = ('id', 'release_type', 'release_date', 'embargo_date')
    raw_id_fields = ('kids_image',)


class ReleaseProxyAdmin( DjangoplicityModelAdmin, CleanHTMLAdmin, RenameAdmin, SyncTranslationAdmin, TranslationDuplicateAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'title', 'published', 'translation_ready', 'lang', 'source', 'last_modified', view_link( 'releases', translation=True ) )
    list_filter = ( 'lang', 'release_type', 'published', 'last_modified', 'created', 'release_date', 'embargo_date', )
    list_editable = ( 'title', 'translation_ready', )
    search_fields = ( 'id', 'old_ids', 'title', 'release_city', 'headline', 'description', 'notes', 'more_information', 'links', 'disclaimer', 'meltwater_keywords' )
    date_hierarchy = 'release_date'
    fieldsets = (
                    ( 'Language', {'fields': ( 'lang', 'source', 'translation_ready', ) } ),
                    ( None, {'fields': ( 'id', 'release_city' ) } ),
                    ( 'Publishing', {'fields': ( 'published', ), } ),
                    ( 'Release', {'fields': ( 'title', 'subtitle', 'headline', 'description', 'notes', 'more_information', 'links', 'disclaimer' ), } ),
                    ( 'Kids Release', {'fields': ( 'kids_title', 'kids_description', ), 'classes': ('collapse',) } ),
                    ( 'Compatibility', {'fields': ('old_ids', 'meltwater_keywords' ), }),
                )
    ordering = ('-release_date', '-id', )
    richtext_fields = ('description', 'more_information', 'links', 'notes', 'disclaimer', 'kids_description',)
    raw_id_fields = ('source',)
    readonly_fields = ( 'id', )
    inlines = [ ReleaseTranslationContactInlineAdmin, ]
    actions = ['action_toggle_published']
    list_select_related = ['source']


def register_with_admin( admin_site ):
    admin_site.register( ReleaseType, ReleaseTypeAdmin )
    admin_site.register( Release, ReleaseAdmin )
    if settings.USE_I18N:
        admin_site.register( ReleaseProxy, ReleaseProxyAdmin )
    admin_site.register( KidsRelease, KidsReleaseAdmin )
    admin_site.register( Country, CountryAdmin )


# Register with default admin site
register_with_admin( admin.site )
