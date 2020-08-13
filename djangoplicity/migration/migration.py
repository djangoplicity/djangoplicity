# -*- coding: utf-8 -*-
#
# djangoplicity-migration
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

from builtins import str
from builtins import object
import logging
from django.contrib.redirects.models import Redirect


def get_logger( conf ):
    if 'logger' in conf:
        name = conf['logger']

    return logging.getLogger( name )


def run_migration( conf, tasks ):
    """
    Execute a complete migration defined by the supplied
    configuration and tasks.

    A global state is maintained and passed to each migration task which
    can decide to use information from the global state or add information
    to it.

    The state is a simple dictionary of values with certain reserved names.

    Usually you'll want to run this method from an import scripts that defines
    your migration.
    """
    i = 1
    total = len(tasks)

    logger = get_logger( conf )
    logger.info("Migration started (%s tasks)...", total )

    state = {}
    for t in tasks:
        logger.info("Running %s (%s out of %s)...", t.__class__.__name__, i, total)
        t.set_conf( conf )
        t.state = state
        try:
            t.run()
        except MigrationError as e:
            if e.can_continue:
                logger.error( "Task failed: %s", e )
            else:
                logger.critical( "Task failed and cannot continue migration: %s", e )
#       except Exception, e:
#           logger.critical( "Unknwon error - stopping migration: %s" % e )
#           break
        state = t.state
        i += 1

    logger.info("Migration finished..." )


class MigrationConfAdapter( object ):
    """
    Class for adding logger capabilities to task and classes.
    """
    conf_injection = []

    def _logger(self):
        return get_logger( self.conf )

    #  Retrieve logger defined in configuration or create new logger
    logger = property( fget=_logger )

    def set_conf( self, conf ):
        """
        Inject configuration into migration task. This will happen just before
        the migration task is executed.
        """
        self.conf = conf

        for a in self.conf_injection:
            try:
                obj = getattr( self, str(a) )
                self.inject_conf( obj )
            except AttributeError:
                pass

    def inject_conf( self, obj ):
        """
        Inject configuration from this object into another object
        """
        if isinstance( obj, MigrationConfAdapter ):
            obj.set_conf( self.conf )


class MigrationError( Exception ):
    """
    Exception to signal an error in a migration task.
    """
    def __init__( self, message, can_continue=True ):
        self.can_continue = can_continue
        super( MigrationError, self ).__init__( message )


class MigrationTask( MigrationConfAdapter ):
    """
    Base class for any kind of migration task providing a minimial interface and
    some helper methods.
    """
    def __init__( self ):
        self.conf = {}

    def run(self):
        """
        Run this migration task. Method that should be overwritten in a subclass of migration task.
        """
        pass

    def _set_state( self, state ):
        """
        Method for ingesting the current global state into the migration before
        migration task is executed.
        """
        self._state = state

    def _get_state( self ):
        """
        Retrieval of global state after migration task have finished.
        """
        tmp = self._state
        self._state = None
        return tmp

    state = property( fget=_get_state, fset=_set_state )


class RedirectTask( MigrationTask ):
    """
    Task for setting up a list of redirects manually.

    RedirectTask( { '<old_path>' : '<newpath>', ... } )
    """
    def __init__( self, redirects ):
        self._redirects = redirects
        super( RedirectTask, self ).__init__()

    def run(self):
        for old, new in list(self._redirects.items()):
            r, created = Redirect.objects.get_or_create( site=self.conf['pages']['site'], old_path=old )
            if created:
                r.new_path = new
                self.logger.info("Created redirect from %s to %s) ..." % (r.old_path, r.new_path) )
            else:
                if r.new_path != new:
                    self.logger.warn("Redirect for %s already exists (%s, %s) ..." % (old, r.new_path, new) )
            r.save()
