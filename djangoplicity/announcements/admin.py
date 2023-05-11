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

from django.conf import settings
from django.contrib import admin
from django.forms import ModelForm
from djangoplicity.announcements.models import (
    Announcement, AnnouncementType, WebUpdate, WebUpdateType,
    AnnouncementImage, AnnouncementVideo, AnnouncementProxy,
    AnnouncementImageComparison
)
from djangoplicity.archives.contrib.admin import DisplaysAdmin, ArchiveAdmin, \
    RenameAdmin, view_link
from djangoplicity.archives.contrib.admin.defaults import \
    TranslationDuplicateAdmin, SyncTranslationAdmin
from djangoplicity.contrib.admin import DjangoplicityModelAdmin, CleanHTMLAdmin
from djangoplicity.metadata.admin_actions import SetProgramMixin
from djangoplicity.metadata.models import Program

# ============================================
# Inline admin generators
# ============================================
def archiveitem_inlineadmin( modelclass ):
    """
    Factory function for creating InlineAdmin for subclasses of
    RelatedAnnouncement abstract model.

    InlineAdmin to be included in related archive model admin.
    """
    class InlineForm( ModelForm ):
        class Meta:
            model = modelclass
            fields = ('announcement',)

    class InlineAdmin( admin.TabularInline ):
        model = modelclass
        form = InlineForm
        extra = 1
        raw_id_fields = ('announcement',)

    return InlineAdmin


def announcement_inlineadmin( modelclass ):
    """
    Factory function for creating InlineAdmin for subclasses of
    RelatedRelease abstract model.

    InlineAdmin to be included in release model admin.
    """
    class InlineForm( ModelForm ):
        class Meta:
            model = modelclass
            fields = ('archive_item', 'override_id', 'order', 'main_visual', )

    class InlineAdmin( admin.TabularInline ):
        model = modelclass
        extra = 3
        form = InlineForm
        raw_id_fields = ('archive_item',)
        ordering = ('order', 'archive_item__pk')

    return InlineAdmin


def announcementinlineadmin( modeladmin, modelname ):
    """
    Add inline admin for
    """
    if modelname == 'AnnouncementImage':
        modeladmin.inlines.append( archiveitem_inlineadmin( AnnouncementImage ) )
    elif modelname == 'AnnouncementVideo':
        modeladmin.inlines.append( archiveitem_inlineadmin( AnnouncementVideo ) )
    elif modelname == 'AnnouncementImageComparison':
        modeladmin.inlines.append( archiveitem_inlineadmin( AnnouncementImageComparison ) )


AnnouncementImageInlineAdmin = announcement_inlineadmin(AnnouncementImage)
AnnouncementVideoInlineAdmin = announcement_inlineadmin(AnnouncementVideo)
AnnouncementImageComparisonInlineAdmin = announcement_inlineadmin(AnnouncementImageComparison)
AnnouncementImageComparisonInlineAdmin = announcement_inlineadmin(AnnouncementImageComparison)


# ============================================
# Announcement admin
# ============================================
#hack: Injecting Release Options into DisplaysAdmin

class AnnouncementTypeAdmin( admin.ModelAdmin ):
    list_display = ( 'name', )
    ordering = ( 'name', )
    search_fields = ( 'name', )
    fieldsets = (
        ( None, {'fields': ( 'name', ) } ),
    )


class AnnouncementDisplaysAdmin(DisplaysAdmin):
    from djangoplicity.announcements.options import AnnouncementOptions
    options = AnnouncementOptions


