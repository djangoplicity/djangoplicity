# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.db import connection


class ReportExecutionError( Exception ):
    """
    An error indicating the execution of a report. This can be eg
    error in the SQL query or in the definition of the report.
    """
    pass


class ReportResult:
    """
    Container for the result of an report execution. Contains the report
    and the result.
    """

    def __init__( self, rep, res ):
        self.report = rep
        self.rows = res


class ReportEngine:
    """
    Engine for executing a report. This basically means running a query against the database,
    and make sure it matches what is defined in the report.
    """

    @staticmethod
    def run_report( report ):
        """
        Execute the report. Throws ReportExecutionError if anything goes wrong.
        """

        try:
            cursor = connection.cursor()
            cursor.execute( report.sql_command )

            rows = cursor.fetchall()
            fields = report.fields
        # Catch all database errors and re-raise an ReportExecutionException
        except Exception as e:
            raise ReportExecutionError( 'Cannot generate report - error in report commands: %s' % e )

        if not rows:
            raise ReportExecutionError( 'Report result was empty.' )

        # Ensure number of columns in data match number of fields
        count_fields = len( fields )
        count_rows = len( rows[0] )

        if count_fields == ():
            raise ReportExecutionError( 'No fields defined in report.' )

        if count_fields > count_rows:
            # More fields than columns in data - raise error
            raise ReportExecutionError( 'Cannot generate report' )
        elif count_fields < count_rows:
            # More columns in data than fields - strip columns to no. of fields.
            rows = map( lambda x: x[0:count_fields], rows )

        return ReportResult( report, rows )
