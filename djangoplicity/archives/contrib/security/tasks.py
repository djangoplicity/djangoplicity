# Djangoplicity
# Copyright 2007-2008 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

from celery.task import task


@task
def update_static_files_protection_cache():
    """
    Celery task to run static files protection
    """
    from djangoplicity.archives.contrib.security import StaticFilesProtectorCache
    logger = update_static_files_protection_cache.get_logger()

    logger.info('Running static file protection for all')
    StaticFilesProtectorCache.run()
    logger.info('Finished running static file protection')
