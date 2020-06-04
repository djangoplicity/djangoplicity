# -*- coding: utf-8 -*-
#
# djangoplicity-archives-importer
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

import os

from django import forms
from django.core.exceptions import FieldDoesNotExist

from djangoplicity.archives.contrib.forms import PriorityField
from djangoplicity.contrib.admin import widgets


class GenericImportForm( forms.Form ):
    """
    Form for a file import row. This form may be subclassed to provided
    extra form fields in import rows. For example please see djangoplicity.media.options.ImageImportForm
    """
    id = forms.CharField( max_length=250, widget=widgets.StaticTextWidget() )
    date_modified = forms.CharField( max_length=250, widget=widgets.StaticTextWidget() )
    title = forms.CharField( max_length=250, widget=forms.TextInput( attrs={'size': '30'} ) )
    priority = PriorityField()
    is_new = forms.BooleanField( required=False, widget=widgets.BooleanIconDisplayWidget )
    formats = forms.CharField( max_length=250, widget=widgets.StaticTextWidget() )
    published = forms.BooleanField( required=False, initial=False )


class GenericImportFormSet ( forms.formsets.BaseFormSet ):
    """
    Form set for an entire table of file import rows
    """
    def add_fields( self, form, index ):
        form.fields["import"] = forms.BooleanField( required=False, widget=widgets.SelectorInput( {'class': 'action-select'} ) )

        super( GenericImportFormSet, self ).add_fields( form, index )


class UploadFileForm ( forms.Form ):
    """
    Files upload form that allows uploading resources into the import directory.

    Requires that ArchiveOptions.Import.scan_directories is passed in constructor when
    creating an instance, e.g.::

        UploadFileForm( directories = options.Import.scan_directories )

    The available list of formats is automatically generated from the scan_directories
    variable.
    """
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    format = forms.ChoiceField( choices=[('1', 'a')] )

    def __init__( self, *args, **kwargs ):
        """
        """
        self.directories = kwargs.get( 'directories', [] )
        self.model = kwargs['model' ]
        del kwargs['directories']
        del kwargs['model']
        super( UploadFileForm, self ).__init__( *args, **kwargs )

        choices = [( x[0], x[0] ) for x in self.directories if hasattr( self.model.Archive, x[0] )]
        choices.sort( key=lambda y: y[1] )
        self.fields['format'].choices = choices

    def handle_files(self, request, path_to_save):
        """
        Write uploaded files to import directory.
        """
        for f in request.FILES.getlist('files'):
            destination = open( os.path.join( path_to_save, f.name ), 'w+' )
            for chunk in f.chunks():
                destination.write( chunk )
            destination.close()

    def clean(self):
        """
        Check if extensions of uploaded files is allowed.
        """
        cleaned_data = self.cleaned_data

        if not self.files:
            return cleaned_data

        # Get cleaned data
        uploaded_files = self.files.getlist('files')
        format = cleaned_data.get('format')

        for uploaded_file in uploaded_files:
            if uploaded_file and format:
                # Find extension of uploaded files
                ( obj_id, ext ) = os.path.splitext( uploaded_file.name )

                # Check maximum length for original files
                try:
                    max_length = self.model._meta.get_field('id').max_length
                except FieldDoesNotExist:
                    max_length = 0

                if max_length and len(obj_id) > max_length:
                    raise forms.ValidationError('Filename for %s original format '
                        'must be shorter than %d characters' %
                        (self.model._meta.verbose_name_plural, max_length))

                # Check against allowed extensions
                for name, allowed_exts in self.directories:
                    if name == format:
                        if ext not in allowed_exts:
                            raise forms.ValidationError( '%s is not a valid extension. Valid extensions for %s format are: %s' % ( ext, format, ( ', ' ).join( allowed_exts ) ) )

        return cleaned_data
