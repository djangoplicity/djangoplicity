# coding: utf-8
#
# Djangoplicity
# Copyright 2007-2015 ESA/Hubble
#
# Authors:
#   Bruno Rino <brino@partner.eso.org>
#

# The way I've been running these tests under django 1.7 (~/dev/eso17 is my mercurial checkout):
# cd ~/dev/eso17/src/djangoplicity/src
# ~/dev/eso17/bin/python -m unittest djangoplicity.tests
#
# Testing for custom model fields done according to instructions here:
# https://docs.djangoproject.com/en/1.7/howto/custom-model-fields/#custom-field-deconstruct-method

import unittest

import djangoplicity.archives.fields
import djangoplicity.massmailer.models

# # Can't figure out how to instantiate this field
# from djangoplicity.translation.fields import TranslationManyToManyField

import djangoplicity.contrib.db.fields

# # This must be dead code, won't even import...
# import djangoplicity.metadata.fields

import djangoplicity.metadata.archives.fields


class FieldsTest(unittest.TestCase):
    def setUp(self):
        import django; django.setup()

    def _run_field_tests(self, klass, my_tests):
        for x, y in my_tests:
            my_field_instance = klass(**{x: y})
            name, path, args, kwargs = my_field_instance.deconstruct()
            new_instance = klass(*args, **kwargs)
            for field_name in set([z[0] for z in my_tests]):
                first = getattr(my_field_instance, field_name)
                second = getattr(new_instance, field_name)
                # if first != second:
                #     import pdb; pdb.set_trace()
                self.assertEqual(first, second, '%s.%s : %s != %s when given %s=%s' %(klass.__name__, field_name, str(first), str(second), x, str(y)))

    def test_id_field(self):
        my_tests = (
            ('max_length', 77),
            ('primary_key', True),
            ('primary_key', False),
            ('help_text', 'Boa Tarde!'),
        )
        self._run_field_tests(djangoplicity.archives.fields.IdField, my_tests)

    def test_priority_field(self):
        my_tests = (
            ('db_index', True),
            ('db_index', False),
            ('help_text', 'Boa Tarde!'),
        )
        self._run_field_tests(djangoplicity.archives.fields.PriorityField, my_tests)

    def test_title_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 200),
            ('db_index', True),
            ('db_index', False),
            ('help_text', 'Boa Tarde!'),
        )
        self._run_field_tests(djangoplicity.archives.fields.TitleField, my_tests)

    def test_release_date_time_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('db_index', True),
            ('db_index', False),
        )
        self._run_field_tests(djangoplicity.archives.fields.ReleaseDateTimeField, my_tests)

    def test_description_field(self):
        my_tests = (
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde!'),
        )
        self._run_field_tests(djangoplicity.archives.fields.DescriptionField, my_tests)

    def test_credit_field(self):
        my_tests = (
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde!'),
        )
        self._run_field_tests(djangoplicity.archives.fields.CreditField, my_tests)

    def test_image_size_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
        )
        self._run_field_tests(djangoplicity.archives.fields.ImageSizeField, my_tests)

    def test_paper_size_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('decimal_places', 77),
            ('decimal_places', 1),
            ('max_digits', 77),
            ('max_digits', 7),
        )
        self._run_field_tests(djangoplicity.archives.fields.PaperSizeField, my_tests)

    def test_pages_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
        )
        self._run_field_tests(djangoplicity.archives.fields.PagesField, my_tests)

    def test_int_size_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
        )
        self._run_field_tests(djangoplicity.archives.fields.IntField, my_tests)

    def test_duration_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.archives.fields.DurationField, my_tests)

    def test_email_field(self):
        my_tests = (
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.archives.fields.EmailField, my_tests)

    def test_url_size_field(self):
        my_tests = (
            ('blank', True),
            ('blank', False),
        )
        self._run_field_tests(djangoplicity.archives.fields.URLField, my_tests)

    def test_choice_field(self):
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('help_text', 'Boa Tarde!')
        )
        self._run_field_tests(djangoplicity.archives.fields.ChoiceField, my_tests)

    def test_task_id_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 40),
        )
        self._run_field_tests(djangoplicity.archives.fields.TaskIdField, my_tests)

    def test_multi_email_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 300),
        )
        self._run_field_tests(djangoplicity.massmailer.models.MultiEmailField, my_tests)


    # def test_translation_many_to_many_field(self):
    #     my_field_instance = TranslationManyToManyField()
    #     name, path, args, kwargs = my_field_instance.deconstruct()
    #     new_instance = TranslationManyToManyField(*args, **kwargs)
    #     self.assertEqual(my_field_instance.only_sources, new_instance.only_sources)

    # def test_translation_many_to_many_field_only_sources_true(self):
    #     my_field_instance = TranslationManyToManyField(only_sources=True)
    #     name, path, args, kwargs = my_field_instance.deconstruct()
    #     new_instance = TranslationManyToManyField(*args, **kwargs)
    #     self.assertEqual(my_field_instance.only_sources, new_instance.only_sources)

    # def test_translation_many_to_many_field_only_sources_false(self):
    #     my_field_instance = TranslationManyToManyField(only_sources=False)
    #     name, path, args, kwargs = my_field_instance.deconstruct()
    #     new_instance = TranslationManyToManyField(*args, **kwargs)
    #     self.assertEqual(my_field_instance.only_sources, new_instance.only_sources)


    def test_language_code_field(self):
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('max_length', 77),
            ('max_length', 2),
            ('default', 'de'),
            ('default', 'en'),
        )
        self._run_field_tests(djangoplicity.contrib.db.fields.LanguageCodeField, my_tests)

    # def test_avm_dead_field():
    #     my_field_instance = SpectralCentralWavelengthField()
    #     name, path, args, kwargs = my_field_instance.deconstruct()
    #     new_instance = SpectralCentralWavelengthField(*args, **kwargs)
    #     self.assertEqual(my_field_instance.max_length, new_instance.max_length)
    #     self.assertEqual(my_field_instance.null, new_instance.null)
    #     self.assertEqual(my_field_instance.blank, new_instance.blank)
    #     self.assertEqual(my_field_instance.verbose_name, new_instance.verbose_name)
    #     self.assertEqual(my_field_instance.help_text, new_instance.help_text)
    #     self.assertEqual(my_field_instance.avm_category, new_instance.avm_category)
    #     self.assertEqual(my_field_instance.avm_name, new_instance.avm_name)


    def test_avm_float_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 23),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFloatField, my_tests)

    def test_avm_two_float_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 47),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMTwoFloatField, my_tests)

    def test_avm_creator_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMCreatorField, my_tests)

    def test_avm_creator_url_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMCreatorURLField, my_tests)

    def test_avm_contact_address_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMContactAddressField, my_tests)

    def test_avm_contact_city_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMContactCityField, my_tests)

    def test_avm_contact_state_province_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMContactStateProvinceField, my_tests)

    def test_avm_contact_postal_code_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMContactPostalCodeField, my_tests)

    def test_avm_contact_country_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMContactCountryField, my_tests)

    def test_avm_rights_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMRightsField, my_tests)

    def test_avm_title_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('db_index', True),
            ('db_index', False),
            ('help_text', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMTitleField, my_tests)

    def test_avm_headline_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMHeadlineField, my_tests)

    def test_avm_keyword_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 300),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMKeywordField, my_tests)

    def test_avm_description_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMDescriptionField, my_tests)

    def test_avm_subject_category_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSubjectCategoryField, my_tests)

    def test_avm_subject_name_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSubjectNameField, my_tests)

    def test_avm_distance_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 30),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMDistanceField, my_tests)

    def test_avm_distance_ly_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 30),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('max_digits', 77),
            ('max_digits', 13),
            ('decimal_places', 77),
            ('decimal_places', 1),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMDistanceLyField, my_tests)

    def test_avm_distance_z_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('max_digits', 77),
            ('max_digits', 5),
            ('decimal_places', 77),
            ('decimal_places', 3),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMDistanceZField, my_tests)

    def test_avm_distance_notes_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMDistanceNotesField, my_tests)

    def test_avm_credit_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
            ('default', ''),
            ('default', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMCreditField, my_tests)

    def test_avm_id_field(self):
        my_tests = (
            ('primary_key', True),
            ('primary_key', False),
            ('help_text', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMIdField, my_tests)

    def test_avm_type_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.TYPE_CHOICES),
            ('max_length', 77),
            ('max_length', 12),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMTypeField, my_tests)

    def test_facility_many_to_many_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.FacilityManyToManyField, my_tests)

    def test_avm_facility_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFacilityField, my_tests)

    def test_avm_instrument_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMInstrumentField, my_tests)

    def test_avm_spectral_color_assignment_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.SPECTRAL_COLOR_ASSIGNMENT_CHOICES),
            ('max_length', 77),
            ('max_length', 11),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpectralColorAssignmentField, my_tests)

    def test_avm_spectral_band_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.SPECTRAL_BAND_CHOICES),
            ('max_length', 77),
            ('max_length', 11),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpectralBandField, my_tests)

    def test_avm_spectral_bandpass_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpectralBandpassField, my_tests)

    def test_avm_spectral_central_wavelength_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpectralCentralWavelengthField, my_tests)

    def test_avm_spectral_notes_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpectralNotesField, my_tests)

    def test_avm_temporal_start_time_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMTemporalStartTimeField, my_tests)

    def test_avm_temporal_integration_time_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMTemporalIntegrationTimeField, my_tests)

    def test_avm_dataset_id_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMDatasetIDField, my_tests)

    def test_avm_spatial_coordinate_frame_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.SPATIAL_COORDINATE_FRAME_CHOICES),
            ('max_length', 77),
            ('max_length', 4),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialCoordinateFrameField, my_tests)

    def test_avm_spatial_equinox_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.SPATIAL_EQUINOX_CHOICES),
            ('max_length', 77),
            ('max_length', 5),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialEquinoxField, my_tests)

    def test_avm_spatial_reference_value_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialReferenceValueField, my_tests)

    def test_avm_spatial_reference_dimension_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialReferenceDimensionField, my_tests)

    def test_avm_spatial_reference_pixel_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialReferencePixelField, my_tests)

    def test_avm_spatial_scale_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialScaleField, my_tests)

    def test_avm_spatial_rotation_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialRotationField, my_tests)

    def test_avm_spatial_coordsystem_projection_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.SPATIAL_COORDSYSTEM_PROJECTION_CHOICES),
            ('max_length', 77),
            ('max_length', 3),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialCoordsystemProjectionField, my_tests)

    def test_avm_spatial_quality_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.SPATIAL_QUALITY_CHOICES),
            ('max_length', 77),
            ('max_length', 8),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialQualityField, my_tests)

    def test_avm_spatial_notes_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialNotesField, my_tests)


    def test_avm_spatial_fits_herader_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMSpatialFITSHeaderField, my_tests)

    def test_avm_publisher_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMPublisherField, my_tests)

    def test_avm_publisher_id_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 255),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMPublisherIdField, my_tests)

    def test_avm_file_type_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.FILE_TYPE_CHOICES),
            ('max_length', 77),
            ('max_length', 4),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFileType, my_tests)

    def test_avm_file_dimensions_width_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFileDimensionWidth, my_tests)

    def test_avm_file_dimensions_height_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFileDimensionHeight, my_tests)

    def test_avm_file_size_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFileSize, my_tests)

    def test_avm_file_duration_field(self):
        my_tests = (
            ('max_length', 77),
            ('max_length', 13),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFileDuration, my_tests)

    def test_avm_file_aspect_ratio_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.FILE_ASPECT_RAITO_CHOICES),
            ('max_length', 77),
            ('max_length', 10),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMFileAspectRatio, my_tests)

    def test_avm_audio_surround_format_field(self):
        from djangoplicity.metadata import consts
        my_tests = (
            ('choices', ((1, 'A'), (2, 'B'), )),
            ('choices', consts.AUDIO_SURROUND_FORMAT_CHOICES),
            ('max_length', 77),
            ('max_length', 10),
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMAudioSurroundFormat, my_tests)

    def test_avm_publication_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMPublicationField, my_tests)

    def test_avm_proposal_id_field(self):
        my_tests = (
            ('null', True),
            ('null', False),
            ('blank', True),
            ('blank', False),
            ('help_text', 'Boa Tarde'),
            ('verbose_name', 'Boa Tarde'),
        )
        self._run_field_tests(djangoplicity.metadata.archives.fields.AVMProposalIDField, my_tests)

