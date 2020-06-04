# -*- coding: utf-8 -*-
#
# djangoplicity-science
# Copyright (c) 2007-2013, European Southern Observatory (ESO)
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

from djangoplicity.archives.contrib.admin.defaults import RenameAdmin, \
    ArchiveAdmin, view_link
from djangoplicity.contrib import admin as dpadmin

from djangoplicity.science.models import ScienceAnnouncement, ScienceAnnouncementImage


class ScienceAnnouncementImageInlineAdmin(admin.TabularInline):
    model = ScienceAnnouncementImage
    fields = ('archive_item', 'override_id', 'order', 'main_visual', 'hide')
    raw_id_fields = ('archive_item', )


class ScienceAnnouncementAdmin(dpadmin.DjangoplicityModelAdmin, RenameAdmin, ArchiveAdmin):
    list_display = ('id', 'title', 'published', 'featured', 'release_date', 'embargo_date', 'last_modified', view_link('scienceannouncements'), )
    list_filter = ('published', 'featured', 'last_modified', 'release_date', 'embargo_date', )
    list_editable = ('title',)
    search_fields = ('id', 'title', 'description', )
    date_hierarchy = 'release_date'
    ordering = ('-release_date', '-last_modified', )
    richtext_fields = ('description', 'contacts', 'links')
    actions = ['action_mutiple_item_displays', 'action_toggle_published', ]
    fieldsets = (
                    (None, {'fields': ('id', )}),
                    ('Publishing', {'fields': ('published', 'featured', 'release_date', 'embargo_date'), }),
                    ('Archive', {'fields': ('title', 'subtitle', 'description', 'links', 'contacts'), }),
                )
    inlines = [ScienceAnnouncementImageInlineAdmin, ]

    def get_queryset(self, request):
        qs = super(ScienceAnnouncementAdmin, self).get_queryset(request)
        return ArchiveAdmin.limit_access(self, request, qs)


def register_with_admin(admin_site):
    admin_site.register(ScienceAnnouncement, ScienceAnnouncementAdmin)

register_with_admin(admin.site)
