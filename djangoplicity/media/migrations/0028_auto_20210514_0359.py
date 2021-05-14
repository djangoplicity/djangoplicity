# -*- coding: utf-8 -*-
# Generated by Django 1.11.21 on 2021-05-14 03:59
from __future__ import unicode_literals

from django.db import migrations, models
import djangoplicity.metadata.archives.fields


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0027_auto_20200629_0713'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='file_type',
            field=djangoplicity.metadata.archives.fields.AVMFileType(blank=True, choices=(('TIFF', 'TIFF'), ('JPEG', 'JPEG'), ('PNG', 'PNG'), ('GIF', 'GIF'), ('PSB', 'PSB'), ('PSD', 'PSD'), ('PDF', 'PDF')), help_text='The format of the file. For images this would include TIFF, JPEG, PNG, GIF, PSD, PDF.', max_length=4, null=True, verbose_name='File Type'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_x_l',
            field=models.DecimalField(blank=True, decimal_places=5, help_text='Horizontal Field of View (west), in degrees', max_digits=10, null=True, verbose_name='FOV x West'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_x_r',
            field=models.DecimalField(blank=True, decimal_places=5, help_text='Horizontal Field of View (east), in degrees', max_digits=10, null=True, verbose_name='FOV x East'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_y_d',
            field=models.DecimalField(blank=True, decimal_places=5, help_text='Vertical Field of View (bottom), in degrees', max_digits=10, null=True, verbose_name='FOV y Bottom'),
        ),
        migrations.AlterField(
            model_name='image',
            name='fov_y_u',
            field=models.DecimalField(blank=True, decimal_places=5, help_text='Vertical Field of View (top), in degrees', max_digits=10, null=True, verbose_name='FOV y Top'),
        ),
        migrations.AlterField(
            model_name='image',
            name='keep_newsfeature',
            field=models.BooleanField(default=False, verbose_name='Disable News Feature Auto-Overwite'),
        ),
        migrations.AlterField(
            model_name='image',
            name='print_layout',
            field=models.BooleanField(default=False, verbose_name='Print Layout'),
        ),
        migrations.AlterField(
            model_name='image',
            name='spatial_coordinate_frame',
            field=djangoplicity.metadata.archives.fields.AVMSpatialCoordinateFrameField(blank=True, choices=(('ICRS', 'ICRS'), ('FK5', 'FK5'), ('FK4', 'FK4'), ('ECL', 'ECL'), ('GAL', 'GAL'), ('SGAL', 'SGAL')), help_text='Coordinate system reference frame. Spatial.CoordinateFrame should be chosen from a pre-defined list.', max_length=4, null=True, verbose_name='Coordinate Frame'),
        ),
        migrations.AlterField(
            model_name='image',
            name='spatial_coordsystem_projection',
            field=djangoplicity.metadata.archives.fields.AVMSpatialCoordsystemProjectionField(blank=True, choices=(('TAN', 'TAN'), ('SIN', 'SIN'), ('ARC', 'ARC'), ('AIT', 'AIT'), ('CAR', 'CAR'), ('CEA', 'CEA')), help_text='A combination of the coordinate system and the projection of the image.', max_length=3, null=True, verbose_name='Coordinate System Projection'),
        ),
        migrations.AlterField(
            model_name='image',
            name='spatial_equinox',
            field=djangoplicity.metadata.archives.fields.AVMSpatialEquinoxField(blank=True, choices=(('J2000', 'J2000'), ('B1950', 'B1950')), help_text='Equinox for Spatial.CoordinateFrame in decimal years.', max_length=5, null=True, verbose_name='Equinox'),
        ),
        migrations.AlterField(
            model_name='image',
            name='spatial_quality',
            field=djangoplicity.metadata.archives.fields.AVMSpatialQualityField(blank=True, choices=(('Full', 'Full'), ('Position', 'Position')), help_text='This qualitatively describes the reliability of the spatial coordinate information in this metadata.', max_length=8, null=True, verbose_name='Quality'),
        ),
        migrations.AlterField(
            model_name='image',
            name='type',
            field=djangoplicity.metadata.archives.fields.AVMTypeField(blank=True, choices=(('Observation', 'Observation'), ('Artwork', 'Artwork'), ('Photographic', 'Photographic'), ('Planetary', 'Planetary'), ('Simulation', 'Simulation'), ('Collage', 'Collage'), ('Chart', 'Chart'), ('Nightscape', 'Nightscape'), ('Day Photo', 'Day Photo'), ('DeepSky Photo', 'DeepSky Photo'), ('Spectrum', 'Spectrum'), ('Annotated Obs', 'Annotated Observation')), help_text='The type of image/media resource.', max_length=30, null=True, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='image',
            name='wallpapers',
            field=models.BooleanField(default=True, verbose_name='Wallpapers'),
        ),
        migrations.AlterField(
            model_name='image',
            name='zoomify',
            field=models.BooleanField(default=False, verbose_name='Zoomable'),
        ),
        migrations.AlterField(
            model_name='imageexposure',
            name='spectral_band',
            field=djangoplicity.metadata.archives.fields.AVMSpectralBandField(blank=True, choices=(('Radio', 'Radio'), ('Millimeter', 'Millimeter'), ('Infrared', 'Infrared'), ('Optical', 'Optical'), ('Ultraviolet', 'Ultraviolet'), ('X-ray', 'X-ray'), ('Gamma-ray', 'Gamma-ray')), help_text='Waveband of the component exposure from a pre-defined list defining the general part of the spectrum covered. One Spectral.Band entry per exposure.', max_length=11, null=True, verbose_name='Spectral Band'),
        ),
        migrations.AlterField(
            model_name='imageexposure',
            name='spectral_color_assignment',
            field=djangoplicity.metadata.archives.fields.AVMSpectralColorAssignmentField(blank=True, choices=(('Purple', 'Purple'), ('Blue', 'Blue'), ('Cyan', 'Cyan'), ('Green', 'Green'), ('Yellow', 'Yellow'), ('Orange', 'Orange'), ('Red', 'Red'), ('Magenta', 'Magenta'), ('Grayscale', 'Grayscale'), ('Pseudocolor', 'Pseudocolor'), ('Luminosity', 'Luminosity')), help_text='The output color that is assigned to an exposure. One Spectral.ColorAssignment entry per exposure.', max_length=11, null=True, verbose_name='Spectral Color Assignment'),
        ),
        migrations.AlterField(
            model_name='video',
            name='audio_surround_format',
            field=djangoplicity.metadata.archives.fields.AVMAudioSurroundFormat(blank=True, choices=(('5.1', '5.1'), ('6.1', '6.1'), ('7.1', '7.1'), ('8.1', '8.1'), ('STEM', 'STEM tracks'), ('Other', 'Other')), help_text='The surround sound format of the audio.', max_length=10, null=True, verbose_name='Surround Sound Format'),
        ),
        migrations.AlterField(
            model_name='video',
            name='file_aspect_ratio',
            field=djangoplicity.metadata.archives.fields.AVMFileAspectRatio(blank=True, choices=(('4:3', '4:3'), ('16:9', '16:9'), ('16:10', '16:10')), help_text='The aspect ratio of the file.', max_length=10, null=True, verbose_name='File Aspect Ratio'),
        ),
        migrations.AlterField(
            model_name='video',
            name='type',
            field=djangoplicity.metadata.archives.fields.AVMTypeField(blank=True, choices=(('Observation', 'Observation'), ('Artwork', 'Artwork'), ('Photographic', 'Photographic'), ('Planetary', 'Planetary'), ('Simulation', 'Simulation'), ('Collage', 'Collage'), ('Chart', 'Chart'), ('Nightscape', 'Nightscape'), ('Day Photo', 'Day Photo'), ('DeepSky Photo', 'DeepSky Photo'), ('Spectrum', 'Spectrum'), ('Annotated Obs', 'Annotated Observation')), help_text='The type of image/media resource.', max_length=30, null=True, verbose_name='Type'),
        ),
        migrations.AlterField(
            model_name='videoaudiotrack',
            name='lang',
            field=models.CharField(choices=[('ab', 'Abkhazian'), ('aa', 'Afar'), ('af', 'Afrikaans'), ('ak', 'Akan'), ('sq', 'Albanian'), ('am', 'Amharic'), ('ar', 'Arabic'), ('an', 'Aragonese'), ('hy', 'Armenian'), ('as', 'Assamese'), ('av', 'Avaric'), ('ae', 'Avestan'), ('ay', 'Aymara'), ('az', 'Azerbaijani'), ('bm', 'Bambara'), ('ba', 'Bashkir'), ('eu', 'Basque'), ('be', 'Belarusian'), ('bn', 'Bengali'), ('bh', 'Bihari languages'), ('bi', 'Bislama'), ('nb', 'Bokmål, Norwegian; Norwegian Bokmål'), ('bs', 'Bosnian'), ('br', 'Breton'), ('bg', 'Bulgarian'), ('my', 'Burmese'), ('ca', 'Catalan; Valencian'), ('km', 'Central Khmer'), ('ch', 'Chamorro'), ('ce', 'Chechen'), ('ny', 'Chichewa; Chewa; Nyanja'), ('zh', 'Chinese'), ('cu', 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'), ('cv', 'Chuvash'), ('kw', 'Cornish'), ('co', 'Corsican'), ('cr', 'Cree'), ('hr', 'Croatian'), ('cs', 'Czech'), ('da', 'Danish'), ('dv', 'Divehi; Dhivehi; Maldivian'), ('nl', 'Dutch; Flemish'), ('dz', 'Dzongkha'), ('en', 'English'), ('eo', 'Esperanto'), ('et', 'Estonian'), ('ee', 'Ewe'), ('fo', 'Faroese'), ('fj', 'Fijian'), ('fi', 'Finnish'), ('fr', 'French'), ('ff', 'Fulah'), ('gd', 'Gaelic; Scottish Gaelic'), ('gl', 'Galician'), ('lg', 'Ganda'), ('ka', 'Georgian'), ('de', 'German'), ('el', 'Greek'), ('gn', 'Guarani'), ('gu', 'Gujarati'), ('ht', 'Haitian; Haitian Creole'), ('ha', 'Hausa'), ('he', 'Hebrew'), ('hz', 'Herero'), ('hi', 'Hindi'), ('ho', 'Hiri Motu'), ('hu', 'Hungarian'), ('is', 'Icelandic'), ('io', 'Ido'), ('ig', 'Igbo'), ('id', 'Indonesian'), ('ia', 'Interlingua (International Auxiliary Language Association)'), ('ie', 'Interlingue; Occidental'), ('iu', 'Inuktitut'), ('ik', 'Inupiaq'), ('ga', 'Irish'), ('it', 'Italian'), ('ja', 'Japanese'), ('jv', 'Javanese'), ('kl', 'Kalaallisut; Greenlandic'), ('kn', 'Kannada'), ('kr', 'Kanuri'), ('ks', 'Kashmiri'), ('kk', 'Kazakh'), ('ki', 'Kikuyu; Gikuyu'), ('rw', 'Kinyarwanda'), ('ky', 'Kirghiz; Kyrgyz'), ('kv', 'Komi'), ('kg', 'Kongo'), ('ko', 'Korean'), ('kj', 'Kuanyama; Kwanyama'), ('ku', 'Kurdish'), ('lo', 'Lao'), ('la', 'Latin'), ('lv', 'Latvian'), ('li', 'Limburgan; Limburger; Limburgish'), ('ln', 'Lingala'), ('lt', 'Lithuanian'), ('lu', 'Luba-Katanga'), ('lb', 'Luxembourgish; Letzeburgesch'), ('mk', 'Macedonian'), ('mg', 'Malagasy'), ('ms', 'Malay'), ('ml', 'Malayalam'), ('mt', 'Maltese'), ('gv', 'Manx'), ('mi', 'Maori'), ('mr', 'Marathi'), ('mh', 'Marshallese'), ('mn', 'Mongolian'), ('na', 'Nauru'), ('nv', 'Navajo; Navaho'), ('nd', 'Ndebele - North; North Ndebele'), ('nr', 'Ndebele - South; South Ndebele'), ('ng', 'Ndonga'), ('ne', 'Nepali'), ('se', 'Northern Sami'), ('no', 'Norwegian'), ('nb', 'Norwegian Bokmal'), ('nn', 'Norwegian Nynorsk; Nynorsk, Norwegian'), ('oc', 'Occitan (post 1500)'), ('oj', 'Ojibwa'), ('or', 'Oriya'), ('om', 'Oromo'), ('os', 'Ossetian; Ossetic'), ('pi', 'Pali'), ('pa', 'Panjabi; Punjabi'), ('fa', 'Persian'), ('pl', 'Polish'), ('pt', 'Portuguese'), ('ps', 'Pushto; Pashto'), ('qu', 'Quechua'), ('ro', 'Romanian; Moldavian; Moldovan'), ('rm', 'Romansh'), ('rn', 'Rundi'), ('ru', 'Russian'), ('sm', 'Samoan'), ('sg', 'Sango'), ('sa', 'Sanskrit'), ('sc', 'Sardinian'), ('sr', 'Serbian'), ('sr-latn', 'Serbian Latin'), ('sn', 'Shona'), ('ii', 'Sichuan Yi; Nuosu'), ('sd', 'Sindhi'), ('si', 'Sinhala; Sinhalese'), ('sk', 'Slovak'), ('sl', 'Slovenian'), ('so', 'Somali'), ('st', 'Sotho; Southern'), ('es', 'Spanish; Castilian'), ('su', 'Sundanese'), ('sw', 'Swahili'), ('ss', 'Swati'), ('sv', 'Swedish'), ('tl', 'Tagalog'), ('ty', 'Tahitian'), ('tg', 'Tajik'), ('ta', 'Tamil'), ('tt', 'Tatar'), ('te', 'Telugu'), ('th', 'Thai'), ('bo', 'Tibetan'), ('ti', 'Tigrinya'), ('to', 'Tonga (Tonga Islands)'), ('ts', 'Tsonga'), ('tn', 'Tswana'), ('tr', 'Turkish'), ('tk', 'Turkmen'), ('tw', 'Twi'), ('ug', 'Uighur; Uyghur'), ('uk', 'Ukrainian'), ('ur', 'Urdu'), ('uz', 'Uzbek'), ('ve', 'Venda'), ('vi', 'Vietnamese'), ('vo', 'Volapük'), ('wa', 'Walloon'), ('cy', 'Welsh'), ('fy', 'Western Frisian'), ('wo', 'Wolof'), ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('yo', 'Yoruba'), ('za', 'Zhuang; Chuang'), ('zu', 'Zulu')], db_index=True, default='en', max_length=7, verbose_name='Language'),
        ),
        migrations.AlterField(
            model_name='videobroadcastaudiotrack',
            name='lang',
            field=models.CharField(choices=[('ab', 'Abkhazian'), ('aa', 'Afar'), ('af', 'Afrikaans'), ('ak', 'Akan'), ('sq', 'Albanian'), ('am', 'Amharic'), ('ar', 'Arabic'), ('an', 'Aragonese'), ('hy', 'Armenian'), ('as', 'Assamese'), ('av', 'Avaric'), ('ae', 'Avestan'), ('ay', 'Aymara'), ('az', 'Azerbaijani'), ('bm', 'Bambara'), ('ba', 'Bashkir'), ('eu', 'Basque'), ('be', 'Belarusian'), ('bn', 'Bengali'), ('bh', 'Bihari languages'), ('bi', 'Bislama'), ('nb', 'Bokmål, Norwegian; Norwegian Bokmål'), ('bs', 'Bosnian'), ('br', 'Breton'), ('bg', 'Bulgarian'), ('my', 'Burmese'), ('ca', 'Catalan; Valencian'), ('km', 'Central Khmer'), ('ch', 'Chamorro'), ('ce', 'Chechen'), ('ny', 'Chichewa; Chewa; Nyanja'), ('zh', 'Chinese'), ('cu', 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'), ('cv', 'Chuvash'), ('kw', 'Cornish'), ('co', 'Corsican'), ('cr', 'Cree'), ('hr', 'Croatian'), ('cs', 'Czech'), ('da', 'Danish'), ('dv', 'Divehi; Dhivehi; Maldivian'), ('nl', 'Dutch; Flemish'), ('dz', 'Dzongkha'), ('en', 'English'), ('eo', 'Esperanto'), ('et', 'Estonian'), ('ee', 'Ewe'), ('fo', 'Faroese'), ('fj', 'Fijian'), ('fi', 'Finnish'), ('fr', 'French'), ('ff', 'Fulah'), ('gd', 'Gaelic; Scottish Gaelic'), ('gl', 'Galician'), ('lg', 'Ganda'), ('ka', 'Georgian'), ('de', 'German'), ('el', 'Greek'), ('gn', 'Guarani'), ('gu', 'Gujarati'), ('ht', 'Haitian; Haitian Creole'), ('ha', 'Hausa'), ('he', 'Hebrew'), ('hz', 'Herero'), ('hi', 'Hindi'), ('ho', 'Hiri Motu'), ('hu', 'Hungarian'), ('is', 'Icelandic'), ('io', 'Ido'), ('ig', 'Igbo'), ('id', 'Indonesian'), ('ia', 'Interlingua (International Auxiliary Language Association)'), ('ie', 'Interlingue; Occidental'), ('iu', 'Inuktitut'), ('ik', 'Inupiaq'), ('ga', 'Irish'), ('it', 'Italian'), ('ja', 'Japanese'), ('jv', 'Javanese'), ('kl', 'Kalaallisut; Greenlandic'), ('kn', 'Kannada'), ('kr', 'Kanuri'), ('ks', 'Kashmiri'), ('kk', 'Kazakh'), ('ki', 'Kikuyu; Gikuyu'), ('rw', 'Kinyarwanda'), ('ky', 'Kirghiz; Kyrgyz'), ('kv', 'Komi'), ('kg', 'Kongo'), ('ko', 'Korean'), ('kj', 'Kuanyama; Kwanyama'), ('ku', 'Kurdish'), ('lo', 'Lao'), ('la', 'Latin'), ('lv', 'Latvian'), ('li', 'Limburgan; Limburger; Limburgish'), ('ln', 'Lingala'), ('lt', 'Lithuanian'), ('lu', 'Luba-Katanga'), ('lb', 'Luxembourgish; Letzeburgesch'), ('mk', 'Macedonian'), ('mg', 'Malagasy'), ('ms', 'Malay'), ('ml', 'Malayalam'), ('mt', 'Maltese'), ('gv', 'Manx'), ('mi', 'Maori'), ('mr', 'Marathi'), ('mh', 'Marshallese'), ('mn', 'Mongolian'), ('na', 'Nauru'), ('nv', 'Navajo; Navaho'), ('nd', 'Ndebele - North; North Ndebele'), ('nr', 'Ndebele - South; South Ndebele'), ('ng', 'Ndonga'), ('ne', 'Nepali'), ('se', 'Northern Sami'), ('no', 'Norwegian'), ('nb', 'Norwegian Bokmal'), ('nn', 'Norwegian Nynorsk; Nynorsk, Norwegian'), ('oc', 'Occitan (post 1500)'), ('oj', 'Ojibwa'), ('or', 'Oriya'), ('om', 'Oromo'), ('os', 'Ossetian; Ossetic'), ('pi', 'Pali'), ('pa', 'Panjabi; Punjabi'), ('fa', 'Persian'), ('pl', 'Polish'), ('pt', 'Portuguese'), ('ps', 'Pushto; Pashto'), ('qu', 'Quechua'), ('ro', 'Romanian; Moldavian; Moldovan'), ('rm', 'Romansh'), ('rn', 'Rundi'), ('ru', 'Russian'), ('sm', 'Samoan'), ('sg', 'Sango'), ('sa', 'Sanskrit'), ('sc', 'Sardinian'), ('sr', 'Serbian'), ('sr-latn', 'Serbian Latin'), ('sn', 'Shona'), ('ii', 'Sichuan Yi; Nuosu'), ('sd', 'Sindhi'), ('si', 'Sinhala; Sinhalese'), ('sk', 'Slovak'), ('sl', 'Slovenian'), ('so', 'Somali'), ('st', 'Sotho; Southern'), ('es', 'Spanish; Castilian'), ('su', 'Sundanese'), ('sw', 'Swahili'), ('ss', 'Swati'), ('sv', 'Swedish'), ('tl', 'Tagalog'), ('ty', 'Tahitian'), ('tg', 'Tajik'), ('ta', 'Tamil'), ('tt', 'Tatar'), ('te', 'Telugu'), ('th', 'Thai'), ('bo', 'Tibetan'), ('ti', 'Tigrinya'), ('to', 'Tonga (Tonga Islands)'), ('ts', 'Tsonga'), ('tn', 'Tswana'), ('tr', 'Turkish'), ('tk', 'Turkmen'), ('tw', 'Twi'), ('ug', 'Uighur; Uyghur'), ('uk', 'Ukrainian'), ('ur', 'Urdu'), ('uz', 'Uzbek'), ('ve', 'Venda'), ('vi', 'Vietnamese'), ('vo', 'Volapük'), ('wa', 'Walloon'), ('cy', 'Welsh'), ('fy', 'Western Frisian'), ('wo', 'Wolof'), ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('yo', 'Yoruba'), ('za', 'Zhuang; Chuang'), ('zu', 'Zulu')], db_index=True, default='en', max_length=7, verbose_name='Language'),
        ),
        migrations.AlterField(
            model_name='videobroadcastaudiotrack',
            name='type',
            field=models.CharField(choices=[('stereo', 'Stereo soundtrack'), ('split_stereo', 'Split stereo'), ('surround', 'Surround 5.1'), ('split_surround', 'Split surround 5.1')], max_length=25, verbose_name='Audio track type'),
        ),
        migrations.AlterField(
            model_name='videoscript',
            name='lang',
            field=models.CharField(choices=[('ab', 'Abkhazian'), ('aa', 'Afar'), ('af', 'Afrikaans'), ('ak', 'Akan'), ('sq', 'Albanian'), ('am', 'Amharic'), ('ar', 'Arabic'), ('an', 'Aragonese'), ('hy', 'Armenian'), ('as', 'Assamese'), ('av', 'Avaric'), ('ae', 'Avestan'), ('ay', 'Aymara'), ('az', 'Azerbaijani'), ('bm', 'Bambara'), ('ba', 'Bashkir'), ('eu', 'Basque'), ('be', 'Belarusian'), ('bn', 'Bengali'), ('bh', 'Bihari languages'), ('bi', 'Bislama'), ('nb', 'Bokmål, Norwegian; Norwegian Bokmål'), ('bs', 'Bosnian'), ('br', 'Breton'), ('bg', 'Bulgarian'), ('my', 'Burmese'), ('ca', 'Catalan; Valencian'), ('km', 'Central Khmer'), ('ch', 'Chamorro'), ('ce', 'Chechen'), ('ny', 'Chichewa; Chewa; Nyanja'), ('zh', 'Chinese'), ('cu', 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'), ('cv', 'Chuvash'), ('kw', 'Cornish'), ('co', 'Corsican'), ('cr', 'Cree'), ('hr', 'Croatian'), ('cs', 'Czech'), ('da', 'Danish'), ('dv', 'Divehi; Dhivehi; Maldivian'), ('nl', 'Dutch; Flemish'), ('dz', 'Dzongkha'), ('en', 'English'), ('eo', 'Esperanto'), ('et', 'Estonian'), ('ee', 'Ewe'), ('fo', 'Faroese'), ('fj', 'Fijian'), ('fi', 'Finnish'), ('fr', 'French'), ('ff', 'Fulah'), ('gd', 'Gaelic; Scottish Gaelic'), ('gl', 'Galician'), ('lg', 'Ganda'), ('ka', 'Georgian'), ('de', 'German'), ('el', 'Greek'), ('gn', 'Guarani'), ('gu', 'Gujarati'), ('ht', 'Haitian; Haitian Creole'), ('ha', 'Hausa'), ('he', 'Hebrew'), ('hz', 'Herero'), ('hi', 'Hindi'), ('ho', 'Hiri Motu'), ('hu', 'Hungarian'), ('is', 'Icelandic'), ('io', 'Ido'), ('ig', 'Igbo'), ('id', 'Indonesian'), ('ia', 'Interlingua (International Auxiliary Language Association)'), ('ie', 'Interlingue; Occidental'), ('iu', 'Inuktitut'), ('ik', 'Inupiaq'), ('ga', 'Irish'), ('it', 'Italian'), ('ja', 'Japanese'), ('jv', 'Javanese'), ('kl', 'Kalaallisut; Greenlandic'), ('kn', 'Kannada'), ('kr', 'Kanuri'), ('ks', 'Kashmiri'), ('kk', 'Kazakh'), ('ki', 'Kikuyu; Gikuyu'), ('rw', 'Kinyarwanda'), ('ky', 'Kirghiz; Kyrgyz'), ('kv', 'Komi'), ('kg', 'Kongo'), ('ko', 'Korean'), ('kj', 'Kuanyama; Kwanyama'), ('ku', 'Kurdish'), ('lo', 'Lao'), ('la', 'Latin'), ('lv', 'Latvian'), ('li', 'Limburgan; Limburger; Limburgish'), ('ln', 'Lingala'), ('lt', 'Lithuanian'), ('lu', 'Luba-Katanga'), ('lb', 'Luxembourgish; Letzeburgesch'), ('mk', 'Macedonian'), ('mg', 'Malagasy'), ('ms', 'Malay'), ('ml', 'Malayalam'), ('mt', 'Maltese'), ('gv', 'Manx'), ('mi', 'Maori'), ('mr', 'Marathi'), ('mh', 'Marshallese'), ('mn', 'Mongolian'), ('na', 'Nauru'), ('nv', 'Navajo; Navaho'), ('nd', 'Ndebele - North; North Ndebele'), ('nr', 'Ndebele - South; South Ndebele'), ('ng', 'Ndonga'), ('ne', 'Nepali'), ('se', 'Northern Sami'), ('no', 'Norwegian'), ('nb', 'Norwegian Bokmal'), ('nn', 'Norwegian Nynorsk; Nynorsk, Norwegian'), ('oc', 'Occitan (post 1500)'), ('oj', 'Ojibwa'), ('or', 'Oriya'), ('om', 'Oromo'), ('os', 'Ossetian; Ossetic'), ('pi', 'Pali'), ('pa', 'Panjabi; Punjabi'), ('fa', 'Persian'), ('pl', 'Polish'), ('pt', 'Portuguese'), ('ps', 'Pushto; Pashto'), ('qu', 'Quechua'), ('ro', 'Romanian; Moldavian; Moldovan'), ('rm', 'Romansh'), ('rn', 'Rundi'), ('ru', 'Russian'), ('sm', 'Samoan'), ('sg', 'Sango'), ('sa', 'Sanskrit'), ('sc', 'Sardinian'), ('sr', 'Serbian'), ('sr-latn', 'Serbian Latin'), ('sn', 'Shona'), ('ii', 'Sichuan Yi; Nuosu'), ('sd', 'Sindhi'), ('si', 'Sinhala; Sinhalese'), ('sk', 'Slovak'), ('sl', 'Slovenian'), ('so', 'Somali'), ('st', 'Sotho; Southern'), ('es', 'Spanish; Castilian'), ('su', 'Sundanese'), ('sw', 'Swahili'), ('ss', 'Swati'), ('sv', 'Swedish'), ('tl', 'Tagalog'), ('ty', 'Tahitian'), ('tg', 'Tajik'), ('ta', 'Tamil'), ('tt', 'Tatar'), ('te', 'Telugu'), ('th', 'Thai'), ('bo', 'Tibetan'), ('ti', 'Tigrinya'), ('to', 'Tonga (Tonga Islands)'), ('ts', 'Tsonga'), ('tn', 'Tswana'), ('tr', 'Turkish'), ('tk', 'Turkmen'), ('tw', 'Twi'), ('ug', 'Uighur; Uyghur'), ('uk', 'Ukrainian'), ('ur', 'Urdu'), ('uz', 'Uzbek'), ('ve', 'Venda'), ('vi', 'Vietnamese'), ('vo', 'Volapük'), ('wa', 'Walloon'), ('cy', 'Welsh'), ('fy', 'Western Frisian'), ('wo', 'Wolof'), ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('yo', 'Yoruba'), ('za', 'Zhuang; Chuang'), ('zu', 'Zulu')], db_index=True, default='en', max_length=7, verbose_name='Language'),
        ),
        migrations.AlterField(
            model_name='videosubtitle',
            name='lang',
            field=models.CharField(choices=[('ab', 'Abkhazian'), ('aa', 'Afar'), ('af', 'Afrikaans'), ('ak', 'Akan'), ('sq', 'Albanian'), ('am', 'Amharic'), ('ar', 'Arabic'), ('an', 'Aragonese'), ('hy', 'Armenian'), ('as', 'Assamese'), ('av', 'Avaric'), ('ae', 'Avestan'), ('ay', 'Aymara'), ('az', 'Azerbaijani'), ('bm', 'Bambara'), ('ba', 'Bashkir'), ('eu', 'Basque'), ('be', 'Belarusian'), ('bn', 'Bengali'), ('bh', 'Bihari languages'), ('bi', 'Bislama'), ('nb', 'Bokmål, Norwegian; Norwegian Bokmål'), ('bs', 'Bosnian'), ('br', 'Breton'), ('bg', 'Bulgarian'), ('my', 'Burmese'), ('ca', 'Catalan; Valencian'), ('km', 'Central Khmer'), ('ch', 'Chamorro'), ('ce', 'Chechen'), ('ny', 'Chichewa; Chewa; Nyanja'), ('zh', 'Chinese'), ('cu', 'Church Slavic; Old Slavonic; Church Slavonic; Old Bulgarian; Old Church Slavonic'), ('cv', 'Chuvash'), ('kw', 'Cornish'), ('co', 'Corsican'), ('cr', 'Cree'), ('hr', 'Croatian'), ('cs', 'Czech'), ('da', 'Danish'), ('dv', 'Divehi; Dhivehi; Maldivian'), ('nl', 'Dutch; Flemish'), ('dz', 'Dzongkha'), ('en', 'English'), ('eo', 'Esperanto'), ('et', 'Estonian'), ('ee', 'Ewe'), ('fo', 'Faroese'), ('fj', 'Fijian'), ('fi', 'Finnish'), ('fr', 'French'), ('ff', 'Fulah'), ('gd', 'Gaelic; Scottish Gaelic'), ('gl', 'Galician'), ('lg', 'Ganda'), ('ka', 'Georgian'), ('de', 'German'), ('el', 'Greek'), ('gn', 'Guarani'), ('gu', 'Gujarati'), ('ht', 'Haitian; Haitian Creole'), ('ha', 'Hausa'), ('he', 'Hebrew'), ('hz', 'Herero'), ('hi', 'Hindi'), ('ho', 'Hiri Motu'), ('hu', 'Hungarian'), ('is', 'Icelandic'), ('io', 'Ido'), ('ig', 'Igbo'), ('id', 'Indonesian'), ('ia', 'Interlingua (International Auxiliary Language Association)'), ('ie', 'Interlingue; Occidental'), ('iu', 'Inuktitut'), ('ik', 'Inupiaq'), ('ga', 'Irish'), ('it', 'Italian'), ('ja', 'Japanese'), ('jv', 'Javanese'), ('kl', 'Kalaallisut; Greenlandic'), ('kn', 'Kannada'), ('kr', 'Kanuri'), ('ks', 'Kashmiri'), ('kk', 'Kazakh'), ('ki', 'Kikuyu; Gikuyu'), ('rw', 'Kinyarwanda'), ('ky', 'Kirghiz; Kyrgyz'), ('kv', 'Komi'), ('kg', 'Kongo'), ('ko', 'Korean'), ('kj', 'Kuanyama; Kwanyama'), ('ku', 'Kurdish'), ('lo', 'Lao'), ('la', 'Latin'), ('lv', 'Latvian'), ('li', 'Limburgan; Limburger; Limburgish'), ('ln', 'Lingala'), ('lt', 'Lithuanian'), ('lu', 'Luba-Katanga'), ('lb', 'Luxembourgish; Letzeburgesch'), ('mk', 'Macedonian'), ('mg', 'Malagasy'), ('ms', 'Malay'), ('ml', 'Malayalam'), ('mt', 'Maltese'), ('gv', 'Manx'), ('mi', 'Maori'), ('mr', 'Marathi'), ('mh', 'Marshallese'), ('mn', 'Mongolian'), ('na', 'Nauru'), ('nv', 'Navajo; Navaho'), ('nd', 'Ndebele - North; North Ndebele'), ('nr', 'Ndebele - South; South Ndebele'), ('ng', 'Ndonga'), ('ne', 'Nepali'), ('se', 'Northern Sami'), ('no', 'Norwegian'), ('nb', 'Norwegian Bokmal'), ('nn', 'Norwegian Nynorsk; Nynorsk, Norwegian'), ('oc', 'Occitan (post 1500)'), ('oj', 'Ojibwa'), ('or', 'Oriya'), ('om', 'Oromo'), ('os', 'Ossetian; Ossetic'), ('pi', 'Pali'), ('pa', 'Panjabi; Punjabi'), ('fa', 'Persian'), ('pl', 'Polish'), ('pt', 'Portuguese'), ('ps', 'Pushto; Pashto'), ('qu', 'Quechua'), ('ro', 'Romanian; Moldavian; Moldovan'), ('rm', 'Romansh'), ('rn', 'Rundi'), ('ru', 'Russian'), ('sm', 'Samoan'), ('sg', 'Sango'), ('sa', 'Sanskrit'), ('sc', 'Sardinian'), ('sr', 'Serbian'), ('sr-latn', 'Serbian Latin'), ('sn', 'Shona'), ('ii', 'Sichuan Yi; Nuosu'), ('sd', 'Sindhi'), ('si', 'Sinhala; Sinhalese'), ('sk', 'Slovak'), ('sl', 'Slovenian'), ('so', 'Somali'), ('st', 'Sotho; Southern'), ('es', 'Spanish; Castilian'), ('su', 'Sundanese'), ('sw', 'Swahili'), ('ss', 'Swati'), ('sv', 'Swedish'), ('tl', 'Tagalog'), ('ty', 'Tahitian'), ('tg', 'Tajik'), ('ta', 'Tamil'), ('tt', 'Tatar'), ('te', 'Telugu'), ('th', 'Thai'), ('bo', 'Tibetan'), ('ti', 'Tigrinya'), ('to', 'Tonga (Tonga Islands)'), ('ts', 'Tsonga'), ('tn', 'Tswana'), ('tr', 'Turkish'), ('tk', 'Turkmen'), ('tw', 'Twi'), ('ug', 'Uighur; Uyghur'), ('uk', 'Ukrainian'), ('ur', 'Urdu'), ('uz', 'Uzbek'), ('ve', 'Venda'), ('vi', 'Vietnamese'), ('vo', 'Volapük'), ('wa', 'Walloon'), ('cy', 'Welsh'), ('fy', 'Western Frisian'), ('wo', 'Wolof'), ('xh', 'Xhosa'), ('yi', 'Yiddish'), ('yo', 'Yoruba'), ('za', 'Zhuang; Chuang'), ('zu', 'Zulu')], db_index=True, default='en', max_length=7, verbose_name='Language'),
        ),
    ]
