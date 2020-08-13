# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from past.builtins import cmp
from builtins import range
from builtins import object
from datetime import datetime
from django import forms
from django.conf import settings
from django.conf.urls import url
from django.contrib.admin import ModelAdmin
from django.contrib.admin.options import IS_POPUP_VAR
from django.contrib.admin.utils import unquote
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.urls import reverse, NoReverseMatch
from django.db import transaction
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.utils.encoding import force_text
from functools import update_wrapper
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import get_text_list
from django.utils.translation import ugettext_lazy as _

from djangoplicity.archives.contrib.templater import Templater, DisplayTemplate, \
    DEFAULT_SETTINGS
from djangoplicity.archives.importer.utils import rerun_import_actions
from djangoplicity.archives.loading import get_archive_modeloptions

__all__ = ( 'ArchiveAdmin', 'view_link', 'DisplaysAdmin', 'RenameAdmin', 'SyncTranslationAdmin', 'DuplicateAdmin', 'MoveResourcesAdmin', 'product_link' )

if settings.USE_I18N:
    from djangoplicity.translation.models import translation_reverse
    reverse_func = translation_reverse
else:
    reverse_func = reverse


class ArchiveAdmin( object ):
    """
    Actions for use with archives.

    The actions can be installed by subclassing
    this class and adding the desired actions to the
    list of actions in the admin - example:

        class Admin( ModelAdmin, ArchiveAdmin )
            actions = ['action_toggle_published',]

    Note, it is important that ModelAdmin is the first
    class in the list of subclasses.
    """

    thumbnail_resource = 'newsmini'

    @staticmethod
    def limit_access( admin_instance, request, qs ):
        """
        Useful method to call from get_queryset() in admin options. This will limit access to
        only display non-default language items (for translations).
        """
        if request.user.has_perm("%s.view_only_non_default" % admin_instance.model._meta.app_label) and not request.user.is_superuser:
            qs = qs.exclude(lang=settings.LANGUAGE_CODE)

        if request.user.has_perm("%s.view_released_%ss_only" % (admin_instance.model._meta.app_label, admin_instance.model._meta.model_name.replace('proxy', ''))) and not request.user.is_superuser:
            # FIXME: Ideally we would get the name of the field from release_date_fieldname
            # but for now it's not easy to fetch the Meta.Archive information
            # for the parents if admin_instance.model is a translation Proxy
            # From django 1.8 _meta.get_parent_list should help
            qs = qs.filter(**{'release_date__lte': datetime.now()})

        return qs

    #
    # Actions
    #

    def _toggle_attribute(self, attribute, request, objects, msg ):
        """
        Toggle boolean attribute of archive item.
        """
        for obj in objects:
            setattr( obj, attribute, not getattr( obj, attribute ) )
            obj.save()
        self.message_user( request, _("%(attribute)s state of selected items were toggled.") % { 'attribute': msg } )

    def action_toggle_published(self, request, objects ):
        return self._toggle_attribute( "published", request, objects, "Published" )
    action_toggle_published.short_description = "Toggle published state"

    def action_toggle_active(self, request, objects ):
        return self._toggle_attribute( "active", request, objects, "Published" )
    action_toggle_published.short_description = "Toggle active state"

    def action_toggle_featured(self, request, objects):
        return self._toggle_attribute( "featured", request, objects, "Featured" )
    action_toggle_featured.short_description = "Toggle featured state"

    def action_toggle_sale(self, request, objects ):
        return self._toggle_attribute( "sale", request, objects, "Sale" )
    action_toggle_sale.short_description = "Toggle sale state"

    def action_toggle_free(self, request, objects ):
        return self._toggle_attribute( "free", request, objects, "For free" )
    action_toggle_free.short_description = "Toggle for free state"

    def action_reimport(self, request, queryset):
        model, options = get_archive_modeloptions(self.model._meta.app_label, self.model._meta.model_name)
        error_ids = []
        message = ""
        if options.Import.actions and model:
            if request.user:
                extra_conf = {'user_id': request.user.pk}
            else:
                extra_conf = {}
            for obj in queryset:
                rerun_import_actions(model, options, obj, extra_conf=extra_conf)

        if error_ids:
            self.message_user(request, "%s: %s" % (message, ", ".join(error_ids)))
    action_reimport.short_description = _("Re-import resources")

    def list_link_thumbnail( self, obj ):
        """
        Callable to include thumbnail of resource in list view.
        """
        try:
            prefix = obj.Archive.Meta.resource_fields_prefix
            res = getattr( obj, '%s%s' % ( prefix, self.thumbnail_resource ) )
            return mark_safe( u'<img src="%s" />' % res.url )
        except AttributeError:
            return 'N/A'
    list_link_thumbnail.allow_tags = True
    list_link_thumbnail.short_description = _(u'Thumbnail')


