# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#   * Neither the name of the European Southern Observatory nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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

from django.http import HttpResponse

from djangoplicity.mailinglists.models import MailChimpListToken, MailChimpList
from djangoplicity.mailinglists.tasks import mailchimp_subscribe, \
    mailchimp_unsubscribe, mailchimp_upemail, mailchimp_cleaned, \
    mailchimp_profile, mailchimp_campaign
from djangoplicity.mailinglists.utils import DataQueryParser

import logging

logger = logging.getLogger(__name__)


class WebHookError(Exception):
    pass


def _get_parameters(request):
    '''
    Extract parameters from webhook request
    '''
    return DataQueryParser.parse(request.POST)


def subscribe_event(request, mlist, fired_at, **kwargs):
    '''
    "type": "subscribe",
    "fired_at": "2009-03-26 21:35:57",
    "data[id]": "8a25ff1d98",
    "data[list_id]": "a6b5da1054",
    "data[email]": "api@mailchimp.com",
    "data[email_type]": "html",
    "data[merges][EMAIL]": "api@mailchimp.com",
    "data[merges][FNAME]": "MailChimp",
    "data[merges][LNAME]": "API",
    "data[merges][INTERESTS]": "Group1,Group2",
    "data[ip_opt]": "10.20.10.30",
    "data[ip_signup]": "10.20.10.30"
    '''
    mailchimp_subscribe.delay(
        list_pk=mlist.pk,
        fired_at=fired_at,
        params=_get_parameters(request),
        **kwargs
    )
    return HttpResponse('')


def unsubscribe_event(request, mlist, fired_at, **kwargs):
    '''
    "type": "unsubscribe",
    "fired_at": "2009-03-26 21:40:57",
    "data[id]": "8a25ff1d98",
    "data[list_id]": "a6b5da1054",
    "data[email]": "api+unsub@mailchimp.com",
    "data[email_type]": "html",
    "data[merges][EMAIL]": "api+unsub@mailchimp.com",
    "data[merges][FNAME]": "MailChimp",
    "data[merges][LNAME]": "API",
    "data[merges][INTERESTS]": "Group1,Group2",
    "data[ip_opt]": "10.20.10.30",
    "data[campaign_id]": "cb398d21d2",
    "data[reason]": "hard"
    '''
    mailchimp_unsubscribe.delay(
        list_pk=mlist.pk,
        fired_at=fired_at,
        params=_get_parameters(request),
        **kwargs
    )
    return HttpResponse('')


def profile_event(request, mlist, fired_at, **kwargs):
    '''
    "type": "profile",
    "fired_at": "2009-03-26 21:31:21",
    "data[id]": "8a25ff1d98",
    "data[list_id]": "a6b5da1054",
    "data[email]": "api@mailchimp.com",
    "data[email_type]": "html",
    "data[merges][EMAIL]": "api@mailchimp.com",
    "data[merges][FNAME]": "MailChimp",
    "data[merges][LNAME]": "API",
    "data[merges][INTERESTS]": "Group1,Group2",
    "data[ip_opt]": "10.20.10.30"
    '''
    mailchimp_profile.delay(
        list_pk=mlist.pk,
        fired_at=fired_at,
        params=_get_parameters(request),
        **kwargs
    )
    return HttpResponse('')


def upemail_event(request, mlist, fired_at, **kwargs):
    '''
    "type": "upemail",
    "fired_at": "2009-03-26 22:15:09",
    "data[list_id]": "a6b5da1054",
    "data[new_id]": "51da8c3259",
    "data[new_email]": "api+new@mailchimp.com",
    "data[old_email]": "api+old@mailchimp.com"
    '''
    mailchimp_upemail.delay(
        list_pk=mlist.pk,
        fired_at=fired_at,
        params=_get_parameters(request),
        **kwargs
    )
    return HttpResponse('')


