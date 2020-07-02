# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import never_cache

from djangoplicity.reports.engine import ReportEngine, ReportExecutionError
from djangoplicity.reports.formatters import ReportFormatter, REPORTS_DEFAULT_FORMATTER
from djangoplicity.reports.models import Report

# Views for viewing reports via the administration interface.
#
# Editing of reports would normally be done via the administration interface, so
# you could eg register the following admin options.
#
# > admin.site.register( ReportGroup, ReportGroupOptions )
# > admin.site.register( Report, ReportAdvancedOptions )
# > other_admin.register( Report, ReportOptions )
#
# This would allow the reports to be edited via the normal administration interface, and
# to be viewed through another administration site.


@staff_member_required
@never_cache
def report_detail( request, report_id ):
    """
    Run a report and format the output.

    Use this view to overwrite the default change view for reports moduel. Do
    this by inserting the following rule in your urls.py

    > ( r'^admin/reports/', include( 'iaumemberdb.reports.urls' ) ),

    The setting REPORTS_DEFAULT_FORMATTER can be used to change the default
    output formatter.
    """

    # Determine output formatter

    # Request parameter 'output' specifies the formatter
    if 'output' in request.GET:
        output_formatter_type = request.GET['output'].lower()
    else:
        # Output formatter defaults to html
        if settings.REPORTS_DEFAULT_FORMATTER:
            output_formatter_type = settings.REPORTS_DEFAULT_FORMATTER
        else:
            output_formatter_type = REPORTS_DEFAULT_FORMATTER
    
    # Retrieve report
    report = get_object_or_404( Report, pk=report_id )

    # Execute and format report
    try:
        result = ReportEngine.run_report( report )
        response = ReportFormatter.format( result, output_formatter_type, request )

        return response
    except ReportExecutionError as e:
        return render(request, 'error.html', {'error_message': e, 'title': _('Report "%s" could not be generated') % report.name})