def _check_embargo(model, obj, request):
    #
    # Embargo staging functionality
    #
    state = { 'is_embargo': False, 'is_staging': False, 'is_published': True }
    now = datetime.now()

    # Test if item is published or not.
    if model.Archive.Meta.published:
        state['is_published'] = getattr( obj, model.Archive.Meta.published_fieldname, None )

    # Test if item is release, embargoed or staging
    if model.Archive.Meta.release_date or model.Archive.Meta.embargo_date:
        # For release dates in the model itself.
        if model.Archive.Meta.release_date:
            release_date = getattr( obj, model.Archive.Meta.release_date_fieldname, None )
            if model.Archive.Meta.release_date and release_date:
                state['is_embargo'] = release_date > now
        if model.Archive.Meta.embargo_date:
            embargo_date = getattr( obj, model.Archive.Meta.embargo_date_fieldname, None )
            if model.Archive.Meta.embargo_date and embargo_date:
                state['is_staging'] = embargo_date > now
    elif hasattr(model.Archive.Meta, 'related_release_date') and hasattr(model.Archive.Meta, 'related_embargo_date'):
        if model.Archive.Meta.related_release_date or model.Archive.Meta.related_embargo_date:
            # For release dates in related models.
            rel_field = model.Archive.Meta.related_release_date[0]
            rel_model_field = model.Archive.Meta.related_release_date[1]
            emb_field = model.Archive.Meta.related_embargo_date[0]
            emb_model_field = model.Archive.Meta.related_embargo_date[1]
            release_date = getattr( getattr( obj, rel_field, None ), rel_model_field, None )
            embargo_date = getattr( getattr( obj, emb_field, None ), emb_model_field, None )
            if model.Archive.Meta.related_release_date and release_date:
                state['is_embargo'] = release_date > now
            if model.Archive.Meta.related_embargo_date and embargo_date:
                state['is_staging'] = embargo_date > now

    return state


def _get_ordered(obj, klass):
    fields = [(name, o) for name, o in list(obj.__dict__.items()) if isinstance(o, klass)]
    fields.sort(lambda (name1, obj1), (name2, obj2): cmp(obj1.creation_counter, obj2.creation_counter))
    return fields


