from django.forms import fields
import djangoplicity.metadata.widgets as avmwidgets


class StringField( fields.CharField ):
    widget = avmwidgets.StringInput


class URLField( fields.URLField ):
    widget = avmwidgets.StringInput


class EmailField( fields.EmailField ):
    widget = avmwidgets.StringInput


class TextField( fields.TextInput ):
    widget = avmwidgets.Textarea


class DateField( fields.DateField ):
    pass


class TwoItemFloatField( fields.MultiValueField ):

    def __init__(self, required=False, widget=avmwidgets.TwoItemFloatWidget(), label=None, initial=None, help_text=None, max_length=None):
        myfields = (
            fields.FloatField( required=False ),
            fields.FloatField( required=False ),
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


class FourItemFloatField( fields.MultiValueField ):

    def __init__(self, required=False, widget=avmwidgets.FourItemFloatWidget(), label=None, initial=None, help_text=None, max_length=None):
        myfields = (
            fields.FloatField( required=False ),
            fields.FloatField( required=False ),
            fields.FloatField( required=False ),
            fields.FloatField( required=False ),
        )
        super( FourItemFloatField, self).__init__(myfields, required=required, widget=widget, label=label, initial=initial, help_text=help_text)

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
#
# Specific Form Elements
#


class ContactNameField( fields.RegexField ):

    def compress(self, data_list):
        if data_list:
            delimiter = ';'
            return delimiter.join([unicode(x) for x in data_list])

        return None


class SubjectCategoryField( fields.CharField ):
    widget = avmwidgets.SubjectCategoryWidget


class DistanceField( fields.MultiValueField ):
    def __init__(self, required=False, widget=avmwidgets.DistanceWidget(), label=None, initial=None, help_text=None, max_length=None):
        myfields = (
            fields.FloatField( required=False ),
            fields.FloatField( required=False )
        )
        super( DistanceField, self).__init__(myfields, required=required, widget=widget, label=label, initial=initial, help_text=help_text)

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
                data_list[0] = '-'
            if not data_list[1]:
                del data_list[1]
            return delimiter.join([str(x) for x in data_list])
        return None
