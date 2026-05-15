# -*- coding: utf-8 -*-
#
# djangoplicity
# Copyright (c) 2007-2015, European Southern Observatory (ESO)
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
import os
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings

from djangoplicity.contentserver.models import ContentServerResource
from djangoplicity.contentserver.tasks import sync_content_server, sync_content_server_resources_model, update_resource_privacy
from djangoplicity.archives.utils import initialize_resource
from djangoplicity.media.consts import MEDIA_CONTENT_SERVERS


class ContentDeliveryAdmin(object):
    def action_resync_resources(self, request, queryset):
        for obj in queryset:
            sync_content_server.delay(obj.__module__, obj.__class__.__name__, obj.pk)
    action_resync_resources.short_description = _("Re-sync resources with content server")

    def action_resync_content_server_resources_model(self, request, queryset):
        for obj in queryset:
            sync_content_server_resources_model.delay(obj.__module__, obj.__class__.__name__, obj.pk)
    action_resync_content_server_resources_model.short_description = _("Re-sync Content Server Resources model")

    def action_resync_resource_privacy(self, request, queryset):
        for obj in queryset:
            update_resource_privacy.delay(obj._meta.app_label, obj._meta.model_name, obj.pk)
    action_resync_resource_privacy.short_description = _("Re-sync resource privacy from content server")

class ContentServerResourceAdmin(admin.ModelAdmin):
    """
    Admin interface for ContentServerResource model
    """
    list_display = [
        'id', 'content_object_link', 'content_type', 'object_id', 'format', 'extension', 'resource_size_display',
        'content_server', 'is_private', 'is_active', 'created_at', 'updated_at', 'content_server_link'
    ]
    list_filter = [
        'format', 'is_directory', 'is_private', 'is_active', 'content_server', 'content_type'
    ]
    search_fields = [
        'content_server_path', 'format', 'extension', 'checksum'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'uploaded_at', 'content_object_link'
    ]
    fieldsets = (
        ('Resource Information', {
            'fields': ('format', 'extension', 'resource_size', 'checksum', 'is_directory')
        }),
        ('Content Server', {
            'fields': ('content_server', 'content_server_path')
        }),
        ('Generic Relation', {
            'fields': ('content_type', 'object_id', 'content_object_link')
        }),
        ('Status', {
            'fields': ('is_private', 'is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['mark_as_deleted', 'reactivate_resources', 'refresh_resource_privacy']
    
    def get_queryset(self, request):
        """
        Optimize queryset to avoid N+1 queries for content_object by selecting related content_type.
        """
        qs = super().get_queryset(request)
        # Prefetch content_type to avoid N+1 queries; content_object is a GenericForeignKey
        return qs.prefetch_related('content_object')

    def resource_size_display(self, obj):
        """Display resource size in human readable format"""
        if obj.resource_size is None:
            return '-'
        elif obj.resource_size < 1024:
            return f"{obj.resource_size} B"
        elif obj.resource_size < 1024 * 1024:
            return f"{obj.resource_size / 1024:.1f} KB"
        elif obj.resource_size < 1024 * 1024 * 1024:
            return f"{obj.resource_size / (1024 * 1024):.1f} MB"
        else:
            return f"{obj.resource_size / (1024 * 1024 * 1024):.1f} GB"
    resource_size_display.short_description = 'Size'
    
    def content_object_link(self, obj):
        pass
        """Create a link to the related content object"""
        if obj.content_type and obj.object_id:
            try:
                content_object = obj.content_object
                if content_object:
                    # Get the admin change URL for the content object
                    admin_url = reverse(
                        f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                        args=[obj.object_id]
                    )
                    return format_html(
                        '<a href="{}">{}</a>',
                        admin_url,
                        f"{obj.content_type.model} #{obj.object_id}"
                    )
            except:
                pass
        return f"{obj.content_type.model} #{obj.object_id}" if obj.content_type else '-'
    content_object_link.short_description = 'Related Object'

    def content_server_link(self, obj):
        if not obj.content_object:
            return None
        resource = getattr(obj.content_object, 'resource_' + obj.format)
        if resource and resource.url:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                resource.url,
                f"View file"
            )
    content_server_link.short_description = 'View file'

    def mark_as_deleted(self, request, queryset):
        """Mark selected resources as deleted"""
        count = queryset.update(is_active=False)
        self.message_user(
            request,
            f"Successfully marked {count} resource(s) as deleted."
        )
    mark_as_deleted.short_description = "Mark selected resources as deleted"
    
    def reactivate_resources(self, request, queryset):
        """Reactivate selected resources"""
        count = queryset.update(is_active=True)
        self.message_user(
            request,
            f"Successfully reactivated {count} resource(s)."
        )
    reactivate_resources.short_description = "Reactivate selected resources"

    def refresh_resource_privacy(self, request, queryset):
        """Refresh privacy value from the content server for selected resources"""
        refreshed = 0
        for resource in queryset:
            try:
                content_server = MEDIA_CONTENT_SERVERS[resource.content_server]
                if not content_server or not hasattr(content_server, 'get_resource_privacy'):
                    continue

                is_private = content_server.get_resource_privacy(resource)
                if is_private is None:
                    continue  # Skip if privacy information is not available
                
                resource.is_private = is_private
                resource.save(update_fields=['is_private'])
                refreshed += 1
            except Exception as e:
                print(f"Error occurred while refreshing privacy for resource {resource}: {e}")
                continue

        self.message_user(
            request,
            f"Successfully refreshed privacy for {refreshed} resource(s)."
        )
    refresh_resource_privacy.short_description = "Refresh privacy from content server"


def register_with_admin(admin_site):
    admin_site.register(ContentServerResource, ContentServerResourceAdmin)
