# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.test import TestCase
from iaumemberdb.tests import AdminTestCase

class ReportsAdminTestCase( AdminTestCase ):
    fixtures = [ 'auth.json', 'reports.json' ]

    def test_report( self ):
        response = self.client.get( '/admin/reports/report/' )
        self.failUnlessEqual( response.status_code, 200 )
        response = self.client.get( '/admin/reports/report/1/' )
        self.failUnlessEqual( response.status_code, 200 )
        response = self.client.get( '/membershipadmin/reports/report/' )
        self.failUnlessEqual( response.status_code, 200 )
        response = self.client.get( '/membershipadmin/reports/report/1/' )
        self.failUnlessEqual( response.status_code, 200 )

    def test_reportgroup( self ):
        response = self.client.get( '/admin/reports/reportgroup/' )
        self.failUnlessEqual( response.status_code, 200 )
        response = self.client.get( '/admin/reports/reportgroup/1/' )
        self.failUnlessEqual( response.status_code, 200 )

class ReportEngineTestCase( TestCase ):
    fixtures = [ 'auth.json', 'reports.json' ]

    def test_report_engine(self):
        #from engine import *
        #from models import *

        report_empty = Report.objects.get( pk=2 )
        report_bad_fields = Report.objects.get( pk=3 )
        report_bad_sql = Report.objects.get( pk=4 )

        self.failUnlessRaises( ReportExecutionError, ReportEngine.run_report, report_empty )
        self.failUnlessRaises( ReportExecutionError, ReportEngine.run_report, report_bad_fields )
        self.failUnlessRaises( ReportExecutionError, ReportEngine.run_report, report_bad_sql )

def report_engine_test():
    """
    >>> from reports.engine import ReportEngine
    >>> from reports.models import *
    >>> group = ReportGroup.objects.create(name='Statistics')
    >>> group.save()
    >>> report = Report.objects.create(name='Good report', group_id=group.id, description='Some description', displayed_fields='Name', sql_command='SELECT name FROM reports_reportgroup' )
    >>> report.save()
    >>> result = ReportEngine.run_report( report )
    >>> result.report
    <Report: Good report>
    >>> result.rows
    ((u'Statistics',), (u'Statistics',))
    """
    pass
