# -*- coding: utf-8 -*-
#
# djangoplicity-remotearchives
# Copyright (c) 2007-2016, European Southern Observatory (ESO)
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

from django.contrib import admin
from django.utils.translation import ugettext as _

from djangoplicity.remotearchives.tasks import fetch_remote_data


class RemoteArchiveAdmin(admin.ModelAdmin):
    fields = ('id', 'published', 'last_fetch', 'data')
    list_display = ('id', 'published', 'last_fetch')
    readonly_fields = ('data', 'last_fetch')
    actions = ['action_fetch_remote_data']

    def action_fetch_remote_data(self, request, objects):
        meta = objects[0].__class__._meta
        fetch_remote_data.delay(meta.app_label, meta.model_name, [o.pk for o in objects])

        self.message_user(request, _('Fetching latest data for selected remote archives.'))
    action_fetch_remote_data.short_description = _('Fetch remote archives data')
