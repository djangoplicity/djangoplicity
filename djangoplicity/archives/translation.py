# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from builtins import object
from django.core.exceptions import ValidationError, ObjectDoesNotExist


class TranslationProxyMixin( object ):
    """
    Mixin for cleaning/validating the id of translated archive items.
    """
    def id_clean(self):
        """ Determine id of translation """
        self._is_existing_translation = True

        # Determine if source exists.
        if self.source is None:
            raise ValidationError("You must provide a translation source.")

        # Serbian Latin is using code sr-Latn, but though we use the full
        # code the lang field we just use 'sr' to keep the IDs simple
        lang = 'sr' if self.lang == 'sr-latn' else self.lang

        # Determine PK if translation is new.
        if not self.pk:
            self._is_existing_translation = False
            self.pk = "%s-%s" % ( self.source.pk, lang )
        else:
            # Check if id matches source and lang
            if self.pk != "%s-%s" % ( self.source.pk, lang ):
                pass  # TODO: It doesn't so change it yourself.
                #old_obj = ReleaseProxy.objects.get( id=self.pk )

        super( self.__class__, self ).clean()

    def id_validate_unique( self, exclude=None ):
        """ Validate that translation language is *not* identical to source language. """
        try:
            if not hasattr( self, '_is_existing_translation' ):
                self._is_existing_translation = True
            if not self._is_existing_translation:
                # Serbian Latin is using code sr-Latn, but though we use the full
                # code the lang field we just use 'sr' to keep the IDs simple
                lang = 'sr' if self.lang == 'sr-latn' else self.lang

                self.__class__.objects.filter( source=self.source.pk, lang=lang ).get()
                raise ValidationError( { 'lang': ["Translation already exists for selected language."] } )
        except ObjectDoesNotExist:
            pass

        super( self.__class__, self ).validate_unique( exclude=exclude )
