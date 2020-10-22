# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django import forms
from django.db import models
from django.utils.translation import ugettext_lazy as _
from djangoplicity.metadata import consts
from djangoplicity.metadata.archives import forms as avmforms
from djangoplicity.metadata.models import TaxonomyHierarchy, SubjectName, Facility, Instrument, Publication, ObservationProposal


class AVMFloatField( models.CharField ):

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 23,
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMFloatField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFloatField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        defaults = {
            'form_class': forms.RegexField,
            'regex': r'^\s*-?(\d*\.?\d*)\s*$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _( u'Enter a valid number.' ),
            }
        }
        defaults.update( kwargs )
        return super( AVMFloatField, self ).formfield( **defaults )


class AVMTwoFloatField( models.CharField ):

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 47,
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMTwoFloatField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMTwoFloatField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        defaults = { 'form_class': avmforms.TwoItemFloatField }
        defaults.update( kwargs )
        return super( AVMTwoFloatField, self ).formfield( **defaults )

    def from_internal(self, value ):
        if value:
            data_list = value.split(';')
            return data_list[:2]
        return []


# =============================================================================
# Astronomy Visualization Metadata
# =============================================================================

class AVMCreatorField( models.CharField ):
    avm_category = "Creator"
    avm_name = "Creator"
    avm_help_text = _( "Original creator of the resource at the organizational level." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMCreatorField.avm_help_text,
            'verbose_name': _( "Creator" )
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMCreatorField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMCreatorField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMCreatorURLField( models.URLField ):
    avm_category = "Creator"
    avm_name = "CreatorURL"
    avm_help_text = _( "A simple URL pointing to the (top level) outreach webpage for the original creator." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMCreatorURLField.avm_help_text,
            'verbose_name': _( "Creator URL" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMCreatorURLField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMCreatorURLField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMContactAddressField( models.CharField ):
    avm_category = "Creator"
    avm_name = "Contact.Address"
    avm_help_text = _( "Street address of the primary contact for the resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMContactAddressField.avm_help_text,
            'verbose_name': _( "Contact Address" )
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMContactAddressField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMContactAddressField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMContactCityField( models.CharField ):
    avm_category = "Creator"
    avm_name = "Contact.City"
    avm_help_text = _( "City of the primary contact for the resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMContactCityField.avm_help_text,
            'verbose_name': _( "Contact City" )
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMContactCityField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMContactCityField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMContactStateProvinceField( models.CharField ):
    avm_category = "Creator"
    avm_name = "Contact.StateProvince"
    avm_help_text = _( "State or province of the primary contact for the resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMContactStateProvinceField.avm_help_text,
            'verbose_name': _( "Contact State/Province" )
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMContactStateProvinceField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMContactStateProvinceField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMContactPostalCodeField( models.CharField ):
    avm_category = "Creator"
    avm_name = "Contact.PostalCode"
    avm_help_text = _( "Zip or postal code of the primary contact for the resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 50,
            'null': True,
            'blank': True,
            'help_text': AVMContactPostalCodeField.avm_help_text,
            'verbose_name': _( "Contact Postalcode" )
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMContactPostalCodeField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMContactPostalCodeField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMContactCountryField( models.CharField ):
    avm_category = "Creator"
    avm_name = "Contact.Country"
    avm_help_text = _( "Country of the primary contact for the resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMContactCountryField.avm_help_text,
            'verbose_name': _( "Contact Country" )
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMContactCountryField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMContactCountryField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMRightsField( models.TextField ):
    avm_category = "Creator"
    avm_name = "Rights"
    avm_help_text = _( "Copyright and related intellectual property rights description." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMRightsField.avm_help_text,
            'verbose_name': _( "Rights" )
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMRightsField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMRightsField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMTitleField( models.CharField ):
    avm_category = "Content"
    avm_name = "Title"
    avm_help_text = _( "General descriptive title given to the image resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'db_index': True,
            'help_text': AVMTitleField.avm_help_text,
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMTitleField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMTitleField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMHeadlineField( models.TextField ):
    avm_category = "Content"
    avm_name = "Headline"
    avm_help_text = _( "Short description of the full caption." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMHeadlineField.avm_help_text
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMHeadlineField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMHeadlineField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMKeywordField ( models.CharField ):

    def __init__(self, *args, **kwargs ):
        self.avm_category = "Content"
        self.avm_name = "Keywords"
        super(AVMKeywordField, self).__init__(
                                        max_length=300,
                                        null=True,
                                        blank=True,
                                        verbose_name="Keywords",
                                        help_text="Keywords associated with the resource resource, separated by commas.")


class AVMDescriptionField( models.TextField ):
    avm_category = "Content"
    avm_name = "Description"
    avm_help_text = _( "Full caption and related description text for the image resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMDescriptionField.avm_help_text,
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMDescriptionField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMDescriptionField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

#class AVMTopLevelHierarchyField( models.CharField ):
#   avm_category = "Content"
#   avm_name = "Subject.Category"
#   avm_help_text = _( u"<p><strong>Typical subject category:</strong><ul><li>Solar System: Planet, Interplanetary Body, Star, Sky Phenomenon, Technology</li><li>Milky Way: Planet, Interplanetary Body, Star, Nebula</li><li>Local Universe (z&lt;=0.1): Star, Nebula, Galaxy</li><li>Early Universe (z&gt;0.1): Galaxy, Cosmology</li><li>Unspecified: any (non-astronomical in nature - e.g. artwork and photographic)</li><li>Local use only: Mission Graphics</li><ul></p>" )
#
#   def __init__( self, *args, **kwargs ):
#       defaults = {
#                   'max_length': 1,
#                   'db_index': True,
#                   'null': True,
#                   'blank': True,
#                   'choices': consts.TOP_LEVEL_HIERARCHY,
#                   'help_text': AVMTopLevelHierarchyField.avm_help_text,
#                   'verbose_name': _( 'Top Level Hierarchy' )
#                  }
#       defaults.update( kwargs )
#
#       super( AVMTopLevelHierarchyField, self ).__init__( *args, **defaults )


class AVMSubjectCategoryField( models.ManyToManyField ):
    avm_category = "Content"
    avm_name = "Subject.Category"
    avm_help_text = _( "The type(s) of object or objects in the resource, or general subject matter of an image, taken from a controlled vocabulary taxonomy." )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'blank': True,
            'help_text': AVMSubjectCategoryField.avm_help_text,
            'verbose_name': _( "Subject Category" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': TaxonomyHierarchy } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( AVMSubjectCategoryField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSubjectCategoryField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSubjectNameField( models.ManyToManyField ):
    avm_category = "Content"
    avm_name = "Subject.Name"
    avm_help_text = _( "Proper names/catalog numbers for key objects/subjects in the image field." )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'blank': True,
            'help_text': AVMSubjectNameField.avm_help_text,
            'verbose_name': _( "Subject Name" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': SubjectName } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( AVMSubjectNameField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSubjectNameField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def value_to_string(self, *args, **kwargs):
        data = super(AVMSubjectNameField, self).value_to_string(self, *args, **kwargs)
        return data


class AVMDistanceField( models.CharField ):
    avm_category = "Content"
    avm_name = "Distance"
    avm_help_text = _( "The distance to the object, measured in light years (list element 1) and/or redshift (list element 2)." )

    def __init__( self, *args, **kwargs ):
        defaults = {
                    'max_length': 30,
                    'null': True,
                    'blank': True,
                    'verbose_name': _( "Distance" ),
                    'help_text': AVMDistanceField.avm_help_text,
                }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMDistanceField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMDistanceField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        defaults = { 'form_class': avmforms.DistanceField }
        defaults.update( kwargs )
        return super( AVMDistanceField, self ).formfield( **defaults )

    def from_internal(self, value ):
        if value:
            data_list = value.split(';')
            if len(data_list) > 0:
                data_list[0] = "" if data_list[0] == "-" else data_list[0]
            if len(data_list) > 1:
                data_list[1] = "" if data_list[1] == "-" else data_list[1]
            return data_list[:2]
        return []


class AVMDistanceLyField( models.DecimalField ):
    avm_category = "Content"
    avm_name = "Distance"
    avm_help_text = _( "The distance to the object, measured in light years." )

    def __init__( self, *args, **kwargs ):
        defaults = {
                    'null': True,
                    'blank': True,
                    'verbose_name': _( "Distance (in ly)" ),
                    'max_digits': 13,  # We dont need numbers larger than 50 billion with one decimal place.
                    'decimal_places': 1,
                    'help_text': AVMDistanceLyField.avm_help_text,
                }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMDistanceLyField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMDistanceLyField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMDistanceZField( models.DecimalField ):
    avm_category = "Content"
    avm_name = "Distance"
    avm_help_text = _( "The distance to the object, measured in redshift." )

    def __init__( self, *args, **kwargs ):
        defaults = {
                    'null': True,
                    'blank': True,
                    'max_digits': 5,  # We need numbers from 0 - XX.DDD
                    'decimal_places': 3,
                    'verbose_name': _( "Distance  (redshift)" ),
                    'help_text': AVMDistanceZField.avm_help_text,
                }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMDistanceZField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMDistanceZField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMDistanceNotesField( models.TextField ):
    avm_category = "Content"
    avm_name = "Distance.Notes"
    avm_help_text = _( "Comment about the contents of the Distance tag." )

    def __init__( self, *args, **kwargs ):
        defaults = {
                'null': True,
                'blank': True,
                'verbose_name': _( "Distance Notes" ),
                'help_text': AVMDistanceNotesField.avm_help_text,
                }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMDistanceNotesField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMDistanceNotesField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMCreditField( models.TextField ):
    avm_category = "Content"
    avm_name = "Credit"
    avm_help_text = _( "The minimum information that the Publisher would like to see mentioned when the resource is used." )
    default_credit = ''

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': False,
            'blank': True,
            'help_text': AVMCreditField.avm_help_text,
        }
        if 'default' in kwargs:
            self.default_credit = kwargs['default']

        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMCreditField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMCreditField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def value_from_object(self, obj):
        value = getattr(obj, self.attname)
        return value if value else self.default_credit


class AVMIdField( models.SlugField ):
    avm_category = "Content"
    avm_name = "ID"
    avm_help_text = _( "This is an identifier for the resource that is unique to the creator." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'primary_key': True,
            'help_text': AVMIdField.avm_help_text,
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMIdField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMIdField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMTypeField( models.CharField ):
    avm_category = "Content"
    avm_name = "Type"
    avm_help_text = _( "The type of image/media resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.TYPE_CHOICES,
            'max_length': 30,
            'null': True,
            'blank': True,
            'verbose_name': _( "Type" ),
            'help_text': AVMTypeField.avm_help_text,
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMTypeField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMTypeField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class FacilityManyToManyField( models.ManyToManyField ):
    """
    This field is not for use with an image model, since it does not ensure
    proper ordering of the facilities for each exposure. use FacilityField instead
    through the Exposure model.
    """
    avm_category = "Observation"
    avm_name = "Facility"
    avm_help_text = _( "Telescopes or observatories used for the observations." )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'blank': True,
            'help_text': FacilityManyToManyField.avm_help_text,
            'verbose_name': _( "Facility" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': Facility } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( FacilityManyToManyField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(FacilityManyToManyField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class InstrumentManyToManyField( models.ManyToManyField ):
    avm_category = "Observation"
    avm_name = "Facility"
    avm_name = "Instrument"
    avm_help_text = _( "Instrument used to collect the data. One Instrument entry per exposure." )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'blank': True,
            'help_text': InstrumentManyToManyField.avm_help_text,
            'verbose_name': _( "Instrument" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': Instrument } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( InstrumentManyToManyField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(InstrumentManyToManyField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMFacilityField( models.ForeignKey ):
    """
    Note: This fields should not be used with an image model. Use
    """
    avm_category = "Observation"
    avm_name = "Facility"
    avm_help_text = _( "Telescopes or observatories used for the observations." )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMFacilityField.avm_help_text,
            'verbose_name': _( "Facility" ),
            'on_delete': models.CASCADE
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': Facility } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( AVMFacilityField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFacilityField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMInstrumentField( models.ForeignKey ):
    """
    """
    avm_category = "Observation"
    avm_name = "Instrument"
    avm_help_text = _( "Instrument used to collect the data. One Instrument entry per exposure." )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMInstrumentField.avm_help_text,
            'verbose_name': _( "Instrument" ),
            'on_delete': models.CASCADE
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': Instrument } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( AVMInstrumentField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(AVMInstrumentField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpectralColorAssignmentField( models.CharField ):
    avm_category = "Observation"
    avm_name = "Spectral.ColorAssignment"
    avm_help_text = _( "The output color that is assigned to an exposure. One Spectral.ColorAssignment entry per exposure." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.SPECTRAL_COLOR_ASSIGNMENT_CHOICES,
            'max_length': 11,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMSpectralColorAssignmentField.avm_help_text,
            'verbose_name': _( "Spectral Color Assignment" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpectralColorAssignmentField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpectralColorAssignmentField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpectralBandField( models.CharField ):
    avm_category = "Observation"
    avm_name = "Spectral.Band"
    avm_help_text = _( "Waveband of the component exposure from a pre-defined list defining the general part of the spectrum covered. One Spectral.Band entry per exposure." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.SPECTRAL_BAND_CHOICES,
            'max_length': 11,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMSpectralBandField.avm_help_text,
            'verbose_name': _( "Spectral Band" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpectralBandField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpectralBandField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpectralBandpassField( models.CharField ):
    avm_category = "Observation"
    avm_name = "Spectral.Bandpass"
    avm_help_text = _( "Bandpass of the individual exposure. One Spectral.Bandpass entry per exposure." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMSpectralBandpassField.avm_help_text,
            'verbose_name': _( "Spectral Bandpass" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpectralBandpassField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpectralBandpassField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpectralCentralWavelengthField( AVMFloatField ):
    avm_category = "Observation"
    avm_name = "Spectral.CentralWavelength"
    avm_help_text = _( "Central wavelength of the filter used for the individual exposure measured in nanometers. One Spectral.CentralWavelength entry per exposure." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpectralCentralWavelengthField.avm_help_text,
            'verbose_name': _( "Spectral Central Wavelength" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpectralCentralWavelengthField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpectralCentralWavelengthField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpectralNotesField( models.TextField ):
    avm_category = "Observation"
    avm_name = "Spectral.Notes"
    avm_help_text = _( "Free-text field to allow for more detailed discussions of bandpasses and color mappings." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpectralNotesField.avm_help_text,
            'verbose_name': _( "Spectral Notes" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpectralNotesField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpectralNotesField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMTemporalStartTimeField( models.DateTimeField ):
    avm_category = "Observation"
    avm_name = "Temporal.StartTime"
    avm_help_text = _( "Start time of the exposure in ISO 8601 format 'yyyy-mm-ddThh:mm' (UT; time portion is optional). One Temporal.StartTime entry per exposure." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMTemporalStartTimeField.avm_help_text,
            'verbose_name': _( "Temporal Start Time" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMTemporalStartTimeField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMTemporalStartTimeField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMTemporalIntegrationTimeField( AVMFloatField ):
    avm_category = "Observation"
    avm_name = "Temporal.IntegrationTime"
    avm_help_text = _( "The exposure time in seconds. One Temporal.IntegrationTime entry per exposure." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMTemporalIntegrationTimeField.avm_help_text,
            'verbose_name': _( "Temporal Integration Time" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMTemporalIntegrationTimeField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMTemporalIntegrationTimeField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMDatasetIDField( models.CharField ):
    avm_category = "Observation"
    avm_name = "DatasetID"
    avm_help_text = _( "Identifier for the source FITS dataset for each exposure in the image. If available, this can be a VO-compliant reference to the dataset [ivo://AuthorityID/ResourceKey]. One DatasetID entry per exposure." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,
            'null': True,
            'blank': True,
            'help_text': AVMDatasetIDField.avm_help_text,
            'verbose_name': _( "Dataset ID" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMDatasetIDField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMDatasetIDField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpatialCoordinateFrameField( models.CharField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.CoordinateFrame"
    avm_help_text = _( "Coordinate system reference frame. Spatial.CoordinateFrame should be chosen from a pre-defined list." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.SPATIAL_COORDINATE_FRAME_CHOICES,
            'max_length': 4,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMSpatialCoordinateFrameField.avm_help_text,
            'verbose_name': _( "Coordinate Frame" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialCoordinateFrameField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialCoordinateFrameField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


# TODO: Field is actually not a CV field, but decimal number or an epoch (J2000/B1950)
class AVMSpatialEquinoxField( models.CharField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.Equinox"
    avm_help_text = _( "Equinox for Spatial.CoordinateFrame in decimal years." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.SPATIAL_EQUINOX_CHOICES,
            'max_length': 5,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMSpatialEquinoxField.avm_help_text,
            'verbose_name': _( "Equinox" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialEquinoxField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialEquinoxField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpatialReferenceValueField( AVMTwoFloatField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.ReferenceValue"
    avm_help_text = _( "Reference coordinates (RA and Dec) for the image (2 element list in decimal degrees)." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpatialReferenceValueField.avm_help_text,
            'verbose_name': _( "Reference Value" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialReferenceValueField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialReferenceValueField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        defaults = { 'form_class': avmforms.SpatialReferenceValueField }
        defaults.update( kwargs )
        return super( AVMSpatialReferenceValueField, self ).formfield( **defaults )


class AVMSpatialReferenceDimensionField( AVMTwoFloatField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.ReferenceDimension"
    avm_help_text = _( "Size of the image in pixels (2 element list)." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpatialReferenceDimensionField.avm_help_text,
            'verbose_name': _( "Reference Dimension" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialReferenceDimensionField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialReferenceDimensionField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        defaults = { 'form_class': avmforms.SpatialReferenceDimensionField }
        defaults.update( kwargs )
        return super( AVMSpatialReferenceDimensionField, self ).formfield( **defaults )


class AVMSpatialReferencePixelField( AVMTwoFloatField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.ReferencePixel"
    avm_help_text = _( "X,Y coordinates of the pixel in the image to which the reference coordinate (Spatial.ReferenceValue) refers (2 element list)." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpatialReferencePixelField.avm_help_text,
            'verbose_name': _( "Reference Pixel" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialReferencePixelField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialReferencePixelField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        defaults = { 'form_class': avmforms.SpatialReferencePixelField }
        defaults.update( kwargs )
        return super( AVMSpatialReferencePixelField, self ).formfield( **defaults )


class AVMSpatialScaleField( AVMTwoFloatField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.Scale"
    avm_help_text = _( "Spatial scale of the image in number of degrees/pixel (2 element list)." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpatialScaleField.avm_help_text,
            'verbose_name': _( "Scale" ),
            'max_length': 80,
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialScaleField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialScaleField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpatialRotationField( AVMFloatField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.Rotation"
    avm_help_text = _( "Position angle of the Y axis in degrees measured east from north." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpatialRotationField.avm_help_text,
            'verbose_name': _( "Rotation" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialRotationField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialRotationField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpatialCoordsystemProjectionField( models.CharField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.CoordsystemProjection"
    avm_help_text = _( "A combination of the coordinate system and the projection of the image." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.SPATIAL_COORDSYSTEM_PROJECTION_CHOICES,
            'max_length': 3,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMSpatialCoordsystemProjectionField.avm_help_text,
            'verbose_name': _( "Coordinate System Projection" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialCoordsystemProjectionField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialCoordsystemProjectionField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpatialQualityField( models.CharField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.Quality"
    avm_help_text = _( "This qualitatively describes the reliability of the spatial coordinate information in this metadata." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.SPATIAL_QUALITY_CHOICES,
            'max_length': 8,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMSpatialQualityField.avm_help_text,
            'verbose_name': _( "Quality" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialQualityField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialQualityField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpatialNotesField( models.TextField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.Notes"
    avm_help_text = _( "Free-text description to expand further on coordinates/geometry of image." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpatialNotesField.avm_help_text,
            'verbose_name': _( "Notes" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialNotesField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialNotesField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMSpatialFITSHeaderField( models.TextField ):
    avm_category = "Coordinate"
    avm_name = "Spatial.FITSheader"
    avm_help_text = _( "Free-text representation of the FITS header from which the AVM spatial tags were derived." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMSpatialFITSHeaderField.avm_help_text,
            'verbose_name': _( "FITS Header" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMSpatialFITSHeaderField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMSpatialFITSHeaderField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMPublisherField( models.CharField ):
    avm_category = "Publisher"
    avm_name = "Publisher"
    avm_help_text = _( "Publisher of the resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMPublisherField.avm_help_text,
            'verbose_name': _( "Publisher" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMPublisherField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMPublisherField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMPublisherIdField( models.CharField ):
    avm_category = "Publisher"
    avm_name = "PublisherID"
    avm_help_text = _( "ID of publisher registered as VAMP providers." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 255,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMPublisherIdField.avm_help_text,
            'verbose_name': _( "Publisher ID" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMPublisherIdField, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMPublisherIdField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

# TODO: related_resources


class AVMFileType( models.CharField ):
    avm_category = "File"
    avm_name = "Type"
    avm_help_text = _( "The format of the file. For images this would include TIFF, JPEG, PNG, GIF, PSD, PDF." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.FILE_TYPE_CHOICES,
            'max_length': 4,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMFileType.avm_help_text,
            'verbose_name': _( "File Type" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMFileType, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFileType, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMFileDimensionWidth( models.PositiveIntegerField ):
    avm_category = "File"
    avm_name = "Dimension"
    avm_help_text = _( "Width in pixels of the image resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMFileDimensionWidth.avm_help_text,
            'verbose_name': _( "Width" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMFileDimensionWidth, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFileDimensionWidth, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMFileDimensionHeight( models.PositiveIntegerField ):
    avm_category = "File"
    avm_name = "Dimension"
    avm_help_text = _( "Height in pixels of the image resource." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMFileDimensionHeight.avm_help_text,
            'verbose_name': _( "Height" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMFileDimensionHeight, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFileDimensionHeight, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMFileSize( models.PositiveIntegerField ):
    # Note: Limited to 4 TB file sizes (on MySQL - i.e unsigned integer.
    avm_category = "File"
    avm_name = "Size"
    avm_help_text = _( "Size of the image resource, measured in kilobytes." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'null': True,
            'blank': True,
            'help_text': AVMFileSize.avm_help_text,
            'verbose_name': _( "File Size" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMFileSize, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFileSize, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


#
# NON-AVM COMPLIANT FIELDS
#
class AVMFileDuration( models.CharField ):
    # TODO: Add validation
    avm_category = "File"
    avm_name = "Duration"
    avm_help_text = _( "The duration of the file in the format hh:mm:ss:frames." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'max_length': 13,
            'null': True,
            'blank': True,
            'help_text': AVMFileDuration.avm_help_text,
            'verbose_name': _( "File Duration" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMFileDuration, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFileDuration, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield( self, **kwargs ):
        defaults = { 'form_class': avmforms.DurationField }
        defaults.update( kwargs )
        return super( AVMFileDuration, self ).formfield( **defaults )


class AVMFileAspectRatio( models.CharField ):
    avm_category = "File"
    avm_name = "AspectRatio"
    avm_help_text = _( "The aspect ratio of the file." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.FILE_ASPECT_RAITO_CHOICES,
            'max_length': 10,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMFileAspectRatio.avm_help_text,
            'verbose_name': _( "File Aspect Ratio" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMFileAspectRatio, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMFileAspectRatio, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMAudioSurroundFormat( models.CharField ):
    avm_category = "Audio"
    avm_name = "SurroundFormat"
    avm_help_text = _( "The surround sound format of the audio." )

    def __init__( self, *args, **kwargs ):
        defaults = {
            'choices': consts.AUDIO_SURROUND_FORMAT_CHOICES,
            'max_length': 10,  # Length of longest word in CV.
            'null': True,
            'blank': True,
            'help_text': AVMAudioSurroundFormat.avm_help_text,
            'verbose_name': _( "Surround Sound Format" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )
        super( AVMAudioSurroundFormat, self ).__init__( *args, **defaults )
        self.my_default_keys = my_default_keys

    def deconstruct(self):
        name, path, args, kwargs = super(AVMAudioSurroundFormat, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


#
# TODO: AVM 1.2 extensions
#
class AVMPublicationField( models.ManyToManyField ):
    # TODO: AVM 1.2 extension
    avm_category = "Content"
    avm_name = "PublicationID"
    avm_help_text = _( "ADS Bibliographic Code" )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'blank': True,
            'help_text': AVMPublicationField.avm_help_text,
            'verbose_name': _( "Publication" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': Publication } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( AVMPublicationField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(AVMPublicationField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class AVMProposalIDField( models.ManyToManyField ):
    # TODO: AVM 1.2 extension
    avm_category = "Content"
    avm_name = "ProposalID"
    avm_help_text = ''  # _( "TODO" )

    def _field_init( self, *args, **kwargs ):
        defaults = {
            'blank': True,
            'help_text': AVMProposalIDField.avm_help_text,
            'verbose_name': _( "Observation Proposal/Program ID" ),
        }
        my_default_keys = list(defaults.keys())
        defaults.update( kwargs )

        if len( args ) == 0 and 'to' not in defaults:
            defaults.update( { 'to': ObservationProposal } )

        self.my_default_keys = my_default_keys
        return (args, defaults)

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( AVMProposalIDField, self ).__init__( *args, **defaults )

    def deconstruct(self):
        name, path, args, kwargs = super(AVMProposalIDField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs
