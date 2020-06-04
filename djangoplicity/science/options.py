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

from django.utils.translation import ugettext_noop

from djangoplicity.archives.contrib import security
from djangoplicity.archives.contrib.browsers import ListBrowser
from djangoplicity.archives.contrib.info import admin_edit_for_site, published
from djangoplicity.archives.contrib.queries.defaults import AllPublicQuery, \
    UnpublishedQuery, EmbargoQuery, StagingQuery
from djangoplicity.archives.options import ArchiveOptions
from djangoplicity.archives.utils import related_archive_items
from djangoplicity.media.info import object_id

from djangoplicity.science.models import ScienceAnnouncement


class ScienceAnnouncementOptions(ArchiveOptions):
    description_template = 'archives/scienceannouncement/object_description.html'

    urlname_prefix = 'scienceannouncements'

    admin = (
        (ugettext_noop(u'Admin'), {'links': (admin_edit_for_site('admin_site'),), 'fields': (published, 'release_date', 'last_modified', 'created'), }),
    )

    info = (
        (ugettext_noop(u'About the Announcement'), {'fields': (object_id,)}),
    )

    downloads = (
        (ugettext_noop(u'Images'), {'resources': ('original', 'large', 'screen'), 'icons': {'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot'}}),
    )

    search_fields = ('id', 'title', 'description', 'contacts', 'links',)

    class Queries(object):
        default = AllPublicQuery(browsers=('normal', 'viewall'), verbose_name=ugettext_noop("Announcements"), feed_name="default")
        embargo = EmbargoQuery(browsers=('normal', 'viewall'), verbose_name=ugettext_noop("Embargoed Announcements"))
        staging = StagingQuery(browsers=('normal', 'viewall'), verbose_name=ugettext_noop("Announcements (Staging)"))

    class Browsers(object):
        normal = ListBrowser()
        viewall = ListBrowser(verbose_name=ugettext_noop(u'View all'), paginate_by=100)

    class ResourceProtection(object):
        unpublished = (UnpublishedQuery, security.UNPUBLISHED_PERMS)
        staging = (StagingQuery, security.STAGING_PERMS)
        embargo = (EmbargoQuery, security.EMBARGO)

    @staticmethod
    def extra_context(obj, lang=None):
        images = related_archive_items(ScienceAnnouncement.related_images, obj)

        return {
            'main_visual': obj.main_visual,
            'images': images,
        }

    @staticmethod
    def feeds():
        from djangoplicity.science.feeds import ScienceAnnouncementFeed
        return {
                '': ScienceAnnouncementFeed,
        }
