# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djangoplicity.archives.fields
import djangoplicity.archives.base
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0006_auto_20150615_2241'),
    ]

    operations = [
        migrations.CreateModel(
            name='VideoScript',
            fields=[
                ('id', djangoplicity.archives.fields.IdField(help_text='Ids are only allowed to contain letters, numbers, underscores or hyphens. They are used in URLs for the archive item.', serialize=False, primary_key=True)),
                ('lang', models.CharField(default=b'en', max_length=7, verbose_name='Language', db_index=True, choices=[(b'ab', b'Abkhazian'), (b'aa', b'Afar'), (b'af', b'Afrikaans'), (b'ak', b'Akan'), (b'sq', b'Albanian'), (b'am', b'Amharic'), (b'ar', b'Arabic'), (b'an', b'Aragonese'), (b'hy', b'Armenian'), (b'as', b'Assamese'), (b'av', b'Avaric'), (b'ae', b'Avestan'), (b'ay', b'Aymara'), (b'az', b'Azerbaijani'), (b'bm', b'Bambara'), (b'ba', b'Bashkir'), (b'eu', b'Basque'), (b'be', b'Belarusian'), (b'bn', b'Bengali'), (b'bh', b'Bihari languages'), (b'bi', b'Bislama'), (b'nb', b'Bokm\xc3\xa5l, Norwegian; Norwegian Bokm\xc3\xa5l'), (b'bs', b'Bosnian'), (b'br', b'Breton'), (b'bg', b'Bulgarian'), (b'my', b'Burmese'), (b'ca', b'Catalan; Valencian'), (b'km', b'Central Khmer'), (b'ch', b'Chamorro'), (b'ce', b'Chechen'), (b'ny', b'Chichewa; Chewa; Nyanja'), (b'zh', b'Chinese'), (b'cu', b'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'), (b'cv', b'Chuvash'), (b'kw', b'Cornish'), (b'co', b'Corsican'), (b'cr', b'Cree'), (b'hr', b'Croatian'), (b'cs', b'Czech'), (b'da', b'Danish'), (b'dv', b'Divehi; Dhivehi; Maldivian'), (b'nl', b'Dutch; Flemish'), (b'dz', b'Dzongkha'), (b'en', b'English'), (b'eo', b'Esperanto'), (b'et', b'Estonian'), (b'ee', b'Ewe'), (b'fo', b'Faroese'), (b'fj', b'Fijian'), (b'fi', b'Finnish'), (b'fr', b'French'), (b'ff', b'Fulah'), (b'gd', b'Gaelic; Scottish Gaelic'), (b'gl', b'Galician'), (b'lg', b'Ganda'), (b'ka', b'Georgian'), (b'de', b'German'), (b'el', b'Greek'), (b'gn', b'Guarani'), (b'gu', b'Gujarati'), (b'ht', b'Haitian; Haitian Creole'), (b'ha', b'Hausa'), (b'he', b'Hebrew'), (b'hz', b'Herero'), (b'hi', b'Hindi'), (b'ho', b'Hiri Motu'), (b'hu', b'Hungarian'), (b'is', b'Icelandic'), (b'io', b'Ido'), (b'ig', b'Igbo'), (b'id', b'Indonesian'), (b'ia', b'Interlingua (International Auxiliary Language Association)'), (b'ie', b'Interlingue; Occidental'), (b'iu', b'Inuktitut'), (b'ik', b'Inupiaq'), (b'ga', b'Irish'), (b'it', b'Italian'), (b'ja', b'Japanese'), (b'jv', b'Javanese'), (b'kl', b'Kalaallisut; Greenlandic'), (b'kn', b'Kannada'), (b'kr', b'Kanuri'), (b'ks', b'Kashmiri'), (b'kk', b'Kazakh'), (b'ki', b'Kikuyu; Gikuyu'), (b'rw', b'Kinyarwanda'), (b'ky', b'Kirghiz; Kyrgyz'), (b'kv', b'Komi'), (b'kg', b'Kongo'), (b'ko', b'Korean'), (b'kj', b'Kuanyama; Kwanyama'), (b'ku', b'Kurdish'), (b'lo', b'Lao'), (b'la', b'Latin'), (b'lv', b'Latvian'), (b'li', b'Limburgan; Limburger; Limburgish'), (b'ln', b'Lingala'), (b'lt', b'Lithuanian'), (b'lu', b'Luba-Katanga'), (b'lb', b'Luxembourgish; Letzeburgesch'), (b'mk', b'Macedonian'), (b'mg', b'Malagasy'), (b'ms', b'Malay'), (b'ml', b'Malayalam'), (b'mt', b'Maltese'), (b'gv', b'Manx'), (b'mi', b'Maori'), (b'mr', b'Marathi'), (b'mh', b'Marshallese'), (b'mn', b'Mongolian'), (b'na', b'Nauru'), (b'nv', b'Navajo; Navaho'), (b'nd', b'Ndebele - North; North Ndebele'), (b'nr', b'Ndebele - South; South Ndebele'), (b'ng', b'Ndonga'), (b'ne', b'Nepali'), (b'se', b'Northern Sami'), (b'no', b'Norwegian'), (b'nb', b'Norwegian Bokmal'), (b'nn', b'Norwegian Nynorsk; Nynorsk, Norwegian'), (b'oc', b'Occitan (post 1500)'), (b'oj', b'Ojibwa'), (b'or', b'Oriya'), (b'om', b'Oromo'), (b'os', b'Ossetian; Ossetic'), (b'pi', b'Pali'), (b'pa', b'Panjabi; Punjabi'), (b'fa', b'Persian'), (b'pl', b'Polish'), (b'pt', b'Portuguese'), (b'ps', b'Pushto; Pashto'), (b'qu', b'Quechua'), (b'ro', b'Romanian; Moldavian; Moldovan'), (b'rm', b'Romansh'), (b'rn', b'Rundi'), (b'ru', b'Russian'), (b'sm', b'Samoan'), (b'sg', b'Sango'), (b'sa', b'Sanskrit'), (b'sc', b'Sardinian'), (b'sr', b'Serbian'), (b'sr-latn', b'Serbian Latin'), (b'sn', b'Shona'), (b'ii', b'Sichuan Yi; Nuosu'), (b'sd', b'Sindhi'), (b'si', b'Sinhala; Sinhalese'), (b'sk', b'Slovak'), (b'sl', b'Slovenian'), (b'so', b'Somali'), (b'st', b'Sotho; Southern'), (b'es', b'Spanish; Castilian'), (b'su', b'Sundanese'), (b'sw', b'Swahili'), (b'ss', b'Swati'), (b'sv', b'Swedish'), (b'tl', b'Tagalog'), (b'ty', b'Tahitian'), (b'tg', b'Tajik'), (b'ta', b'Tamil'), (b'tt', b'Tatar'), (b'te', b'Telugu'), (b'th', b'Thai'), (b'bo', b'Tibetan'), (b'ti', b'Tigrinya'), (b'to', b'Tonga (Tonga Islands)'), (b'ts', b'Tsonga'), (b'tn', b'Tswana'), (b'tr', b'Turkish'), (b'tk', b'Turkmen'), (b'tw', b'Twi'), (b'ug', b'Uighur; Uyghur'), (b'uk', b'Ukrainian'), (b'ur', b'Urdu'), (b'uz', b'Uzbek'), (b've', b'Venda'), (b'vi', b'Vietnamese'), (b'vo', b'Volap\xc3\xbck'), (b'wa', b'Walloon'), (b'cy', b'Welsh'), (b'fy', b'Western Frisian'), (b'wo', b'Wolof'), (b'xh', b'Xhosa'), (b'yi', b'Yiddish'), (b'yo', b'Yoruba'), (b'za', b'Zhuang; Chuang'), (b'zu', b'Zulu')])),
                ('published', models.BooleanField(default=False, db_index=True, verbose_name='Published')),
                ('last_modified', models.DateTimeField(auto_now=True, verbose_name='Last modified')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('video', djangoplicity.translation.fields.TranslationForeignKey(to='media.Video')),
            ],
            options={
                'verbose_name': 'Video Script',
            },
            bases=(djangoplicity.archives.base.ArchiveModel, models.Model),
        ),

    ]
