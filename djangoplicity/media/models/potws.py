# -*- coding: utf-8 -*-
#
# djangoplicity-media
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

from datetime import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django.db.models import signals
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible
from djangoplicity.archives import fields as archive_fields
from djangoplicity.archives.base import ArchiveModel
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.archives.utils import propagate_release_date, release_date_change_check
from djangoplicity.media.models.comparisons import ImageComparison, ImageComparisonProxy
from djangoplicity.media.models.images import Image, ImageProxy
from djangoplicity.media.models.videos import Video, VideoProxy
from djangoplicity.translation.models import TranslationForeignKey, \
    TranslationModel

# Picture of the Week translations
# ================================
# POTWs only links to related objects, and does not itself have any
# fields to translate. However to not make queries overly complex
# and make the model fit with the rest of the code infrastructure
# we make it into a translation model.
#
# This was we can easily get all POTWs for a given language


@python_2_unicode_compatible
class PictureOfTheWeek( ArchiveModel, TranslationModel ):
    """
    Model representing that an picture of the week. The model
    can either use an image or a video as it's main visual. The release date
    set will be propagate to the image/video model.
    """
    id = archive_fields.IdField()
    image = TranslationForeignKey( Image, blank=True, null=True, only_sources=False, on_delete=models.CASCADE )
    video = TranslationForeignKey( Video, blank=True, null=True, only_sources=False, on_delete=models.CASCADE )
    comparison = models.ForeignKey( ImageComparison, blank=True, null=True, on_delete=models.CASCADE )
    auto_update = True

    def visual(self):
        """
        Obtain either an image or a video if specified.
        """
        if self.image:
            return self.image
        elif self.video:
            return self.video
        elif self.comparison:
            return self.comparison
        else:
            return None

    def get_absolute_url(self):
        """
        URL of image or video detail view, since POTW does not
        use its own detail view.
        """
        v = self.visual()
        return v.get_absolute_url() if v else None

    def rename( self, new_pk ):
        '''
        Extend Archive's rename() to send email notification if original is renamed
        '''
        if self.published and self.is_source() and hasattr(settings, 'RELEASE_RENAME_NOTIFY'):
            msg_subject = 'Picture of the Week renamed: %s -> %s' % ( self.pk, new_pk )
            msg_body = """https://www.eso.org/public/images/%s/""" % new_pk
            msg_from = getattr(settings, 'DEFAULT_FROM_EMAIL', '')
            msg_to = getattr(settings, 'POTW_RENAME_NOTIFY', '')
            if msg_from and msg_to:
                send_mail( msg_subject, msg_body, msg_from, msg_to, fail_silently=False )

        return super( PictureOfTheWeek, self ).rename(new_pk)

    def save( self, **kwargs ):
        signals.post_save.disconnect( PictureOfTheWeek.post_save_handler, sender=PictureOfTheWeek )
        signals.post_save.disconnect( PictureOfTheWeek.post_related_save_handler, sender=Image )
        signals.post_save.disconnect( PictureOfTheWeek.post_related_save_handler, sender=ImageProxy )
        signals.post_save.disconnect( PictureOfTheWeek.post_related_save_handler, sender=Video )
        signals.post_save.disconnect( PictureOfTheWeek.post_related_save_handler, sender=VideoProxy )
        signals.post_save.disconnect( PictureOfTheWeek.post_related_save_handler, sender=ImageComparison )
        signals.post_save.disconnect( PictureOfTheWeek.post_related_save_handler, sender=ImageComparisonProxy )
        super( PictureOfTheWeek, self ).save( **kwargs )
        signals.post_save.connect( PictureOfTheWeek.post_save_handler, sender=PictureOfTheWeek )
        signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=Image )
        signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=ImageProxy )
        signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=Video )
        signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=VideoProxy )
        signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=ImageComparison )
        signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=ImageComparisonProxy )

    @classmethod
    def get_latest(cls):
        """
        Method to get the latest public POTW
        """
        try:
            now = datetime.now()
            im = cls.objects.filter( published=True, release_date__lt=now, embargo_date__lt=now ).order_by('-release_date')[0]
            return im
        except IndexError:
            raise cls.DoesNotExist

    def __str__(self):
        v = self.visual()
        return "%s - %s" % (self.id, v.title) if v else self.id

    @classmethod
    def post_save_handler( cls, sender, instance=None, created=False, raw=False, **kwargs ):
        """
        Automatically create/delete POTW translations for images/videos/comparisons.
        """
        if instance.auto_update and not raw:
            # Delete all translations and add new ones
            instance.translations.all().delete()
            for attr in ['image', 'comparison', 'video', ]:
                # If related object exists and has translations, then
                # create corresponding potw translations for all.
                related_object = getattr( instance, attr )
                if related_object and isinstance( related_object, TranslationModel ):
                    for related_obj_trans in related_object.translations.all():
                        potw_trans = PictureOfTheWeekProxy( **{
                            attr: related_obj_trans,
                            'lang': related_obj_trans.lang,
                            'source': instance,
                            'translation_ready': related_obj_trans.translation_ready,
                            'published': related_obj_trans.published,
                        } )
                        potw_trans.clean()
                        potw_trans.save()
                    # Stop processing since we can only have one
                    # image, comparison or video defined at a given time.
                    break

    @classmethod
    def post_related_save_handler( cls, sender, instance=None, created=False, raw=False, **kwargs ):
        """
        Once a related object is saved, we might need to run post_save_handle for the POTW
        """
        if not raw:
            if isinstance( instance, TranslationModel ):
                instance = instance if instance.is_source() else instance.source
                for potw in instance.pictureoftheweek_set.all():
                    cls.post_save_handler( sender, instance=potw, created=created, raw=raw )

    class Meta:
        ordering = ('-release_date', )
        verbose_name_plural = _('Pictures of the Week')
        app_label = 'media'
        permissions = [
            ( "view_only_non_default", "Can view only non default language" ),
        ]

    class Translation:
        fields = ['image', 'video', 'comparison']
        excludes = [ 'published', 'last_modified', 'created', ]

    class Archive:
        class Meta:
            release_date = True
            embargo_date = True
            last_modified = True
            created = True
            published = True
            rename_pk = ('media_pictureoftheweek', 'id')
            rename_fks = (
                            ('media_pictureoftheweek', 'source_id'),
                            ('media_image', 'release_date_owner'),
                            ('media_video', 'release_date_owner'),
                            ('media_imagecomparison', 'release_date_owner'),
                        )
            sort_fields = ['last_modified', 'release_date']


