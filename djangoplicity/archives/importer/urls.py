# -*- coding: utf-8 -*-
#
# djangoplicity-archives-importer
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

"""
For the file import feature to work for an archive, the archive must be listed
in settings.ARCHIVES.
"""

from django.conf.urls import url
from djangoplicity.archives.importer.views import manage_archive_imports, upload_file
from djangoplicity.archives.loading import get_archives


def urlpatterns_for_archive_import( options, model, urlpatterns=None ):
    """
    Similar to general archives urloptions, only it applies to the import module URLs only
    """
    prefix = options.urlname_prefix

    urlpatterns = [
       url( r'^%s/$' % prefix, manage_archive_imports, {'archive_options': options, 'archive_model': model}, name="%s_%s_import" % (model._meta.app_label, model._meta.model_name) ),
       url( r'^%s/upload/$' % prefix, upload_file, {'archive_options': options, 'archive_model': model}, name="%s_%s_import_upload" % (model._meta.app_label, model._meta.model_name) ),
    ]
    return urlpatterns


#
# Generate URL patterns
#
urlpatterns = []

for model, opt in get_archives():
    if hasattr( opt.Import, 'scan_directories' ) and opt.Import.scan_directories:
        urlpatterns += urlpatterns_for_archive_import( opt, model )
