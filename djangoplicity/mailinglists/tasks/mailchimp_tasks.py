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

from celery.task import task
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.utils.encoding import smart_unicode
from urllib import urlencode
from djangoplicity.mailinglists.models import MailChimpList, MailChimpListToken


__all__ = [
    'mailchimp_subscribe', 'mailchimp_unsubscribe', 'mailchimp_upemail',
    'mailchimp_cleaned', 'mailchimp_profile', 'mailchimp_campaign',
    'webhooks', 'clean_tokens', 'mailchimplist_fetch_info',
]


# ===========
# Event tasks
# ===========

def _log_webhook_action(logger, ip, user_agent, action, ml, message=''):
    '''
    Helper function for logging where a webhook request came from.
    '''
    logger.info('Webhook %s action; list %s: %s; IP: %s User Agent: %s' %
        (action, ml, message, ip, user_agent))


def _object_identifier(obj):
    if isinstance(obj, models.Model):
        return (
            smart_unicode(obj._meta),
            smart_unicode(obj._get_pk_val(), strings_only=True),
        )
    else:
        return (None, None)


def _get_list(list_pk):
    return MailChimpList.objects.get(pk=list_pk)


def keys2str( kwargs ):
    """
    Convert the keys of a dictionary into string keys.
    """
    newkwargs = {}
    for k, v in kwargs.items():
        newkwargs[str( k )] = v
    return newkwargs


@task(name='mailinglists.mailchimp_subscribe', ignore_result=True)
def mailchimp_subscribe(list_pk=None, fired_at=None, params=None, ip=None,
    user_agent=None):
    '''
    User subscribed via MailChimp.
    Remove from bad address if on the list and dispatch actions.
    '''
    if params is None:
        params = {}

    logger = mailchimp_subscribe.get_logger()
    _log_webhook_action(logger, ip, user_agent, 'subscribe', list_pk)

    #
    # Deregister bad email address if exists.
    #
    from djangoplicity.mailinglists.models import BadEmailAddress
    email = params.get('email', '')

    if email:
        try:
            BadEmailAddress.objects.get(email=email).delete()
        except BadEmailAddress.DoesNotExist:
            pass

    from djangoplicity.mailinglists.models import MailChimpEventAction

    mlist = _get_list(list_pk)

    if 'merges' in params:
        obj = mlist.get_object_from_mergefields(params['merges'])
        kwargs = mlist.parse_merge_fields(params['merges'])
        if obj:
            kwargs['model_identifier'], kwargs['pk'] = _object_identifier(obj)

        for a in MailChimpEventAction.get_actions(list_pk, on_event='on_subscribed'):
            a.dispatch(**keys2str(kwargs))


@task(name='mailinglists.mailchimp_unsubscribe', ignore_result=True)
def mailchimp_unsubscribe(list_pk=None, fired_at=None, params=None, ip=None,
    user_agent=None):
    '''
    Email was unsubscribed from list.
    '''
    if params is None:
        params = {}

    logger = mailchimp_unsubscribe.get_logger()
    _log_webhook_action(logger, ip, user_agent, 'unsubscribe', list_pk)

    from djangoplicity.mailinglists.models import MailChimpEventAction

    mlist = _get_list(list_pk)
    obj = mlist.get_object_from_mergefields(params['merges'])
    kwargs = mlist.parse_merge_fields(params['merges'])
    kwargs['model_identifier'], kwargs['pk'] = _object_identifier(obj)

    for a in MailChimpEventAction.get_actions(list_pk, on_event='on_unsubscribe'):
        a.dispatch(**keys2str(kwargs))


@task(name='mailinglists.mailchimp_cleaned', ignore_result=True)
def mailchimp_cleaned(list_pk=None, fired_at=None, params=None, ip=None,
    user_agent=None):
    '''
    Email was removed from MailChimp list because it was invalid.
    Register bad email address and dispatch actions
    If list is linked, then get the object
    '''
    if params is None:
        params = {}

    logger = mailchimp_cleaned.get_logger()
    _log_webhook_action(logger, ip, user_agent, 'cleaned', list_pk)

    # Register bad email address
    from djangoplicity.mailinglists.models import BadEmailAddress

    email = params.get('email', '')

    # Prevent subscriber from being put any list again, unless explicitly
    # subscribing again.
    if email:
        BadEmailAddress.objects.get_or_create(email=email)

    # Dispatch actions
    from djangoplicity.mailinglists.models import MailChimpEventAction

    mlist = _get_list(list_pk)
    kwargs = {'email': email}

    if mlist.content_type and mlist.primary_key_field:
        # List is connected, so retrieve member info via email address so we
        # can determine the object id
        obj = mlist.get_object_from_mergefields(
            mlist.get_member_info(email=email)['merge_fields']
        )
        if not obj:
            return

        kwargs['model_identifier'], kwargs['pk'] = _object_identifier(obj)

    for a in MailChimpEventAction.get_actions(list_pk, on_event='on_cleaned'):
        a.dispatch(**keys2str(kwargs))


@task(name='mailinglists.mailchimp_upemail', ignore_result=True)
def mailchimp_upemail(list_pk=None, fired_at=None, params=None, ip=None,
    user_agent=None):
    '''
    User updated their email address.
    '''
    if params is None:
        params = {}

    logger = mailchimp_upemail.get_logger()
    _log_webhook_action(logger, ip, user_agent, 'upemail', list_pk)

    from djangoplicity.mailinglists.models import MailChimpEventAction

    for a in MailChimpEventAction.get_actions(list_pk, on_event='on_upemail'):
        a.dispatch(**keys2str(params))


