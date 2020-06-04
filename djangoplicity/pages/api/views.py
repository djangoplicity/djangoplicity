# -*- coding: utf-8 -*-
#
# djangoplicity
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

from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from rest_framework import viewsets
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.generics import get_object_or_404

from djangoplicity.pages.models import Page, PageProxy
from djangoplicity.pages.api.serializers import PageSerializer


# REST views for live page update
class PageAPIView(viewsets.ModelViewSet):
    permission_classes = (DjangoModelPermissions, )
    model = Page
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    def get_object(self):
        '''
        Overriding rest_framework.generics.GenericAPIView.get_object()
        '''
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        try:
            obj = Page.objects.get(**filter_kwargs)
        except Page.DoesNotExist:
            # The page doesn't exist so let let's check if it's a page translation
            obj = get_object_or_404( PageProxy.objects.all(), **filter_kwargs)

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def partial_update(self, request, *args, **kwargs):
        '''
        Extend partial_update to check which fields have change and add
        a LogEntry to the admin interface
        '''
        changed_fields = []
        page = self.get_object()

        # Look for updated fields
        for field in PageSerializer.Meta.fields:
            try:
                data = request.data.get(field, '')
                if data and data != getattr(page, field):
                    # Field has changed
                    changed_fields.append(field)
            except AttributeError:
                continue

        result = super(PageAPIView, self).partial_update(request, *args, **kwargs)

        if changed_fields:
            change_message = 'Changed (with live edit) %s' % ', '.join(changed_fields)
            LogEntry.objects.log_action(
                user_id=request.user.id,
                content_type_id=ContentType.objects.get_for_model(page).pk,
                object_id=page.id,
                object_repr=unicode(page),
                action_flag=CHANGE,
                change_message=change_message
            )

        return result