class DisplaysAdmin ( ModelAdmin ):
    """
    Adds functionality to ModelAdmin to view an object's Displays
    """

    displays_template = 'admin/displays.html'

    # Form template to use - defaults to
    #   NOT ENABLED ATM
    #  * admin/<app>/<model>/rename_form.html
    #  * admin/<app>/rename_form.html
    #  * admin/rename_form.html

    displays = DEFAULT_SETTINGS

    def get_urls(self):
        """ Get all URLs for this admin """
        urls = super( DisplaysAdmin, self ).get_urls()
        extra_urls = [
            url( r'^(.+)/change/displays/$', self.admin_site.admin_view( self.displays_view ) ),
            url( r'^displays/$', self.admin_site.admin_view( self.multiple_displays_view ),)
        ]

        return extra_urls + urls

    def _get_displays(self, obj, context=None):
        if context is None:
            context = {}

        templater = Templater(obj, self.options)

        displays = []

        for d, display_type in _get_ordered(self.options.Display, DisplayTemplate):

            dd = {
                'display': [templater.render(d, context)],
                'name': display_type.name,
                'key': d
            }

            displays.append(dd)

        return displays

    def _get_queryset_displays(self, queryset, context=None):
        if context is None:
            context = {}

        types = _get_ordered(self.options.Display, DisplayTemplate)
        displays = [{} for i in range(len(types))]
        for obj in queryset:
            templater = Templater(obj, self.options)
            context['state'] = _check_embargo(self.model, obj, None)
            i = 0
            for key, typ in types:
                displays[i] = {
                    'display': displays[i].get('display', []) + [templater.render(key, context)],
                    'name': typ.name,
                    'key': key
                }
                i += 1

        return displays

    def displays_view( self, request, object_id, extra_context=None ):
        "The 'displays' admin view for this model."
        model = self.model
        opts = model._meta

        try:
            obj = self.get_queryset( request ).get( pk=unquote( object_id ) )
        except model.DoesNotExist:
            raise Http404( _( '%(name)s object with primary key %(key)r does not exist.' ) % {'name': force_text( opts.verbose_name ), 'key': escape( object_id )} )

        state = _check_embargo(model, obj, request)
        displays = self._get_displays( obj, {'state': state, 'request': request } )

        if not displays:
            raise Http404()

        context = {
            'title': _( 'Displays for %s' ) % force_text( opts.verbose_name ),
            'object_id': object_id,
            'is_popup': True,
            'media': self.media,
            'app_label': opts.app_label,
            'displays': displays,
        }
        context.update( extra_context or {} )

        return render(request, self.displays_template, context)

    def action_mutiple_item_displays(self, request, queryset ):
        opts = self.model._meta
        app_label = opts.app_label

        if not queryset:
            raise Http404

        displays = self._get_queryset_displays(queryset, {})

        context = {
            "title": "Displays",
            "object_name": force_text( opts.verbose_name ),
            'displays': displays,
            "opts": opts,
            "media": self.media,
            "app_label": app_label,
            'current_app': self.admin_site.name,
        }

        return render(request, self.displays_template, context)

    action_mutiple_item_displays.short_description = _("Get Multiple Displays")

    def multiple_displays_view( self, request, object_id, extra_context=None ):
        return

    class Media:
        js = (settings.JQUERY_JS, )
        css = { 'all': (settings.DJANGOPLICITY_ADMIN_CSS, ) }


