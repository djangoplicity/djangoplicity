# -*- coding: utf-8 -*-
#
# djangoplicity-cutter
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

from functools import update_wrapper

from django.conf.urls import url
from django.conf import settings
from django.contrib.admin import ModelAdmin

from djangoplicity.cutter.views import CropView


class CropAdmin(ModelAdmin):
    def get_urls(self):
        '''
        Catch /admin/<app>/<model>/<id>/rename/ URLs and direct them to
        the crop view
        '''
        # Tool to wrap class method into a view
        # START: Copied from django.contrib.admin.options

        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name
        # END: Copied from django.contrib.admin.options

        urlpatterns = [
            url(
                r'^(?P<pk>.+)/crop/$',
                wrap(self.get_view()),
                name='%s_%s_crop' % info
            )
        ]

        # Note, must be last one, otherwise the change view
        # consumes everything else.
        urlpatterns += super(CropAdmin, self).get_urls()

        return urlpatterns

    def get_view(self):
        return CropView.as_view(
            model=self.model,
            opts=self.model._meta,
            media=self.media,
        )

    class Media:
        js = (settings.JQUERY_JS, 'js/crop.js')
        css = {
            'all': ('css/crop.css', ),
        }
