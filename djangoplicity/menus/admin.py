# -*- coding: utf-8 -*-
#
# djangoplicity-menus
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

from django.contrib import admin
from djangoplicity.menus.models import Menu, MenuItem
from mptt.admin import MPTTModelAdmin


class MenuAdmin( admin.ModelAdmin ):
    list_display = ( 'name', 'hide_menu_root', 'expansion_depth', 'max_depth' )
    list_filter = ( 'hide_menu_root', )
    search_fields = ( 'name', )
    fieldsets = (
        ( None, {'fields': ( 'name', ) } ),
        ( 'Menu style', {'fields': ( 'hide_menu_root', 'expansion_depth', 'max_depth' ) } ),
    )


class MenuItemAdmin( MPTTModelAdmin ):
    list_display = ( 'title', 'link', 'published', 'is_primary', 'on_click', 'menu', 'move_up', 'move_down' )
    list_filter = ( 'menu', 'published', 'on_click', )
    search_fields = ( 'title', 'link', )
    actions = ('action_toggle_published', 'action_toggle_primary' )
    fieldsets = (
        ( None, {'fields': ( 'title', 'link', 'parent' ) } ),
        ( 'Advanced Options', {'fields': ( 'published', 'on_click', 'menu', 'is_primary' ), 'classes': ['collapse'] } ),
    )

    def formfield_for_foreignkey( self, db_field, request, **kwargs ):
        return super( MenuItemAdmin, self ).formfield_for_foreignkey( db_field, request, **kwargs )

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

        self.message_user( request, "Published state of selected items were toggled.")
    action_toggle_published.short_description = "Toggle published state"

    def action_toggle_primary(self, request, objects ):
        """
        Toggle is_primary state of archive item.
        """
        for obj in objects:
            obj.is_primary = not obj.is_primary
            obj.save()

        self.message_user( request, "\"Is primary\" state of selected items were toggled.")
    action_toggle_primary.short_description = "Toggle primary state"

    def get_queryset(self, request):
        return super(MenuItemAdmin, self).get_queryset(request).select_related('menu')


def register_with_admin( admin_site ):
    admin_site.register( Menu, MenuAdmin )
    admin_site.register( MenuItem, MenuItemAdmin )

# Register with default admin site
register_with_admin( admin.site )
