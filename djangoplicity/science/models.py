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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext

from djangoplicity.archives import fields as archivesfields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.contrib import types
from djangoplicity.archives.resources import ResourceManager
from djangoplicity.media.models import Image
from djangoplicity.translation.models import TranslationModel


class ScienceAnnouncement(ArchiveModel, TranslationModel):
    """
    Similar to press releases but with fewer fields.
    """
    id = archivesfields.IdField()
    title = archivesfields.TitleField()
    subtitle = models.CharField(max_length=255, blank=True, help_text=_(u"Optional subtitle to be shown just above the headline."))
    description = archivesfields.DescriptionField()
    contacts = models.TextField(blank=True, help_text=_(u'Contacts'))
    links = models.TextField(blank=True, help_text=_(u'Links'))
    featured = models.BooleanField(default=True)
    related_images = models.ManyToManyField(Image, through='ScienceAnnouncementImage')

    def _set_main_visual(self, vis):
        self._main_visual_cache = vis

    def _get_main_visual(self):
        try:
            return self._main_visual_cache
        except AttributeError:
            try:
                vis = ScienceAnnouncementImage.objects.filter(main_visual=True, science_announcement=self).get()
                self._main_visual_cache = vis.archive_item
                return vis.archive_item
            except IndexError:
                return None
            except ScienceAnnouncementImage.DoesNotExist:
                return None

    main_visual = property(_get_main_visual)

    class Meta:
        ordering = ['-release_date', '-id']
        get_latest_by = "release_date"
        permissions = [
            ("view_only_non_default", "Can view only non default language"),
        ]

    def get_absolute_url(self):
        return reverse('scienceannouncements_detail', args=[str(self.id)])

    def __unicode__(self):
        return u"%s: %s" % (self.id, self.title)

    class Archive:
        pdf = ResourceManager(type=types.PDFType)
        pdfsm = ResourceManager(type=types.PDFType)
        sciencepaper = ResourceManager(type=types.PDFType, verbose_name=_('Science paper'))

        class Meta:
            root = settings.SCIENCEANNOUNCEMENTS_ARCHIVE_ROOT
            release_date = True
            embargo_date = True
            last_modified = True
            created = True
            published = True
            rename_pk = ('science_scienceannouncement', 'id')
            rename_fks = (
                ('media_image', 'release_date_owner'),
                ('science_scienceannouncementimage', 'science_announcement_id'),
            )
            sort_fields = ['last_modified', 'release_date', ]


# =======================================
# Related images, etc.
# =======================================

class RelatedScienceAnnouncement(models.Model):
    """
    Abstract model to link another archive item (e.g. visuals) to a
    ScienceAnnouncement. The Model should be subclassed and used as
    a many-to-many intermediary model::

        class RelatedAnnouncementScienceImage(RelatedRAnnouncement):
            archive_item = models.ForeignKey(Image, verbose_name=('Image'))

            class Meta:
                verbose_name = _('...')
    """

    science_announcement = models.ForeignKey(ScienceAnnouncement, verbose_name=_('Related science announcement'))
    # The announcement to link with another archive item.

    order = models.PositiveSmallIntegerField(blank=True, null=True)
    # Used to define an order for the archive items, in case this should not be via the alphabetic order of the id.

    main_visual = models.BooleanField(default=False)
    # Defines the primary visual for an announcement - the user is responsible for only selecting one main visual.

    override_id = models.SlugField(blank=True, null=True, verbose_name=_('Override ID'))
    # In case you ingest a visual into several announcements, this field can be
    # used to override the id.

    hide = models.BooleanField(default=False, verbose_name=_('Hide on kiosk'))
    # Define if the visual should be hidden if used for e.g. the kiosk

    def __unicode__(self):
        return ugettext("Archive Item for Science Announcement %s" % (unicode(self.science_announcement.id)))

    class Meta:
        abstract = True


class ScienceAnnouncementImage(RelatedScienceAnnouncement):
    """ Images related to an announcement. """
    archive_item = models.ForeignKey(Image, verbose_name=_('Related Image'))
