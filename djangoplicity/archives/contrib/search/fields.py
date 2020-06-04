# -*- coding: utf-8 -*-
#
# djangoplicity-archives
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
from __future__ import unicode_literals

from datetime import datetime
from django.db.models import F, Q
from django.db.utils import DatabaseError
from django.forms import fields, widgets
from django.http import Http404
from django.utils.translation import ugettext_lazy as _
from djangoplicity.archives.contrib.search.consts import ADV_SEARCH_START_YEAR, \
    IMAGE_DIMS, IMAGE_SIZES, LOGIC_REPR, PRIO_CHOICES, VALID_OPERATORS, \
    VIDEO_DIMS, VIDEO_SIZES, FOV_CHOICES
from djangoplicity.archives.contrib.search.widgets import LazySelectDateWidget
from djangoplicity.archives.contrib.search.utils import _get_facilities, \
    _get_instruments, _get_categories
from djangoplicity.metadata.consts import TYPE_CHOICES


class SearchField( fields.Field ):
    """
    Encapsulates a search object. Provides methods for:
    - getting a corresponding Q object
    - rendering the search form
    """

    model_field = ''
    value = None
    operator = 'icontains'
    help_text = ''
    logic_repr = {}

    def __init__( self, model_field='', help_text=None, *args, **kwargs ):
        if model_field:
            self.model_field = model_field

        if self.operator not in VALID_OPERATORS:
            raise Exception( "Invalid search operator. Valid choices are %s." % VALID_OPERATORS )

        kwargs['required'] = kwargs.get( 'required', False )

        if not help_text:
            help_text = self.help_text
        kwargs['help_text'] = help_text

        super( SearchField, self ).__init__( *args, **kwargs )

    def repr( self, value ):
        str = ''
        if value:
            str += self.logic_repr.get( self.operator, LOGIC_REPR.get( self.operator ) )
            str += " %s" % self._value_repr( value )
            return str
        else:
            return ''

    def _value_repr( self, value ):
        return "'%s'" % value

    def query( self, value=None, operator=None ):
        value = self.value if not value else value
        operator = self.operator if not operator else operator
        if value:
            if operator:
                kwargs = {self.model_field + '__' + operator: value}
            else:
                kwargs = {self.model_field: value}
            return Q( **kwargs )

        else:
            return Q()

    def render( self ):
        pass

    def is_separator( self ):
        return False


class IdSearchField( SearchField, fields.CharField ):
    """
    Handles single ID lookups
    """
    model_field = 'id'
    label = _( 'Id' )
    help_text = _( 'Show only items with ID containing this string. e.g. heic1017' )


class RelatedIdSearchField( SearchField, fields.CharField ):
    model_field = 'release_id'
    operator = 'icontains'
    help_text = _( 'Show only items containing references to Release IDs containing this string. e.g. heic1017' )
    label = _( 'Related ID' )


class TextSearchField( SearchField, fields.CharField ):
    model_field = 'title'
    operator = 'icontains'


class FileTypeSearchField():
    pass


class ImageSizeSearchField( SearchField, fields.ChoiceField ):
    operator = 'gte'

    def __init__( self, *args, **kwargs ):
        super( ImageSizeSearchField, self ).__init__( *args, **kwargs )
        self.choices = IMAGE_SIZES

    def query( self, value=None, operator=None ):
        value = self.value if not value else value
        if not value:
            return Q()

        x, y, n_pixels = IMAGE_DIMS.get( value, ( None, None, None ) )
        if not x:
            return Q()

        return Q(Q(width__gte=x) & Q(height__gte=y)) | \
            Q(Q(width__gte=y) & Q( height__gte=x)) | \
            Q(n_pixels__gte=n_pixels)

    def _value_repr( self, value ):
        for key, size in IMAGE_SIZES:
            if str( key ) == value:
                return "%s" % size

        return ''


class FOVSearchField(SearchField, fields.ChoiceField):
    operator = 'exact'

    def __init__(self, *args, **kwargs):
        super(FOVSearchField, self).__init__(*args, **kwargs)
        self.choices = FOV_CHOICES

    def query(self, value=None, operator=None):
        value = self.value if not value else value

        if not value:
            return Q()

        value = int(value)

        # We can't have F() on the left side of expressions, so we use
        # e.g. y = n - F(x) instead of F(x) + F(y) = n

        if value == 1:
            # Equivalent to -fov_x_l + fov_x_r = 360:
            return Q(fov_x_r=360 + F('fov_x_l'))

        if value == 2:
            # Equivalent to -fov_x_l + fov_x_r = 360:
            # and -fov_y_d + fov_y_u = 180
            return Q(
                Q(fov_x_r=360 + F('fov_x_l')) &
                Q(fov_y_u=180 + F('fov_y_d'))
            )

        if value == 3:
            # Equivalent to -fov_x_l + fov_x_r = 360:
            # and -fov_y_d + fov_y_u >= 90
            return Q(
                Q(fov_x_r=360 + F('fov_x_l')) &
                Q(fov_y_u__gte=90 + F('fov_y_d'))
            )

        if value == 4:
            # Equivalent to (-fov_x_l + fov_x_r >= 180) and
            # (-fov_x_l + fov_x_r < 270):
            return Q(
                Q(fov_x_r__gte=180 + F('fov_x_l')) &
                Q(fov_x_r__lt=270 + F('fov_x_l'))
            )

        if value == 5:
            # Equivalent to (-fov_x_l + fov_x_r >= 270) and
            # (-fov_x_l + fov_x_r < 360):
            return Q(
                Q(fov_x_r__gte=270 + F('fov_x_l')) &
                Q(fov_x_r__lt=360 + F('fov_x_l'))
            )

        return Q()

    def _value_repr(self, value):
        for key, size in FOV_CHOICES:
            try:
                if key == int(value):
                    return '%s' % size
            except ValueError:
                raise Http404

        return ''