class DuplicateAdmin( ModelAdmin ):
    """
    Adds functionality to ModelAdmin to duplicate an object, giving it a new primary key.
    """

    duplicate_form_template = None
    # Form template to use - defaults to
    #   * admin/<app>/<model>/duplicate_form.html
    #   * admin/<app>/duplicate_form.html
    #   * admin/duplicate_form.html

    duplicate_form = None
    # Form to use for duplicating. Note the form MUST have a field
    # called new_pk.

    def get_urls( self ):
        """
        Catch /admin/<app>/<model>/<id>/duplicate/ URLs and direct them to
        the duplicate view.

        View is named "media_image_duplicate" and takes one argument.
        """
        # Tool to wrap class method into a view
        # START: Copied from django.contrib.admin.options

        def wrap( view ):
            def wrapper( *args, **kwargs ):
                return self.admin_site.admin_view( view )( *args, **kwargs )
            return update_wrapper( wrapper, view )

        info = self.model._meta.app_label, self.model._meta.model_name
        # END: Copied from django.contrib.admin.options

        #
        urlpatterns = [
            url( r'^(.+)/duplicate/$',
                wrap( self.duplicate_view ),
                name='%s_%s_duplicate' % info ),
        ]

        # Note, must be last one, otherwise the change view
        # consumes everything else.
        urlpatterns += super( DuplicateAdmin, self ).get_urls()

        return urlpatterns

    def get_duplicate_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin duplicate view.
        """
        if self.duplicate_form:
            return self.duplicate_form
        else:
            class DuplicateForm( forms.Form ):
                new_pk = obj._meta.pk.formfield( initial=obj.pk )

                def clean_new_pk(self):
                    data = self.cleaned_data['new_pk']

                    if data == obj.pk:
                        raise forms.ValidationError(_("%(label)s %(value)s is the existing %(label)s of the item." % {'label': self.fields['new_pk'].label, 'value': data}))

                    try:
                        obj.__class__.objects.get(pk=data)
                        raise forms.ValidationError(_("%(label)s %(value)s already exists" % {'label': self.fields['new_pk'].label, 'value': data}))
                    except ObjectDoesNotExist:
                        return data

            return DuplicateForm

    def response_duplicate(self, request, obj ):
        """
        Determines the HttpResponse for the change_view stage.
        """
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = _( 'The %(name)s "%(obj)s" was duplicated successfully.' ) % {'name': force_text( opts.verbose_name ), 'obj': force_text( obj )}

        self.message_user( request, msg )
        return HttpResponseRedirect( "../../%s/" % pk_value )

    def render_duplicate_form(self, request, context, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label

        context.update( {
            'has_add_permission': self.has_add_permission( request ),
            'has_change_permission': self.has_change_permission( request, obj ),
            'has_delete_permission': self.has_delete_permission( request, obj ),
            'has_absolute_url': hasattr( self.model, 'get_absolute_url' ),
            'form_url': mark_safe( form_url ),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model( self.model ).id,
            'current_app': self.admin_site.name,
        } )

        return render(request, self.duplicate_form_template or [
            "admin/%s/%s/duplicate_form.html" % ( app_label, opts.object_name.lower() ),
            "admin/%s/duplicate_form.html" % app_label,
            "admin/duplicate_form.html"
        ], context)

    def construct_duplicate_message(self, request, form ):
        """
        Construct a change message from a duplicated object.
        """
        if form.changed_data:
            return _('Duplicated %s.') % get_text_list(form.changed_data, _('and'))
        else:
            return _('Entry not duplicated.')

    def process_obj(self, obj):
        return obj

    def save_duplicate(self, request, obj, form ):
        newpk = form.cleaned_data['new_pk']
        obj = self.process_obj(obj)
        obj.pk = newpk
        obj.save()
        return obj

    def duplicate_view( self, request, object_id, extra_context=None ):
        "The 'duplicate' admin view for this model."
        model = self.model
        opts = model._meta

        try:
            obj = self.get_queryset( request ).get( pk=unquote( object_id ) )
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission( request, obj ):
            raise PermissionDenied

        if obj is None:
            raise Http404( _( '%(name)s object with primary key %(key)r does not exist.' ) % {'name': force_text( opts.verbose_name ), 'key': escape( object_id )} )

        DuplicateForm = self.get_duplicate_form( request, obj )
        if request.method == 'POST':
            with transaction.atomic():
                form = DuplicateForm( request.POST )
                if form.is_valid():
                    form_validated = True
                    new_object = self.save_duplicate( request, obj, form )
                else:
                    form_validated = False
                    new_object = obj

            if form_validated:
                duplicate_message = self.construct_duplicate_message( request, form )
                self.log_change( request, new_object, duplicate_message )
                return self.response_duplicate( request, new_object )
        else:
            form = DuplicateForm()

        media = self.media + form.media

        context = {
            'title': _( 'Duplicate %s' ) % force_text( opts.verbose_name ),
            'form': form,
            'object_id': object_id,
            'original': obj,
            'is_popup': (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            'errors': forms.util.ErrorList(['test']) if form.errors else None,
            'media': mark_safe( media ),
            'app_label': opts.app_label,
        }
        context.update( extra_context or {} )
        return self.render_duplicate_form( request, context, obj=obj )


class TranslationDuplicateAdmin( DuplicateAdmin ):
    def get_duplicate_form( self, request, obj=None, **kwargs ):
        """
        Returns a Form class for use in the admin duplicate view.
        """
        if self.duplicate_form:
            return self.duplicate_form
        else:
            model_klass = obj._meta.proxy_for_model  # This only works for proxy models

            class DuplicateForm( forms.Form ):
                lang = obj.source._meta.get_field( 'lang' ).formfield( initial=obj.lang )
                source = obj.source._meta.pk.formfield( initial=obj.source.id, label='Translation Source:', help_text='Please note: Id of source - please do not append language suffix.' )

                def clean_source( self ):
                    data = self.cleaned_data['source']
                    try:
                        model_klass.objects.get( pk=data )
                    except ObjectDoesNotExist:
                        raise forms.ValidationError( _( "%(label)s %(value)s does not exist" % {'label': self.fields['source'].label, 'value': data} ) )
                    return data

                def clean( self ):
                    data = super( DuplicateForm, self ).clean()

                    if self.is_valid():
                        try:
                            obj.__class__.objects.get( pk="%s%s" % ( self.cleaned_data['source'], self.cleaned_data['lang'] ) )
                            raise forms.ValidationError( _( "%(label)s %(value)s already exists" % {'label': self.fields['lang'].label, 'value': "'%s'" % self.cleaned_data['lang']} ) )
                        except ObjectDoesNotExist:
                            return data
                    else:
                        return data
            return DuplicateForm

    def save_duplicate( self, request, obj, form ):
        lang = form.cleaned_data['lang']
        obj = self.process_obj( obj )
        obj.lang = lang
        obj.pk = obj.generate_duplicate_id( lang )
        obj.save()
        return obj


class RenameAdmin (ModelAdmin):
    """
    Adds functionality to ModelAdmin to rename an object with a custom primary key.
    """

    # Form template to use - defaults to
    #   * admin/<app>/<model>/rename_form.html
    #   * admin/<app>/rename_form.html
    #   * admin/rename_form.html
    rename_form_template = None

    # Form to use for renaming. Note the form MUST have a field
    # called new_pk.
    rename_form = None

    def get_urls( self ):
        """
        Catch /admin/<app>/<model>/<id>/rename/ URLs and direct them to
        the rename view.

        View is named "media_image_rename" and takes one argument.
        """
        # Tool to wrap class method into a view
        # START: Copied from django.contrib.admin.options

        def wrap( view ):
            def wrapper( *args, **kwargs ):
                return self.admin_site.admin_view( view )( *args, **kwargs )
            return update_wrapper( wrapper, view )

        info = self.model._meta.app_label, self.model._meta.model_name
        # END: Copied from django.contrib.admin.options

        #
        urlpatterns = [
            url( r'^(.+)/change/rename/$',
                wrap( self.rename_view ),
                name='%s_%s_rename' % info ),
        ]

        # Note, must be last one, otherwise the change view
        # consumes everything else.
        urlpatterns += super( RenameAdmin, self ).get_urls()

        return urlpatterns

    def get_rename_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin rename view.
        """
        if self.rename_form:
            return self.rename_form
        else:
            class RenameForm( forms.Form ):
                new_pk = obj._meta.pk.formfield( initial=obj.pk )

                def clean_new_pk(self):
                    data = self.cleaned_data['new_pk']

                    if data == obj.pk:
                        raise forms.ValidationError(_("%(label)s %(value)s is the existing %(label)s of the item." % {'label': self.fields['new_pk'].label, 'value': data}))

                    try:
                        obj.__class__.objects.get(pk=data)
                        raise forms.ValidationError(_("%(label)s %(value)s already exists" % {'label': self.fields['new_pk'].label, 'value': data}))
                    except ObjectDoesNotExist:
                        return data

            return RenameForm

    def response_rename(self, request, obj ):
        """
        Determines the HttpResponse for the change_view stage.
        """
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = _( 'The %(name)s "%(obj)s" was renamed successfully.' ) % {'name': force_text( opts.verbose_name ), 'obj': force_text( obj )}

        self.message_user( request, msg )
        return HttpResponseRedirect( "../../../%s/" % pk_value )

    def render_rename_form(self, request, context, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label

        context.update( {
            'has_add_permission': self.has_add_permission( request ),
            'has_change_permission': self.has_change_permission( request, obj ),
            'has_delete_permission': self.has_delete_permission( request, obj ),
            'has_absolute_url': hasattr( self.model, 'get_absolute_url' ),
            'form_url': mark_safe( form_url ),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model( self.model ).id,
            'current_app': self.admin_site.name,
        } )

        return render(request, self.rename_form_template or [
            "admin/%s/%s/rename_form.html" % ( app_label, opts.object_name.lower() ),
            "admin/%s/rename_form.html" % app_label,
            "admin/rename_form.html"
        ], context)

    def save_rename(self, request, obj, form ):
        newpk = form.cleaned_data['new_pk']
        newobj = obj.rename( newpk )
        return newobj

    def rename_view( self, request, object_id, extra_context=None ):
        "The 'rename' admin view for this model."
        model = self.model
        opts = model._meta

        try:
            obj = self.get_queryset( request ).get( pk=unquote( object_id ) )
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission( request, obj ):
            raise PermissionDenied

        if obj is None:
            raise Http404( _( '%(name)s object with primary key %(key)r does not exist.' ) % {'name': force_text( opts.verbose_name ), 'key': escape( object_id )} )

        RenameForm = self.get_rename_form( request, obj )
        if request.method == 'POST':
            with transaction.atomic():
                form = RenameForm( request.POST )
                if form.is_valid():
                    form_validated = True
                    new_object = self.save_rename( request, obj, form )
                else:
                    form_validated = False
                    new_object = obj

            if form_validated:
                rename_message = _('Renamed {old} to {new}').format(old=obj.pk, new=new_object.pk)
                self.log_change(request, new_object, rename_message)
                return self.response_rename(request, new_object)
        else:
            form = RenameForm()

        media = self.media + form.media

        context = {
            'title': _( 'Rename %s' ) % force_text( opts.verbose_name ),
            'form': form,
            'object_id': object_id,
            'original': obj,
            'is_popup': (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            'errors': form.errors,
            'media': mark_safe( media ),
            'app_label': opts.app_label,
        }
        context.update( extra_context or {} )
        return self.render_rename_form( request, context, obj=obj )


class SyncTranslationAdmin (ModelAdmin):
    """
    Adds functionality to ModelAdmin to update translations of similar
    languages (e.g.: de -> de-ch, de-at)
    """

    # Form template to use - defaults to
    # * admin/<app>/<model>/sync_translation_form.html
    # * admin/<app>/sync_translation_form.html
    # * admin/sync_translation_form.html
    synctranslation_form_template = None

    # Form to use for renaming. Note the form MUST have a field
    # called new_pk.
    synctranslation_form = None

    def get_urls( self ):
        """
        Catch /admin/<app>/<model>/<id>/synctranslation/ URLs and direct them to
        the confirmation view.

        View is named "media_image_synctranslation" and takes one argument.
        """
        # Tool to wrap class method into a view
        # START: Copied from django.contrib.admin.options

        def wrap( view ):
            def wrapper( *args, **kwargs ):
                return self.admin_site.admin_view( view )( *args, **kwargs )
            return update_wrapper( wrapper, view )

        info = self.model._meta.app_label, self.model._meta.model_name
        # END: Copied from django.contrib.admin.options

        #
        urlpatterns = [
            url( r'^(.+)/synctranslation/$',
                wrap( self.synctranslation_view ),
                name='%s_%s_synctranslation' % info ),
        ]

        # Note, must be last one, otherwise the change view
        # consumes everything else.
        urlpatterns += super( SyncTranslationAdmin, self ).get_urls()

        return urlpatterns

    def response_synctranslation(self, request, obj ):
        """
        Determines the HttpResponse for the change_view stage.
        """
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = _( 'The translations in the same language family as %(name)s "%(obj)s" were updated successfully.' ) % {'name': force_text( opts.verbose_name ), 'obj': force_text( obj )}

        self.message_user( request, msg )
        return HttpResponseRedirect( "../../%s/" % pk_value )

    def render_synctranslation_form(self, request, context, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label

        context.update( {
            'has_add_permission': self.has_add_permission( request ),
            'has_change_permission': self.has_change_permission( request, obj ),
            'has_delete_permission': self.has_delete_permission( request, obj ),
            'has_absolute_url': hasattr( self.model, 'get_absolute_url' ),
            'form_url': mark_safe( form_url ),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model( self.model ).id,
            'current_app': self.admin_site.name,
        } )

        return render(request, self.synctranslation_form_template or [
            "admin/%s/%s/synctranslation_form.html" % ( app_label, opts.object_name.lower() ),
            "admin/%s/synctranslation_form.html" % app_label,
            "admin/synctranslation_form.html"
        ], context)

    def synctranslation_view( self, request, object_id, extra_context=None ):
        "The 'synctranslation' admin view for this model."
        model = self.model
        opts = model._meta

        try:
            obj = self.get_queryset( request ).get( pk=unquote( object_id ) )
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission( request, obj ):
            raise PermissionDenied

        if obj is None:
            raise Http404( _( '%(name)s object with primary key %(key)r does not exist.' ) % {'name': force_text( opts.verbose_name ), 'key': escape( object_id )} )

        if request.method == 'POST':
            with transaction.atomic():
                obj.update_family_translations()
                self.log_change( request, obj, 'TODO' )
            return self.response_synctranslation( request, obj )

        context = {
            'title': _( 'Sync translations %s' ) % force_text( opts.verbose_name ),
            'is_popup': (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            'obj': obj,
            'app_label': opts.app_label,
        }
        context.update( extra_context or {} )
        return self.render_synctranslation_form( request, context, obj=obj )


class MoveResourcesAdmin (ModelAdmin):
    """
    Adds functionality to ModelAdmin to move resources for an object with a custom primary key.
    """

    # Form template to use - defaults to
    #   * admin/<app>/<model>/move_form.html
    #   * admin/<app>/move_form.html
    #   * admin/move_form.html
    move_form_template = None

    # Form to use for renaming. Note the form MUST have a field
    # called new_pk.
    move_form = None

    def get_urls( self ):
        """
        Catch /admin/<app>/<model>/<id>/move/ URLs and direct them to
        the move view.

        """
        # Tool to wrap class method into a view
        # START: Copied from django.contrib.admin.options
        def wrap( view ):
            def wrapper( *args, **kwargs ):
                return self.admin_site.admin_view( view )( *args, **kwargs )
            return update_wrapper( wrapper, view )

        info = self.model._meta.app_label, self.model._meta.model_name
        # END: Copied from django.contrib.admin.options

        #
        urlpatterns = [
            url( r'^(.+)/move/$',
                wrap( self.move_view ),
                name='%s_%s_move' % info ),
        ]

        # Note, must be last one, otherwise the change view
        # consumes everything else.
        urlpatterns += super( MoveResourcesAdmin, self ).get_urls()

        return urlpatterns

    def get_move_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin rename view.
        """
        if self.move_form:
            return self.move_form
        else:
            class MoveForm( forms.Form ):
                new_pk = obj._meta.pk.formfield( initial=obj.pk )

                def clean_new_pk(self):
                    data = self.cleaned_data['new_pk']

                    if data == obj.pk:
                        raise forms.ValidationError(_("%(label)s %(value)s is the existing %(label)s of the item." % {'label': self.fields['new_pk'].label, 'value': data}))

                    try:
                        obj.__class__.objects.get(pk=data)
                    except ObjectDoesNotExist:
                        raise forms.ValidationError(_("%(label)s %(value)s doesn't exists - cannot move resources." % {'label': self.fields['new_pk'].label, 'value': data}))

                    return data

            return MoveForm

    def response_move(self, request, obj ):
        """
        Determines the HttpResponse for the change_view stage.
        """
        opts = obj._meta
        pk_value = obj._get_pk_val()

        msg = _( 'The resources of %(name)s "%(obj)s" was moved successfully.' ) % {'name': force_text( opts.verbose_name ), 'obj': force_text( obj )}

        self.message_user( request, msg )
        return HttpResponseRedirect( "../../%s/" % pk_value )

    def render_move_form(self, request, context, form_url='', obj=None):
        opts = self.model._meta
        app_label = opts.app_label

        context.update( {
            'has_add_permission': self.has_add_permission( request ),
            'has_change_permission': self.has_change_permission( request, obj ),
            'has_delete_permission': self.has_delete_permission( request, obj ),
            'has_absolute_url': hasattr( self.model, 'get_absolute_url' ),
            'form_url': mark_safe( form_url ),
            'opts': opts,
            'content_type_id': ContentType.objects.get_for_model( self.model ).id,
            'current_app': self.admin_site.name,
        } )

        return render(request, self.move_form_template or [
            "admin/%s/%s/move_form.html" % ( app_label, opts.object_name.lower() ),
            "admin/%s/move_form.html" % app_label,
            "admin/move_form.html"
        ], context)

    def construct_move_message(self, request, form ):
        """
        Construct a change message from a renamed object.
        """
        if form.changed_data:
            return _('Moved %s.') % get_text_list(form.changed_data, _('and'))
        else:
            return _('Resources not moved.')

    def save_move(self, request, obj, form ):
        newpk = form.cleaned_data['new_pk']
        obj.move_resources( newpk )
        return obj

    def move_view( self, request, object_id, extra_context=None ):
        "The 'move' admin view for this model."
        model = self.model
        opts = model._meta

        try:
            obj = self.get_queryset( request ).get( pk=unquote( object_id ) )
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission( request, obj ):
            raise PermissionDenied

        if obj is None:
            raise Http404( _( '%(name)s object with primary key %(key)r does not exist.' ) % {'name': force_text( opts.verbose_name ), 'key': escape( object_id )} )

        MoveForm = self.get_move_form( request, obj )
        if request.method == 'POST':
            with transaction.atomic():
                form = MoveForm( request.POST )
                if form.is_valid():
                    form_validated = True
                    new_object = self.save_move( request, obj, form )
                else:
                    form_validated = False
                    new_object = obj

            if form_validated:
                move_message = self.construct_move_message( request, form )
                self.log_change( request, new_object, move_message )
                return self.response_move( request, new_object )
        else:
            form = MoveForm()

        media = self.media + form.media

        context = {
            'title': _( 'Move %s resources' ) % force_text( opts.verbose_name ),
            'form': form,
            'object_id': object_id,
            'original': obj,
            'is_popup': (IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            'errors': forms.util.ErrorList(['test']) if form.errors else None,
            'media': mark_safe( media ),
            'app_label': opts.app_label,
        }
        context.update( extra_context or {} )
        return self.render_move_form( request, context, obj=obj )


def view_link( urlprefix, translation=False ):
    def f( obj ):
        kwargs = {}
        if translation and obj.is_translation():
            kwargs = { 'lang': obj.lang }
        try:
            return '<a href="%s">View</a>' % reverse_func( "%s_detail" % urlprefix, args=[obj.source.id if translation and obj.is_translation() else obj.id], **kwargs )
        except NoReverseMatch:
            return ''
    f.short_description = _("Link")
    f.allow_tags = True
    return f


def product_link( admin_app ):
    def f( obj ):
        if not obj.product:
            return ''
        try:
            return '<a href="%s">Product</a>' % reverse( '%s:%s_%s_change' % (admin_app, obj.product._meta.app_label, obj.product._meta.model_name ), args=[obj.product.pk] )
        except NoReverseMatch:
            return ''
    f.short_description = _("Product")
    f.allow_tags = True
    return f
