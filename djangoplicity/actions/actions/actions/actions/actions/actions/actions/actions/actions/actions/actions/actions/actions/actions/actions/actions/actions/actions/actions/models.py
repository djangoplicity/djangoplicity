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

from django.core.cache import cache
from django.db import models
from django.db.models.signals import post_save

from djangoplicity.actions.plugins import ActionPlugin

logger = logging.getLogger( 'djangoplicity' )


class Action( models.Model ):
    """
    Model for defining actions ( plugin + configuration )
    """
    _plugins = {}

    plugin = models.CharField( max_length=255, choices=[] )
    name = models.CharField( max_length=255 )

    def __init__( self, *args, **kwargs ):
        """
        Set choices for plugin field dynamically based on registered plugins.
        """
        super( Action, self ).__init__( *args, **kwargs )
        self._meta.get_field( 'plugin' )._choices = Action.get_plugin_choices()

    def get_plugincls( self ):
        """
        Get the plug-in class for this action.
        """
        try:
            return self._plugins[ self.plugin ]
        except KeyError:
            raise Exception( "Plug-in %s does not exists." % self.plugin )

    def get_plugin( self ):
        """
        Get an instance of the plug-in for this action
        """
        cls = self.get_plugincls()
        return cls( self.get_parameters() )

    def get_parameters( self ):
        """
        Get parameters to be send to the action
        """
        return dict( [( p.name, p.get_value() ) for p in ActionParameter.objects.filter( action=self ) ] )

    def dispatch( self, *args, **kwargs ):
        """
        Execute action - note the action will be executed in the background.
        """
        plugincls = self.get_plugincls()
        plugincls.dispatch( self.get_parameters(), *args, **kwargs )

    @classmethod
    def register_plugin( cls, actioncls ):
        """
        Register a new action plug-in.
        """
        if issubclass( actioncls, ActionPlugin ):
            cls._plugins[actioncls.get_class_path()] = actioncls

    @classmethod
    def get_plugin_choices( cls ):
        """
        Get list of action plug-in choices
        """
        choices = [ ( p, pcls.action_name ) for p, pcls in cls._plugins.items() ]
        choices.sort( key=lambda x: x[1] )
        return list( choices )

    @classmethod
    def post_save_handler( cls, sender=None, instance=None, created=False, raw=False, using=None, **kwargs ):
        """
        Callback to save a blank value for all parameters for this plugin and remove unknown parameters
        """
        if instance and not raw:
            known_params = dict( [( p.name, p ) for p in ActionParameter.objects.filter( action=instance )] )

            for p, desc, t in instance.get_plugincls().action_parameters:
                touched = False
                try:
                    param = ActionParameter.objects.get( action=instance, name=p )
                except ActionParameter.DoesNotExist:
                    param = ActionParameter( action=instance, name=p )
                    touched = True

                for attr, val in [( 'type', t ), ( 'help_text', desc )]:
                    if getattr( param, attr ) != val:
                        setattr( param, attr, val )
                        touched = True

                if touched:
                    param.save()

                try:
                    del known_params[ param.name ]
                except KeyError:
                    pass

            # Delete unknown parameters
            for param in known_params.values():
                param.delete()

    def __unicode__( self ):
        return "%s: %s" % ( self.get_plugincls().name, self.name )

    class Meta:
        ordering = ['name']


class ActionParameter( models.Model ):
    """
    Parameter for an action
    """
    action = models.ForeignKey( Action )
    name = models.SlugField( max_length=255, unique=False )
    value = models.CharField( max_length=255, blank=True, default='' )
    type = models.CharField( max_length=4, default='str', choices=[ ( 'str', 'Text' ), ( 'int', 'Integer' ), ( 'bool', 'Boolean' ), ( 'date', 'Date' ), ] )
    help_text = models.CharField( max_length=255, blank=True )

    def get_value( self ):
        """
        Return value in the proper type
        """
        if self.type == 'str':
            return self.value
        elif self.type == 'int':
            try:
                return int( self.value )
            except ValueError:
                return None
        elif self.type == 'bool':
            return ( self.value ).lower() == 'true'
        elif self.type == 'date':
            return self.value

    def __unicode__( self ):
        return u"%s = %s (%s)" % ( self.name, self.value, self.type )

    class Meta:
        ordering = ['action', 'name']
        unique_together = ['action', 'name']


