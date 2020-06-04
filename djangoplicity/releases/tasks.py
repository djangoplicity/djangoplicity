# -*- coding: utf-8 -*-
#
# djangoplicity-releases
# Copyright (c) 2007-2014, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

from datetime import datetime, timedelta
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from celery.task import task

from djangoplicity.releases.models import Release, ReleaseImage, ReleaseVideo, ReleaseImageComparison
from djangoplicity.announcements.models import Announcement, AnnouncementImage, AnnouncementVideo


@task( name='releases.check_propagation', ignore_result=True )
def check_propagation():
    """
    Go through all releases changed during the last hour, and check that the release and embargo dates have been properly propagated.
    """
    now = datetime.now()
    d = timedelta(hours=1, minutes=2)
    # d = timedelta(days=100)

    success = True
    result = []

    for obj in Release.objects.filter(last_modified__gt=now - d):
        result.append('\n\n## RELEASE ID: %s\n' % obj.id)
        result.append('release: %s, embargo: %s\n' % (obj.release_date, obj.embargo_date))
        related_success = check_related_propagation(obj, 'images', ReleaseImage, result)
        success = success and related_success
        related_success = check_related_propagation(obj, 'videos', ReleaseVideo, result)
        success = success and related_success
        related_success = check_related_propagation(obj, 'comparisons', ReleaseImageComparison, result)
        success = success and related_success

    for obj in Announcement.objects.filter(last_modified__gt=now - d):
        result.append('\n\n## ANNOUNCEMENT ID: %s\n' % obj.id)
        result.append('release: %s, embargo: %s\n' % (obj.release_date, obj.embargo_date))
        related_success = check_related_propagation(obj, 'images', AnnouncementImage, result)
        success = success and related_success
        related_success = check_related_propagation(obj, 'videos', AnnouncementVideo, result)
        success = success and related_success

    text = ''.join(result)

    if not success:
        text = '##################\n## ERRORS FOUND ##\n##################\n' + text

    # # for command line use
    # # bin/python -c 'from djangoplicity.releases.tasks import check_propagation; check_propagation()'
    # if text:
    #   print text
    # else:
    #   print 'No changes'

    if not success:
        emails = ['brino@partner.eso.org', 'Gurvan.Bazin@eso.org']
        sitename = Site.objects.get_current().name
        send_mail('[djangoplicity: %s] Release date propagation report' % sitename, text, None, emails)


def check_related_propagation(main_obj, related_label, related, return_result):
    success = True
    result = []

    if isinstance(main_obj, Release):
        objects = related.objects.filter(release=main_obj)
    elif isinstance(main_obj, Announcement):
        objects = related.objects.filter(announcement=main_obj)

    for related_obj in objects:
        status = ''
        obj = related_obj.archive_item
        override_id = related_obj.override_id

        if override_id and override_id != main_obj.id:
            status = 'overriden'
        else:
            if obj.release_date != main_obj.release_date:
                status += '\n    * release_date: %s  ' % obj.release_date
                success = False
            if obj.embargo_date != main_obj.embargo_date:
                status += '\n    * embargo_date: %s  ' % obj.embargo_date
                success = False

        if status == '':
            status = 'OK'
        result.append('  %s: %s\n' % (obj.id, status))

    if result:
        return_result.append(related_label + ':\n')
        return_result.extend(result)
    return success
