# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf import settings
from django.contrib import admin
from django.db import models
from django.forms import TextInput, ModelForm
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from djangoplicity.contrib import admin as dpadmin
from djangoplicity.archives.contrib.admin import ArchiveAdmin
from djangoplicity.archives.contrib.admin.defaults import SyncTranslationAdmin, \
    TranslationDuplicateAdmin
from djangoplicity.pages.forms import PageForm
from djangoplicity.pages.models import PageGroup, Page, URL, EmbeddedPageKey, \
    Section, PageProxy


class URLAdminInline(admin.TabularInline):
    model = URL
    extra = 1
    formfield_overrides = {
            models.CharField: {'widget': TextInput(attrs={'size': '100'})}
    }


class PageGroupAdmin( admin.ModelAdmin ):
    fieldsets = (
            (None, {'fields': ('name', 'description', 'groups', 'full_access')}),
    )
    list_display = ('name', )
    search_fields = ('name', 'description', )
    ordering = ('name', )


class PageAdmin( dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, SyncTranslationAdmin ):
    fieldsets = [
            (None, {'fields': ('title', 'lang', 'content' )}),
            ('Javascript', {'classes': ['collapse'], 'fields': ('script', )}),
            ('Metadata', {'fields': ( 'description', 'keywords', 'opengraph_image' )}),
            ('Visual style', {'classes': ['collapse'], 'fields': ('section', 'template_name')}),
            ('Publishing', {'classes': ['collapse'], 'fields': ( 'login_required', 'published', 'start_publishing', 'end_publishing')}),
            ('Advanced options (experts only)', {'classes': ['collapse'], 'fields': ('embedded', 'dynamic', 'raw_html', 'live_edit', 'redirect_url')}),
    ]
    list_filter = ('published', 'section', 'embedded', 'login_required', 'last_modified', )
    list_display = ('title', 'main_url', 'start_publishing', 'end_publishing', 'last_modified', 'is_online', 'view_link' )
    search_fields = ('url__url', 'title', 'content', 'description', 'keywords', 'template_name')
    ordering = ('title', )
    actions = ['action_toggle_published', ]
    inlines = [URLAdminInline, ]
    form = PageForm

    def view_link( self, obj ):
        """
        Callable to include thumbnail of resource in list view.
        """
        return mark_safe('<a href="%s">View</a>' % obj.get_absolute_url() )
    view_link.short_description = _("Link")
    view_link.allow_tags = True

    def main_url(self, obj):
        return obj.get_absolute_url()

    #
    # Actions
    #
    def action_toggle_published(self, request, objects ):
        """
        Toggle published state of archive item.
        """
        for obj in objects:
            obj.published = not obj.published
            obj.save()

        self.message_user( request, _("Published state of selected items were toggled."))
    action_toggle_published.short_description = "Toggle published state"

    def action_set_pagegroup(self, request, queryset, pagegroup=None, remove=False):
        """
        Action method for set/removing pagegroups to page.
        """
        for obj in queryset:
            if remove:
                obj.groups.remove(pagegroup)
            else:
                obj.groups.add(pagegroup)

    def get_form(self, request, obj=None, **kwargs):
        '''
        Only superusers can add/remove pages from/to groups
        '''
        groups_fieldset = ('Groups', {'classes': ['collapse'], 'fields': ('groups', )})

        if request.user.is_superuser:
            if groups_fieldset not in self.fieldsets:
                self.fieldsets.append(groups_fieldset)
        elif groups_fieldset in self.fieldsets:
            self.fieldsets.remove(groups_fieldset)

        return super(PageAdmin, self).get_form(request, obj, **kwargs)

    def _get_user_page_groups(self, request):
        '''
        Returns the list of PageGroup the current user is a member of,
        and whether or not the user is a member of a full access group
        '''
        try:
            pgroups = getattr(request.user, 'pgroups')
        except AttributeError:
            pgroups = PageGroup.objects.filter(
                groups__in=request.user.groups.all()
            )
            request.user.pgroups = pgroups

        full_access = any([ x.full_access for x in pgroups ])

        return pgroups, full_access

    def get_queryset(self, request):
        '''
        Filter the queryset based on the current users' permissions
        '''
        qs = super(PageAdmin, self).get_queryset(request).prefetch_related('url_set')

        # Get list of PageGroup the current user is a member of:
        pgroups, full_access = self._get_user_page_groups(request)

        # If we don't have any configured PageGroup we assume
        # standard permissions apply:
        if PageGroup.objects.count() == 0:
            return qs

        if request.user.is_superuser or full_access:
            return qs

        return qs.filter(groups__in=pgroups)

    def has_add_permission(self, request):
        dummy, full_access = self._get_user_page_groups(request)

        if request.user.is_superuser or full_access:
            return True

        # If we don't have any configured PageGroup we assume
        # standard permissions apply:
        if PageGroup.objects.count() == 0:
            return True

        return False

    def has_change_permission(self, request, obj=None):
        '''
        Check whether user has change permission
        '''
        pgroups, full_access = self._get_user_page_groups(request)

        if request.user.is_superuser or full_access:
            return True

        if obj is None:
            return super(PageAdmin, self).has_change_permission(request, obj)

        for pgroup in obj.groups.all():
            if pgroup in pgroups:
                return True

        # If we don't have any configured PageGroup we assume
        # standard permissions apply:
        if PageGroup.objects.count() == 0:
            return True

        return False

    def has_delete_permission(self, request, obj=None):
        '''
        Check whether user has delete permission.
        Only superuser and full_access user should be able to delete pages
        '''
        dummy, full_access = self._get_user_page_groups(request)

        if request.user.is_superuser or full_access:
            return True

        # If we don't have any configured PageGroup we assume
        # standard permissions apply:
        if PageGroup.objects.count() == 0:
            return True

        return False

    def _make_pagegroup_action(self, pagegroup, remove=False):
        """
        Helper method to define an admin action for a specific pagegroup
        """
        name = 'unset_group_%s' % pagegroup.pk if remove else 'set_group_%s' % pagegroup.pk

        def action(modeladmin, request, queryset):
            return modeladmin.action_set_pagegroup(request, queryset,
                pagegroup=pagegroup, remove=remove)

        return ( name, ( action, name, "%s page group %s" % ("Unset" if remove else "Set", pagegroup.name) ) )

    def get_actions(self, request):
        '''
        Add actions to add/remove page groups based on user permissions
        '''
        actions = super(PageAdmin, self).get_actions(request)

        dummy, full_access = self._get_user_page_groups(request)

        if request.user.is_superuser or full_access:
            actions.update( dict( [self._make_pagegroup_action( g, remove=False ) for g in PageGroup.objects.filter(full_access=False).order_by( 'name' )] ) )
            actions.update( dict( [self._make_pagegroup_action( g, remove=True ) for g in PageGroup.objects.filter(full_access=False).order_by( 'name' )] ) )

        return actions