class ActionLog( models.Model ):
    """
    Logging of executed actions
    """
    timestamp = models.DateTimeField( auto_now_add=True )
    success = models.BooleanField( default=True )
    plugin = models.CharField( max_length=255 )
    name = models.CharField( max_length=255 )
    parameters = models.TextField( blank=True )
    args = models.TextField( blank=True )
    kwargs = models.TextField( blank=True )
    error = models.TextField( blank=True )

    class Meta:
        ordering = ['-timestamp']


class EventAction( models.Model ):
    action = models.ForeignKey( Action )
    on_event = models.CharField( max_length=50, choices=[], db_index=True )

    @classmethod
    def _get_key( cls ):
        """
        _key class variable must be specified by each subclass.
        """
        raise NotImplementedError
    _key = property( _get_key )

    def save( self, *args, **kwargs ):
        super( EventAction, self ).save( *args, **kwargs )
        self.clear_cache()

    @classmethod
    def clear_cache( cls, *args, **kwargs ):
        """
        Ensure cache is reset in case any change is made.
        """
        logger.debug( "clearing action cache" )
        cache.delete( cls._key )

    @classmethod
    def create_cache( cls, *args, **kwargs ):
        """
        Generate new action cache.

        The cache has two ways of indexing:
            * by related object then event
            * or, event then related object

        Since ``rel_pk'' are always numbers, and ``on_event'' is
        always characters, the keys will not collide.

        cache = {
            '<rel_pk>' : {
                '<on_event>' : [ <action>, ... ],
                ...
            },
            ...
            '<on_event>' : {
                '<rel_pk>' : [ <action>, ... ],
                '<rel_pk>' : [ <action>, ... ],
            },
            ...
        }
        """
        logger.debug( "generating action cache" )
        action_cache = {}
        for a in cls.objects.all().select_related('action').order_by( 'model_object', 'on_event', 'action' ):
            g_pk = str( a.model_object.pk )
            # by group_pk, event
            if g_pk not in action_cache:
                action_cache[ g_pk ] = {}
            if a.on_event not in action_cache[g_pk]:
                action_cache[ g_pk ][a.on_event] = []

            if a.on_event not in action_cache:
                action_cache[a.on_event] = {}
            if g_pk not in action_cache[a.on_event]:
                action_cache[a.on_event][ g_pk ] = []

            action_cache[ g_pk ][a.on_event].append( a.action )
            action_cache[ a.on_event ][g_pk].append( a.action )

            # by event, group_pk = actions

        cache.set( cls._key, action_cache )
        return action_cache

    @classmethod
    def get_cache( cls ):
        """
        Get the action cache - generate it if necessary.

        Caches results to prevent many queries to the database. Currently the entire
        table is cached, however in case of issues, this caching strategy can be improved.
        """
        action_cache = cache.get( cls._key )

        # Prime cache if needed
        if action_cache is None:
            action_cache = cls.create_cache()

        return action_cache

    @classmethod
    def get_actions_for_event( cls, on_event, pk=None ):
        """
        """
        action_cache = cls.get_cache()

        try:
            actions = action_cache[on_event]
            return actions if pk is None else actions[str( pk )]
        except:
            return {} if pk is None else []

    @classmethod
    def get_actions( cls, pk, on_event=None ):
        """
        Get all actions defined for a certain group.
        """
        action_cache = cls.get_cache()

        if isinstance( pk, models.Model ):
            pk = pk.pk

        # Find actions for this group
        try:
            actions = action_cache[ str( pk ) ]
            return actions if on_event is None else actions[on_event]
        except KeyError:
            return {} if on_event is None else []

    class Meta:
        abstract = True

# Connect signal handlers
post_save.connect( Action.post_save_handler, sender=Action )
