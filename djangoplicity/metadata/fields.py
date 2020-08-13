from past.builtins import basestring
from avm import forms as avmforms
from avm.consts import *
from django import forms
from django.core import exceptions
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode


###
# Abstract AVM Fields
###

class AVMField( models.Field ):
    """
    Generic AVM fields
    """

    def to_xmp( self, value ):
        """
        Hook to return a Python object appropriate for the Python AVM Library.

        It should be implemented by subclasses of AVMField.
        """
        raise NotImplementedError('Subclasses must implement this method.')


class AVMStringField( AVMField ):
    """
    AVM String Field

    :Inherits: AVMField
    """
    def get_internal_type(self):
        return "CharField"

    def to_python(self, value):
        if isinstance(value, basestring):
            return value
        if value is None:
            if self.null:
                return value
            else:
                raise exceptions.ValidationError(
                    _("This field cannot be null."))
        return smart_unicode(value)

    def to_xmp(self, value):
        if value:
            return value

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length, 'form_class': forms.CharField }
        defaults.update(kwargs)
        return super(AVMStringField, self).formfield(**defaults)


class AVMURLField( models.URLField, AVMStringField ):
    """
    AVM URL Field
    """
    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length, 'form_class': avmforms.URLField }
        defaults.update(kwargs)
        return super(AVMURLField, self).formfield(**defaults)


class AVMEmailField( models.EmailField, AVMStringField ):
    """
    AVM Email Field
    """

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length, 'form_class': avmforms.EmailField }
        defaults.update(kwargs)
        return super(AVMEmailField, self).formfield(**defaults)


class AVMTextField( models.TextField, AVMField ):
    """
    AVMTextField
    """
    def to_xmp(self, value):
        if value:
            return value

    def formfield(self, **kwargs):
        defaults = {'widget': avmforms.TextField}
        defaults.update(kwargs)
        return super(AVMTextField, self).formfield(**defaults)


class AVMFloatField( AVMStringField ):
    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            'regex': r'^\s*(\d*.?\d*)\s*$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _(u'Enter a number.'),
            }
        }
        defaults.update(kwargs)
        return super(AVMFloatField, self).formfield(**defaults)


class AVMTwoFloatField( AVMStringField ):

    def to_xmp(self, value):
        """ Needs work"""
        if value:
            data_list = value.split(';')

            return data_list

    def formfield(self, **kwargs):
        defaults = { 'form_class': avmforms.TwoItemFloatField }
        defaults.update(kwargs)
        return super(AVMTwoFloatField, self).formfield(**defaults)


class AVMFourFloatField( AVMTwoFloatField ):

    def formfield(self, **kwargs):
        defaults = { 'form_class': avmforms.FourItemFloatField }
        defaults.update(kwargs)
        return super(AVMFourFloatField, self).formfield(**defaults)


class SemicolonSeparatedStringField(models.CharField, AVMStringField):

    def to_xmp(self, value):
        if value:
            xmp_list = []
            data = value.split(';')
            for item in data:
                item = item.strip()
                if len(item) != 0:
                    xmp_list.append(item)

            return xmp_list

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            'regex': r'^[\a-zA-Z0-9_\-\s;]+$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _(u'Enter only alphanumeric characters separated by semicolons.'),
            }
        }
        defaults.update(kwargs)
        return super(SemicolonSeparatedStringField, self).formfield(**defaults)


class SemicolonSeparatedFloatField( SemicolonSeparatedStringField ):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            'regex': r'^\s*(\d*.?\d*)\s*(;\s*\d*.?\d*\s*)*;?$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _(u'Enter only numbers separated by semicolons.'),
            }
        }
        defaults.update(kwargs)
        return super(SemicolonSeparatedFloatField, self).formfield(**defaults)


class SemicolonSeparatedDateTimeField( SemicolonSeparatedStringField ):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            'regex': r'^\s*(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\s*(;\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})*;?$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _(u'Enter datetime values in the format yyyy-mm-ddThh:mm:ss separated by semicolons.'),
            }
        }
        defaults.update(kwargs)
        return super(SemicolonSeparatedDateTimeField, self).formfield(**defaults)


