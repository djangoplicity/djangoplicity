# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.contrib.admin.models import LogEntry
from django.http import Http404
from django.shortcuts import render

ENTRIES_PER_PAGE = 100


def list_admin_log_entries(request, start=0):

    if not request.user.is_superuser:
        raise Http404

    start = int(start)
    all = LogEntry.objects.all()
    cnt = all.count()
    entries = all[start:start + ENTRIES_PER_PAGE]
    limits = (start, start + len(entries))

    if start > 0:
        prev = start - ENTRIES_PER_PAGE
        if prev < 0:
            prev = 0
    else:
        prev = False

    if limits[1] == start + ENTRIES_PER_PAGE:
        next = start + ENTRIES_PER_PAGE
    else:
        next = False

    return render(request, 'admin/log/list_entries.html', {
        'entries': entries,
        'limits': limits,
        'prev': prev,
        'next': next,
        'total': cnt
    })
