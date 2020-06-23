# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
#
# Copyright (c) 2007-2013, European Southern Observatory (ESO)
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

from djangoplicity.archives.contrib.browsers import ListBrowser
from djangoplicity.archives.contrib.templater import DisplayTemplate
from djangoplicity.newsletters.queries import NewsletterCategoryQuery
from djangoplicity.archives.importer.import_actions import move_resources, \
    process_image_derivatives
from djangoplicity.archives.options import ArchiveOptions


class NewsletterOptions(ArchiveOptions):
    urlname_prefix = 'newsletters'

    search_fields = ('id', 'subject', 'editorial_text', 'text')

    class Queries( object ):
        default = NewsletterCategoryQuery(browsers=('normal', 'viewall'), relation_field='type',
                    url_field='slug', title_field='name', use_category_title=True,
                    verbose_name='%s')
        site_embed = NewsletterCategoryQuery(browsers=('html_embed',), relation_field='type',
                    url_field='slug', title_field='name', use_category_title=True,
                    verbose_name='%s')

    class Browsers(object):
        normal = ListBrowser(paginate_by=50, index_template='index_newsletters.html')
        viewall = ListBrowser(paginate_by=100)
        html_embed = ListBrowser(verbose_name='HTML', paginate_by=100, index_template='index_newsletters_embed.html')

    class Import(object):
        uploadable = True
        metadata = 'original'
        scan_directories = [
            ('original', ('.jpg', '.jpeg', '.tif', '.tiff')),
        ]
        actions = [
            move_resources,
            process_image_derivatives(),
        ]

    class Display():
        esonews = DisplayTemplate( 'file', 'archives/newsletters/translations_list.html', name='Translations list' )