@task(name='mailinglists.mailchimp_profile', ignore_result=True)
def mailchimp_profile(list_pk=None, fired_at=None, params=None, ip=None,
    user_agent=None ):
    '''
    User updated his profile
    '''
    if params is None:
        params = {}

    logger = mailchimp_profile.get_logger()
    _log_webhook_action(logger, ip, user_agent, 'profile', list_pk)

    from djangoplicity.mailinglists.models import MailChimpEventAction

    mlist = _get_list(list_pk)
    obj = mlist.get_object_from_mergefields(params['merges'])
    kwargs = mlist.parse_merge_fields(params['merges'])
    kwargs['model_identifier'], kwargs['pk'] = _object_identifier(obj)

    for a in MailChimpEventAction.get_actions(list_pk, on_event='on_profile'):
        a.dispatch(**keys2str(kwargs))


@task(name='mailinglists.mailchimp_campaign', ignore_result=True)
def mailchimp_campaign(list_pk=None, fired_at=None, params=None, ip=None,
    user_agent=None):
    '''
    Sent when a campaign is sent or cancelled
    '''
    if params is None:
        params = {}

    logger = mailchimp_campaign.get_logger()
    _log_webhook_action(logger, ip, user_agent, 'campaign', list_pk)

    from djangoplicity.mailinglists.models import MailChimpEventAction

    for a in MailChimpEventAction.get_actions(list_pk, on_event='on_campaign'):
        a.dispatch(**keys2str(params))


# =============
# Webhook tasks
# =============

@task(name='mailinglists.clean_tokens', ignore_result=True)
def clean_tokens():
    '''
    Remove invalid tokens from the database. A token is considered invalid
    10 minutes after it expired.
    '''
    ten_minutes_ago = datetime.now() - timedelta(minutes=10)
    MailChimpListToken.objects.filter(expired__lte=ten_minutes_ago).delete()


@task(name='mailinglists.webhooks', ignore_result=True)
def webhooks(list_id=None):
    '''
    Celery task for installing webhooks for lists in MailChimp. If ``list_id``
    is provided webhooks for only the specific list will be installed. If
    ``list_id`` is none, webhooks for all lists will be installed.
    '''
    # Only run on production
    if settings.SITE_ENVIRONMENT != 'prod':
        return

    logger = webhooks.get_logger()

    baseurl = 'https://{}{}'.format(
        Site.objects.get_current().domain,
        reverse('djangoplicity_mailinglists:mailchimp_webhook'),
    )

    # Check, one or many lists.
    queryargs = {
        'connected': True,
        'synchronize': True,
    }
    if list_id is not None:
        queryargs['list_id'] = list_id

    lists = MailChimpList.objects.filter(**queryargs)

    if not lists and list_id:
        raise Exception('List with list id %s does not exists' % list_id)

    for l in lists:
        logger.info('Adding/removing webhooks from list id %s' % l.list_id)

        # Create access token
        token = MailChimpListToken.create(l)
        hookurl = '{}?{}'.format(baseurl, urlencode(token.hook_params()))

        # Specify which events will trigger the webhook
        events = {
            'subscribe': True,
            'unsubscribe': True,
            'profile': True,
            'cleaned': True,
            'upemail': True,
            'campaign': True,
        }

        # Specifiy which sources of events will trigger the webhook
        sources = {
            'user': True,
            'admin': True,
            'api': False,
        }

        def create_webhook():
            # Create new webhook for the list
            # pylint: disable=cell-var-from-loop
            logger.info('Will run lists.webhooks.create for list %s with url %s'
                % (l.list_id, hookurl))
            l.connection(
                'lists.webhooks.create',
                l.list_id, {
                    'url': hookurl,
                    'events': events,
                    'sources': sources,
                }
            )

        # We use transaction.on_commit to make sure Mailchimp won't try to
        # validate the webhooks before they are commited to the DB
        transaction.on_commit(create_webhook)

        # Expire existing tokens for the list
        MailChimpListToken.objects.exclude(pk=token.pk).filter(
            list=l, expired__isnull=True
        ).update(expired=datetime.now())

        # Get list of all webhooks for the list
        logger.info('Will run lists.webhooks.all for list %s' % l.list_id)
        response = l.connection('lists.webhooks.all', l.list_id)

        for webhook in response['webhooks']:
            if not webhook['url'].startswith(baseurl):
                # This webhook was not installed by this site as it has
                # a different base URL, we ignore it
                continue

            if webhook['url'] == hookurl:
                # This is the webhook we just created
                continue

            logger.info('Will run lists.webhooks.delete for list %s with url %s'
                % (l.list_id, webhook['url']))
            l.connection('lists.webhooks.delete', l.list_id, webhook['id'])


@task(name='mailinglists.mailchimplist_fetch_info', ignore_result=True)
def mailchimplist_fetch_info(list_id=None):
    '''
    Celery task to fetch info from MailChimp and store it locally.
    '''
    logger = mailchimplist_fetch_info.get_logger()

    # Only run on production
    if settings.SITE_ENVIRONMENT != 'prod':
        return

    try:
        if list_id:
            lists = MailChimpList.objects.filter(list_id=list_id)
        else:
            lists = MailChimpList.objects.filter(synchronize=True)

        for chimplist in lists:
            logger.info('Fetching info for mailchimp list %s' % chimplist.list_id)
            chimplist.fetch_info()
            chimplist.save()
    except MailChimpList.DoesNotExist:
        raise Exception('MailChimpList %s does not exist.' % list_id)
