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

from builtins import str
from builtins import object
from django.conf import settings
from django.contrib import admin
from django.db.models import Q
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.utils.html import strip_tags

from djangoplicity.announcements.admin import announcementinlineadmin
from djangoplicity.archives.contrib.admin.defaults import RenameAdmin, \
        ArchiveAdmin, view_link, DisplaysAdmin, TranslationDuplicateAdmin, \
        SyncTranslationAdmin
from djangoplicity.contentserver.admin import ContentDeliveryAdmin
from djangoplicity.contrib import admin as dpadmin
from djangoplicity.contrib.admin import AdminRichTextAreaWidget
from djangoplicity.cutter.admin import CropAdmin
from djangoplicity.media.consts import IMAGE_AVM_FORMATS
from djangoplicity.media.models import ImageExposure, ImageContact, Image, \
        VideoContact, Video, VideoSubtitle, ImageColor, Color, PictureOfTheWeek, \
        ImageComparison, ImageProxy, ImageComparisonProxy, PictureOfTheWeekProxy, \
        VideoProxy, VideoAudioTrack, VideoBroadcastAudioTrack, VideoScript
from djangoplicity.metadata.models import Category, TaggingStatus
from djangoplicity.releases.admin import releaseinlineadmin
from django import forms
from django.contrib import messages

# ============================================
# Mixin
# ============================================
class SetCategoryMixin( object ):
    def action_set_web_category( self, request, queryset, category=None ):
        """
        Action method for set/removing web categories to images/videos.
        """
        if category:
            for obj in queryset:
                obj.web_category.add(category)

    def _make_web_category_action( self, category ):
        """
        Helper method to define an admin action for a specific group
        """
        name = 'set_group_%s' % category.url

        def action(modeladmin, request, queryset):
            return modeladmin.action_set_web_category( request, queryset, category=category )

        return ( name, ( action, name, "Set category %s" % str(category) ) )


# ============================================
# Image Exposure Inline
# ============================================
class ImageExposureInlineForm( ModelForm ):
    class Meta:
        model = ImageExposure
        fields = '__all__'


class ImageExposureInlineAdmin( admin.StackedInline ):
    model = ImageExposure
    extra = 3
    form = ImageExposureInlineForm
    template = 'admin/media/image/edit_inline/stacked.html'


# ============================================
# Image Contact Inline
# ============================================
class ImageContactInlineForm( ModelForm ):
    class Meta:
        model = ImageContact
        fields = '__all__'


class ImageContactInlineAdmin( admin.StackedInline ):
    model = ImageContact
    extra = 3
    form = ImageContactInlineForm
    template = 'admin/media/image/edit_inline/stacked.html'


# ============================================
# Video Exposure Inline
# ============================================
class VideoContactInlineForm( ModelForm ):
    class Meta:
        model = VideoContact
        fields = '__all__'


class VideoContactInlineAdmin( admin.StackedInline ):
    model = VideoContact
    extra = 3
    form = VideoContactInlineForm
    template = 'admin/media/video/edit_inline/stacked.html'


# ============================================
# Color admin
# ============================================
class ColorAdmin( admin.ModelAdmin ):
    list_display = ( 'id', 'name', 'upper_limit', )
    list_editable = ( 'name', 'upper_limit', )
    fieldsets = (
            ( None, {'fields': ( 'id', 'name', 'upper_limit', ) } ),
            )
    ordering = ( 'upper_limit', )


class ImageColorAdmin( admin.ModelAdmin ):
    list_display = ( 'color', 'image', 'ratio', )
    list_filter = ( 'color', )
    fieldsets = (
            ( None, {'fields': ( 'color', 'image', 'ratio', ) } ),
            )
    ordering = ('color', )


class TaggingStatusExcludeListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Exclude Tagging Status')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'exclude_tagging_status'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        tagging = [(tagging_status.slug, tagging_status.name) for tagging_status in TaggingStatus.objects.all()]
        # Mixed tagging statuses
        try:
            coords = TaggingStatus.objects.get(slug='coords')
            coords_no = TaggingStatus.objects.get(slug='coords_no')
            mixed_slug = '{},{}'.format(coords.slug, coords_no.slug)
            mixed_name = '{} & {}'.format(coords.name, coords_no.name)
            tagging.append((mixed_slug, mixed_name,))
        except TaggingStatus.DoesNotExist:
            pass
        return tagging

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        value = self.value()
        if value is not None:
            # Multiple tags separated by commas
            if ',' in value:
                return queryset.exclude(tagging_status__slug__in=value.split(','))
            return queryset.exclude(tagging_status__slug=value)


class MissingExposureFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Exposures')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'missing_exposures'

    def lookups(self, request, model_admin):
        return (
            ('True', 'Missing Exposures'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.exclude(tagging_status__slug__in=('no_exp',)).filter(
                Q(imageexposure__facility__isnull=True) |
                Q(imageexposure__instrument__isnull=True) |
                Q(imageexposure__spectral_color_assignment__isnull=True)
            )


class ChangeCreditForm(forms.Form):
    new_value = forms.CharField(widget=AdminRichTextAreaWidget())

    def change_value(self, queryset):
        new_value = self.cleaned_data['new_value']
        queryset.update(credit=new_value)


# ============================================
# Image admin
# ============================================
class ImageAdmin( dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, RenameAdmin, CropAdmin, ArchiveAdmin, SetCategoryMixin, ContentDeliveryAdmin ):
    list_display = ( 'id', 'release_date_owner', 'release_date', 'embargo_date', 'get_credit', 'list_link_thumbnail', 'title', 'width', 'height', 'priority', 'published', 'featured', 'last_modified', 'created', view_link('images') )
    list_editable = ( 'priority', 'title',)
    list_filter = ( 'published', 'featured', 'last_modified', 'created', 'tagging_status', 'type', TaggingStatusExcludeListFilter, MissingExposureFilter, 'web_category', 'spatial_quality', 'file_type', 'colors', 'content_server', 'content_server_ready' )
    filter_horizontal = ( 'web_category', 'subject_category', 'subject_name', 'tagging_status', 'proposal', 'publication')
    search_fields = ( 'id', 'title', 'headline', 'description', 'credit', )
    fieldsets = (
        ( None, {'fields': ( 'id', 'priority', 'published', ('featured', 'zoomify', 'wallpapers', 'print_layout', 'zoomable', 'keep_newsfeature'), ) } ),
        ( _(u'Language'), {'fields': ( 'lang', ) } ),
        ( _(u'Status'), {'fields': ( 'tagging_status', ), 'classes': ('collapse',) } ),
        ( _(u'Content Metadata'), {'fields': ( 'title', 'headline', 'description', 'credit', 'web_category', 'subject_category', 'subject_name', 'distance_ly', 'distance_ly_is_accurate', 'distance_z', 'distance_notes', 'type', 'proposal', 'publication'), 'classes': ('collapse',) } ),
        ( _(u'Coordinate Metadata'), {'fields': ( 'spatial_coordinate_frame', 'spatial_equinox', 'spatial_reference_value', 'spatial_reference_dimension',
            'spatial_reference_pixel', 'spatial_scale', 'spatial_rotation', 'spatial_coordsystem_projection', 'spatial_quality', 'spatial_notes', ), 'classes': ('collapse',) } ),
        ( _(u'Creator Metadata'), {'fields': ( 'creator', 'creator_url', 'contact_address', 'contact_city', 'contact_state_province', 'contact_postal_code', 'contact_country', 'rights', ), 'classes': ('collapse',) } ),
        ( _(u'Publisher Metadata'), {'fields': ( 'publisher', 'publisher_id', ), 'classes': ('collapse',) } ),
        ( _(u'File Metadata'), {'fields': ( 'file_type', 'width', 'height', ('fov_x_l', 'fov_x_r'), ('fov_y_d', 'fov_y_u'), 'file_size', 'magnet_uri' ), 'classes': ('collapse',) } ),
        ( _(u'Observation Metadata'), {'fields': ( 'spectral_notes', ), 'classes': ('collapse',) } ),
        ( _(u'External References'), {'fields': ( 'long_caption_link', 'press_release_link' ), 'classes': ('collapse',) } ),
        ( _(u'Publishing (advanced)'), {'fields': ( ('release_date', 'embargo_date'), 'release_date_owner' ), 'classes': ('collapse',) } ),
        ( _(u'Content Delivery'), {'fields': ( 'content_server', 'content_server_ready'), 'classes': ('collapse',) } ),
    )
    ordering = ('-last_modified', )
    richtext_fields = ('description', 'credit')
    readonly_fields = ('id', 'content_server_ready')
    actions = ['action_toggle_published', 'action_toggle_featured', 'action_avm_content_review', 'action_avm_observation_review', 'action_avm_coordinate_review', 'action_write_avm', 'action_reimport', 'action_resync_resources', 'edit_bulk_credit_action']
    inlines = [ ImageExposureInlineAdmin, ImageContactInlineAdmin ]

    def get_credit(self, obj):
        return strip_tags(obj.credit)

    get_credit.short_description = _("Credits")
    get_credit.allow_tags = True

    def edit_bulk_credit_action(self, request, queryset):
        if request.method == 'POST':
            form = ChangeCreditForm(request.POST)
            if form.is_valid():
                form.change_value(queryset)
                self.message_user(request, _('The credit fields has been successfully modified.'))
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = ChangeCreditForm()
        return render(request, 'admin/media/image/edit_credit_form.html', context={'queryset': queryset, 'form': form})
    edit_bulk_credit_action.short_description = _('Change credits in bulk')

    def get_queryset(self, request):
        qs = super(ImageAdmin, self).get_queryset(request)
        return ArchiveAdmin.limit_access(self, request, qs)

    def status( self, obj ):
        """ List all statuses """
        return ", ".join( [x.slug for x in obj.tagging_status.all().order_by('slug')] )

    def action_write_avm( self, request, queryset ):
        try:
            from djangoplicity.media.tasks import write_metadata

            for obj in queryset:
                write_metadata.delay( obj.id, IMAGE_AVM_FORMATS )
            self.message_user( request, _("Writing AVM to selected images.") )
        except Exception as e:
            self.message_user( request, _("This djangoplicity installation does not support writing AVM to images (%s)." % str( e ) ) )
    action_write_avm.short_description = _("Write AVM to images")

    def action_avm_content_review( self, request, queryset ):
        return self._action_avm_review( request, queryset, "avm_content_list.html", _("AVM Content Review") )
    action_avm_content_review.short_description = _("AVM Content Review")

    def action_avm_observation_review( self, request, queryset ):
        return self._action_avm_review( request, queryset, "avm_observation_list.html", _("AVM Observation Review") )
    action_avm_observation_review.short_description = _("AVM Observation Review")

    def action_avm_coordinate_review( self, request, queryset ):
        return self._action_avm_review( request, queryset, "avm_coordinate_list.html", _("AVM Coordinate Review") )
    action_avm_coordinate_review.short_description = _("AVM Coordinate Review")

    def _action_avm_review(self, request, queryset, template_name, title ):
        opts = self.model._meta
        app_label = opts.app_label

        context = {
            "title": title,
            "object_name": force_text( opts.verbose_name ),
            'objects': queryset,
            "opts": opts,
            "app_label": app_label,
        }

        # Display the confirmation page
        return render(request, "admin/%s/%s/%s" % ( app_label, opts.object_name.lower(), template_name ), context)

    def get_actions( self, request ):
        """
        Dynamically add admin actions for setting the subject category
        """
        actions = super( ImageAdmin, self ).get_actions( request )
        actions.update( dict( [self._make_web_category_action( c ) for c in Category.objects.filter( type__name='Images' ).order_by( 'name' )] ) )
        return actions

    class Media:
        css = { 'all': (settings.MEDIA_URL + settings.SUBJECT_CATEGORY_CSS,) }  # Extra widget for subject category field



# ============================================
# Image proxy admin
# ============================================
class ImageProxyInlineForm( ModelForm ):
    class Meta:
        model = ImageProxy
        fields = ( 'id', 'published', 'translation_ready', 'lang', )


class ImageProxyInlineAdmin( admin.TabularInline ):
    model = ImageProxy
    extra = 0
    form = ImageProxyInlineForm


class ImageProxyAdmin( dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, RenameAdmin, TranslationDuplicateAdmin, SyncTranslationAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'title', 'published', 'translation_ready', 'lang', 'source', 'last_modified', view_link( 'images', translation=True ) )
    list_filter = ( 'lang', 'published', 'last_modified', 'created', 'release_date', 'embargo_date', )
    list_editable = ( 'title', 'translation_ready', )
    search_fields = ImageAdmin.search_fields
    fieldsets = (
                    ( 'Language', {'fields': ( 'lang', 'source', 'translation_ready', ) } ),
                    ( None, {'fields': ( 'id', ) } ),
                    ( 'Publishing', {'fields': ( 'published', ), } ),
                    ( 'Image', {'fields': ( 'title', 'headline', 'description', ), } ),
                )
    ordering = ImageAdmin.ordering
    richtext_fields = ImageAdmin.richtext_fields
    raw_id_fields = ( 'source', )
    readonly_fields = ( 'id', )
    inlines = []
    actions = ['action_toggle_published']
    list_select_related = ['source']

    def get_queryset( self, request ):
        qs = super( ImageProxyAdmin, self ).get_queryset( request )
        return ImageProxyAdmin.limit_access( self, request, qs )


ImageAdmin.inlines += [ImageProxyInlineAdmin]


# ============================================
# Video admin
# ============================================
class VideoAdmin( dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, RenameAdmin, ArchiveAdmin, SetCategoryMixin, ContentDeliveryAdmin ):
    list_display = ( 'id', 'release_date_owner', 'release_date', 'embargo_date', 'list_link_thumbnail', 'title', 'file_duration', 'priority', 'published', 'featured', 'last_modified', view_link('videos') )
    list_editable = ( 'priority', 'title', )
    list_filter = ( 'published', 'featured', 'tagging_status', 'last_modified', 'created', 'web_category', 'content_server', 'content_server_ready', 'use_youtube' )
    filter_horizontal = ( 'web_category', 'subject_category', 'subject_name')
    search_fields = ( 'id', 'title', 'headline', 'description', 'credit',)
    fieldsets = (
                    ( None, {'fields': ( 'id', 'priority', 'published', 'featured') } ),
                    ( _(u'Language'), {'fields': ( 'lang', ) } ),
                    ( _(u'Status'), {'fields': ( 'tagging_status', ), 'classes': ('collapse',) } ),
                    ( _(u'Content Metadata'), {'fields': ( 'title', 'headline', 'description', 'credit', 'web_category', 'subject_category', 'subject_name', 'type', 'facility', ), 'classes': ('collapse',) } ),
                    ( _(u'Creator Metadata'), {'fields': ( 'creator', 'creator_url', 'contact_address', 'contact_city', 'contact_state_province', 'contact_postal_code', 'contact_country', 'rights', ), 'classes': ('collapse',) } ),
                    ( _(u'Publisher Metadata'), {'fields': ( 'publisher', 'publisher_id', ), 'classes': ('collapse',) } ),
                    ( _(u'File Metadata'), {'fields': ( 'width', 'height', 'file_duration', 'file_aspect_ratio', 'file_size', 'frame_rate', 'magnet_uri' ), 'classes': ('collapse',) } ),
                    ( _(u'Audio Metadata'), {'fields': ( 'audio_surround_format', ), 'classes': ('collapse',) } ),
                    ( _(u'Content Delivery'), {'fields': ( 'content_server', 'content_server_ready', 'youtube_video_id', 'use_youtube'), 'classes': ('collapse',) } ),
                    ( _(u'Publishing (advanced)'), {'fields': ( ('release_date', 'embargo_date'), 'release_date_owner' ), 'classes': ('collapse',) } ),
                )
    ordering = ('-last_modified', )
    richtext_fields = ('description', 'credit', )
    readonly_fields = ('content_server_ready', )
    actions = ['action_toggle_published', 'action_toggle_featured', 'action_update_subtitles', 'action_reimport', 'action_video_extras', 'action_resync_resources', 'action_youtube_upload', 'action_generate_thumbnail']
    inlines = [ VideoContactInlineAdmin ]

    class Media:
        css = { 'all': (settings.MEDIA_URL + settings.SUBJECT_CATEGORY_CSS,) }  # Extra widget for subject category field

    def get_queryset( self, request ):
        qs = super( VideoAdmin, self ).get_queryset( request )
        return ArchiveAdmin.limit_access( self, request, qs )

    def action_update_subtitles(self, request, objects):
        try:
            from djangoplicity.media.tasks import video_embed_subtitles

            for obj in objects:
                for f in settings.VIDEOS_SUBTITLES_FORMATS:
                    video_embed_subtitles.delay( obj.pk, f)
            self.message_user( request, _("Updating subtitles for selected videos.") )
        except Exception as e:
            self.message_user( request, _("Error while updating subtitles." % str( e ) ) )

    action_update_subtitles.short_description = "Update subtitles"

    def action_video_extras(self, request, objects):
        from djangoplicity.media.tasks import video_extras

        for obj in objects:
            video_extras.delay('media', 'Video', obj.pk)
        self.message_user( request, _("Updating metadata from file for selected videos") )

    action_video_extras.short_description = "Update metadata from file"

    def action_youtube_upload(self, request, objects):
        from djangoplicity.media.tasks import upload_youtube

        for obj in objects:
            if obj.youtube_video_id:
                # Video has already been uploaded
                continue
            upload_youtube.delay(obj.pk, request.user.pk)
        self.message_user(request, _('Uploading video to YouTube'))

    action_youtube_upload.short_description = 'Upload video to YouTube'

    def action_generate_thumbnail(self, request, objects):
        from djangoplicity.celery.serialtaskset import SerialSendTaskSet

        for obj in objects:
            taskset = SerialSendTaskSet()
            taskset.add('media.generate_thumbnail', args=['media', 'Video', obj.pk], kwargs={'force_generation': True})
            taskset.add('djangoplicity.cutter.tasks.process_images_derivatives', args=['media', 'Video', request.user.pk, [obj.pk]])
            taskset.send_task()
        self.message_user(request, _('Generating thumbnail of videos'))

    action_generate_thumbnail.short_description = 'Generate thumbnail at position: {}'.format(getattr(settings, 'VIDEOS_THUMBNAIL_POSITION', 5))

    def get_actions( self, request ):
        """
        Dynamically add admin actions for setting the subject category
        """
        actions = super( VideoAdmin, self ).get_actions( request )
        actions.update( dict( [self._make_web_category_action( c ) for c in Category.objects.filter( type__name='Videos' ).order_by( 'name' )] ) )
        return actions


# ============================================
# Video proxy admin
# ============================================
class VideoProxyInlineForm( ModelForm ):
    class Meta:
        model = VideoProxy
        fields = ( 'id', 'published', 'translation_ready', 'lang', )


class VideoProxyInlineAdmin( admin.TabularInline ):
    model = VideoProxy
    extra = 0
    form = VideoProxyInlineForm


class VideoProxyAdmin( dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, RenameAdmin, TranslationDuplicateAdmin, SyncTranslationAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'title', 'published', 'translation_ready', 'lang', 'source', 'last_modified', view_link( 'videos', translation=True ) )
    list_filter = ( 'lang', 'published', 'last_modified', 'created', 'release_date', 'embargo_date', )
    list_editable = ( 'title', 'translation_ready', )
    search_fields = VideoAdmin.search_fields
    fieldsets = (
                    ( 'Language', {'fields': ( 'lang', 'source', 'translation_ready', ) } ),
                    ( None, {'fields': ( 'id', ) } ),
                    ( 'Publishing', {'fields': ( 'published', ), } ),
                    ( 'Video', {'fields': ( 'title', 'headline', 'description', ), } ),
                )
    ordering = VideoAdmin.ordering
    richtext_fields = VideoAdmin.richtext_fields
    raw_id_fields = ( 'source', )
    readonly_fields = ( 'id', )
    inlines = []
    actions = ['action_toggle_published']
    list_select_related = ['source']


VideoAdmin.inlines += [VideoProxyInlineAdmin]


# ============================================
# Video subtitle admin
# ============================================
class VideoSubtitleAdmin( dpadmin.DjangoplicityModelAdmin, RenameAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'video', 'lang', 'published', 'last_modified' )
    list_filter = ( 'published', 'last_modified', 'created')
    search_fields = ( 'id', 'video__title', 'lang')
    fieldsets = (
                    ( None, {'fields': ( 'id', 'video', 'lang', 'published' ) } ),
                )
    ordering = ('-last_modified', )
    readonly_fields = ('id',)
    actions = ['action_toggle_published']
    raw_id_fields = ('video',)
    inlines = []

    class Media:
        css = { 'all': (settings.MEDIA_URL + settings.SUBJECT_CATEGORY_CSS,) }  # Extra widget for subject category field


# ============================================
# Video audio track admin
# ============================================
class VideoAudioTrackAdmin( dpadmin.DjangoplicityModelAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'video', 'lang', 'published', 'last_modified' )
    list_filter = ( 'published', 'last_modified', 'created')
    search_fields = ( 'id', 'video__title', 'lang')
    fieldsets = (
                    ( None, {'fields': ( 'id', 'video', 'lang', 'published' ) } ),
                )
    ordering = ('-last_modified', )
    readonly_fields = ('id',)
    actions = ['action_toggle_published']
    raw_id_fields = ('video',)
    inlines = []

    class Media:
        css = { 'all': (settings.MEDIA_URL + settings.SUBJECT_CATEGORY_CSS,) }  # Extra widget for subject category field


# ============================================
# Video broadcast audio track admin
# ============================================
class VideoBroadcastAudioTrackAdmin( dpadmin.DjangoplicityModelAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'video', 'type', 'lang', 'published', 'last_modified' )
    list_filter = ( 'published', 'last_modified', 'created', 'type')
    search_fields = ( 'id', 'video__title', 'lang')
    fieldsets = (
                    ( None, {'fields': ( 'id', 'video', 'type', 'lang', 'published' ) } ),
                )
    ordering = ('-last_modified', )
    readonly_fields = ('id',)
    actions = ['action_toggle_published']
    raw_id_fields = ('video',)
    inlines = []

    class Media:
        css = { 'all': (settings.MEDIA_URL + settings.SUBJECT_CATEGORY_CSS,) }  # Extra widget for subject category field


# ============================================
# Video script admin
# ============================================
class VideoScriptAdmin( dpadmin.DjangoplicityModelAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'video', 'lang', 'published', 'last_modified' )
    list_filter = ( 'published', 'last_modified', 'created')
    search_fields = ( 'id', 'video__title', 'lang')
    fieldsets = (
                    ( None, {'fields': ( 'id', 'video', 'lang', 'published' ) } ),
                )
    ordering = ('-last_modified', )
    readonly_fields = ('id',)
    actions = ['action_toggle_published']
    raw_id_fields = ('video',)
    inlines = []


# ============================================
# Picture of the week admin
# ============================================
#hack: Injecting Release Options into DisplaysAdmin
class POTWDisplaysAdmin( DisplaysAdmin ):
    from djangoplicity.media.options import PictureOfTheWeekOptions
    options = PictureOfTheWeekOptions


class PictureOfTheWeekAdmin( dpadmin.DjangoplicityModelAdmin, POTWDisplaysAdmin, RenameAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'potw_thumbnail', 'visual_title', 'visual_type', 'published', 'release_date', 'embargo_date' )
    list_filter = ( 'published', 'last_modified', 'created', 'release_date', 'embargo_date', )
    list_editable = ( 'published',)
    search_fields = ( 'id', 'image__id', 'image__title', 'video__id', 'video__title', )
    date_hierarchy = 'release_date'
    fieldsets = (
        ( None, {'fields': ( 'id', ) } ),
        ( _(u'Language'), {'fields': ( 'lang', ) } ),
        ( 'Publishing', {'fields': ( 'published', ('release_date', 'embargo_date'), ), } ),
        ( 'Picture of the Week', {'fields': ( 'image', 'comparison' ), } ),  # Video is on purpose omitted here, as e.g. newsletter does not have support for displaying POTW which are videos
    )
    ordering = ('-release_date', '-id', )
    raw_id_fields = ('image', 'comparison')
    actions = ['action_mutiple_item_displays', 'action_toggle_published']
    inlines = []  # Do not remove - will cause (PictureOfTheWeekProxyInlineAdmin to be embedded in all admin classes).
    list_select_related = ['image', 'video', 'comparison']

    def visual_title( self, obj ):
        v = obj.visual()
        return str( v ) if v else ""
    visual_title.short_description = _(u'Title')

    def visual_type( self, obj ):
        if obj.image:
            return _("Image")
        elif obj.video:
            return _("Video")
        elif obj.comparison:
            return _("Comparison")
        else:
            return ""
    visual_type.short_description = _('Type')

    def potw_thumbnail( self, obj ):
        """
        Wrapper around list_link_thumbnail to use the main visual
        as thumbnail instead of the POTW object itself.
        """
        return self.list_link_thumbnail( obj.visual() )
    potw_thumbnail.allow_tags = True
    potw_thumbnail.short_description = _(u'Thumbnail')

    def get_queryset( self, request ):
        qs = super( PictureOfTheWeekAdmin, self ).get_queryset( request )
        return ArchiveAdmin.limit_access( self, request, qs )


# ============================================
# POTW proxy admin
# ============================================
class PictureOfTheWeekProxyInlineForm( ModelForm ):
    class Meta:
        model = PictureOfTheWeekProxy
        fields = ( 'id', 'published', 'translation_ready', 'lang', )


class PictureOfTheWeekProxyInlineAdmin( admin.TabularInline ):
    model = PictureOfTheWeekProxy
    extra = 0
    max_num = 0
    form = PictureOfTheWeekProxyInlineForm
    readonly_fields = ( 'published', 'translation_ready', 'lang', )


class PictureOfTheWeekProxyAdmin( dpadmin.DjangoplicityModelAdmin, RenameAdmin, TranslationDuplicateAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'published', 'translation_ready', 'lang', 'source', 'last_modified' )
    list_filter = ( 'lang', 'published', 'last_modified', 'created', 'release_date', 'embargo_date', )
    search_fields = PictureOfTheWeekAdmin.search_fields
    fieldsets = (
                    ( 'Language', {'fields': ( 'lang', 'source', 'translation_ready', ) } ),
                    ( None, {'fields': ( 'id', ) } ),
                    ( 'Publishing', {'fields': ( 'published', 'release_date', 'embargo_date' ), } ),
                )
    ordering = PictureOfTheWeekAdmin.ordering
    raw_id_fields = ( 'source', 'image', 'video')
    readonly_fields = ( 'id', 'published', 'release_date', 'embargo_date', 'image', 'video' )
    list_select_related = ['image', 'video', 'comparison', 'source']
    inlines = []


PictureOfTheWeekAdmin.inlines += [PictureOfTheWeekProxyInlineAdmin]


# ============================================
# Image comparison admin
# ============================================
class ImageComparisonAdmin(dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, RenameAdmin, ArchiveAdmin):
    list_display = ('id', 'list_link_thumbnail', 'title', 'published', 'priority', 'release_date', 'embargo_date', view_link('imagecomparisons'))
    list_filter = ('published', 'last_modified', 'created', 'release_date', 'embargo_date',)
    list_editable = ('published', 'title', 'priority',)
    search_fields = ('id', 'title', 'description', 'credit',)
    date_hierarchy = 'release_date'
    fieldsets = (
                    (None, {'fields': ('id', 'priority') }),
                    ( _(u'Language'), {'fields': ( 'lang', ) } ),
                    ('Publishing', {'fields': ('published', ('release_date', 'embargo_date'), ), }),
                    ('Content', {'fields': ('title', 'description', 'credit', 'image_before', 'image_after'), }),
                )
    ordering = ('-release_date', '-id',)
    raw_id_fields = ('image_before', 'image_after')
    richtext_fields = ('description', 'credit',)
    actions = ['action_toggle_published', 'action_reimport']
    inlines = []

    def get_queryset( self, request ):
        qs = super( ImageComparisonAdmin, self ).get_queryset( request )
        return ArchiveAdmin.limit_access( self, request, qs )


# ============================================
# Image comparison proxy admin
# ============================================
class ImageComparisonProxyInlineForm( ModelForm ):
    class Meta:
        model = ImageComparisonProxy
        fields = ( 'id', 'published', 'translation_ready', 'lang', )


class ImageComparisonProxyInlineAdmin( admin.TabularInline ):
    model = ImageComparisonProxy
    extra = 0
    form = ImageComparisonProxyInlineForm


class ImageComparisonProxyAdmin( dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, RenameAdmin, TranslationDuplicateAdmin, SyncTranslationAdmin, ArchiveAdmin ):
    list_display = ( 'id', 'title', 'published', 'translation_ready', 'lang', 'source', 'last_modified', view_link( 'imagecomparisons', translation=True ) )
    list_filter = ( 'lang', 'published', 'last_modified', 'created', 'release_date', 'embargo_date', )
    list_editable = ( 'title', 'translation_ready', )
    search_fields = ImageComparisonAdmin.search_fields
    fieldsets = (
                    ( 'Language', {'fields': ( 'lang', 'source', 'translation_ready', ) } ),
                    ( None, {'fields': ( 'id', ) } ),
                    ( 'Publishing', {'fields': ( 'published', ), } ),
                    ( 'Content', {'fields': ( 'title', 'description', 'credit', ), } ),
                )
    ordering = ImageComparisonAdmin.ordering
    richtext_fields = ImageComparisonAdmin.richtext_fields
    raw_id_fields = ( 'source', )
    readonly_fields = ( 'id', )
    inlines = []

    def get_queryset( self, request ):
        return super( ImageComparisonProxyAdmin, self ).get_queryset( request ).select_related('source')


ImageComparisonAdmin.inlines += [ImageComparisonProxyInlineAdmin]


# ============================================
# Ingest release inline admins into model admins
# ============================================
releaseinlineadmin( ImageAdmin, 'ReleaseImage' )
releaseinlineadmin( ImageComparisonAdmin, 'ReleaseImageComparison' )
releaseinlineadmin( VideoAdmin, 'ReleaseVideo' )
announcementinlineadmin( ImageAdmin, 'AnnouncementImage' )
announcementinlineadmin( VideoAdmin, 'AnnouncementVideo' )


# ============================================
# Registration
# ============================================
def register_with_admin( admin_site ):
    admin_site.register( Image, ImageAdmin )
    if settings.USE_I18N:
        admin_site.register( ImageProxy, ImageProxyAdmin )
        admin_site.register( VideoProxy, VideoProxyAdmin )
        admin_site.register( PictureOfTheWeekProxy, PictureOfTheWeekProxyAdmin )
        admin_site.register( ImageComparisonProxy, ImageComparisonProxyAdmin )
    admin_site.register( Video, VideoAdmin )
    admin_site.register( VideoSubtitle, VideoSubtitleAdmin )
    admin_site.register( VideoAudioTrack, VideoAudioTrackAdmin )
    admin_site.register( VideoBroadcastAudioTrack, VideoBroadcastAudioTrackAdmin )
    admin_site.register( VideoScript, VideoScriptAdmin )
    admin_site.register( Color, ColorAdmin )
    admin_site.register( ImageColor, ImageColorAdmin )
    admin_site.register( PictureOfTheWeek, PictureOfTheWeekAdmin )
    admin_site.register( ImageComparison, ImageComparisonAdmin )


# Register with default admin site
register_with_admin( admin.site )
