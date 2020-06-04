# -*- coding: utf-8 -*-
#
# djangoplicity-celery
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

import os
from importlib import import_module

from celery.signals import task_failure
from celery.task import task
from celery.utils.log import get_task_logger

from django.conf import settings
from django.core.mail import mail_admins

logger = get_task_logger(__name__)

@task
def clearsessions():
    engine = import_module(settings.SESSION_ENGINE)
    engine.SessionStore.clear_expired()
    logger.info('Cleared Django sessions')


@task_failure.connect()
def celery_task_failure_email(**kwargs):
    '''
	Celery 4.0 onward has no method to send emails on failed tasks
    so this event handler is intended to replace it
    Only runs on production systems
    '''
    if os.environ.get('ENVIRONMENT') != 'prod':
        return

    host = os.environ.get('SERVER')

    error = unicode(kwargs['exception']).replace('\n', '')

    subject = u'[{host}] Error: Task {sender.name} ({task_id}): {error}'.format(
        queue_name=u'celery',  # `sender.queue` doesn't exist in 4.1?
        host=host,
        error=error,
        **kwargs
    )

    message = u'''Task {sender.name} with id {task_id} raised exception:
{exception!r}


Task was called with args: {args} kwargs: {kwargs}.

The contents of the full traceback was:

{einfo}
    '''.format(
        **kwargs
    )

    mail_admins(subject, message)
