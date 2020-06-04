# -*- coding: utf-8 -*-
#
# djangoplicity-privacy
# Copyright (c) 2007-2018, European Southern Observatory (ESO)
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

import json

from django.conf import settings
from django.http import HttpResponse

from djangoplicity.translation.middleware import set_preferred_language

from .middleware import PRIVACY_COOKIE_NAME


def accept_privacy_notice(request):
    '''
    This view is called when the privacy notice is accepted
    '''
    response = HttpResponse(status=204)

    if request.method == 'POST':
        max_age = 60 * 60 * 24 * 62  # Two months

        response.set_cookie(PRIVACY_COOKIE_NAME, 'True',
            max_age=max_age, domain=settings.SESSION_COOKIE_DOMAIN)

        # If site uses language and a language code is given we set the user's
        # default language
        if settings.USE_I18N:
            data = json.loads(request.body)
            if 'LANGUAGE_CODE' in data:
                request.PREFERRED_LANGUAGE = data['LANGUAGE_CODE']
                set_preferred_language(request, response)

    return response
