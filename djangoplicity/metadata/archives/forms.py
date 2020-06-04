# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from django.forms import fields
from django.utils.translation import ugettext_lazy as _

from djangoplicity.metadata.archives import widgets


class TwoItemFloatField( fields.MultiValueField ):
    label1 = None
    label2 = None
    joinlabel = None

    def __init__(self, required=False, widget=None, label=None, initial=None, help_text=None, max_length=None, empty_value=''):
        if not widget:
            widget = widgets.TwoItemFloatWidget( label1=self.label1, label2=self.label2, joinlabel=self.joinlabel )

        # Override admin widget.
        if not isinstance( widget, widgets.TwoItemFloatWidget ):
            widget = widgets.TwoItemFloatWidget( attrs={ 'class': 'vTextField' }, label1=self.label1, label2=self.label2, joinlabel=self.joinlabel )

        myfields = (
            fields.FloatField( required=False ),
            fields.FloatField( required=False )
        )
        super( TwoItemFloatField, self).__init__(myfields, required=required, widget=widget, label=label, initial=initial, help_text=help_text)

    def compress(self, data_list):
        """
        Returns a single value for the given list of values. The values can be
        assumed to be valid.

        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), this might return a datetime
        object created by combining the date and time in data_list.
        """
        if data_list:
            delimiter = ';'
            return delimiter.join([unicode(x) for x in data_list])
        return None


#class FourItemFloatField( fields.MultiValueField ):
#
#   def __init__(self, required=False, widget=widgets.FourItemFloatWidget(), label=None, initial=None, help_text=None, max_length=None):
#       myfields = (
#           fields.FloatField( required=False ),
#           fields.FloatField( required=False ),
#           fields.FloatField( required=False ),
#           fields.FloatField( required=False ),
#       )
#       super( FourItemFloatField, self).__init__(myfields, required=required, widget=widget, label=label, initial=initial, help_text=help_text)
#
#   def compress(self, data_list):
#       """
#       Returns a single value for the given list of values. The values can be
#       assumed to be valid.
#
#       For example, if this MultiValueField was instantiated with
#       fields=(DateField(), TimeField()), this might return a datetime
#       object created by combining the date and time in data_list.
#       """
#       if data_list:
#           delimiter = ';'
#           return delimiter.join([unicode(x) for x in data_list])
#       return None


class SpatialReferenceValueField( TwoItemFloatField ):
    label1 = _("RA")
    label2 = _("Dec")


class SpatialReferenceDimensionField( TwoItemFloatField ):
    #label1 = _("px")
    label2 = _("px")
    joinlabel = "x"


class SpatialReferencePixelField( TwoItemFloatField ):
    label1 = _("px")
    label2 = _("px")
    #joinlabel = "x"


class DistanceField( TwoItemFloatField ):
    label1 = _("light years")
    label2 = _("redshift")

    def compress(self, data_list):
        """
        Returns a single value for the given list of values. The values can be
        assumed to be valid.

        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), this might return a datetime
        object created by combining the date and time in data_list.
        """
        if data_list:
            delimiter = ';'

            if not data_list[0]:
                data_list[0] = ''
            if not data_list[1]:
                del data_list[1]
            return delimiter.join([str(x) for x in data_list])
        return None


class DurationField( fields.MultiValueField ):
    label1 = _("hours")
    label2 = _("mins")
    label3 = _("secs")
    label4 = _("frames")

    def __init__(self, required=False, widget=None, label=None, initial=None, help_text=None, max_length=None, empty_value=''):
        if not widget:
            widget = widgets.DurationWidget( label1=self.label1, label2=self.label2, label3=self.label3, label4=self.label4, attrs={ 'max_legnth': 5 } )

        # Override admin widget.
        if not isinstance( widget, widgets.DurationWidget ):
            widget = widgets.DurationWidget( attrs={ 'class': 'vTextField', 'max_length': 5 }, label1=self.label1, label2=self.label2, label3=self.label3, label4=self.label4, )

        myfields = (
            fields.IntegerField( required=False, min_value=0 ),
            fields.IntegerField( required=False, min_value=0, max_value=59 ),
            fields.IntegerField( required=False, min_value=0, max_value=59 ),
            fields.IntegerField( required=False, min_value=0, max_value=99 ),
        )
        super( DurationField, self).__init__(myfields, required=required, widget=widget, label=label, initial=initial, help_text=help_text)

    def compress(self, data_list):
        """
        Returns a single value for the given list of values. The values can be
        assumed to be valid.

        For example, if this MultiValueField was instantiated with
        fields=(DateField(), TimeField()), this might return a datetime
        object created by combining the date and time in data_list.
        """
        if data_list:
            data_list = [int(x) if x else 0 for x in data_list]
            return u'%d:%0*d:%0*d:%0*d' % ( data_list[0], 2, data_list[1], 2, data_list[2], 3, data_list[3] )
        return None
