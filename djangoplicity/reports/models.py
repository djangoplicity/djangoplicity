# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

import django
if django.VERSION >= (2, 0):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse

@python_2_unicode_compatible
class ReportGroup( models.Model ):
    """
    Defines groups of reports.
    """

    # Name of the group
    name = models.CharField( max_length=100 )

    def __str__( self ):
        return self.name

    class Meta:
        ordering = ['name']


# pylint: disable=R0921
@python_2_unicode_compatible
class Report( models.Model ):
    """
    A report is essential a SQL query in the database, that can be displayed
    using some output formatter to show it in eg HTML or CSV.
    """

    #
    # Database model
    #

    # Name of the report
    name = models.CharField( max_length=100 )

    #is_email_list = models.BooleanField()
    #""" Whether the report generates an e-mail list """

    # Group of report
    group = models.ForeignKey( ReportGroup, on_delete=models.CASCADE)

    # Whether the report can be used for mass mailing
    is_mailable = models.BooleanField(default=False)

    # A description of the report
    description = models.TextField(blank=True, null=True)

    # Displayed column headings for the query. This is used to change
    displayed_fields = models.TextField( help_text=_('Please write the fields to be displayed in a semi-colon seprated format') )

    # The SQL query for the report - backend specific
    sql_command = models.TextField( _('SQL Command') )

    #
    # Auxillary variables and methods
    #
    # A list of fields, that is computed from displayed_fields,
    # as soon as the fields property is requested.
    field_list = None

    def get_fields( self ):
        """
        Get the list of fields (column headings), by splitting
        the displayed_fields and saving the result.
        """
        if self.field_list is None:
            self.field_list = [ s.strip() for s in self.displayed_fields.split( ';' ) ]

        return self.field_list

    def set_fields( self, fields ):
        """
        Unimplemented, since we do not need to set the fields,
        that is done through displayed_fields.
        """
        raise NotImplementedError()

    # Property for accessing the list of fields for the report
    fields = property( get_fields, set_fields )

    def has_email_field(self):
        """ Checks wheter one of the displayed field is an email field. """
        for f in self.fields:
            if f.lower() == 'email' or f.lower() == 'e-mail':
                return True
        return False

    def get_email_position(self):
        """ Returns the position  """
        i = 0
        for f in self.fields:
            if f.lower() == 'email' or f.lower() == 'e-mail':
                return i
            i += 1
        return -1

    def get_absolute_url(self):
        return reverse('report-detail', args=[self.pk])

    def __str__( self ):
        return self.name

    class Meta:
        ordering = ['name']