class AnnouncementAdmin(DjangoplicityModelAdmin, CleanHTMLAdmin, AnnouncementDisplaysAdmin, RenameAdmin, ArchiveAdmin,
                        SetProgramMixin):
    list_display = ('id', 'announcement_type', 'title', 'get_programs', 'published', 'featured', 'release_date',
                    'embargo_date', 'last_modified', view_link( 'announcements'), )
    list_filter = ('announcement_type', 'published', 'featured', 'last_modified', 'release_date', 'embargo_date',
                   'programs')
    list_editable = ( 'announcement_type', 'title',)
    search_fields = ( 'id', 'title', 'description', 'announcement_type__name', )
    date_hierarchy = 'release_date'
    ordering = ( '-release_date', '-last_modified', )
    richtext_fields = ( 'description', 'contacts', 'links' )
    actions = ['action_mutiple_item_displays', 'action_toggle_published', ]
    fieldsets = (
                    ( None, {'fields': ( 'id', ('announcement_type', )), } ),
                    ( 'Language', {'fields': ( 'lang', ) } ),
                    ( 'Publishing', {'fields': ( 'published', 'featured', 'release_date', 'embargo_date'  ), } ),
                    ('Programs', {'fields': ('programs',)}),
                    ( 'Archive', {'fields': ( 'title', 'subtitle', 'description', 'links', 'contacts' ), } ),
                )
    inlines = [
        AnnouncementImageInlineAdmin, AnnouncementVideoInlineAdmin,
        AnnouncementImageComparisonInlineAdmin
    ]
    filter_horizontal = ('programs',)

    def get_queryset( self, request ):
        qs = super( AnnouncementAdmin, self ).get_queryset( request )
        return ArchiveAdmin.limit_access( self, request, qs )

    def get_actions(self, request):
        """
        Dynamically add admin actions for setting the programs
        """
        actions = super(AnnouncementAdmin, self).get_actions(request)
        actions.update(
            dict([self._make_program_action(c) for c in Program.objects.filter(
                types__name='Announcements').order_by('name')]))
        return actions

    def formfield_for_dbfield(self, db_field, **kwargs):
        '''
        Cache the announcement_type choices to speed up admin list view
        '''
        request = kwargs['request']
        formfield = super(AnnouncementAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in ('announcement_type', ):
            choices_cache = getattr(request, '%s_choices_cache' % db_field.name, None)
            if choices_cache is not None:
                formfield.choices = choices_cache
            else:
                setattr(request, '%s_choices_cache' % db_field.name, formfield.choices)
        return formfield


# ============================================
# Announcement proxy admin
# ============================================
class AnnouncementProxyInlineForm( ModelForm ):
    class Meta:
        model = AnnouncementProxy
        fields = ( 'id', 'published', 'translation_ready', 'lang', )


class AnnouncementProxyInlineAdmin( admin.TabularInline ):
    model = AnnouncementProxy
    extra = 0
    form = AnnouncementProxyInlineForm


class AnnouncementProxyAdmin( DjangoplicityModelAdmin, CleanHTMLAdmin, RenameAdmin, TranslationDuplicateAdmin, SyncTranslationAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'title', 'published', 'translation_ready', 'lang', 'source', 'last_modified', view_link( 'announcements', translation=True ) )
    list_filter = ( 'lang', 'published', 'last_modified', 'created', 'release_date', 'embargo_date', )
    list_editable = ( 'title', 'translation_ready', )
    search_fields = AnnouncementAdmin.search_fields
    fieldsets = (
                    ( 'Language', {'fields': ( 'lang', 'source', 'translation_ready', ) } ),
                    ( None, {'fields': ( 'id', ) } ),
                    ( 'Publishing', {'fields': ( 'published', 'featured', 'release_date', 'embargo_date' ), } ),
                    ( 'Archive', {'fields': ( 'title', 'subtitle', 'description', 'links', 'contacts' ), } ),
                )
    ordering = AnnouncementAdmin.ordering
    richtext_fields = AnnouncementAdmin.richtext_fields
    raw_id_fields = ( 'source', )
    readonly_fields = ( 'id', 'release_date', 'embargo_date', 'featured' )
    actions = ['action_toggle_published']
    list_select_related = ['source']


AnnouncementAdmin.inlines += [AnnouncementProxyInlineAdmin]


# ============================================
# Web updates admin
# ============================================
class WebUpdateAdmin( DjangoplicityModelAdmin, RenameAdmin, ArchiveAdmin ):
    list_display = ['id', 'title', 'link', 'type', 'published', 'release_date', 'last_modified']
    list_editable = ['title', 'link', 'type', ]
    list_filter = ['published', 'release_date', 'type']
    search_fields = ['id', 'title', 'link', 'type__name', 'description']
    date_hierarchy = 'release_date'
    ordering = ( '-release_date', '-last_modified', )
    richtext_fields = ( 'description', )
    actions = ['action_toggle_published', ]
    readonly_fields = ['last_modified', 'created']
    fieldsets = (
                    ( None, {'fields': ( 'id', ( 'last_modified', 'created' ), ) } ),
                    ( 'Publishing', {'fields': ( 'published', 'release_date', ), } ),
                    ( 'Archive', {'fields': ( 'type', 'title', 'link', 'description', ), } ),
                )

    def formfield_for_dbfield(self, db_field, **kwargs):
        '''
        Cache the type choices to speed up admin list view
        '''
        request = kwargs['request']
        formfield = super(WebUpdateAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name in ('type', ):
            choices_cache = getattr(request, '%s_choices_cache' % db_field.name, None)
            if choices_cache is not None:
                formfield.choices = choices_cache
            else:
                setattr(request, '%s_choices_cache' % db_field.name, formfield.choices)
        return formfield


class WebUpdateTypeAdmin( admin.ModelAdmin ):
    list_display = ['name', ]
    search_fields = ['name', ]


# ============================================
# Register
# ============================================
def register_with_admin( admin_site ):
    admin_site.register( Announcement, AnnouncementAdmin )
    if settings.USE_I18N:
        admin_site.register( AnnouncementProxy, AnnouncementProxyAdmin )
    admin_site.register( WebUpdateType, WebUpdateTypeAdmin )
    admin_site.register( WebUpdate, WebUpdateAdmin )
    admin_site.register( AnnouncementType, AnnouncementTypeAdmin )


register_with_admin( admin.site )
