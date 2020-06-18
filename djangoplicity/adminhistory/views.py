# -*- coding: utf-8 -*-
#
# djangoplicity-adminhistory
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
from __future__ import unicode_literals

from django.contrib.admin.models import LogEntry
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.db import models
from django.http import Http404
from django.shortcuts import render
from django.utils.http import urlencode
import operator
from functools import reduce

# Fields to search through
_fields = ['user__username', 'object_repr', 'object_id', 'change_message']

# Mapping of query paramters to LogEntry fields
queryparams = (
    ('u', 'user'),
    ('ct', 'content_type'),
    ('id', 'object_id'),
    ('a', 'action_flag'),
)

# Create special permission


@staff_member_required
def adminhistory_view(request):
    """
    View for browsing the admin history (i.e a log over all objects that have been edited
    via the administration interface)
    """
    # Require super-user access to browse
    if not (request.user.is_superuser or request.user.username == 'eson'):
        raise Http404

    #
    # Make query set
    #
    querydict = {}
    qs = LogEntry.objects.all().select_related('content_type', 'user')

    # Search
    val = request.GET.get("s", None)
    searchval = ""
    if _fields and val:
        qobjects = []
        for f in _fields:
            arg = "%s__icontains" % f
            qobjects.append(models.Q(**{arg: val}))
        qs = qs.filter(reduce(operator.or_, qobjects))
        querydict['s'] = val
        searchval = val

    # Get page parameters and filter result.
    for p, f in queryparams:
        val = request.GET.get(p, None)
        if val:
            qs = qs.filter(**{f: val})
            querydict[p] = val

    # Get page num
    try:
        page = int(request.GET.get('p', '1'))
    except ValueError:
        page = 1

    paginator = Paginator(qs, 100)

    # Adapt page to list
    try:
        objects = paginator.page(page)
    except (EmptyPage, InvalidPage):
        objects = paginator.page(paginator.num_pages)

    # Build query string
    querystring = urlencode(querydict)
    querystring = "?" if not querystring else "?%s&" % querystring

    # Render template
    return render(request, 'admin/adminhistory/list.html', {
            'objects': objects,
            'messages': [],
            'querystring': querystring,
            'querydict': querydict,
            'searchval': searchval,
        },
    )
