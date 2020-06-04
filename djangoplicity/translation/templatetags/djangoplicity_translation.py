# -*- coding: utf-8 -*-
#
# djangoplicity-translation
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

from django.template import Library
from django.template.defaulttags import URLNode
from django.utils import translation
from django.utils.encoding import force_text
from django.utils.html import conditional_escape

from djangoplicity.translation.models import get_path_for_language, get_language_from_path


register = Library()


@register.tag
def transurl( parser, token ):
    """
    Returns an absolute URL matching given view with its parameters.

    See django.templatetags.future.url and django.template.defaulttags.URLNode
    """
    from django.template.defaulttags import url
    return TransURLNode.from_urlnode( url( parser, token ) )


class TransURLNode( URLNode ):
    @classmethod
    def from_urlnode( cls, node ):
        return cls( node.view_name, node.args, node.kwargs, node.asvar )

    # COPIED FROMdjango.template.defaulttags.URLNode
    def __init__(self, view_name, args, kwargs, asvar):
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    # COPIED FROMdjango.template.defaulttags.URLNode with modifications to use translatio_reverse instead
    def render(self, context):
        from django.urls import reverse, NoReverseMatch
        from djangoplicity.translation.models import translation_reverse

        args = [arg.resolve(context) for arg in self.args]
        kwargs = {
            force_text(k, 'ascii'): v.resolve(context)
            for k, v in self.kwargs.items()
        }
        view_name = self.view_name.resolve(context)
        try:
            current_app = context.request.current_app
        except AttributeError:
            try:
                current_app = context.request.resolver_match.namespace
            except AttributeError:
                current_app = None
        # Try to look up the URL. If it fails, raise NoReverseMatch unless the
        # {% url ... as var %} construct is used, in which case return nothing.
        url = ''
        try:
            url = reverse(view_name, args=args, kwargs=kwargs, current_app=current_app)
            url = translation_reverse(view_name, args=args, kwargs=kwargs,
                current_app=current_app, lang=translation.get_language())
        except NoReverseMatch:
            if self.asvar is None:
                raise

        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            if context.autoescape:
                url = conditional_escape(url)
            return url


@register.filter
def url_for_lang(path, lang):
    '''
    Return the url for the given languge
    e.g.: /public/ (de) -> /public/germany/
    '''

    # Get the "original" path in case we're dealing with a translated path
    path = get_language_from_path(path)[2]

    return get_path_for_language(lang, path)
