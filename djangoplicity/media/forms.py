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

from __future__ import absolute_import

from collections import OrderedDict

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from djangoplicity.archives.importer.forms import GenericImportForm
from djangoplicity.archives.contrib.forms import PriorityField
from djangoplicity.contrib.admin import widgets
from djangoplicity.media.models import Image


class ImageImportForm( GenericImportForm ):
    """
    Extra form fields for the image file import
    """
    zoomify = forms.BooleanField( required=False, initial=True )
    wallpapers = forms.BooleanField( required=False, initial=True )

    def __init__(self, *args, **kwargs):
        '''
        Add an optional credit field after the title if IMAGE_IMPORT_SHOW_CREDIT
        is True
        '''
        super(ImageImportForm, self).__init__(*args, **kwargs)

        if not getattr(settings, 'IMAGE_IMPORT_SHOW_CREDIT', False):
            return

        new_fields = OrderedDict()
        for key, value in self.fields.items():  # pylint: disable=access-member-before-definition
            new_fields[key] = value
            if key == 'title':
                new_fields['credit'] = forms.CharField(
                    max_length=250, widget=forms.TextInput(attrs={'size': '30'}))

        self.fields = new_fields


class ImageComparisonImportForm( GenericImportForm ):
    """
    Extra form fields for the image file import
    """
    image_before = forms.SlugField( required=True )
    image_after = forms.SlugField( required=True )

    def _clean_image( self, image_field ):
        data = self.cleaned_data[image_field]
        try:
            data = Image.objects.get( pk=data )
        except Image.DoesNotExist:
            raise ValidationError( "Image does not exists." )
        return data

    def clean_image_before( self ):
        return self._clean_image( 'image_before' )

    def clean_image_after( self ):
        return self._clean_image( 'image_after' )


class VideoImportForm( GenericImportForm ):
    """
    Extra form fields for the video file import
    """
    delete_old_formats = forms.BooleanField( required=False, initial=True )

    def __init__(self, *args, **kwargs):
        '''
        Add an optional credit field after the title if VIDEO_IMPORT_SHOW_CREDIT
        is True
        '''
        super(VideoImportForm, self).__init__(*args, **kwargs)

        if not getattr(settings, 'VIDEO_IMPORT_SHOW_CREDIT', False):
            return

        new_fields = OrderedDict()
        for key, value in self.fields.items():  # pylint: disable=access-member-before-definition
            new_fields[key] = value
            if key == 'title':
                new_fields['credit'] = forms.CharField(
                    max_length=250, widget=forms.TextInput(attrs={'size': '30'}))

        self.fields = new_fields


class SubtitleImportForm ( forms.Form ):
    """
    form for subtitle import
    """

    id = forms.CharField( max_length=250, widget=widgets.StaticTextWidget() )
    date_modified = forms.CharField( max_length=250, widget=widgets.StaticTextWidget() )
    video = forms.CharField( max_length=250, widget=widgets.StaticTextWidget() )
    lang = forms.CharField( max_length=2, widget=widgets.StaticTextWidget() )
    priority = PriorityField()
    is_new = forms.BooleanField( required=False, widget=widgets.BooleanIconDisplayWidget )
    formats = forms.CharField( max_length=250, widget=widgets.StaticTextWidget() )
    published = forms.BooleanField( required=False, initial=False )
