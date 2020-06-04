# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django import forms
from djangoplicity.archives.contrib.forms import widgets

__all__ = ( 'PriorityField', )


class PriorityField( forms.IntegerField ):
    def __init__( self, widget=None, **kwargs ):
        if not widget:
            widget = widgets.PriorityWidget()  # widgets.TwoItemFloatWidget( label1=self.label1, label2=self.label2, joinlabel=self.joinlabel )

        # Override admin widget.
        if not isinstance( widget, widgets.PriorityWidget ):
            widget = widgets.PriorityWidget( attrs={ 'class': 'vIntegerField' } )

        kwargs['widget'] = widget
        super( PriorityField, self ).__init__( **kwargs )