class VideoSizeSearchField( SearchField, fields.ChoiceField ):
    operator = 'gte'

    def __init__( self, *args, **kwargs ):
        super( VideoSizeSearchField, self ).__init__( *args, **kwargs )
        self.choices = VIDEO_SIZES

    def query( self, value=None, operator=None ):
        value = self.value if not value else value
        if not value:
            return Q()

        x, y = VIDEO_DIMS.get( value, ( None, None ) )
        if not x:
            return Q()

        return Q( Q( width__gte=x ) & Q( height__gte=y ) ) | Q( Q( width__gte=y ) & Q( height__gte=x ) )

    def _value_repr( self, value ):
        for key, size in VIDEO_SIZES:
            if str( key ) == value:
                return "%s" % size

        return ''


class DateSearchField( SearchField, fields.DateField ):
    """
    Handles date searches
    Default behaviour is =, ie exact date
    """
    model_field = 'release_date'
    widget = LazySelectDateWidget( years=range( ADV_SEARCH_START_YEAR, datetime.now().year + 2 ) )

    def repr( self, value ):
        if value:
            return self._value_repr( value )


class DateSinceSearchField( DateSearchField ):
    operator = 'gte'


class DateUntilSearchField( DateSearchField ):
    operator = 'lte'


class MinimumValueSearchField( SearchField ):
    """
    Handles minimum values e.g. Priority
    """


class PrioritySearchField( SearchField, fields.ChoiceField ):
    operator = 'gte'
    model_field = 'priority'

    def __init__( self, *args, **kwargs ):
        super( PrioritySearchField, self ).__init__( *args, **kwargs )
        self.choices = PRIO_CHOICES

    def _value_repr( self, value ):
        for key, choice in self.choices:
            if value == str( key ):
                return unicode(choice)


class MultiSearchField( SearchField ):

    widget = widgets.CheckboxSelectMultiple

    def query( self, value=None, operator=None ):
        value = self.value if not value else value

        queries = Q()

        if not value:
            return queries

        for v in value:
            queries = queries | super( MultiSearchField, self ).query( value=v )

        return queries

    def _value_repr( self, value ):
        strs = []
        if value:
            for v in value:
                for key, choice in self.choices:
                    if v == str( key ):
                        strs.append( "'%s'" % choice )
            return " or ".join( strs )


class AVMTypeSearchField( MultiSearchField, fields.MultipleChoiceField ):
    """
    Handles multiple selections (checklists)
    """

    model_field = 'type'
    help_text = _( 'Leave unselected for all results.' )

    def __init__( self, *args, **kwargs ):
        super( AVMTypeSearchField, self ).__init__( *args, **kwargs )
        self.choices = TYPE_CHOICES


class AVMImageFacilitySearchField( MultiSearchField, fields.MultipleChoiceField ):
    model_field = 'imageexposure__facility'
    operator = 'exact'
    help_text = _( 'Leave unselected for all results.' )

    def _get_choices( self ):
        return _get_facilities()

    choices = property(_get_choices, fields.ChoiceField._set_choices)


class AVMFacilitySearchField( MultiSearchField, fields.MultipleChoiceField ):
    model_field = 'facility'
    operator = 'exact'
    help_text = _( 'Leave unselected for all results.' )

    def _get_choices( self):
        return _get_facilities()

    choices = property(_get_choices, fields.ChoiceField._set_choices)


class AVMImageInstrumentSearchField( MultiSearchField, fields.MultipleChoiceField ):
    model_field = 'imageexposure__instrument'
    operator = 'exact'
    help_text = _( 'Leave unselected for all results.' )

    def _get_choices( self):
        return _get_instruments()

    choices = property(_get_choices, fields.ChoiceField._set_choices)


class AVMSubjectCategorySearchField( MultiSearchField, fields.MultipleChoiceField ):
    model_field = 'subject_category__id'
    operator = 'exact'
    widget = widgets.SelectMultiple
    help_text = _( 'Hold Ctrl+click (Command+click on a Mac) for multiple selection.' )

    def _get_choices( self):
        return _get_categories()

    choices = property(_get_choices, fields.ChoiceField._set_choices)


class ManyToManySearchField( MultiSearchField, fields.MultipleChoiceField ):
    operator = 'exact'
    widget = widgets.SelectMultiple
    help_text = _( 'Hold Ctrl+click (Command+click on a Mac) for multiple selection.' )

    def _get_choices( self):
        try:
            return self.choices_func()
        except DatabaseError:
            return []

    choices = property(_get_choices, fields.ChoiceField._set_choices)

    def __init__( self, choices_func=lambda: [], *args, **kwargs ):
        super( ManyToManySearchField, self ).__init__( *args, **kwargs )
        self.choices_func = choices_func


class AVMSubjectNameSearchField( SearchField, fields.CharField ):
    model_field = ['subject_name__name', 'subject_name__alias']
    operator = 'icontains'
    help_text = _( 'e.g. M 31' )

    def query( self, value=None, operator=None ):
        result = Q()
        for my_model_field in self.model_field:
            result = result | SearchField(my_model_field).query(value=value)
        return result


class BooleanSearchField ( SearchField, fields. BooleanField ):
    operator = 'exact'

    def _value_repr( self, value ):
        if value:
            return "True"


class ChoiceSearchField( SearchField ):
    """
    Handles single selections (dropdown-box like)
    """

    model_field = 'type'


class SeparatorField( SearchField, fields.CharField ):
    def query( self, value=None, operator=None ):
        return Q()

    def is_separator( self ):
        return True
