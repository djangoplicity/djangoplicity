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

from django.apps import apps
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.encoding import smart_unicode

from djangoplicity.actions.plugins import ActionPlugin  # pylint: disable=E0611

from djangoplicity.utils.history import add_admin_history  # pylint: disable=E0611


class MailmanAction(ActionPlugin):
    """
    An action plugin is a configureable celery task,
    that can be dynamically connected to events in the system.
    """
    action_parameters = [
        ('list_name', 'Mailman list name - must be defined in djangoplicity', 'str'),
    ]
    abstract = True

    @classmethod
    def get_arguments(cls, conf, *args, **kwargs):
        """
        Parse incoming arguments. Email lookup:
        1) if an 'email' kwarg is provided, then the value is used.
        2) otherwise
        """
        email = None
        if 'email' in kwargs:
            email = kwargs['email']
        else:
            for v in kwargs.values():
                if hasattr( v, 'email' ):
                    email = v.email
                    break

        return ( [], { 'email': email } )

    def _get_list(self, list_name):

        from djangoplicity.mailinglists.models import List
        return List.objects.get( name=list_name )


class MailmanSubscribeAction(MailmanAction):
    action_name = 'Mailman subscribe'

    def run(self, conf, email=None):
        """
        Subscribe to mailman list
        """
        if email:
            list = self._get_list( conf['list_name'] )
            list.subscribe( email=email, async=False )
            self.get_logger().info("Subscribed %s to mailman list %s" % ( email, list.name ) )


class MailmanUnsubscribeAction(MailmanAction):
    action_name = 'Mailman unsubscribe'

    def run(self, conf, email=None):
        """
        Unsubscribe from mailman list
        """
        if email:
            list = self._get_list( conf['list_name'] )
            list.unsubscribe( email=email, async=False )
            self.get_logger().info("Unsubscribed %s to mailman list %s" % ( email, list.name ) )


class MailmanUpdateAction( MailmanAction ):
    action_name = 'Mailman update subscription'

    @classmethod
    def get_arguments(cls, conf, *args, **kwargs):
        if 'instance' in kwargs and 'changes' in kwargs:
            instance = kwargs['instance']
            changes = kwargs['changes']
            model_identifier = smart_unicode( instance._meta )
            pk = smart_unicode( instance._get_pk_val(), strings_only=True )
            return ( [], { 'model_identifier': model_identifier, 'pk': pk, 'changes': changes } )

        return ( [], { 'model_identifier': None, 'pk': None, 'changes': {} } )

    def run(self, conf, model_identifier=None, changes={}, **kwargs ):
        """
        Email address was updated so change subscriber
        """
        if 'email' not in changes:
            return

        from_email, to_email = changes['email']

        if from_email != to_email and from_email is not None and to_email is not None:
            # from/to email can be empty but not none (empty basically means unsubscribe).
            list = self._get_list( conf['list_name'] )
            if from_email != '':
                list.unsubscribe( email=from_email, async=False )
                self.get_logger().info( "Unsubscribed %s to mailman list %s" % ( from_email, list.name ) )
            if to_email != '':
                list.subscribe( email=to_email, async=False )
                self.get_logger().info( "Subscribed %s to mailman list %s" % ( to_email, list.name ) )


class MailmanSyncAction( MailmanAction ):
    action_name = 'Mailman synchronize'
    action_parameters = MailmanAction.action_parameters + [
        ('remove_existing', 'Remove any mailman subscriber not defined in djangoplicity.', 'bool'),
    ]

    @classmethod
    def get_arguments( cls, conf, *args, **kwargs ):
        model_identifier = None
        pk = None
        for v in kwargs.values():
            if isinstance( v, models.Model ) and hasattr( v, 'get_emails' ) and callable( v.get_emails ):
                model_identifier = smart_unicode( v._meta )
                pk = smart_unicode( v._get_pk_val(), strings_only=True )
                break
        return ( [], { 'model_identifier': model_identifier, 'pk': pk } )

    def _get_emails( self, model_identifier, pk ):
        """
        Get the list of emails to synchronize
        """
        cls = apps.get_model( *model_identifier.split( "." ) )
        obj = cls.objects.get( pk=pk )
        return obj, obj.get_emails()

    def run( self, conf, model_identifier=None, pk=None ):
        """
        """
        if model_identifier and pk:
            obj, emails = self._get_emails( model_identifier, pk )
            mlist = self._get_list( conf['list_name'] )

            # Convert from ValuesListQuerySet to list:
            emails = list(emails)

            mailman_emails = mlist.get_mailman_emails()
            for email in set(emails) - mailman_emails:
                # Remove contact from the group
                try:
                    c = obj.contact_set.get(email=email)
                except ObjectDoesNotExist:
                    continue

                obj.contact_set.remove(c)
                emails.remove(email)
                self.get_logger().info(u'Removed %s from %s' % (c, obj))
                add_admin_history(c,
                    'Mailman Sync (%s): Removed from %s' %
                    (conf['list_name'], obj)
                )

                # Add contact to 'unsub' group (create group if it doesn't exist)
                cls = apps.get_model(*model_identifier.split( "." ))
                l, _created = cls.objects.get_or_create(name='unsub_%s' % obj.name)

                c.groups.add(l)
                self.get_logger().info(u'Added %s to %s' % (c, l))
                add_admin_history(c,
                    'Mailman Sync (%s): Added to group %s' %
                    (conf['list_name'], l)
                )

            mlist.update_subscribers( emails )
            mlist.push( remove_existing=conf['remove_existing'] )


MailmanSubscribeAction.register()
MailmanUnsubscribeAction.register()
MailmanUpdateAction.register()
MailmanSyncAction.register()
