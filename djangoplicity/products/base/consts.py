# -*- coding: utf-8 -*-
#
# djangoplicity-products
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
Definition of "constants" for the product archives.
"""

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

DEFAULT_CREDIT = settings.DEFAULT_CREDIT if hasattr( settings, 'DEFAULT_CREDIT' ) else ''

COVER_CHOICES = (
    ('Hardcover', 'Hardcover'),
    ('Softcover', 'Softcover'),
)

LANGUAGE_CHOICES = (
    ('ab', 'Abkhaz'),
    ('aa', 'Afar'),
    ('af', 'Afrikaans'),
    ('ak', 'Akan'),
    ('sq', 'Albanian'),
    ('am', 'Amharic'),
    ('ar', 'Arabic'),
    ('an', 'Aragonese'),
    ('hy', 'Armenian'),
    ('as', 'Assamese'),
    ('av', 'Avaric'),
    ('ae', 'Avestan'),
    ('ay', 'Aymara'),
    ('az', 'Azerbaijani'),
    ('bm', 'Bambara'),
    ('ba', 'Bashkir'),
    ('eu', 'Basque'),
    ('be', 'Belarusian'),
    ('bn', 'Bengali'),
    ('bh', 'Bihari'),
    ('bi', 'Bislama'),
    ('bs', 'Bosnian'),
    ('br', 'Breton'),
    ('bg', 'Bulgarian'),
    ('my', 'Burmese'),
    ('ca', 'Catalan'),
    ('ch', 'Chamorro'),
    ('ce', 'Chechen'),
    ('ny', 'Chichewa'),
    ('zh', 'Chinese'),
    ('cv', 'Chuvash'),
    ('kw', 'Cornish'),
    ('co', 'Corsican'),
    ('cr', 'Cree'),
    ('hr', 'Croatian'),
    ('cs', 'Czech'),
    ('da', 'Danish'),
    ('dv', 'Divehi'),
    ('nl', 'Dutch'),
    ('dz', 'Dzongkha'),
    ('en', 'English'),
    ('et', 'Estonian'),
    ('ee', 'Ewe'),
    ('fo', 'Faroese'),
    ('fj', 'Fijian'),
    ('fi', 'Finnish'),
    ('fr', 'French'),
    ('ff', 'Fula'),
    ('gl', 'Galician'),
    ('ka', 'Georgian'),
    ('de', 'German'),
    ('el', 'Greek'),
    ('kl', 'Greenlandic'),
    ('gn', 'Guarani'),
    ('gu', 'Gujarati'),
    ('ht', 'Haitian'),
    ('ha', 'Hausa'),
    ('he', 'Hebrew'),
    ('hz', 'Herero'),
    ('hi', 'Hindi'),
    ('ho', 'Hiri Motu'),
    ('hu', 'Hungarian'),
    ('is', 'Icelandic'),
    ('ig', 'Igbo'),
    ('id', 'Indonesian'),
    ('iu', 'Inuktitut'),
    ('ik', 'Inupiaq'),
    ('ga', 'Irish'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('jv', 'Javanese'),
    ('kn', 'Kannada'),
    ('kr', 'Kanuri'),
    ('ks', 'Kashmiri'),
    ('kk', 'Kazakh'),
    ('km', 'Khmer'),
    ('ki', 'Kikuyu'),
    ('rw', 'Kinyarwanda'),
    ('ky', 'Kirghiz'),
    ('rn', 'Kirundi'),
    ('kv', 'Komi'),
    ('kg', 'Kongo'),
    ('ko', 'Korean'),
    ('ku', 'Kurdish'),
    ('kj', 'Kwanyama'),
    ('lo', 'Lao'),
    ('la', 'Latin'),
    ('lv', 'Latvian'),
    ('li', 'Limburgish'),
    ('ln', 'Lingala'),
    ('lt', 'Lithuanian'),
    ('lu', 'Luba-Katanga'),
    ('lg', 'Luganda'),
    ('lb', 'Luxembourgish'),
    ('mk', 'Macedonian'),
    ('mg', 'Malagasy'),
    ('ms', 'Malay'),
    ('ml', 'Malayalam'),
    ('mt', 'Maltese'),
    ('gv', 'Manx'),
    ('mi', 'Maori'),
    ('mr', 'Marathi'),
    ('mh', 'Marshallese'),
    ('mn', 'Mongolian'),
    ('na', 'Nauru'),
    ('nv', 'Navajo'),
    ('ng', 'Ndonga'),
    ('ne', 'Nepali'),
    ('nd', 'North Ndebele'),
    ('se', 'Northern Sami'),
    ('no', 'Norwegian'),
    ('nb', 'Norwegian Bokm�l'),
    ('nn', 'Norwegian Nynorsk'),
    ('ii', 'Nuosu'),
    ('oc', 'Occitan'),
    ('oj', 'Ojibwe'),
    ('or', 'Oriya'),
    ('om', 'Oromo'),
    ('os', 'Ossetian'),
    ('pi', 'Pali'),
    ('pa', 'Panjabi'),
    ('ps', 'Pashto'),
    ('fa', 'Persian'),
    ('pl', 'Polish'),
    ('pt', 'Portuguese'),
    ('qu', 'Quechua'),
    ('ro', 'Romanian'),
    ('rm', 'Romansh'),
    ('ru', 'Russian'),
    ('sm', 'Samoan'),
    ('sg', 'Sango'),
    ('sa', 'Sanskrit'),
    ('sc', 'Sardinian'),
    ('gd', 'Scottish Gaelic'),
    ('sr', 'Serbian'),
    ('sr-latn', 'Serbian Latin'),
    ('sn', 'Shona'),
    ('sd', 'Sindhi'),
    ('si', 'Sinhala'),
    ('sk', 'Slovak'),
    ('sl', 'Slovene'),
    ('so', 'Somali'),
    ('nr', 'South Ndebele'),
    ('st', 'Southern Sotho'),
    ('es', 'Spanish'),
    ('su', 'Sundanese'),
    ('sw', 'Swahili'),
    ('ss', 'Swati'),
    ('sv', 'Swedish'),
    ('tl', 'Tagalog'),
    ('ty', 'Tahitian'),
    ('tg', 'Tajik'),
    ('ta', 'Tamil'),
    ('tt', 'Tatar'),
    ('te', 'Telugu'),
    ('th', 'Thai'),
    ('bo', 'Tibetan Standard'),
    ('ti', 'Tigrinya'),
    ('to', 'Tonga'),
    ('ts', 'Tsonga'),
    ('tn', 'Tswana'),
    ('tr', 'Turkish'),
    ('tk', 'Turkmen'),
    ('tw', 'Twi'),
    ('ug', 'Uighur'),
    ('uk', 'Ukrainian'),
    ('ur', 'Urdu'),
    ('uz', 'Uzbek'),
    ('ve', 'Venda'),
    ('vi', 'Vietnamese'),
    ('wa', 'Walloon'),
    ('cy', 'Welsh'),
    ('fy', 'Western Frisian'),
    ('wo', 'Wolof'),
    ('xh', 'Xhosa'),
    ('yi', 'Yiddish'),
    ('yo', 'Yoruba'),
    ('za', 'Zhuang'),
    ('zu', 'Zulu'),
)

IMAGE_DOWNLOADS = ( _(u'Images'), {'resources': ( 'original', 'large', 'screen' ), 'icons': { 'original': 'phot', 'large': 'phot', 'medium': 'phot', 'screen': 'phot' } } )

FILE_DOWNLOADS = ( _(u'Files'), {
    'resources': ( 'pdf', 'pdfsm', 'epub', 'zip', 'ps', 'pdfen', 'pdfensm', 'pdfes',
        'pdfessm''pdfde', 'pdfdesm', 'pdffr', 'pdfit', 'pdffi', 'pdfpt',
        'pdfse', 'pdfnl', 'pdffr'  ),
    'icons': {
        'epub': 'doc',
        'pdf': 'doc',
        'pdfsm': 'doc',
        'zip': 'zip',
        'ps': 'doc',
        'pdfen': 'doc',
        'pdfensm': 'doc',
        'pdfes': 'doc',
        'pdfessm': 'doc',
        'pdfde': 'doc',
        'pdfdesm': 'doc',
        'pdfit': 'doc',
        'pdffi': 'doc',
        'pdfpt': 'doc',
        'pdfse': 'doc',
        'pdfnl': 'doc',
        'pdffr': 'doc',
    }
})


# the purpose of these functions is to mask the value change accros projects from django migrations
def DEFAULT_CREDIT_FUNC():
    return DEFAULT_CREDIT


def COVER_CHOICES_FUNC():
    return COVER_CHOICES


def LANGUAGE_CHOICES_FUNC():
    return LANGUAGE_CHOICES
