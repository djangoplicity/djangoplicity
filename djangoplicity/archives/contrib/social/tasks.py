# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>

import requests

from celery.task import task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


@task
def facebook_refresh(url):
    '''
    Asks Facebook to re-scrape information from the URL
    '''
    for proto in ('http', 'https'):
        data = {'id': '%s://%s' % (proto, url), 'scrape': 'true'}
        requests.post('https://graph.facebook.com', data=data)

    logger.info('Updated Facebook information for: "%s"', url)
