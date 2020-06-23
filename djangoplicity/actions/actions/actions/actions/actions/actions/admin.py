# -*- coding: utf-8 -*-
#
# djangoplicity-actions
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
#

from django.contrib import admin
from djangoplicity.actions.models import Action, ActionParameter, ActionLog


class ActionParameterInlineAdmin( admin.TabularInline ):
    model = ActionParameter
    extra = 0
    max_num = 0
    readonly_fields = ['type', 'help_text', 'name']
    can_delete = False
    fields = ['name', 'value', 'type', 'help_text', ]


class ActionAdmin( admin.ModelAdmin ):
    list_display = [ 'name', 'plugin' ]
    list_filter = ['plugin']
    search_fields = [ 'name', 'plugin', ]
    inlines = [ ActionParameterInlineAdmin ]


class ActionLogAdmin( admin.ModelAdmin ):
    list_display = [ 'timestamp', 'name', 'plugin', 'parameters', 'success', ]
    list_filter = ['plugin', 'success', 'timestamp']
    search_fields = [ 'name', 'plugin', 'error', 'parameters', 'args', 'kwargs' ]
    readonly_fields = [ 'timestamp', 'name', 'plugin', 'parameters', 'success', 'error', 'args', 'kwargs' ]

    def has_add_permission( self, request ):
        """
        ActionLog should only be browsed, hence we prevent all users from adding new
        entries.
        """
        return False


def register_with_admin( admin_site ):
    admin_site.register( Action, ActionAdmin )
    admin_site.register( ActionLog, ActionLogAdmin )

# Register with default admin site
register_with_admin( admin.site )
