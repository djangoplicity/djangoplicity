# -*- coding: utf-8 -*-
#
# Djangoplicity
# Copyright 2007-2010 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#

import logging
import logging.handlers
import os
from django.conf import settings


def define_logger( name, level=logging.INFO, file_logging=True, logdir=None, max_size=100 ):
    """
    Helper method for defining a Python logger.
    """
    logger = logging.getLogger( name )
    if settings.DEBUG:
        logger.setLevel( logging.DEBUG )
    else:
        logger.setLevel( level )

    formatter = logging.Formatter( '%(asctime)s %(levelname)-8s %(message)s', '%a, %d %b %Y %H:%M:%S' )

    if file_logging and logdir is not None:
        logfile = os.path.join( logdir, name + ".log" )
        handler = logging.handlers.RotatingFileHandler( logfile, maxBytes=max_size * 1024 * 1024, backupCount=5 )
        handler.setFormatter( formatter )
        logger.addHandler( handler )
    else:
        handler = logging.StreamHandler()
        handler.setFormatter( formatter )
        logger.addHandler( handler )

    return logger
