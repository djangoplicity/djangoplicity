# -*- coding: utf-8 -*-
#
# djangoplicity-releases
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

from djangoplicity.archives.views import GenericDetailView
from django.http import Http404


def dict_from_obj( obj, *args ):
    tmp = {}
    for f in args:
        tmp[f] = getattr(obj, f)
    return tmp

ALLOWED_IPS = ['127.0.0.1', '134.171.' ]
ALLOWED_HOSTS = ['.eso.org']


class KidsDetailView( GenericDetailView ):
    """
    Archive detail view for kids press releases

    Will just use detail_kids.html to render the press release instead of detail.html

    The view is installed in options.py
    """
    def vary_on( self, request, model, obj, state, admin_rights, **kwargs ):
        return ['kids', ]

    def select_template( self, model, obj, **kwargs ):
        return super( KidsDetailView, self ).select_template( model, obj, suffix='_kids' )

    def render( self, request, model, obj, state, admin_rights, **kwargs ):
        if not obj.kids_title:
            raise Http404
        return super( KidsDetailView, self ).render( request, model, obj, state, admin_rights, **kwargs )
