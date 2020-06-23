# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
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
#

from django import forms
from django.contrib import admin
from djangoplicity.mailinglists.models import BadEmailAddress, Subscriber, \
    Subscription, List, MailChimpList, MailChimpListToken, MailChimpMergeVar, \
    MergeVarMapping, MailChimpEventAction, MailChimpGrouping, GroupMapping, \
    MailChimpGroup


class MailChimpListForm( forms.ModelForm ):
    def __init__( self, *args, **kwargs ):
        super( MailChimpListForm, self ).__init__( *args, **kwargs )
        if 'primary_key_field' in self.fields and 'instance' in kwargs and kwargs['instance']:
            self.fields['primary_key_field'].queryset = MailChimpMergeVar.objects.filter( list=kwargs['instance'].id, public=False )


class SubscriptionInlineAdmin( admin.TabularInline ):
    model = Subscription
    extra = 0


class MailChimpMergeVarInlineAdmin( admin.TabularInline ):
    model = MailChimpMergeVar
    extra = 0
    max_num = 0
    readonly_fields = ['name', 'tag', 'required', 'field_type', 'public', 'show', 'default', 'size', ]
    can_delete = False
    fields = ['name', 'tag', 'required', 'field_type', 'public', 'show', 'default', 'size', ]


class MailChimpGroupInlineAdmin( admin.TabularInline ):
    model = MailChimpGroup
    extra = 0
    max_num = 0
    readonly_fields = ['name', ]
    can_delete = False
    fields = ['name', ]


class MailChimpGroupingInlineAdmin( admin.TabularInline ):
    model = MailChimpGrouping
    extra = 0
    max_num = 0
    readonly_fields = ['name', 'option', ]
    can_delete = False
    fields = ['name', 'option', ]


class GroupMappingInlineAdmin( admin.TabularInline ):
    model = GroupMapping
    extra = 0


