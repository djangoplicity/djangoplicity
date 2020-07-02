# -*- coding: utf-8 -*-
#
# djangoplicity-translation
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

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import locale
import pycountry


# If you use two letter language codes, and the default country for a
# language does not suit you, you can either change the language code
# into a five letter code (e.g. en-uk) or override the default country
# with this setting.
DEFAULT_COUNTRY4LANG = getattr( settings, 'DEFAULT_COUNTRY4LANG', {} )

# In case the same language have significantly different dialects
# in two countries and needs to be treated nearly as two different languages
# this settings can be used to set both languages to main languages.
#
# This is primiarly the case with Portuguese in Portugal and Brazil.
LANGUAGE_DIALECTS = getattr( settings, 'LANGUAGE_DIALECTS', {} )

COUNTRY_GROUPS = getattr( settings, 'COUNTRY_GROUPS', {} )
DEFAULT_COUNTRY_GROUP = getattr( settings, 'DEFAULT_COUNTRY_GROUP', '' )


def _cmp_country( a, b ):
    if a[1][0][3] == b[1][0][3]:
        return cmp( a[0], b[0] )
    else:
        return cmp( a[1][0][3], b[1][0][3] )


def get_codes( code ):
    # Determine language and country from 2-5 letters language codes.
    if len( code ) == 2:
        if code in DEFAULT_COUNTRY4LANG:
            # We want to be able to override the default country
            # from language found using the locale.normalize().
            # E.g. we might want default country to be 'uk' for language 'en'
            lang = code.lower()
            ctry = DEFAULT_COUNTRY4LANG[lang]
            return (lang, ctry)
        else:
            # If you pass normalize() a 2 letter code  like 'el' it returns
            # a normalised locale name like 'el_GR.ISO8859-7', from where you
            # can get the default country code
            return locale.normalize( code )[:5].lower().split( "_" )
    elif code == 'sr-latn':
        # This is a special case which didn't seem to be recognized by the
        # locale module
        return ['sr', 'rs']
    elif len( code ) == 5:
        return code.lower().split( "-" )
    else:
        raise ImproperlyConfigured( "Invalid language code in settings.LANGUAGES: %s" % code )


def _get_lang_country_mapping():
    return ( {}, {}, [], [] )
    """
    Generate a dictionary of countries and their languages from the
    LANGUAGES settings code.

    {
        'gr' : [( 'el', 'Greek' ), ],
        'be' : [( 'de', 'German/Belgium' ), ( 'fr', 'French/Belgium' ), ( 'nl', 'Dutch/Belgium' ), ],
        'pt' : [( 'pt', 'Portuguese/Portugal' ), ],
        'br' : [( 'pt', 'Portuguese/Brazil' ), ],
    }
    """
    countries = {}
    languages = {}
    for code, name in settings.LANGUAGES:
        lang, ctry = get_codes( code )

        # Countries
        if ctry not in countries:
            countries[ctry] = []
        countries[ctry].append( ( lang, name, code ) )

        # Languages
        if lang not in languages:
            languages[lang] = []
        is_main_language = len( code ) == 2 or ( lang in LANGUAGE_DIALECTS and LANGUAGE_DIALECTS[lang] == ctry )
        languages[lang].append( ( ctry, name, code, is_main_language ) )

    #
    # Sort the dictionaries for making lists
    #
    def getter( x ):
        try:
            return pycountry.countries.get( alpha2=x[0].upper() if x[0] != 'uk' else 'GB' )  # Special case for UK
        except KeyError:
            return x[0]

    countries_list = countries.items()
    countries_list.sort( key=getter )

    languages_list = languages.items()
    languages_list.sort( key=lambda x: x[0][1] )

    return ( countries, languages, countries_list, languages_list )


def _get_main_lang_list( languages_list ):
    ls = []
    for lang, ctrys in languages_list:
        for ctry, name, code, is_main_lang in ctrys:
            if is_main_lang:
                ls.append( ( lang, ctry, name, code ) )
    ls.sort( key=lambda x: x[2] )
    return ls

COUNTRIES, LANGUAGES, COUNTRIES_LIST, LANGUAGES_LIST = _get_lang_country_mapping()
MAIN_LANGUAGES_LIST = _get_main_lang_list( LANGUAGES_LIST )
LANGUAGE_CODES = [l[0] for l in settings.LANGUAGES]
