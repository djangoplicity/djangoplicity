# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.db import connection


class ReportExecutionError(Exception):
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

    def __init__(self, rep, res):
        self.report = rep
        self.rows = res


class ReportEngine:
    """
    Engine for executing a report. This basically means running a query against the database,
    and make sure it matches what is defined in the report.
    """

    @staticmethod
    def run_report(report):
        """
        Executes the report. Throws ReportExecutionError in the following cases:
        - Database Error.
        - No rows.
        - Report without fields
        - More fields than columns

        TODO: check fields are not empty before fetching db.
        """

        try:
            cursor = connection.cursor()
            cursor.execute(report.sql_command)

            rows = cursor.fetchall()
            fields = report.fields
        except Exception as e:
            # Catch all database errors and re-raise an ReportExecutionException
            raise ReportExecutionError(
                'Cannot generate report - error in report commands: %s' % e)

        if rows == []:
            raise ReportExecutionError('Report result was empty.')

        # Ensure number of columns in data match number of fields
        fields_count = len(fields)
        columns_count = len(rows[0])

        if fields == ['']:
            raise ReportExecutionError('No fields defined in report.')

        if fields_count > columns_count:
            # More fields than columns in data - raise error
            raise ReportExecutionError('Cannot generate report')
        elif fields_count < columns_count:
            # More columns in data than fields: strip columns to number of fields.
            rows = [x[0:fields_count] for x in rows]

        return ReportResult(report, rows)