# ========================================================================
# Translation proxy model
# ========================================================================

class PictureOfTheWeekProxy( PictureOfTheWeek, TranslationProxyMixin ):
    """
    Image proxy model for creating admin only to edit
    translated objects.
    """
    objects = PictureOfTheWeek.translation_objects

    def clean( self ):
        # Note: For some reason it's not possible to
        # to define clean/validate_unique in TranslationProxyMixin
        # so we have to do this trick, where we add the methods and
        # call into translation proxy mixin.
        self.id_clean()

    def validate_unique( self, exclude=None ):
        self.id_validate_unique( exclude=exclude )

    class Meta:
        proxy = True
        verbose_name = _('Picture of the Week translation')
        app_label = 'media'

    class Archive:
        class Meta:
            rename_pk = ( 'media_pictureoftheweek', 'id' )
            rename_fks = (
                            ('media_pictureoftheweek', 'source_id'),
                            ('media_image', 'release_date_owner'),
                            ('media_video', 'release_date_owner'),
                            ('media_imagecomparison', 'release_date_owner'),
                        )


# Send notification email when translation_ready is changed to True
#signals.pre_save.connect( PictureOfTheWeekProxy.send_notification_mail, sender=PictureOfTheWeekProxy )
signals.pre_save.connect( release_date_change_check, sender=PictureOfTheWeek )
signals.pre_save.connect( release_date_change_check, sender=PictureOfTheWeekProxy )
signals.post_save.connect( PictureOfTheWeek.post_save_handler, sender=PictureOfTheWeek )
signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=Image )
signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=ImageProxy )
signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=Video )
signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=VideoProxy )
signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=ImageComparison )
signals.post_save.connect( PictureOfTheWeek.post_related_save_handler, sender=ImageComparisonProxy )
#signals.post_delete( PictureOfTheWeek.post_delete_handler, sender=PictureOfTheWeek ) # note needed, since related objects are deleted when source is deleted

# Propagate PictureOfTheWeek release date to Image and Videos.
propagate_release_date( PictureOfTheWeek.image )
propagate_release_date( PictureOfTheWeek.video )
propagate_release_date( PictureOfTheWeek.comparison )
