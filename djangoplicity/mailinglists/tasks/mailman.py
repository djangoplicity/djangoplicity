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
from django.conf import settings


@task( name="mailinglists.mailman_send_subscribe", ignore_result=True )
def mailman_send_subscribe( subscription_pk ):
    """
    Task to subscribe an email to a mailman list. Task is executed
    when e.g. a person subscribes via e.g. mailchimp.
    """
    # Only run on production
    if settings.SITE_ENVIRONMENT != 'prod':
        return

    from djangoplicity.mailinglists.models import Subscription

    logger = mailman_send_unsubscribe.get_logger()

    sub = Subscription.objects.get( pk=subscription_pk )
    sub.list.mailman._subscribe( sub.subscriber.email )

    logger.info( "Subscribed %s to mailman list %s" % ( sub.subscriber.email, sub.list.name ) )


@task( name="mailinglists.mailman_send_unsubscribe", ignore_result=True )
def mailman_send_unsubscribe( subscription_pk ):
    """
    Task to subscribe an email to a mailman list. Task is executed
    when e.g. a person subscribes via e.g. mailchimp.
    """
    # Only run on production
    if settings.SITE_ENVIRONMENT != 'prod':
        return

    from djangoplicity.mailinglists.models import Subscription

    logger = mailman_send_unsubscribe.get_logger()

    sub = Subscription.objects.get( pk=subscription_pk )
    email = sub.subscriber.email
    sub.delete()

    sub.list.mailman._unsubscribe( sub.subscriber.email )

    logger.info( "Unsubscribed %s from mailman list %s" % email )
