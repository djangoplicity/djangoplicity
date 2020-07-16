# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from future import standard_library
standard_library.install_aliases()
from builtins import str
import csv
import urllib.request, urllib.parse, urllib.error
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

# == Formatting of reports ==
# Reports executed by the report engine uses an output formatter for
# generating the actual report.
#
# # Simple usage example
# >>> report = get_object_or_404( Report, pk = 1 )
# >>> result = ReportEngine.run_report( report )
# >>> response = ReportFormatter.format( result, 'html' )
#
# == OutputFormatters ==
# OutputFormatters needs to be registered with the ReportFormatter before
# being usable. Setting the REPORT_REGISTER_FORMATTERS to true in settings.py
# will automatically register the standard output formatters. Additionally
# formatters can be registered by:
#
# # Example of registering PDF output formatter
# >>> ReportViewer.register( PDFOutputFormatter, 'pdf' )
#
# Insert this in eg the __init__.py of your module. This allows report
# to be generated in PDF by appending the query string as follows:
#
# .../reports/report/1/?output=pdf

# Default output formatter setting
REPORTS_DEFAULT_FORMATTER = 'html'

#
# Exceptions
#


class AlreadyRegistered( Exception ):
    """ Signals that an output formatter has already been registered. """
    pass


class NotRegistered( Exception ):
    """ Signals that an output formatter is not registered. """
    pass


#
# Output Formatter classes
#
class OutputFormatter:
    """
    Superclass for all output formatters. An output formatter must
    inherit from this class and implement the metod format. Otherwise the
    the output formatter cannot be reigstered with the report viewer.
    """

    def format( self, report_result, request ):
        """
        Method must be overwritten by subclasses,  otherwise an exception
        is thrown.

        Every output formatter must return a HttpResponse object.
        """
        raise NotImplementedError


class CSVOutputFormatter( OutputFormatter ):
    """
    Output formatter for CSV files. This class can generate a
    CSV file for a report.
    """

    def format( self, report_result, request ):
        """
        See documentation for OutputFormatter.format( report_result )

        **Character encoding:** Formatter will try to generate CSV file
        in latin-1 encoding. If it fails an error will be returned, with
        information on how to get the CSV file in UTF8 encoding.

        CSV files in UTF8 encoding however cannot be read properly in Excel
        on OS X, and must be imported in a special way on Windows.

        The conversion into the proper encoding first converts everything
        into unicode, and then from the unicode string it tries to convert to
        the requested encoding.

        Note the conversion into unicode string assumes that all 8-bit strings are
        UTF8 encoded! Since the data comes from the database, this should also
        be the case otherwise there is probably in an error in the encoding used
        for the given table.

        Newlines in text strings will also be replaced with two spaces.
        """
        # Create the csv HttpResponse object .
        response = HttpResponse( content_type='text/csv' )
        response['Content-Disposition'] = "attachment; filename=report.csv"

        writer = csv.writer( response )

        # Get encoding parameter
        encoding = "latin-1"

        if 'encoding' in request.GET and request.GET['encoding'] == "utf8":
            encoding = "utf8"

        try:
            # Write header
            writer.writerow( [str(x).encode(encoding) for x in report_result.report.fields] )

            # Write rows
            for row in report_result.rows:
                cells = []

                for x in row:
                    if isinstance( x, str ):
                        cells.append( str(x, encoding='utf8' ).encode(encoding) )
                    elif isinstance( x, str ):
                        cells.append( x.encode( encoding ) )
                    else:
                        cells.append( str(x).encode(encoding) )

                    # Replace newlines in fields to prevent problems with loading
                    # CSV file.
                    cells = [x.replace("\r\n", '  ') for x in cells]
                    cells = [x.replace("\n", '   ') for x in cells]

                writer.writerow( cells )

            return response
        except UnicodeError:
            return render(request, 'reports/csverror.html', {
                    'url': request.path + '?' + urllib.parse.urlencode( {'output': request.GET['output'], 'encoding': 'utf8' } )
            })


class XLSXOutputFormatter(OutputFormatter):
    '''
    XLSX formatter
    '''
    def format(self, report_result, request):

        book = Workbook()
        sheet = book.active

        # Write headers
        sheet.append(report_result.report.fields)

        # Write rows
        for row in report_result.rows:
            sheet.append(row)

        response = HttpResponse(
            content=save_virtual_workbook(book),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; ' \
            'filename=report-{}.xlsx'.format(report_result.report.pk)

        return response


class HTMLOutputFormatter( OutputFormatter ):
    """
    Output formatter for HTML. Uses a template to generate the output.
    """

    def format( self, report_result, request ):
        """
        See documentation for OutputFormatter.format( report_result )
        """
        return render(
                request,
                'reports/report_view.html',
                {
                    'fields': report_result.report.fields,
                    'results': report_result.rows,
                    'total': len( report_result.rows ),
                    'title': report_result.report.name
                }
            )


#
# Report viewer
#
class ReportFormatter:
    """
    Controller for running report formatters.

    Contains a class variables and static methods for registering output formatters,
    and formatting a ReportResult with a given formatter.
    """

    # Map from type to output formatter
    registry = {}

    @staticmethod
    def register( formatter, type ):
        """
        Register an output formatter with a specific type. Only subclasses of
        OutputFormatter can be registered, otherwise a TypeError is raised.
        """
        type = type.lower()

        if type in ReportFormatter.registry:
            raise AlreadyRegistered( _( 'The output formatter type "%s" is already registered.' ) % type )

        if issubclass( formatter, OutputFormatter ):
            ReportFormatter.registry[ type ] = formatter()
        else:
            raise TypeError( _( 'Ouput formatter must be of type OutputFormatter' ) )

    @staticmethod
    def format( report_result, type, request ):
        """
        Format an report using the given type.
        """
        if type in ReportFormatter.registry:
            formatter = ReportFormatter.registry[type]
        else:
            raise NotRegistered( _( 'The output formatter type "%s" is not registered.' ) % type )

        return formatter.format( report_result, request )


#
# Register standard formatters
#
if settings.REPORT_REGISTER_FORMATTERS is True:
    ReportFormatter.register(HTMLOutputFormatter, 'html')
    ReportFormatter.register(CSVOutputFormatter, 'csv')
    ReportFormatter.register(XLSXOutputFormatter, 'xlsx')
