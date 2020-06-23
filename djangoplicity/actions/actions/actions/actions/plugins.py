# -*- coding: utf-8 -*-
#
# djangoplicity-actions
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
Djangoplicity Actions
"""

import logging

from celery.task import Task

from django.conf import settings
from django.db import transaction

logger = logging.getLogger(__name__)


class ActionPlugin( Task ):
    """
    Interface for action plugins. The plugin itself is responsible for
    consuming the configurable parameters that it is given in the
    init constructor.

    Example of bare minium plugin::

        class SimpleAction( ActionPlugin ):
            action_name = 'Simple action'

            def run( self, conf ):
                print "Run"

        SimpleAction.register()
    """
    abstract = True

    action_name = ''
    action_parameters = []

    def run( self, conf, *args, **kwargs ):
        """
        This method must be implemented by every subclass.
        """
        raise NotImplementedError

    def on_failure( self, exc, task_id, args, kwargs, einfo ):
        """
        Log a failure
        """
        from djangoplicity.actions.models import ActionLog

        ActionLog(
            success=False,
            plugin=self.get_class_path(),
            name=self.action_name,
            parameters=';'.join( [ "%s = %s" % ( unicode( k ), unicode( v ) ) for k, v in args[0].items() ] ),
            args='; '.join( [unicode( x ) for x in args[1:]] ),
            kwargs=';'.join( [ "%s = %s" % ( unicode( k ), unicode( v ) ) for k, v in kwargs.items() ] ),
            error=einfo.traceback,
        ).save()

    def on_success( self, retval, task_id, args, kwargs ):
        """
        Log a success
        """
        from djangoplicity.actions.models import ActionLog
        ActionLog(
            success=True,
            plugin=self.get_class_path(),
            name=self.action_name,
            parameters=';'.join( [ "%s = %s" % ( unicode( k ), unicode( v ) ) for k, v in args[0].items() ] ),
            args='; '.join( [unicode( x ) for x in args[1:]] ),
            kwargs=';'.join( [ "%s = %s" % ( unicode( k ), unicode( v ) ) for k, v in kwargs.items() ] ),
        ).save()

    @classmethod
    def dispatch( cls, conf, *args, **kwargs ):
        """
        Method is called by Action.dispatch together with the desired configuration.

        Custom processing of the input parameters can be done via the get_arguments_method.
        """
        if settings.SITE_ENVIRONMENT != 'prod':
            logger.info('Actions are only run on production system, won\'t run: %s', cls)
            return

        args, kwargs = cls.get_arguments( conf, *args, **kwargs )
        transaction.on_commit(
            lambda: cls.delay( conf, *args, **kwargs )
        )

    @classmethod
    def get_arguments( cls, conf, *args, **kwargs ):
        """
        Custom processing of input parameters (e.g. convert objects to primary keys).

        By default the input arguments are just passed through.
        """
        return ( args, kwargs )

    @classmethod
    def get_class_path( cls ):
        """
        Get the complete import path for this module.
        """
        return "%s.%s" % ( cls.__module__, cls.__name__ )

    @classmethod
    def register( cls ):
        """
        Register plugin.
        """
        from djangoplicity.actions.models import Action
        Action.register_plugin( cls )
