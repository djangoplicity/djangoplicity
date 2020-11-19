# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.forms import widgets
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


class LabeledTextInput( widgets.TextInput ):
    """
    A single input box with a label behind the field, to designate e.g
    the required unit for the field.
    """
    def __init__( self, label=None, attrs=None ):
        self.label = label
        super( LabeledTextInput, self ).__init__( attrs=attrs )

    def render( self, name, value, attrs=None, renderer=None):
        output = super( LabeledTextInput, self ).render( name, value, attrs=attrs )

        if self.label:
            return mark_safe( u"%s %s" % ( output, _( self.label ) ) )
        else:
            return output


class TwoItemFloatWidget( widgets.MultiWidget ):
    def __init__( self, attrs=None, label1=None, label2=None, joinlabel=None ):
        self.joinlabel = joinlabel

        multi_widget = (
            LabeledTextInput( label=label1, attrs=attrs ),
            LabeledTextInput( label=label2, attrs=attrs )
                )
        super( TwoItemFloatWidget, self ).__init__( multi_widget, attrs )

    def format_output( self, rendered_widgets ):
        if self.joinlabel:
            return ( u'&nbsp;%s&nbsp;' % self.joinlabel ).join( rendered_widgets )
        else:
            return u'&nbsp;&nbsp;&nbsp;'.join( rendered_widgets )

    def decompress( self, value ):
        if value:
            return value.split( ';' )
        return [None, None]


class FourItemFloatWidget( widgets.MultiWidget ):
    def __init__( self, attrs=None, label1=None, label2=None, label3=None, label4=None ):
        multi_widget = (
            LabeledTextInput( label=label1, attrs=attrs ),
            LabeledTextInput( label=label2, attrs=attrs ),
            LabeledTextInput( label=label3, attrs=attrs ),
            LabeledTextInput( label=label4, attrs=attrs ),
                )
        super( FourItemFloatWidget, self ).__init__( multi_widget, attrs )

    def format_output( self, rendered_widgets ):
        return u'&nbsp;&nbsp;&nbsp;'.join( rendered_widgets )

    def decompress( self, value ):
        if value:
            return value.split( ';' )
        return [None, None]


class DistanceWidget( TwoItemFloatWidget ):
    def decompress( self, value ):
        if value:
            return [None if x == '-' else x for x in value.split( ';' )]

        return [None, None]


class DurationWidget( widgets.MultiWidget ):
    def __init__( self, attrs=None, label1=None, label2=None, label3=None, label4=None ):
        multi_widget = (
            LabeledTextInput( label=label1, attrs=attrs ),
            LabeledTextInput( label=label2, attrs=attrs ),
            LabeledTextInput( label=label3, attrs=attrs ),
            LabeledTextInput( label=label4, attrs=attrs ),
                )
        super( DurationWidget, self ).__init__( multi_widget, attrs )

    def format_output( self, rendered_widgets ):
        return u'&nbsp;&nbsp;&nbsp;'.join( rendered_widgets )

    def decompress( self, value ):
        if value:
            return [int(x) for x in value.split( ':' )]
        return [None, None, None, None]
