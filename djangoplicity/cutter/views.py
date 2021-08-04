# -*- coding: utf-8 -*-
#
# djangoplicity-cutter
# Copyright (c) 2007-2016, European Southern Observatory (ESO)
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

from __future__ import division

from builtins import str
import json
from collections import OrderedDict

from django.contrib import messages
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect, Http404
from django.utils.translation import ugettext as _
from django.views.generic import UpdateView

from djangoplicity.archives.resources import ImageResourceManager


class CropView(UpdateView):
    template_name = 'admin/cutter/crop_form.html'
    fields = ('crop_offsets', )
    media = None
    opts = None

    def get_object(self, queryset=None):
        '''
        We override the queryset to make sure the pk is unquoting to avoid
        issues with pks with undescores
        '''
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        # Next, try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg)

        # If none of those are defined, it's an error.
        if pk is None:
            raise AttributeError("Generic detail view %s must be called with "
                                "either an object pk or a slug."
                                % self.__class__.__name__)
        else:
            queryset = queryset.filter(pk=unquote(pk))

        try:
            # Get the single item from the filtered queryset
            obj = queryset.get()
        except queryset.model.DoesNotExist:
            raise Http404(_("No %(verbose_name)s found matching the query") %
                        {'verbose_name': queryset.model._meta.verbose_name})
        return obj

    def get_context_data(self, **kwargs):
        context = super(CropView, self).get_context_data(**kwargs)

        archive = self.get_object()
        offsets = json.loads(archive.crop_offsets) if archive.crop_offsets else {}
        crop_display_resource = getattr(archive, 'resource_%s' %
                                    archive.Archive.Meta.crop_display_format)


        # Get list of cropped formats
        crop_formats = OrderedDict()

        if archive.width and archive.height:
            for fmt_name in dir(self.model.Archive):
                fmt = getattr(self.model.Archive, fmt_name)

                if isinstance(fmt, ImageResourceManager) and fmt.type.width and \
                    fmt.type.height:

                    if archive.width / archive.height == fmt.type.width / fmt.type.height:
                        continue

                    if archive.width / archive.height > fmt.type.width / fmt.type.height:
                        ratio = crop_display_resource.height / archive.height
                        ratio_fmt = crop_display_resource.height / fmt.type.height
                        crop = 'horizontal'
                        width = int(round((crop_display_resource.width - fmt.type.width * ratio_fmt) / 2))
                        height = 0
                    else:
                        ratio = crop_display_resource.width / archive.width
                        ratio_fmt = crop_display_resource.width / fmt.type.width
                        crop = 'vertical'
                        width = 0
                        height = int(round((crop_display_resource.height - fmt.type.height * ratio_fmt) / 2))

                    aspect = fmt.type.width / fmt.type.height

                    # We convert the aspect to unicode as JSON uses
                    # strings as keys, and to make sure we use a doted decimal
                    # instead of coma, regardless of the rendering language
                    aspect = str(aspect)

                    try:
                        offset = offsets[aspect]
                    except KeyError:
                        offset = 0

                    try:
                        crop_formats[aspect]['formats'].append(fmt_name)
                    except KeyError:
                        crop_formats[aspect] = {
                            'formats': [fmt_name],
                            'aspect': aspect,
                            'crop': crop,
                            'width': width,
                            'height': height,
                            'offset': int(round(offset * ratio)),
                            'ratio': str(ratio),
                        }

        context['crop_formats'] = crop_formats
        context['media'] = self.media
        context['opts'] = self.opts
        context['app_label'] = self.opts.app_label
        context['crop_display_resource'] = crop_display_resource

        return context

    def post(self, request, *args, **kwargs):
        archive = self.get_object()
        messages.add_message(request, messages.INFO, 'Crop offsets updated.')

        offsets = {}
        for k, v in list(request.POST.items()):
            if not k.startswith('offset-'):
                continue

            k = k.split('-')[1]
            offset = int(v)

            if offset != 0:
                ratio = request.POST.get('ratio-%s' % k)
                offsets[k] = offset / float(ratio)

        self.model.objects.filter(pk=archive.pk).update(
            crop_offsets=json.dumps(offsets)
        )

        self.model.reimport_resources(archive, request.user)

        return HttpResponseRedirect(request.path)
