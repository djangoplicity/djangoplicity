# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.test import TestCase
from djangoplicity.test.testcases import AdminTestCase

from models import Report, ReportGroup
from engine import ReportEngine, ReportExecutionError, ReportResult


class ReportsAdminTestCase(AdminTestCase):
    fixtures = ['reports.json']

    def test_report_access(self):
        response = self.client.get('/admin/reports/report/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/reports/report/1/')
        self.assertEqual(response.status_code, 302)

    def test_report_redirect(self):
        """
        Tests that the redirection is actually triggering report view
        """
        response = self.client.get('/admin/reports/report/1/', follow=True)
        # TODO: Finish

    def test_reportgroup_access(self):
        response = self.client.get('/admin/reports/reportgroup/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/reports/reportgroup/1/')
        self.assertEqual(response.status_code, 302)


class ReportEngineTestCase(TestCase):
    fixtures = ['reports.json']

    def test_report_engine_exceptions(self):
        report_empty = Report.objects.get(pk=2)
        report_empty_fields = Report.objects.get(pk=3)
        report_bad_sql = Report.objects.get(pk=4)
        report_too_many_fields = Report.objects.get(pk=5)

        self.failUnlessRaises(ReportExecutionError,
                              ReportEngine.run_report, report_empty)
        self.failUnlessRaises(ReportExecutionError,
                              ReportEngine.run_report, report_empty_fields)
        self.failUnlessRaises(ReportExecutionError,
                              ReportEngine.run_report, report_bad_sql)
        self.failUnlessRaises(ReportExecutionError,
                              ReportEngine.run_report, report_too_many_fields)

    def test_report_engine(self):
        group = ReportGroup.objects.create(name='Grouped Reports')
        report = Report.objects.create(
            name='Grouped Report Names',
            group_id=group.id,
            description='Life is wonderful',
            displayed_fields='Name',
            sql_command='SELECT name FROM reports_reportgroup'
        )

        result = ReportEngine.run_report(report)

        self.assertEqual(result.report, report)
        
        all_reports = [(u'Statistics',), (u'Grouped Reports',)]
        self.assertEqual(result.rows, all_reports)
