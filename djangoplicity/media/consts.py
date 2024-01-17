# -*- coding: utf-8 -*-
#
# djangoplicity-media
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
from django.utils.translation import ugettext_lazy as _


MEDIA_CONTENT_SERVERS = getattr(settings, 'MEDIA_CONTENT_SERVERS', {})

#
# Path to MP4Box and mp4fragment command line utilities
#
MP4BOX_PATH = getattr(settings, 'MP4BOX_PATH', '/usr/local/bin/MP4Box')
MP4FRAGMENT_PATH = getattr(settings, 'MP4FRAGMENT_PATH', '/usr/local/bin/mp4fragment')


#
# Colour definitions
#
COLOR = (
    ( 'purple', _( 'Purple' ) ),
    ( 'blue', _( 'Blue' ) ),
    ( 'cyan', _( 'Cyan' ) ),
    ( 'green', _( 'Green' ) ),
    ( 'yellow', _( 'Yellow' ) ),
    ( 'orange', _( 'Orange' ) ),
    ( 'red', _( 'Red' ) ),
    ( 'magenta', _( 'Magenta' ) ),
    ( 'black', _( 'Black' ) ),
    ( 'white', _( 'White' ) ),
)

#
# List of MP4 Box languages for subtitles
#
SUBTITLE_LANGUAGES = [
    ( 'ab', 'Abkhazian' ),
    ( 'aa', 'Afar' ),
    ( 'af', 'Afrikaans' ),
    ( 'ak', 'Akan' ),
    ( 'sq', 'Albanian' ),
    ( 'am', 'Amharic' ),
    ( 'ar', 'Arabic' ),
    ( 'an', 'Aragonese' ),
    ( 'hy', 'Armenian' ),
    ( 'as', 'Assamese' ),
    ( 'av', 'Avaric' ),
    ( 'ae', 'Avestan' ),
    ( 'ay', 'Aymara' ),
    ( 'az', 'Azerbaijani' ),
    ( 'bm', 'Bambara' ),
    ( 'ba', 'Bashkir' ),
    ( 'eu', 'Basque' ),
    ( 'be', 'Belarusian' ),
    ( 'bn', 'Bengali' ),
    ( 'bh', 'Bihari languages' ),
    ( 'bi', 'Bislama' ),
    ( 'nb', 'Bokmål, Norwegian; Norwegian Bokmål' ),
    ( 'bs', 'Bosnian' ),
    ( 'br', 'Breton' ),
    ( 'bg', 'Bulgarian' ),
    ( 'my', 'Burmese' ),
    ( 'ca', 'Catalan; Valencian' ),
    ( 'km', 'Central Khmer' ),
    ( 'ch', 'Chamorro' ),
    ( 'ce', 'Chechen' ),
    ( 'ny', 'Chichewa; Chewa; Nyanja' ),
    ( 'zh', 'Chinese' ),
    ( 'cu', 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic' ),
    ( 'cv', 'Chuvash' ),
    ( 'kw', 'Cornish' ),
    ( 'co', 'Corsican' ),
    ( 'cr', 'Cree' ),
    ( 'hr', 'Croatian' ),
    ( 'cs', 'Czech' ),
    ( 'da', 'Danish' ),
    ( 'dv', 'Divehi; Dhivehi; Maldivian' ),
    ( 'nl', 'Dutch; Flemish' ),
    ( 'dz', 'Dzongkha' ),
    ( 'en', 'English' ),
    ( 'eo', 'Esperanto' ),
    ( 'et', 'Estonian' ),
    ( 'ee', 'Ewe' ),
    ( 'fo', 'Faroese' ),
    ( 'fj', 'Fijian' ),
    ( 'fi', 'Finnish' ),
    ( 'fr', 'French' ),
    ( 'ff', 'Fulah' ),
    ( 'gd', 'Gaelic; Scottish Gaelic' ),
    ( 'gl', 'Galician' ),
    ( 'lg', 'Ganda' ),
    ( 'ka', 'Georgian' ),
    ( 'de', 'German' ),
    ( 'el', 'Greek' ),
    ( 'gn', 'Guarani' ),
    ( 'gu', 'Gujarati' ),
    ( 'ht', 'Haitian; Haitian Creole' ),
    ( 'ha', 'Hausa' ),
    ( 'he', 'Hebrew' ),
    ( 'hz', 'Herero' ),
    ( 'hi', 'Hindi' ),
    ( 'ho', 'Hiri Motu' ),
    ( 'hu', 'Hungarian' ),
    ( 'is', 'Icelandic' ),
    ( 'io', 'Ido' ),
    ( 'ig', 'Igbo' ),
    ( 'id', 'Indonesian' ),
    ( 'ia', 'Interlingua (International Auxiliary Language Association)' ),
    ( 'ie', 'Interlingue; Occidental' ),
    ( 'iu', 'Inuktitut' ),
    ( 'ik', 'Inupiaq' ),
    ( 'ga', 'Irish' ),
    ( 'it', 'Italian' ),
    ( 'ja', 'Japanese' ),
    ( 'jv', 'Javanese' ),
    ( 'kl', 'Kalaallisut; Greenlandic' ),
    ( 'kn', 'Kannada' ),
    ( 'kr', 'Kanuri' ),
    ( 'ks', 'Kashmiri' ),
    ( 'kk', 'Kazakh' ),
    ( 'ki', 'Kikuyu; Gikuyu' ),
    ( 'rw', 'Kinyarwanda' ),
    ( 'ky', 'Kirghiz; Kyrgyz' ),
    ( 'kv', 'Komi' ),
    ( 'kg', 'Kongo' ),
    ( 'ko', 'Korean' ),
    ( 'kj', 'Kuanyama; Kwanyama' ),
    ( 'ku', 'Kurdish' ),
    ( 'lo', 'Lao' ),
    ( 'la', 'Latin' ),
    ( 'lv', 'Latvian' ),
    ( 'li', 'Limburgan; Limburger; Limburgish' ),
    ( 'ln', 'Lingala' ),
    ( 'lt', 'Lithuanian' ),
    ( 'lu', 'Luba-Katanga' ),
    ( 'lb', 'Luxembourgish; Letzeburgesch' ),
    ( 'mk', 'Macedonian' ),
    ( 'mg', 'Malagasy' ),
    ( 'ms', 'Malay' ),
    ( 'ml', 'Malayalam' ),
    ( 'mt', 'Maltese' ),
    ( 'gv', 'Manx' ),
    ( 'mi', 'Maori' ),
    ( 'mr', 'Marathi' ),
    ( 'mh', 'Marshallese' ),
    ( 'mn', 'Mongolian' ),
    ( 'na', 'Nauru' ),
    ( 'nv', 'Navajo; Navaho' ),
    ( 'nd', 'Ndebele - North; North Ndebele' ),
    ( 'nr', 'Ndebele - South; South Ndebele' ),
    ( 'ng', 'Ndonga' ),
    ( 'ne', 'Nepali' ),
    ( 'se', 'Northern Sami' ),
    ( 'no', 'Norwegian' ),
    ( 'nb', 'Norwegian Bokmal' ),
    ( 'nn', 'Norwegian Nynorsk; Nynorsk, Norwegian' ),
    ( 'oc', 'Occitan (post 1500)' ),
    ( 'oj', 'Ojibwa' ),
    ( 'or', 'Oriya' ),
    ( 'om', 'Oromo' ),
    ( 'os', 'Ossetian; Ossetic' ),
    ( 'pi', 'Pali' ),
    ( 'pa', 'Panjabi; Punjabi' ),
    ( 'fa', 'Persian' ),
    ( 'pl', 'Polish' ),
    ( 'pt', 'Portuguese' ),
    ( 'ps', 'Pushto; Pashto' ),
    ( 'qu', 'Quechua' ),
    ( 'ro', 'Romanian; Moldavian; Moldovan' ),
    ( 'rm', 'Romansh' ),
    ( 'rn', 'Rundi' ),
    ( 'ru', 'Russian' ),
    ( 'sm', 'Samoan' ),
    ( 'sg', 'Sango' ),
    ( 'sa', 'Sanskrit' ),
    ( 'sc', 'Sardinian' ),
    ( 'sr', 'Serbian' ),
    ( 'sr-latn', 'Serbian Latin' ),
    ( 'sn', 'Shona' ),
    ( 'ii', 'Sichuan Yi; Nuosu' ),
    ( 'sd', 'Sindhi' ),
    ( 'si', 'Sinhala; Sinhalese' ),
    ( 'sk', 'Slovak' ),
    ( 'sl', 'Slovenian' ),
    ( 'so', 'Somali' ),
    ( 'st', 'Sotho; Southern' ),
    ( 'es', 'Spanish; Castilian' ),
    ( 'su', 'Sundanese' ),
    ( 'sw', 'Swahili' ),
    ( 'ss', 'Swati' ),
    ( 'sv', 'Swedish' ),
    ( 'tl', 'Tagalog' ),
    ( 'ty', 'Tahitian' ),
    ( 'tg', 'Tajik' ),
    ( 'ta', 'Tamil' ),
    ( 'tt', 'Tatar' ),
    ( 'te', 'Telugu' ),
    ( 'th', 'Thai' ),
    ( 'bo', 'Tibetan' ),
    ( 'ti', 'Tigrinya' ),
    ( 'to', 'Tonga (Tonga Islands)' ),
    ( 'ts', 'Tsonga' ),
    ( 'tn', 'Tswana' ),
    ( 'tr', 'Turkish' ),
    ( 'tk', 'Turkmen' ),
    ( 'tw', 'Twi' ),
    ( 'ug', 'Uighur; Uyghur' ),
    ( 'uk', 'Ukrainian' ),
    ( 'ur', 'Urdu' ),
    ( 'uz', 'Uzbek' ),
    ( 've', 'Venda' ),
    ( 'vi', 'Vietnamese' ),
    ( 'vo', 'Volapük' ),
    ( 'wa', 'Walloon' ),
    ( 'cy', 'Welsh' ),
    ( 'fy', 'Western Frisian' ),
    ( 'wo', 'Wolof' ),
    ( 'xh', 'Xhosa' ),
    ( 'yi', 'Yiddish' ),
    ( 'yo', 'Yoruba' ),
    ( 'za', 'Zhuang; Chuang' ),
    ( 'zu', 'Zulu' ),
]

#
# Default values for certain AVM fields.
#
DEFAULT_CREATOR = settings.DEFAULT_CREATOR if hasattr( settings, 'DEFAULT_CREATOR' ) else None
DEFAULT_CREATOR_URL = settings.DEFAULT_CREATOR_URL if hasattr( settings, 'DEFAULT_CREATOR_URL' ) else None
DEFAULT_CONTACT_ADDRESS = settings.DEFAULT_CONTACT_ADDRESS if hasattr( settings, 'DEFAULT_CONTACT_ADDRESS' ) else None
DEFAULT_CONTACT_CITY = settings.DEFAULT_CONTACT_CITY if hasattr( settings, 'DEFAULT_CONTACT_CITY' ) else None
DEFAULT_CONTACT_STATE_PROVINCE = settings.DEFAULT_CONTACT_STATE_PROVINCE if hasattr( settings, 'DEFAULT_CONTACT_STATE_PROVINCE' ) else None
DEFAULT_CONTACT_POSTAL_CODE = settings.DEFAULT_CONTACT_POSTAL_CODE if hasattr( settings, 'DEFAULT_CONTACT_POSTAL_CODE' ) else None
DEFAULT_CONTACT_COUNTRY = settings.DEFAULT_CONTACT_COUNTRY if hasattr( settings, 'DEFAULT_CONTACT_COUNTRY' ) else None
DEFAULT_RIGHTS = settings.DEFAULT_RIGHTS if hasattr( settings, 'DEFAULT_RIGHTS' ) else None
DEFAULT_PUBLISHER = settings.DEFAULT_PUBLISHER if hasattr( settings, 'DEFAULT_PUBLISHER' ) else None
DEFAULT_PUBLISHER_ID = settings.DEFAULT_PUBLISHER_ID if hasattr( settings, 'DEFAULT_PUBLISHER_ID' ) else None
DEFAULT_CREDIT = settings.DEFAULT_CREDIT if hasattr( settings, 'DEFAULT_CREDIT' ) else ''
DEFAULT_VIDEOS_FRAME_RATE = settings.DEFAULT_VIDEOS_FRAME_RATE if hasattr( settings, 'DEFAULT_VIDEOS_FRAME_RATE' ) else 25


# the purpose of these functions is to mask the value change accros projects from django migrations

def DEFAULT_CREATOR_FUNC():
    return DEFAULT_CREATOR


def DEFAULT_VIDEOS_FRAME_RATE_FUNC():
    return DEFAULT_VIDEOS_FRAME_RATE


def DEFAULT_CREATOR_URL_FUNC():
    return DEFAULT_CREATOR_URL


def DEFAULT_CONTACT_ADDRESS_FUNC():
    return DEFAULT_CONTACT_ADDRESS


def DEFAULT_CONTACT_CITY_FUNC():
    return DEFAULT_CONTACT_CITY


def DEFAULT_CONTACT_STATE_PROVINCE_FUNC():
    return DEFAULT_CONTACT_STATE_PROVINCE


def DEFAULT_CONTACT_POSTAL_CODE_FUNC():
    return DEFAULT_CONTACT_POSTAL_CODE


def DEFAULT_CONTACT_COUNTRY_FUNC():
    return DEFAULT_CONTACT_COUNTRY


def DEFAULT_RIGHTS_FUNC():
    return DEFAULT_RIGHTS


def DEFAULT_PUBLISHER_FUNC():
    return DEFAULT_PUBLISHER


def DEFAULT_PUBLISHER_ID_FUNC():
    return DEFAULT_PUBLISHER_ID


def DEFAULT_CREDIT_FUNC():
    return DEFAULT_CREDIT

#
# List of image formats which should embed AVM medatadata
#

IMAGE_AVM_FORMATS = getattr(
    settings,
    'IMAGE_AVM_FORMATS',
    (
        'original',
        'large',
        'publicationtiff40k',
        'publicationtiff25k',
        'publicationtiff10k',
        'publicationtiff',
        'publicationjpg',
        'screen',
        'thumb700x',
        'banner1920',
        'wallpaper1',
        'wallpaper2',
        'wallpaper3',
        'wallpaper4',
        'wallpaper5',
    ),
)

SPLIT_AUDIO_TYPES = (
    ('stereo', 'Stereo soundtrack'),
    ('split_stereo', 'Split stereo'),
    ('surround', 'Surround 5.1'),
    ('split_surround', 'Split surround 5.1'),
    ('712surround', '7.1.2 Surround'),
    ('audio_description', 'Audio Description'),
)
