# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

import hotshot
import hotshot.stats
import json
import os
import re
import sys
import StringIO
import tempfile

from django.conf import settings
from django.contrib.redirects.middleware import RedirectFallbackMiddleware
from django.contrib.redirects.models import Redirect
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpResponse, HttpResponsePermanentRedirect
from django import http

from djangoplicity.translation.models import get_language_from_path, get_path_for_language


words_re = re.compile(r'\s+')

group_prefix_re = [
    re.compile('^.*/django/[^/]+'),
    re.compile('^(.*)/[^/]+$'),  # extract module path
    re.compile('.*'),            # catch strange entries
]


class RegexRedirectMiddleware( object ):
    r"""
    Middleware that redirects request based on a list of regular
    expressions.

    Put the following in the settings::
        REGEX_REDIRECTS = (
            ( re.compile( '/hubbleshop/webshop/webshop.php\?cateogry=(books|cdroms)' ), '/shop/\g<1>/' ),
        )
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response = self.process_response(request, response)

        return response

    def process_response(self, request, response ):
        if response and response.status_code == 404:
            regexs = getattr( settings, 'REGEX_REDIRECTS', [] )
            path = request.get_full_path()

            for p in regexs:
                if p[0].match( path ):
                    return HttpResponsePermanentRedirect( p[0].sub( p[1], path ) )

        return response


class UserInExceptionMiddleware( object ):
    """
    Include user and email if logged in in exception
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        return response

    def process_exception( self, request, exception ):
        if request.user.is_authenticated():
            request.META['USER'] = request.user.username
            request.META['USER_EMAIL'] = request.user.email


class DjangoplicityRedirectFallbackMiddleware(RedirectFallbackMiddleware):
    '''
    Extend from the standard RedirectFallbackMiddleware to better handle
    languages redirections
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response = self.process_response(request, response)

        return response

    def process_response(self, request, response):
        if not settings.USE_I18N:
            return super(DjangoplicityRedirectFallbackMiddleware, self).process_response(request, response)

        if response.status_code != 404:
            return response  # No need to check for a redirect for non-404 responses.

        full_path = request.get_full_path()
        current_site = get_current_site(request)

        r = None
        try:
            r = Redirect.objects.get(site=current_site, old_path=full_path)
        except Redirect.DoesNotExist:
            pass

        if not r:
            # Let's check if the current path is a local (translated) path
            # and whether we have a redirect for the original path
            lang, dummy_prefix, original_path = get_language_from_path(full_path)

            if full_path != original_path:
                try:
                    r = Redirect.objects.get(site=current_site, old_path=original_path)

                    # We update the Redirects' new_path with the prefix of the
                    # current language to prevent another redirect round trip
                    # later on but we don't save it
                    r.new_path = get_path_for_language(lang, r.new_path)
                except Redirect.DoesNotExist:
                    pass

        if settings.APPEND_SLASH and not request.path.endswith('/'):
            # Try appending a trailing slash.
            path_len = len(request.path)
            full_path = full_path[:path_len] + '/' + full_path[path_len:]
            try:
                r = Redirect.objects.get(site=current_site, old_path=full_path)
            except Redirect.DoesNotExist:
                pass

        if r is not None:
            if r.new_path == '':
                return http.HttpResponseGone()
            return http.HttpResponsePermanentRedirect(r.new_path)

        # No redirect was found. Return the response.
        return response


class ProfileMiddleware(object):
    '''
    Displays hotshot profiling for any view.
    http://yoursite.com/yourview/?prof

    Add the "prof" key to query string by appending ?prof (or &prof=)
    and you'll see the profiling results in your browser.
    It's set up to only be available in django's debug mode, is available for superuser otherwise,
    but you really shouldn't add this middleware to any production configuration.

    WARNING: It uses hotshot profiler which is not thread safe.
    '''
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        self.process_request(request)

        response = self.get_response(request)

        response = self.process_response(request, response)

        return response

    def process_request(self, request):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            self.tmpfile = tempfile.mktemp()
            self.prof = hotshot.Profile(self.tmpfile)

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            return self.prof.runcall(callback, request, *callback_args, **callback_kwargs)

    def get_group(self, f):
        for g in group_prefix_re:
            name = g.findall(f)
            if name:
                return name[0]

    def get_summary(self, results_dict, total):
        l = [(item[1], item[0]) for item in results_dict.items()]
        l.sort(reverse=True)
        l = l[:40]

        res = '   tottime\n'
        for item in l:
            res += '%4.1f%% %7.3f %s\n' % (100 * item[0] / total if total else 0, item[0], item[1])

        return res

    def summary_for_files(self, stats_str):
        stats_str = stats_str.split('\n')[5:]

        mystats = {}
        mygroups = {}

        total = 0

        for s in stats_str:
            fields = words_re.split(s)
            if len(fields) == 7:
                time = float(fields[2])
                total += time
                f = fields[6].split(':')[0]

                if f not in mystats:
                    mystats[f] = 0
                mystats[f] += time

                group = self.get_group(f)
                if group not in mygroups:
                    mygroups[group] = 0
                mygroups[group] += time

        return '<pre>' +\
        ' ---- By file ----\n\n' + self.get_summary(mystats, total) + '\n' + \
        ' ---- By group ---\n\n' + self.get_summary(mygroups, total) + \
        '</pre>'

    def process_response(self, request, response):
        if (settings.DEBUG or request.user.is_superuser) and 'prof' in request.GET:
            self.prof.close()

            out = StringIO.StringIO()
            old_stdout = sys.stdout
            sys.stdout = out

            stats = hotshot.stats.load(self.tmpfile)
            stats.sort_stats('time', 'calls')
            stats.print_stats()

            sys.stdout = old_stdout
            stats_str = out.getvalue()

            if response and response.content and stats_str:
                response.content = '<pre>' + stats_str + '</pre>'

            response.content = '\n'.join(response.content.split('\n')[:40])

            response.content += self.summary_for_files(stats_str)

            os.unlink(self.tmpfile)

        return response


class NonHtmlDebugToolbarMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response = self.process_response(request, response)

        return response

    def process_response(self, request, response):
        debug = request.GET.get('debug', 'UNSET')

        if debug != 'UNSET':
            if response['Content-Type'] == 'application/octet-stream':
                new_content = '<html><body>Binary Data, ' \
                    'Length: {}</body></html>'.format(len(response.content))
                response = HttpResponse(new_content)
            elif response['Content-Type'] != 'text/html':
                content = response.content
                try:
                    json_ = json.loads(content)
                    content = json.dumps(json_, sort_keys=True, indent=2)
                except ValueError:
                    pass
                response = HttpResponse('<html><body><pre>{}'
                            '</pre></body></html>'.format(content))

        return response
