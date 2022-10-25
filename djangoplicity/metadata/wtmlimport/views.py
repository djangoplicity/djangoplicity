# -*- coding: utf-8 -*-
#
# djangoplicity-media
# Copyright (c) 2007-2015, European Southern Observatory (ESO)
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

from builtins import str
import xml.etree.ElementTree as ET

from django import forms
from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.views.generic import FormView

from djangoplicity.media.models import Image

import django
if django.VERSION >= (2, 0):
    from django.urls import reverse_lazy
else:
    from django.core.urlresolvers import reverse_lazy


class MultiFileInput(forms.FileInput):
    def render(self, name, value, attrs={}, renderer=None):
        attrs['multiple'] = 'multiple'
        return super(MultiFileInput, self).render(name, None, attrs=attrs)

    def value_from_datadict(self, data, files, name):
        if hasattr(files, 'getlist'):
            return files.getlist(name)
        else:
            return [files.get(name)]


class MultiFileField(forms.FileField):
    widget = MultiFileInput
    default_error_messages = {
        'min_num': u"Ensure at least %(min_num)s files are uploaded (received %(num_files)s).",
        'max_num': u"Ensure at most %(max_num)s files are uploaded (received %(num_files)s).",
        'file_size': u"File: %(uploaded_file_name)s, exceeded maximum upload size."
    }

    def __init__(self, *args, **kwargs):
        self.min_num = kwargs.pop('min_num', 0)
        self.max_num = kwargs.pop('max_num', None)
        self.maximum_file_size = kwargs.pop('maximum_file_size', None)
        super(MultiFileField, self).__init__(*args, **kwargs)

    def to_python(self, data):
        ret = []
        for item in data:
            ret.append(super(MultiFileField, self).to_python(item))
        return ret

    def validate(self, data):
        super(MultiFileField, self).validate(data)
        num_files = len(data)
        if len(data) and not data[0]:
            num_files = 0
        if num_files < self.min_num:
            raise ValidationError(self.error_messages['min_num'] % {'min_num': self.min_num, 'num_files': num_files})
        elif self.max_num and num_files > self.max_num:
            raise ValidationError(self.error_messages['max_num'] % {'max_num': self.max_num, 'num_files': num_files})
        for uploaded_file in data:
            if uploaded_file.size > self.maximum_file_size:
                raise ValidationError(self.error_messages['file_size'] % { 'uploaded_file_name': uploaded_file.name})


class WTMLForm(forms.Form):
    files = MultiFileField(min_num=1, max_num=40, maximum_file_size=100 * 1024)  # 100KB

@login_required
class WTMLMetadataImport(FormView):
    form_class = WTMLForm
    template_name = 'admin/metadata/wtml_metadata_import.html'
    success_url = reverse_lazy('wtml_metadata_import')

    def form_valid(self, form):
        self.process_files()
        messages.add_message(self.request, messages.SUCCESS, 'Import complete, a summary email was sent to %s' % self.request.user.email)
        return super(WTMLMetadataImport, self).form_valid(form)

    def process_files(self):
        message = ''

        for f in self.request.FILES.getlist('files'):

            if not f.name.endswith('.wtml'):
                message += '%s: Invalid extension\n' % f.name
                continue

            root = ET.fromstring(f.read())

            imageset = root.find('Place/ForegroundImageSet/ImageSet')

            if imageset is None:
                message += '%s: Invalid file\n' % f.name
                continue

            keys = ('Rotation', 'CenterY', 'CenterX', 'BaseDegreesPerTile',
                    'OffsetX', 'OffsetY')

            missing_keys = []
            for key in keys:
                if key not in list(imageset.keys()):
                    missing_keys.append(key)

            if missing_keys:
                message += '%s: Invalid file, missing keys: %s\n' % \
                        (f.name, ', '.join(missing_keys))

            pk = f.name[:-5]
            i = None
            try:
                i = Image.objects.get(pk=pk)
            except Image.DoesNotExist:
                pass

            if not i:
                # Image not found, try replacing ' ' by '-'
                try:
                    i = Image.objects.get(pk=pk.replace(' ', '-'))
                except Image.DoesNotExist:
                    pass

            if not i:
                # Image not found, try replacing ' ' by '_'
                try:
                    i = Image.objects.get(pk=pk.replace(' ', '-'))
                except Image.DoesNotExist:
                    message += '%s: Image not found in archive: "%s"\n' % (f.name, pk)
                    continue

            # Set image attributes
            i.spatial_coordinate_frame = 'ICRS'
            i.spatial_equinox = 'J2000'
            i.spatial_coordsystem_projection = 'TAN'
            # We cast CenterX and Y to float to round them as expected
            center_x = float(imageset.get('CenterX'))
            center_y = float(imageset.get('CenterY'))
            i.spatial_reference_value = '%s;%s' % (center_x, center_y)
            i.spatial_scale = '-%s;%s' % (imageset.get('BaseDegreesPerTile'), imageset.get('BaseDegreesPerTile'))
            rotation = imageset.get('Rotation')
            if rotation.startswith('-'):
                i.spatial_rotation = rotation[1:]
            else:
                i.spatial_rotation = '-%s' % rotation
            pixel_x = float(imageset.get('OffsetX'))
            pixel_y = float(imageset.get('OffsetY'))
            try:
                dimension_x, dimension_y = i.get_spatial_reference_dimension()
            except ValueError:
                message += '%s: Invalid spatial reference dimension\n' % pk
                continue
            if float(dimension_x) % 2:
                pixel_x += 0.5
            if float(dimension_y) % 2:
                pixel_y += 0.5
            i.spatial_reference_pixel = '%s;%s' % (pixel_x, pixel_y)
            i.spatial_quality = 'Position'

            i.save()
            message += '%s: Successfully parsed\n' % f.name

            change_message = 'Imported from WTML file: Coordinate Frame, Equinox, Reference Value, Reference Pixel, Scale, Rotation, Coordinate System Projection'
            LogEntry.objects.log_action(
                user_id=self.request.user.id,
                content_type_id=ContentType.objects.get_for_model(i).pk,
                object_id=i.pk,
                object_repr=str(i),
                action_flag=CHANGE,
                change_message=change_message
            )

        if self.request.user.email:
            send_mail(
                'WTML Files import summary',
                message,
                'no-reply@eso.org',
                [self.request.user.email],
                fail_silently=True
            )