class AVMDateField( models.DateField, AVMField ):

    def to_xmp(self, value):
        """ Need to find out the returned type"""
        if value:
            return value

    def formfield(self, **kwargs):
        defaults = {'form_class': avmforms.DateField}
        defaults.update(kwargs)
        return super(AVMDateField, self).formfield(**defaults)


###
# Specific AVM Fields
###

#
# Creator Fields
#
class CreatorField( AVMStringField ):
    def __init__(self, *args, **kwargs):
        self.avm_category = "Creator"
        self.avm_name = "Creator"
        super(CreatorField, self).__init__(
                                       max_length=50,
                                       null=True,
                                       blank=True,
                                       verbose_name="Creator",
                                       help_text="Original creator of the resource at the organizational level."
                                           )


class CreatorURLField( AVMURLField ):
    def __init__(self, *args, **kwargs):
        self.avm_category = "Creator"
        self.avm_name = "CreatorURL"
        super(CreatorURLField, self).__init__(
                                          max_length=50,
                                          null=True,
                                          blank=True,
                                          verbose_name="Creator URL",
                                          help_text="A simple URL pointing to the (top level) outreach webpage for the original creator."
                                              )


class ContactNameField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.Name"
        super(ContactNameField, self).__init__(
                                           max_length=50,
                                           null=True,
                                           blank=True,
                                           verbose_name="Contact Name",
                                           help_text="Name(s) of the primary contact(s) for the resource."
                                               )


