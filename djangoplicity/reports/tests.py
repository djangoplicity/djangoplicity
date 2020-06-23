# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.test import TestCase
from djangoplicity.test.testcases import AdminTestCase
from django.http import Http404

from models import Report, ReportGroup
from engine import ReportEngine, ReportExecutionError, ReportResult


class ReportsAdminTestCase(AdminTestCase):
    fixtures = ['reports.json']

    def test_report_access(self):
        response = self.client.get('/admin/reports/report/')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/reports/report/1/')
        self.assertEqual(response.status_code, 302)

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

        self.assertRaises(ReportExecutionError,
                          ReportEngine.run_report, report_empty)
        self.assertRaises(ReportExecutionError,
                          ReportEngine.run_report, report_empty_fields)
        self.assertRaises(ReportExecutionError,
                          ReportEngine.run_report, report_bad_sql)
        self.assertRaises(ReportExecutionError,
                          ReportEngine.run_report, report_too_many_fields)

    def test_column_trimming(self):
        report_few_fields = Report.objects.get(pk=6)
        result = ReportEngine.run_report(report_few_fields)
        first_result = result.rows[0]

        self.assertEqual(len(report_few_fields.fields), len(first_result))

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


class ReportViewTestCase(AdminTestCase):
    fixtures = ['reports.json']

    def test_report_existance(self):
        response = self.client.get('/reports/report/1/')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/reports/report/404')
        # redirects to a 404 page
        self.assertEqual(response.status_code, 301)

    def test_report_with_different_formats(self):
        response = self.client.get('/reports/report/1/?output=csv')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/reports/report/1/?output=xlsx')
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/reports/report/1/?output=html')
        self.assertEqual(response.status_code, 200)

    def test_report_html_template(self):
        report = Report.objects.get(pk=1)

        response = self.client.get('/reports/report/1/?output=html')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/report_view.html')
        self.assertContains(response, report.name)
    
    def test_report_csv_error_template(self):
        response = self.client.get('/reports/report/7/?output=csv')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reports/csverror.html')


class ReportModelTestCase(TestCase):
    fixtures = ['reports.json']
    
    def test_email_checking(self):
        report_with_email = Report.objects.get(pk=8)
        self.assertEqual(report_with_email.has_email_field(), True)
        self.assertNotEqual(report_with_email.get_email_position(), -1)

        report_without_email = Report.objects.get(pk=1)
        self.assertEqual(report_without_email.has_email_field(), False)
        self.assertEqual(report_without_email.get_email_position(), -1)
