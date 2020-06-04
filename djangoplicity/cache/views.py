# -*- coding: utf-8 -*-
#
# djangoplicity-cache
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
#

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.cache.backends.base import InvalidCacheBackendError
from django.shortcuts import render


@login_required
@user_passes_test( lambda u: u.is_superuser, settings.LOGIN_URL )
def main( request ):
    """
    """
    return render(request, 'admin/cache/index.html', {
        'title': 'Cache Administration'
    })


@login_required
@user_passes_test( lambda u: u.is_superuser, settings.LOGIN_URL )
def clear_cache_view( request ):
    """
    View to clear the cache
    """
    if request.method == 'POST':
        from djangoplicity.cache.tasks import clear_cache_now
        clear_cache_now.delay()
        return render(request, 'admin/cache/clear.html', {
            'started': True,
            'title': 'Clear cache',
        })
    else:
        return render(request, 'admin/cache/clear.html', {
            'title': 'Clear cache',
        })


@login_required
@user_passes_test( lambda u: u.is_superuser, settings.LOGIN_URL )
def memcache_info( request ):
    """
    View to display memcache statistics

    Only works with Django 1.3+ using the settings.CACHES setting.
    """
    try:
        # Check if memcache is used:
        hosts = []

        for backend in settings.CACHES.values():
            if backend["BACKEND"] == 'django.core.cache.backends.memcached.MemcachedCache':
                hosts.extend( backend["LOCATION"] )

        if not hosts:
            raise InvalidCacheBackendError("You are not using memcache as cache backend - %s" % settings.CACHES)

        # Import module
        try:
            import memcache
        except ImportError:
            raise InvalidCacheBackendError("Statistics only works with python-memcache and not e.g. the cmemcache module.")

        # Retrieve statistics from servers
        mc = memcache.Client( hosts, debug=0 )
        stats = mc.get_stats()

        # Regroup statistics for display purposes.
        header = ['']
        keys = []

        for host in stats:
            header.append( host[0] )
            keys += host[1].keys()

        keys = list(set(keys))
        keys.sort()
        rows = []

        for k in keys:
            r = [k]
            for host in stats:
                try:
                    r.append( host[1][k] )
                except KeyError:
                    r.append( "" )

            rows.append( r )

        table = [header] + rows

        return render(request, 'admin/cache/memcache_info.html', {
            'title': 'Memcached statistics',
            'has_memcache': True,
            'stats': table,
        })
    except InvalidCacheBackendError, e:
        return render(request, 'admin/cache/memcache_info.html', {
            'title': 'Memcached statistics',
            'has_memcache': False,
            'error_message': unicode(e),
        })
