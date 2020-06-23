# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
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
#

"""
The celery tasks defined here are all wrapping features defined in the models.
"""

from requests.exceptions import HTTPError

from celery.task import task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache


logger = get_task_logger(__name__)


LOCK_EXPIRE = 60 * 5  # Lock to ensure only one task at a time is run


def acquire_lock(lock_id):
    return cache.add(lock_id, True, LOCK_EXPIRE)


def release_lock(lock_id):
    return cache.delete(lock_id)


@task(name="newsletters.send_scheduled_newsletter", ignore_result=True)
def send_scheduled_newsletter(newsletter_pk):
    """
    Task to start sending a scheduled newsletter - this task should normally
    be invoked with the eta keyword argument (e.g apply_async(pk, eta=..))

    The task will be revoked if the schedule is cancelled via the admin
    interface.

    Notes:
    - A task with eta/countdown will survive if workers are restarted.
    - The eta/countdown argument only ensures that the task will be
        run after the defined time. If workers are overloaded it might be
        delayed.
    """
    from djangoplicity.newsletters.models import Newsletter

    lock_id = 'send_scheduled_newsletter_%s' % newsletter_pk

    if acquire_lock(lock_id):
        try:
            nl = Newsletter.objects.get(pk=newsletter_pk)
            logger.info("Starting to send scheduled newsletter %s" % newsletter_pk)
            nl._send()
        finally:
            release_lock(lock_id)
    else:
        logger.info('Scheduled Newsletter %s is already being sent by another worker'
                    % newsletter_pk)


@task(name="newsletters.send_newsletter", ignore_result=True)
def send_newsletter(newsletter_pk):
    """
    Task to start sending a newsletter
    """
    from djangoplicity.newsletters.models import Newsletter

    lock_id = 'send_newsletter_%s' % newsletter_pk

    if acquire_lock(lock_id):
        try:
            nl = Newsletter.objects.get(pk=newsletter_pk)
            logger.info("Starting to send newsletter %s" % newsletter_pk)
            nl._send_now()
        finally:
            release_lock(lock_id)
    else:
        logger.info('Newsletter %s is already being sent by another worker'
                    % newsletter_pk)


@task(name="newsletters.send_newsletter_test", ignore_result=True)
def send_newsletter_test(newsletter_pk, emails):
    """
    Task to start sending a newsletter
    """
    from djangoplicity.newsletters.models import Newsletter

    lock_id = 'send_newsletter_test_%s' % newsletter_pk

    if acquire_lock(lock_id):
        try:
            nl = Newsletter.objects.get(pk=newsletter_pk)
            logger.info("Starting to send test newsletter %s" % newsletter_pk)
            nl._send_test(emails)
        finally:
            release_lock(lock_id)
    else:
        logger.info('Newsletter %s is already being sent (test)' % newsletter_pk)


@task(name="newsletters.schedule_newsletter", ignore_result=True)
def schedule_newsletter(newsletter_pk, user_pk):
    """
    Task to schedule a newsletter for delivery.
    """
    from djangoplicity.newsletters.models import Newsletter

    lock_id = 'schedule_newsletter_%s' % newsletter_pk

    if acquire_lock(lock_id):
        try:
            nl = Newsletter.objects.get(pk=newsletter_pk)
            logger.info("Scheduling newsletter %s" % newsletter_pk)
            nl._schedule(user_pk)
        finally:
            release_lock(lock_id)
    else:
        logger.info('Newsletter %s is already being scheduled by another worker'
                    % newsletter_pk)


@task(name="newsletters.unschedule_newsletter", ignore_result=True)
def unschedule_newsletter(newsletter_pk, user_pk):
    """
    Task to unschedule a newsletter for delivery.
    """
    from djangoplicity.newsletters.models import Newsletter

    lock_id = 'unschedule_newsletter_%s' % newsletter_pk

    if acquire_lock(lock_id):
        try:
            nl = Newsletter.objects.get(pk=newsletter_pk)
            logger.info("Unscheduling newsletter %s" % newsletter_pk)
            nl._unschedule(user_pk)
        finally:
            release_lock(lock_id)
    else:
        logger.info('Newsletter %s is already being unscheduled by another worker'
                    % newsletter_pk)


@task(name="newsletters.abuse_reports", ignore_result=True)
def abuse_reports():
    '''
    Generate a report for abuse reports for campaigns sent
    over the last 4 weeks.
    This task is meant to be run once a week
    '''
    # Only run on production
    if settings.SITE_ENVIRONMENT != 'prod':
        return

    from datetime import datetime, timedelta
    from django.core.mail import EmailMessage
    from djangoplicity.mailinglists.models import MailChimpList
    from django.contrib.sites.models import Site

    email_from = 'no-reply@eso.org'
    email_reply_to = 'no-reply@eso.org'
    email_to = ['osandu@partner.eso.org', 'lars@eso.org']

    #  Calculate the date 4 weeks ago
    start_date = datetime.today() - timedelta(weeks=4)
    #  Calculate the date one week ago
    week_ago = datetime.today() - timedelta(weeks=1)

    body = ''
    n_complaints = 0

    for ml in MailChimpList.objects.all():
        logger.debug('Will run campaigns.all for list %s', ml.list_id)
        try:
            response = ml.connection(
                'campaigns.all',
                get_all=True,
                list_id=ml.list_id,
                since_send_time=start_date.isoformat(),
                fields='campaigns.id,campaigns.settings.title'
            )
        except HTTPError as e:
            logger.error('campaigns.all: %s', e.response.text)
            raise e

        if response['total_items'] == 0:
            continue

        content = ''

        for campaign in response['campaigns']:

            logger.debug('Will run reports.abuse_reports.all for campaign %s',
                campaign['id'])
            try:
                response = ml.connection(
                    'reports.abuse_reports.all',
                    campaign_id=campaign['id'],
                    since_send_time=week_ago.isoformat()
                )
            except HTTPError as e:
                logger.error('reports.abuse_reports.all: %s', e.response.text)
                raise e

            if response['total_items'] == 0:
                continue

            n_complaints += response['total_items']

            if not content:
                name = 'MailChimp List: %s' % ml.name
                content = '=' * len(name) + '\n'
                content += name + '\n'
                content += '=' * len(name) + '\n'

            title = 'Campaign: %s (%d complaints)' % (
                campaign['settings']['title'],
                response['total_items'])
            content += '\n' + title + '\n'
            content += '-' * len(title) + '\n'

            for complaint in response['abuse_reports']:
                try:
                    member = ml.connection(
                        'lists.members.get',
                        complaint['list_id'],
                        complaint['email_id'],
                    )
                except HTTPError as e:
                    logger.error('lists.members.get: %s', e.response.text)
                    raise e

                content += '%s Reason: %s' % (member['email_address'],
                    member['unsubscribe_reason']) + '\n'

        body += content

    if body:
        logger.info('Sending report for %d complaints' % n_complaints)
        # Prepare the message:
        msg = EmailMessage()
        msg.headers = {'Reply-To': email_reply_to}
        msg.subject = '%d complaints reported in MailChimp for %s' % (n_complaints, Site.objects.get_current().domain)
        msg.from_email = email_from
        msg.to = email_to
        msg.body = body

        msg.send()
    else:
        logger.info('No Mailchimp Complaints found')
