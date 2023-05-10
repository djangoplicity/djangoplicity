# -*- coding: utf-8 -*-
#
# djangoplicity
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

from htmllaundry import sanitize
from htmllaundry.cleaners import DocumentCleaner


CustomCleaner = DocumentCleaner
CustomCleaner.allow_tags = [
    'blockquote', 'a', 'img', 'em', 'p', 'strong', 'h1', 'h2', 'h3', 'h4',
    'h5', 'ul', 'ol', 'li', 'sub', 'sup', 'abbr', 'acronym', 'dl', 'dt', 'dd',
    'cite', 'dft', 'br', 'table', 'tr', 'td', 'th', 'thead', 'tbody', 'tfoot',
    'div'
]
CustomCleaner.scripts = False
CustomCleaner.javascripts = False
CustomCleaner.add_nofollow = False

def clean_html(content):
    return sanitize(content, CustomCleaner)

def convert_html_entities(value):
    '''
    Converts HTML entities like &amp; to unicode characters like &
    See:
    https://www.semicolonworld.com/question/42860/decode-html-entities-in-python-string
    https://docs.python.org/3/library/html.html#html.unescape
    '''
    try:
        # Python 2.6-2.7 
        from HTMLParser import HTMLParser
        html = HTMLParser()
    except ImportError:
        # Python 3
        try:
            from html.parser import HTMLParser
            html = HTMLParser()
        except ImportError:
            import html
    return html.unescape(value)