def cleaned_event(request, mlist, fired_at, **kwargs):
    '''
    "type": "cleaned",
    "fired_at": "2009-03-26 22:01:00",
    "data[list_id]": "a6b5da1054",
    "data[campaign_id]": "4fjk2ma9xd",
    "data[reason]": "hard",
    "data[email]": "api+cleaned@mailchimp.com"
    '''
    mailchimp_cleaned.delay(
        list_pk=mlist.pk,
        fired_at=fired_at,
        params=_get_parameters(request),
        **kwargs
    )
    return HttpResponse('')


def campaign_event(request, mlist, fired_at, **kwargs):
    '''
    Example:
    "type": "campaign",
    "fired_at": "2009-03-26 21:31:21",
    "data[id]": "5aa2102003",
    "data[subject]": "Test Campaign Subject",
    "data[status]": "sent",
    "data[reason]": "",
    "data[list_id]": "a6b5da105
    '''
    mailchimp_campaign.delay(
        list_pk=mlist.pk,
        fired_at=fired_at,
        params=_get_parameters(request),
        **kwargs
    )
    return HttpResponse('')


EVENT_HANDLERS = {
    'subscribe': subscribe_event,
    'unsubscribe': unsubscribe_event,
    'upemail': upemail_event,
    'cleaned': cleaned_event,
    'profile': profile_event,
    'campaign': campaign_event,
}


def mailchimp_webhook(request, require_secure=False):
    '''
    MailChimp webhook view (see http://apidocs.mailchimp.com/webhooks/)

    Validates the request to ensure it is from MailChimp, and delegates
    event processing to event handlers.

    Validation checks::
      * POST request
      * HTTPS request
      * Validate token (not expired, and belongs to list being updated)
      * Validate that list exists

    A request to mailchimp_webook must be completed within 15 seconds, thus
    event handlers should only gather the data they need, and send the rest
    for background processing.
    '''
    if not request.is_secure():
        if require_secure:
            logger.error('[Webhook] Not SSL request')
            return HttpResponse('')

    # Get token
    try:
        token = request.GET['token']
    except KeyError:
        logger.error('[Webhook] No "token" GET parameter')
        return HttpResponse('')

    # Check token
    t = MailChimpListToken.get_token(token)

    if t is None:
        logger.error('[Webhook] Token %s not found', token)
        return HttpResponse('')

    if 'HTTP_X_REAL_IP' in request.META:
        key = 'HTTP_X_REAL_IP'
    else:
        key = 'REMOTE_ADDR'
    ip = request.META[key]

    # Check user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if user_agent == 'MailChimp.com WebHook Validator':
        return HttpResponse('')
    if user_agent != 'MailChimp.com':
        logger.error('[Webhook] User-agent not MailChimp.com - was %s',
            user_agent)
        return HttpResponse('')

    try:
        # Check expected request type
        if request.method != 'POST':
            raise WebHookError('Not a POST request')

        # Get parameters
        event_type = request.POST['type']
        fired_at = request.POST['fired_at']
        list_id = request.POST['data[list_id]']
    except KeyError as e:
        raise WebHookError('Missing webhook post parameter "%s"', e.args[0])

    # Check webhook event_type
    if event_type not in ('subscribe', 'unsubscribe', 'profile', 'upemail',
        'cleaned', 'campaign'):
        raise WebHookError('Unknown webhook type %s' % event_type)

    # Check if list exists
    try:
        mlist = MailChimpList.objects.get(list_id=list_id)
    except MailChimpList.DoesNotExist:
        raise WebHookError('List %s does not exists' % list_id)

    # Validate token for list
    if not t.validate_token(mlist):
        raise WebHookError('Token invalid')

    # Get event handler
    try:
        view = EVENT_HANDLERS[event_type]
    except KeyError:
        raise WebHookError('Internal error - no event handler defined for %s.'
            % event_type)

    # Pass to event handler for processing.
    logger.info('[Webhook] Request accepted: %s', event_type)
    return view(request, mlist, fired_at, ip=ip, user_agent=user_agent)