class MergeVarMappingInlineAdmin( admin.TabularInline ):
    model = MergeVarMapping
    extra = 0

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(MergeVarMappingInlineAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'merge_var':
            # dirty trick so queryset is evaluated and cached in .choices
            formfield.choices = formfield.choices
        return formfield


class SubscriberAdmin( admin.ModelAdmin ):
    list_display = ['email', ]
    search_fields = ['email', ]
    inlines = [SubscriptionInlineAdmin]


class SubscriptionAdmin( admin.ModelAdmin ):
    list_display = ['subscriber', 'list']
    list_filter = ['list', ]
    search_fields = ['subscriber__email', 'list__name']


class ListAdmin( admin.ModelAdmin ):
    list_display = ['name', 'password', 'subscriptions_count', 'admin_url', 'last_sync']
    search_fields = ['name', 'password']
#   actions = ['action_sync']
    readonly_fields = ['last_sync']

    def subscriptions_count( self, obj ):
        return Subscription.objects.filter( list=obj ).count()
    subscriptions_count.short_description = "subscribers"

    def admin_url( self, obj ):
        url = obj.mailman.get_admin_url()
        return """<a href="%s">Mailman</a>""" % url if url else ""
    admin_url.short_description = "Admin URL"
    admin_url.allow_tags = True

#   def action_sync( self, request, queryset ):
#       for _obj in queryset:
#           pass  # synchronize_mailman.delay( obj.name )
#       self.message_user( request, "Started synchronization of mailman lists %s." % ", ".join( [l.name for l in queryset] ) )
#   action_sync.short_description = "Synchronize lists"


#class MailChimpSourceListInlineAdmin( admin.TabularInline ):
#   model = MailChimpSourceList
#   extra = 0

class MailChimpListAdmin( admin.ModelAdmin ):
    form = MailChimpListForm
    list_display = ['list_id', 'admin_url', 'name', 'default_from_name', 'default_from_email', 'email_type_option', 'member_count', 'open_rate', 'click_rate', 'connected', 'last_sync', ]
    list_filter = ['email_type_option', 'last_sync', 'connected', ]
    search_fields = ['api_key', 'list_id', 'name', 'web_id', 'default_from_name', 'default_from_email', 'email_type_option', 'default_subject']
    inlines = [MailChimpMergeVarInlineAdmin, MailChimpGroupInlineAdmin, MailChimpGroupingInlineAdmin, MergeVarMappingInlineAdmin, GroupMappingInlineAdmin]
    fieldsets = (
        (
            None,
            {
                'fields': ( 'api_key', 'list_id', 'synchronize' ),
            }
        ),
        (
            'List information',
            {
                'description': 'Following information is configured in MailChimp administration interface.',
                'fields': (
                    'name',
                    'web_id',
                    'email_type_option',
                    'default_from_name',
                    'default_from_email',
                    'default_subject',
                    'default_language',
                ),
            }
        ),
        (
            'Statistics',
            {
                'description': 'Following information is collected by MailChimp.',
                'fields': (
                    'list_rating',
                    'member_count',
                    'unsubscribe_count',
                    'cleaned_count',
                    'member_count_since_send',
                    'unsubscribe_count_since_send',
                    'cleaned_count_since_send',
                    'avg_sub_rate',
                    'avg_unsub_rate',
                    'target_sub_rate',
                    'open_rate',
                    'click_rate',
                ),
                'classes': ( 'collapse', ),

            }
        ),
        (
            'Synchronization',
            {
                'fields': (
                    'connected',
                    'last_sync',
                ),
                'classes': ( 'collapse', ),
            }
        ),
        (
            'Model mapping',
            {
                'fields': (
                    'content_type',
                    'primary_key_field',
                ),
                'classes': ( 'collapse', ),
            }
        ),
    )

    readonly_fields = [
        'name',
        'web_id',
        'email_type_option',
        'default_from_name',
        'default_from_email',
        'default_subject',
        'default_language',
        'list_rating',
        'member_count',
        'unsubscribe_count',
        'cleaned_count',
        'member_count_since_send',
        'unsubscribe_count_since_send',
        'cleaned_count_since_send',
        'avg_sub_rate',
        'avg_unsub_rate',
        'target_sub_rate',
        'open_rate',
        'click_rate',
        'connected',
        'last_sync',
    ]

    actions = ['action_update_info', 'action_install_webhooks']

    def admin_url( self, obj ):
        url = obj.get_admin_url()
        return """<a href="%s">MailChimp</a>""" % url if url else ""
    admin_url.short_description = "Admin URL"
    admin_url.allow_tags = True

    def action_update_info( self, request, queryset ):
        """
        Action to request statistics to be updated.
        """
        from djangoplicity.mailinglists.tasks import mailchimplist_fetch_info
        for obj in queryset:
            mailchimplist_fetch_info.delay( obj.list_id )
        self.message_user( request, "Updating statistics from lists %s." % ", ".join( [l.name for l in queryset] ) )
    action_update_info.short_description = "Update statistics from MailChimp"

    def action_install_webhooks( self, request, queryset ):
        """
        Action to request webhooks to be installed in MailChimp.
        """
        from djangoplicity.mailinglists.tasks import webhooks
        for obj in queryset:
            webhooks.delay( list_id=obj.list_id )
        self.message_user( request, "Installing webhooks for lists %s." % ", ".join( [l.name for l in queryset] ) )
    action_install_webhooks.short_description = "Install webhooks"


class MailChimpEventActionAdmin( admin.ModelAdmin ):
    list_display = ['model_object', 'on_event', 'action', ]
    list_filter = [ 'on_event', 'action', 'model_object', ]
    search_fields = ['action__name', 'on_event']


class BadEmailAddressAdmin( admin.ModelAdmin ):
    list_display = ['email', 'timestamp', ]
    list_filter = ['timestamp', ]
    search_fields = ['email']


class MailChimpListTokenAdmin( admin.ModelAdmin ):
    list_display = ['list', 'uuid', 'token', 'expired' ]
    list_filter = ['expired', 'list']
    search_fields = ['uuid', 'token']
    readonly_fields = ['list', 'uuid', 'token', 'expired', 'get_absolute_url' ]
    ordering = ['-expired']

    fields = ['list', 'uuid', 'token', 'expired', 'get_absolute_url' ]

    def has_add_permissions( self, request ):
        return False

    def has_change_permissions( self, request ):
        return False


def register_with_admin( admin_site ):
    admin_site.register( Subscriber, SubscriberAdmin )
    admin_site.register( Subscription, SubscriptionAdmin )
    admin_site.register( List, ListAdmin )
    admin_site.register( MailChimpList, MailChimpListAdmin )
    #admin_site.register( MailChimpSourceList, MailChimpSourceListAdmin )
    #admin_site.register( MailChimpSubscriberExclude, MailChimpSubscriberExcludeAdmin )
    admin_site.register( BadEmailAddress, BadEmailAddressAdmin )
    admin_site.register( MailChimpListToken, MailChimpListTokenAdmin )
    admin_site.register( MailChimpEventAction, MailChimpEventActionAdmin )


# Register with default admin site
register_with_admin( admin.site )
