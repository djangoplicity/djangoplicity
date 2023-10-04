# -*- coding: utf-8 -*-
#
# djangoplicity-archives
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
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

from django.conf import settings
from django.shortcuts import redirect, render
from djangoplicity.archives.contrib.search import AdvancedSearchForm
from djangoplicity.archives.browsers import select_template, lang_templates


def archive_search_form( request, model=None, options=None, **kwargs ):
    asf = AdvancedSearchForm( options=options, request=request )

    if request.GET and asf.form.is_valid():
        # Remove empty values from request.GET
        params = request.GET.copy()
        for k, v in request.GET.lists():
            if not v or v == ['']:
                del params[k]
        return redirect( "%s?%s" % ( asf.url_list(), params.urlencode() ) )

    context = {
            'options': options,
            'asf': asf,
            'archive_title': options.AdvancedSearch.Meta.verbose_name,
            'archive': model._meta.verbose_name,
    }

    template_names = [
        "archives/%s/advanced_search.html" % model._meta.object_name.lower(),
        "archives/advanced_search.html",
    ]

    # Internationalization for template I18N
    if settings.USE_I18N:
        template_names = lang_templates( model, template_names ) + template_names

    template_name = select_template( template_names )

    return render(request, template_name, context)