class ContactEmailField( AVMEmailField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.Email"
        super(ContactEmailField, self).__init__(
                                            max_length=50,
                                            null=True,
                                            blank=True,
                                            verbose_name="Contact Email",
                                            help_text="Email(s) of the primary contact(s) for the resource.")


class ContactTelephoneField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.Telephone"
        super(ContactTelephoneField, self).__init__(
                                                max_length=50,
                                                null=True,
                                                blank=True,
                                                verbose_name="Contact Telephone",
                                                help_text="Phone number of the primary contact(s) for the resource.")


class ContactAddressField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.Address"
        super(ContactAddressField, self).__init__(
                                              max_length=150,
                                              null=True,
                                              blank=True,
                                              verbose_name="Contact Address",
                                              help_text="Street address of the primary contact for the resource.")


class ContactCityField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.City"
        super(ContactCityField, self).__init__(
                                           max_length=100,
                                           null=True,
                                           blank=True,
                                           verbose_name="Contact City",
                                           help_text="City of the primary contact for the resource.")


class ContactStateProvinceField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.StateProvince"
        super(ContactStateProvinceField, self).__init__(
                                                    max_length=100,
                                                    null=True,
                                                    blank=True,
                                                    verbose_name="Contact State/Province",
                                                    help_text="State or province of the primary contact for the resource.")


class ContactPostalCodeField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.PostalCode"
        super(ContactPostalCodeField, self).__init__(
                                                 max_length=50,
                                                 null=True,
                                                 blank=True,
                                                 verbose_name="Contact Postalcode",
                                                 help_text="Zip or postal code of the primary contact for the resource.")


class ContactCountryField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Contact.Country"
        super(ContactCountryField, self).__init__(
                                              max_length=100,
                                              null=True,
                                              blank=True,
                                              verbose_name="Contact Country",
                                              help_text="Country of the primary contact for the resource.")


class RightsField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Creator"
        self.avm_name = "Rights"
        super(RightsField, self).__init__(
                                      max_length=100,
                                      null=True,
                                      blank=True,
                                      verbose_name="Rights",
                                      help_text="Copyright and related intellectual property rights description.")


#
# Content Fields
#

class TitleField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Title"
        super(TitleField, self).__init__(
                                     max_length=100,
                                     null=True,
                                     blank=True,
                                     verbose_name="Title",
                                     help_text="General descriptive title given to the image resource.")


class HeadlineField( AVMTextField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Headline"
        super(HeadlineField, self).__init__(
                                        null=True,
                                        blank=True,
                                        verbose_name="Headline",
                                        help_text="Short description of the full caption.")


class DescriptionField( AVMTextField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Description"
        super(DescriptionField, self).__init__(
                                           null=True,
                                           blank=True,
                                           verbose_name="Description",
                                           help_text="Full caption and related description text for the image resource.")


class SubjectCategoryField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Subject.Category"
        super(SubjectCategoryField, self).__init__(
                                               max_length=100,
                                               null=True,
                                               blank=True,
                                               verbose_name="Subject Category",
                                               help_text="The type(s) of object or objects in the resource, or general subject matter of an image, taken from a controlled vocabulary taxonomy.")

    def to_xmp(self, value):
        if value:
            data_list = value.split(';')
            return data_list

    def formfield(self, **kwargs):
        defaults = {
            'form_class': avmforms.SubjectCategoryField,
            'max_length': self.max_length,
        }
        defaults.update(kwargs)
        return super(AVMStringField, self).formfield(**defaults)


class SubjectNameField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Subject.Name"
        super(SubjectNameField, self).__init__(
                                           max_length=100,
                                           null=True,
                                           blank=True,
                                           verbose_name="Subject Name",
                                           help_text="Proper names/catalog numbers for key objects/subjects in the image field."
       )


class DistanceField( AVMTwoFloatField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Distance"
        super( DistanceField, self ).__init__(
                                          max_length=30,
                                          null=True,
                                          blank=True,
                                          verbose_name="Distance",
                                          help_text="The distance to the object, measured in light years (list element 1) and/or redshift (list element 2)."
                                          )

    def to_xmp(self, value):
        """ Needs work"""
        if value:
            data_list = value.split(';')
            avm_list = []
            for item in data_list:
                if item == '-':
                    avm_list.append(item)
                if item == '':
                    pass
                else:
                    item = item
                    avm_list.append(item)

            return avm_list

    def formfield(self, **kwargs):
        defaults = { 'form_class': avmforms.DistanceField }
        defaults.update(kwargs)
        return super(DistanceField, self).formfield(**defaults)


class DistanceNotesField( AVMTextField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Distance.Notes"
        super(DistanceNotesField, self).__init__(
                                             null=True,
                                             blank=True,
                                             verbose_name="Distance Notes",
                                             help_text="Comment about the contents of the Distance tag."
                                                 )


class ReferenceURLField( AVMURLField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "ReferenceURL"
        super(ReferenceURLField, self).__init__(
                                            null=True,
                                            blank=True,
                                            verbose_name="Reference URL",
                                            help_text="Webpage containing more information about this specific image."
                                                )


class CreditField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Credit"
        super(CreditField, self).__init__(
                                      max_length=300,
                                      null=True,
                                      blank=True,
                                      verbose_name="Credit",
                                      help_text="The minimum information that the Publisher would like to see mentioned when the resource is used."
                                          )


class DateField( AVMDateField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Date"
        super(DateField, self).__init__(
                                    max_length=50,
                                    null=True,
                                    blank=True,
                                    verbose_name="Date",
                                    help_text="Date that the resource was created or made available."
                                        )


class IDField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "ID"
        super(IDField, self).__init__(
                                  max_length=50,
                                  null=True,
                                  blank=True,
                                  verbose_name="ID",
                                  help_text="This is an identifier for the resource that is unique to the creator."
                                      )


class TypeField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Type"
        super(TypeField, self).__init__(
                                    choices=TYPE_CHOICES,
                                    max_length=12,
                                    null=True,
                                    blank=True,
                                    verbose_name="Type",
                                    help_text="The type of image/media resource."
                                        )


class ImageProductQualityField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Content"
        self.avm_name = "Image.ProductQuality"
        super(ImageProductQualityField, self).__init__(
                                                   choices=IMAGE_PRODUCT_QUALITY_CHOICES,
                                                   max_length=8,
                                                   null=True,
                                                   blank=True,
                                                   verbose_name="Image Product Quality",
                                                   help_text="Qualitative image quality assessment."
                                                       )


#
# Observation Fields
#

class FacilityField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Facility"
        super(FacilityField, self).__init__(
                                        max_length=150,
                                        null=True,
                                        blank=True,
                                        verbose_name="Facility",
                                        help_text="Telescopes or observatories used for the observations."
                                            )


class InstrumentField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Instrument"
        super(InstrumentField, self).__init__(
                                          max_length=150,
                                          null=True,
                                          blank=True,
                                          verbose_name="Instrument",
                                          help_text="Instrument used to collect the data. One Instrument entry per exposure."
                                              )


class SpectralColorAssignmentField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Spectral.ColorAssignment"
        super(SpectralColorAssignmentField, self).__init__(
                                                       max_length=150,
                                                       null=True,
                                                       blank=True,
                                                       verbose_name="Spectral Color Assignment",
                                                       help_text="The output color that is assigned to an exposure. One Spectral.ColorAssignment entry per exposure."
                                                           )

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            'regex': r'^\s*(Purple|Blue|Cyan|Green|Yellow|Orange|Red|Magenta|Grayscale|Pseudocolor)\s*(;\s*(Purple|Blue|Cyan|Green|Yellow|Orange|Red|Magenta|Grayscale|Pseudocolor)\s*)*;?$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _(u'Enter only values from the controlled vocabulary: Purple, Blue, Cyan, Green, Yellow, Orange, Red, Magenta, Grayscale, Pseudocolor'),
            }
        }
        defaults.update(kwargs)
        return super(SemicolonSeparatedStringField, self).formfield(**defaults)


class SpectralBandField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Spectral.Band"
        super(SpectralBandField, self).__init__(
                                            max_length=150,
                                            null=True,
                                            blank=True,
                                            verbose_name="Spectral Band",
                                            help_text="Waveband of the component exposure from a pre-defined list defining the general part of the spectrum covered. One Spectral.Band entry per exposure."
                                                )

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.RegexField,
            'regex': r'^\s*(Radio|Millimeter|Infrared|Optical|Ultraviolet|X-ray|Gamma-ray)\s*(;\s*(Radio|Millimeter|Infrared|Optical|Ultraviolet|X-ray|Gamma-ray)\s*)*;?$',
            'max_length': self.max_length,
            'error_messages': {
                'invalid': _(u'Enter only values from the controlled vocabulary: Radio, Millimeter, Infrared, Optical, Ultraviolet, X-ray, Gamma-ray'),
            }
        }
        defaults.update(kwargs)
        return super(SemicolonSeparatedStringField, self).formfield(**defaults)


class SpectralBandpassField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Spectral.Bandpass"
        super(SpectralBandpassField, self).__init__(
                                                max_length=150,
                                                null=True,
                                                blank=True,
                                                verbose_name="Spectral Bandpass",
                                                help_text="Bandpass of the individual exposure. One Spectral.Bandpass entry per exposure."
                                                    )


class SpectralCentralWavelengthField( SemicolonSeparatedFloatField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Spectral.CentralWavelength"
        super(SpectralCentralWavelengthField, self).__init__(
                                                         max_length=150,
                                                         null=True,
                                                         blank=True,
                                                         verbose_name="Spectral Central Wavelength",
                                                         help_text="Central wavelength of the filter used for the individual exposure measured in nanometers. One Spectral.CentralWavelength entry per exposure."
                                                             )


class SpectralNotesField( AVMTextField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Spectral.Notes"
        super(SpectralNotesField, self).__init__(
                                             null=True,
                                             blank=True,
                                             verbose_name="Spectral Notes",
                                             help_text="Free-text field to allow for more detailed discussions of bandpasses and color mappings."
                                                 )


class TemporalStartTimeField( SemicolonSeparatedDateTimeField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Temporal.StartTime"
        super(TemporalStartTimeField, self).__init__(
                                                 max_length=150,
                                                 null=True,
                                                 blank=True,
                                                 verbose_name="Temporal Start Time",
                                                 help_text="Start time of the exposure in ISO 8601 format 'yyyy-mm-ddThh:mm' (UT; time portion is optional). One Temporal.StartTime entry per exposure."
                                                     )


class TemporalIntegrationTimeField( SemicolonSeparatedFloatField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "Temporal.IntegrationTime"
        super(TemporalIntegrationTimeField, self).__init__(
                                                       max_length=150,
                                                       null=True,
                                                       blank=True,
                                                       verbose_name="Temporal Integration Time",
                                                       help_text="The exposure time in seconds. One Temporal.IntegrationTime entry per exposure."
                                                           )


class DatasetIDField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Observation"
        self.avm_name = "DatasetID"
        super(DatasetIDField, self).__init__(
                                         max_length=150,
                                         null=True,
                                         blank=True,
                                         verbose_name="Dataset ID",
                                         help_text="Identifier for the source FITS dataset for each exposure in the image. If available, this can be a VO-compliant reference to the dataset [ivo://AuthorityID/ResourceKey]. One DatasetID entry per exposure."
                                             )


#
# Coordinate Fields
#

class SpatialCoordinateFrameField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.CoordinateFrame"
        super(SpatialCoordinateFrameField, self).__init__(
                                                      max_length=4,
                                                      choices=SPATIAL_COORDINATE_FRAME_CHOICES,
                                                      null=True,
                                                      blank=True,
                                                      verbose_name="Spatial Coordinate Frame",
                                                      help_text="Coordinate system reference frame. Spatial.CoordinateFrame should be chosen from a pre-defined list."
                                                          )


class SpatialEquinoxField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.Equinox"
        super(SpatialEquinoxField, self).__init__(
                                              max_length=5,
                                              choices=SPATIAL_EQUINOX_CHOICES,
                                              null=True,
                                              blank=True,
                                              verbose_name="Spatial Equinox",
                                              help_text="Equinox for Spatial.CoordinateFrame in decimal years."
                                                  )


class SpatialReferenceValueField( AVMTwoFloatField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.ReferenceValue"
        super(SpatialReferenceValueField, self).__init__(
                                                     max_length=50,
                                                     null=True,
                                                     blank=True,
                                                     verbose_name="Spatial Reference Value",
                                                     help_text="Reference coordinates (RA and Dec) for the image (2 element list in decimal degrees)."
                                                         )


class SpatialReferenceDimensionField( AVMTwoFloatField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.ReferenceDimension"
        super(SpatialReferenceDimensionField, self).__init__(
                                                         max_length=50,
                                                         null=True,
                                                         blank=True,
                                                         verbose_name="Spatial Reference Dimension",
                                                         help_text="Size of the image in pixels (2 element list)."
                                                             )


class SpatialReferencePixelField( AVMTwoFloatField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.ReferencePixel"
        super(SpatialReferencePixelField, self).__init__(
                                                     max_length=50,
                                                     null=True,
                                                     blank=True,
                                                     verbose_name="Spatial Reference Pixel",
                                                     help_text="X,Y coordinates of the pixel in the image to which the reference coordinate (Spatial.ReferenceValue) refers (2 element list)."
                                                         )


class SpatialScaleField( AVMTwoFloatField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.Scale"
        super(SpatialScaleField, self).__init__(
                                            max_length=50,
                                            null=True,
                                            blank=True,
                                            verbose_name="Spatial Scale",
                                            help_text="Spatial scale of the image in number of degrees/pixel (2 element list)."
                                                )


class SpatialRotationField( AVMFloatField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.Rotation"
        super(SpatialRotationField, self).__init__(
                                               max_length=50,
                                               blank=True,
                                               null=True,
                                               verbose_name="Spatial Rotation",
                                               help_text="Position angle of the Y axis in degrees measured east from north."
                                                   )


class SpatialCoordsystemProjectionField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.CoordsystemProjection"
        super(SpatialCoordsystemProjectionField, self).__init__(
                                                            max_length=3,
                                                            null=True,
                                                            choices=SPATIAL_COORDSYSTEM_PROJECTION_CHOICES,
                                                            blank=True,
                                                            verbose_name="Spatial Coordsystem Projection",
                                                            help_text="A combination of the coordinate system and the projection of the image."
                                                                )


class SpatialQualityField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.Quality"
        super(SpatialQualityField, self).__init__(
                                              max_length=8,
                                              null=True,
                                              blank=True,
                                              choices=SPATIAL_QUALITY_CHOICES,
                                              verbose_name="Spatial Quality",
                                              help_text="This qualitatively describes the reliability of the spatial coordinate information in this metadata."
                                                  )


class SpatialNotesField( AVMTextField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.Notes"
        super(SpatialNotesField, self).__init__(
                                            null=True,
                                            blank=True,
                                            verbose_name="Spatial Notes",
                                            help_text="Free-text description to expand further on coordinates/geometry of image."
                                                )


class SpatialFITSHeaderField( AVMTextField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.FITSheader"
        super(SpatialFITSHeaderField, self).__init__(
                                                 null=True,
                                                 blank=True,
                                                 verbose_name="Spatial FITS Header",
                                                 help_text="Free-text representation of the FITS header from which the AVM spatial tags were derived."
                                                     )


class SpatialCDMatrixField( AVMFourFloatField ):
    def __init__(self):
        self.avm_category = "Coordinate"
        self.avm_name = "Spatial.CDMatrix"
        super(SpatialCDMatrixField, self).__init__(
                                               max_length=100,
                                               null=True,
                                               blank=True,
                                               verbose_name="Spatial CD Matrix",
                                               help_text="Matrix representation of scale/rotation terms.  Deprecated since 1.0"
                                                   )


#
# Publisher Fields
#

class PublisherField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Publisher"
        self.avm_name = "Publisher"
        super(PublisherField, self).__init__(
                                         max_length=50,
                                         null=True,
                                         blank=True,
                                         verbose_name="Publisher",
                                         help_text="Publisher of the resource."
                                             )


class PublisherIDField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Publisher"
        self.avm_name = "PublisherID"
        super(PublisherIDField, self).__init__(
                                           max_length=50,
                                           null=True,
                                           blank=True,
                                           verbose_name="Publisher ID",
                                           help_text="ID of publisher registered as VAMP providers."
                                               )


class ResourceIDField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Publisher"
        self.avm_name = "ResourceID"
        super(ResourceIDField, self).__init__(
                                          max_length=50,
                                          null=True,
                                          blank=True,
                                          verbose_name="Resource ID",
                                          help_text="This identifies a specific 'instance' of a resource; e.g. one image in one file format at one resolution. This allows the same resource (image) to be offered in different formats and resolutions. Together with the PublisherID, each registered resource is uniquely identified in the database."
                                              )


class ResourceURLField( AVMURLField ):
    def __init__(self):
        self.avm_category = "Publisher"
        self.avm_name = "ResourceURL"
        super(ResourceURLField, self).__init__(
                                           null=True,
                                           blank=True,
                                           verbose_name="Resource URL",
                                           help_text="A unique URL pointing to the specific online image/image archive is needed to identify where to obtain the image. Each ResourceID is paired with a matching ResourceURL."
                                               )


class RelatedResourcesField( SemicolonSeparatedStringField ):
    def __init__(self):
        self.avm_category = "Publisher"
        self.avm_name = "RelatedResources"
        super(RelatedResourcesField, self).__init__(
                                                max_length=50,
                                                null=True,
                                                blank=True,
                                                verbose_name="Related Resources",
                                                help_text="The format is a list of PublisherID/ID values that will reference specific resources registered in VAMP (though not specific 'instances')."
                                                    )


class MetadataDateField( AVMDateField ):
    def __init__(self):
        self.avm_category = "Publisher"
        self.avm_name = "MetadataDate"
        super(MetadataDateField, self).__init__(
                                            max_length=50,
                                            null=True,
                                            blank=True,
                                            verbose_name="Metadata Date",
                                            help_text="The date of the metadata content for the image.",
                                                )


class MetadataVersionField( AVMStringField ):
    def __init__(self):
        self.avm_category = "Publisher"
        self.avm_name = "MetadataVersion"
        super(MetadataVersionField, self).__init__(
                                               max_length=3,
                                               choices=METADATA_VERSION_CHOICES,
                                               null=True,
                                               blank=True,
                                               verbose_name="Metadata Version",
                                               help_text="This is the version of the applied metadata definition."
                                                   )


class MetadataCompletenessField( models.CharField ):
    def __init__(self, *args, **kwargs):
        super(MetadataCompletenessField, self).__init__(
                                                    max_length=4,
        )


class MetadataValidityField( models.BooleanField ):
    def __init__(self, *args, **kwargs):
        super(MetadataValidityField, self).__init__(
                                                blank=True,
                                                null=True,
                                                *args,
                                                **kwargs
        )