class EmbeddedPageKeyAdmin( admin.ModelAdmin ):
    fieldsets = (
            (None, {'fields': ('title', 'page_key', 'page', 'description' )}),
    )
    list_display = ('title', 'page', 'page_key', 'last_modified' )
    list_filter = ( 'last_modified', 'application' )
    search_fields = ( 'page_key', 'page__title', 'description' )
    ordering = [ 'page__title' ]
    list_select_related = True
    raw_id_fields = ("page", )


class SectionAdmin( admin.ModelAdmin ):
    fieldsets = (
            (None, {'fields': ('name', 'template', 'append_title' )}),
    )
    list_display = ('name', 'template', 'append_title')
    search_fields = ('name', 'template', 'append_title')
    ordering = ('name', )


# ============================================
# Page proxy admin
# ============================================
class PageProxyInlineForm( ModelForm ):
    class Meta:
        model = PageProxy
        fields = ( 'id', 'translation_ready', 'lang', )


class PageProxyAdmin( dpadmin.DjangoplicityModelAdmin, dpadmin.CleanHTMLAdmin, SyncTranslationAdmin, TranslationDuplicateAdmin, ArchiveAdmin ):
    list_display = ('title', 'main_url', 'start_publishing', 'end_publishing', 'last_modified', 'is_online', 'view_link' )
    list_filter = ('published', 'lang', 'section', 'embedded', 'login_required', 'last_modified', )
    list_display_links = ('title', )
    search_fields = PageAdmin.search_fields
    fieldsets = (
            ( 'Language', {'fields': ( 'lang', 'source', 'translation_ready', ) } ),
            ('Publishing', {'fields': ('published', )}),
            (None, {'fields': ('title', 'content' )}),
            ('Metadata', {'fields': ( 'description', 'keywords' )}),
    )
    ordering = PageAdmin.ordering
    raw_id_fields = ( 'source', )
    form = PageForm
    list_select_related = ['source']

    def get_queryset(self, request):
        return super(PageProxyAdmin, self).get_queryset(request).prefetch_related(
            'source__url_set'
        )

    def view_link( self, obj ):
        """
        Callable to include thumbnail of resource in list view.
        """
        return mark_safe('<a href="%s">View</a>' % obj.get_absolute_url() )
    view_link.short_description = _("Link")
    view_link.allow_tags = True

    def main_url(self, obj):
        return obj.get_absolute_url()

#class ContextProcessorOptions( admin.ModelAdmin ):
#   fieldsets = (
#                (None, {'fields': ('name', 'module' )}),
#               )
#   list_display = ('name', 'module')
#   search_fields = ('name', 'module')
#   ordering = ('name', )


def register_with_admin( admin_site ):
    admin_site.register( PageGroup, PageGroupAdmin )
    admin_site.register( Page, PageAdmin )
    if settings.USE_I18N:
        admin_site.register( PageProxy, PageProxyAdmin )
    admin_site.register( EmbeddedPageKey, EmbeddedPageKeyAdmin )
    admin_site.register( Section, SectionAdmin )


# Register with default admin site
register_with_admin( admin.site )
