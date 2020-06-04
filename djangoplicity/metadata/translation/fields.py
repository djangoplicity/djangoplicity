# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

"""
The AVM fields that is based on ForeignKey and ManyToManyField does not work well with
translation models. Hence, these fields extends the fields to behave properly with
translated models.
"""

from djangoplicity.metadata.archives.fields import AVMSubjectCategoryField, \
    AVMSubjectNameField, AVMFacilityField, AVMInstrumentField, AVMProposalIDField, \
    AVMPublicationField, FacilityManyToManyField, InstrumentManyToManyField
from djangoplicity.translation.fields import TranslationManyToManyField, \
    TranslationForeignKey


class TranslationAVMSubjectCategoryField( TranslationManyToManyField, AVMSubjectCategoryField ):
    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationAVMSubjectCategoryField, self ).__init__( *args, **defaults )


class TranslationAVMSubjectNameField( TranslationManyToManyField, AVMSubjectNameField ):
    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationAVMSubjectNameField, self ).__init__( *args, **defaults )


class TranslationFacilityManyToManyField( TranslationManyToManyField, FacilityManyToManyField ):
    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationFacilityManyToManyField, self ).__init__( *args, **defaults )


class TranslationAVMFacilityField( TranslationForeignKey, AVMFacilityField ):
    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationAVMFacilityField, self ).__init__( *args, **defaults )


class TranslationInstrumentManyToManyField( TranslationManyToManyField, InstrumentManyToManyField ):
    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationInstrumentManyToManyField, self ).__init__( *args, **defaults )


class TranslationAVMInstrumentField( TranslationForeignKey, AVMInstrumentField ):

    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationAVMInstrumentField, self ).__init__( *args, **defaults )


#
# TODO: AVM 1.2 extensions
#

class TranslationAVMPublicationField( TranslationManyToManyField, AVMPublicationField ):
    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationAVMPublicationField, self ).__init__( *args, **defaults )


class TranslationAVMProposalIDField( TranslationManyToManyField, AVMProposalIDField ):
    def __init__( self, *args, **kwargs ):
        args, defaults = self._field_init( *args, **kwargs )
        super( TranslationAVMProposalIDField, self ).__init__( *args, **defaults )
