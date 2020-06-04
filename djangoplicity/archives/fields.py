# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.db import models
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives.contrib import forms

import re

# Wrappers around existing Fields that sets default values and help text.

__all__ = (
    'IdField', 'PriorityField', 'TitleField', 'ReleaseDateTimeField',
    'DescriptionField', 'CreditField', 'ImageSizeField', 'PagesField',
    'PaperSizeField', 'IntField', 'EmailField', 'URLField', 'ChoiceField',
    'DurationField', 'TaskIdField',
)

# PRIORITY_CHOICES = (
#   ('0', _(u'Very High')),
#   ('1', _(u'High')),
#   ('2', _(u'Medium')),
#   ('3', _(u'Low')),
#   ('4', _(u'Very Low')),
# )


class IdField(models.SlugField):

    def __init__(self, *args, **kwargs):
        defaults = {
            'primary_key': True,
            'help_text': _('Ids are only allowed to contain letters, numbers, underscores or hyphens. They are used in URLs for the archive item.')
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(IdField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(IdField, self).deconstruct()
        # kwargs['primary_key'] = self.primary_key
        # kwargs['help_text'] = self.help_text
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    @staticmethod
    def get_valid_id(id):
        """
        Returns a string filtered of out all occurrences of non-letter, number, underscore or hyphen chars from given string 'id'
        """
        return re.sub(r"[^\w-]", "", id)


class PriorityField(models.PositiveSmallIntegerField):

    def __init__(self, *args, **kwargs):
        defaults = {
            #'choices': PRIORITY_CHOICES,
            'help_text': _(u'Priority of product (100 highest, 0 lowest) - high priority products are ranked higher in search results than low priority products.'),
            'db_index': True,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(PriorityField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(PriorityField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.PriorityField }
        defaults.update( kwargs )
        return super(PriorityField, self).formfield( **defaults )


class TitleField(models.CharField):
    """
    Field for storing a product title.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'max_length': 200,
            'help_text': _(u"Title is shown in browser window. Use a good informative title, since search engines normally display the title on their result pages."),
            'db_index': True,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(TitleField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(TitleField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class ReleaseDateTimeField(models.DateTimeField):
    """
    Field for storing a release date (either release, embargo or staging)
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'null': True,
            'db_index': True,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(ReleaseDateTimeField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(ReleaseDateTimeField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class DescriptionField(models.TextField):
    """
    Field for storing a textual description line.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'help_text': u'',
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(DescriptionField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(DescriptionField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class CreditField(models.TextField):
    """
    Field for storing a credit line.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'help_text': u'',
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(CreditField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(CreditField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class ImageSizeField(models.PositiveSmallIntegerField):
    """
    Field for representing width and height of an image.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'null': True,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(ImageSizeField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(ImageSizeField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class PaperSizeField(models.DecimalField):
    """
    Field for representing width and height of an image.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'null': True,
            'max_digits': 7,
            'decimal_places': 1,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(PaperSizeField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(PaperSizeField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class PagesField(models.PositiveSmallIntegerField):
    """
    Field for representing width and height of an image.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'null': True,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(PagesField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(PagesField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class IntField(models.PositiveIntegerField):
    """
    Field for representing width and height of an image.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'null': True,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(IntField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(IntField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class DurationField(models.PositiveIntegerField):
    """
    Field for representing duration of a piece (audio, video, etc) in seconds.
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'null': True,
            'help_text': u'Duration of audio/video in seconds',
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(DurationField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(DurationField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class EmailField(models.EmailField):
    """
    Field for storing an E-mail address
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
            'help_text': u'',
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(EmailField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(EmailField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class URLField(models.URLField):
    """
    Field for storing a valid URL
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'blank': True,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(URLField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(URLField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class ChoiceField(models.PositiveSmallIntegerField):

    def __init__(self, *args, **kwargs):
        defaults = {
            'choices': None,
            'help_text': _(u'Choice.'),
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(ChoiceField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(ChoiceField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs


class TaskIdField(models.CharField):
    """
    Field for storing any associated task id
    """
    def __init__(self, *args, **kwargs):
        defaults = {
            'max_length': 40,
        }
        self.my_default_keys = defaults.keys()
        defaults.update( kwargs )
        super(TaskIdField, self).__init__(*args, **defaults)

    def deconstruct(self):
        name, path, args, kwargs = super(TaskIdField, self).deconstruct()
        for key in self.my_default_keys:
            kwargs[key] = getattr(self, key)
        return name, path, args, kwargs
