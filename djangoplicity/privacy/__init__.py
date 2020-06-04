# -*- coding: utf-8 -*-
#
# djangoplicity-privacy
# Copyright (c) 2007-2018, European Southern Observatory (ESO)
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

'''
Django application to handle privacy notice


Installation
============
Add 'djangoplicity.privacy' to INSTALLED_APPS
Set ENABLE_DJANGOPLICITY_PRIVACY = True in settings.py

Add 'djangoplicity.privacy.middleware.PrivacyMiddleware' to MIDDLEWARE,
    it must be running *before* LocaleMiddleware if it is also configured
Update urls.py:
    from djangoplicity.privacy.views import accept_privacy_notice

    urlpatterns += [
        url(r'^public/accept-privacy-notice/', accept_privacy_notice, name='accept_privacy_notice')
    ]

Add the following code in the core template:
{% if not request.privacy_notice_accepted %}
    {% include 'privacy/notice.html' %}
{% endif %}

Set the CSS for #privacy-notice

If necessary update the privacy notice note by overriding
{% block privacy-notice %} and {% block privacy-button-text %} in
templates/privacy/notice.html
'''
