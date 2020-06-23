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

from django.apps import apps
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils.encoding import smart_unicode

from djangoplicity.actions.plugins import ActionPlugin  # pylint: disable=E0611


class MailChimpAction(ActionPlugin):
    '''
    An action plugin is a configurable celery task,
    that can be dynamically connected to events in the system.
    '''
    action_parameters = [
        ('list_id', 'MailChimp list id - must be defined in djangoplicity', 'str'),
    ]

    @classmethod
    def get_arguments(cls, conf, *args, **kwargs):
        model_identifier = None
        pk = None
        for val in list(args) + list(kwargs.values()):
            if isinstance(val, models.Model):
                try:
                    val._meta.get_field('email')

                    # Same method as used in django.core.serializer.python
                    model_identifier = smart_unicode(val._meta)
                    pk = smart_unicode(val._get_pk_val(), strings_only=True)
                    break
                except FieldDoesNotExist:
                    pass

        result = {'model_identifier': model_identifier, 'pk': pk}
        if 'email' in kwargs:
            result['email'] = kwargs['email']

        return ([], result)

    def _get_object(self, model_identifier, pk):
        """
        Helper method to get the object being linked to.
        """
        # Same method as used in django.core.serializer.python
        Model = apps.get_model(*model_identifier.split("."))
        return Model.objects.get(pk=pk)

    def _get_list(self, list_id):
        from djangoplicity.mailinglists.models import MailChimpList
        return MailChimpList.objects.get(list_id=list_id)


class MailChimpSubscribeAction(MailChimpAction):
    action_name = 'MailChimp subscribe'
    action_parameters = MailChimpAction.action_parameters + [
        ('double_optin', 'Flag to control whether a double opt-in confirmation '
            'message is sent, defaults to true. Abusing this may cause our '
            'MailChimp account to be suspended.', 'bool'),
        ('send_welcome', 'If double_optin is false and this is true, a welcome '
            'email will be sent if this subscribe succeeds. If double_optin is '
            'true, this has no effect. defaults to false.', 'bool'),
    ]

    def run(self, conf, model_identifier=None, pk=None):
        '''
        Subscribe to MailChimp list
        '''
        if model_identifier and pk:
            obj = self._get_object(model_identifier, pk)
            mlist = self._get_list(conf['list_id'])
            merge_fields = mlist.create_merge_fields(obj)

            if not obj.email:
                self.get_logger().info('Can\'t subscribe contact %d to '
                    'MailChimp list %s: no email address' % (obj.id, mlist.name))
                return

            mlist.subscribe(
                obj.email,
                merge_fields=merge_fields,
                double_optin=conf['double_optin'],
                send_welcome=conf['send_welcome'],
                async=False,
            )
            self.get_logger().info(
                'Subscribed %s to MailChimp list %s' % (obj.email, mlist.name))

            # except Exception, e:
            #   if '%s is a known bad email address' % obj.email in e.message:
            #       # Mailchimp knows that this address is invalid, so we update the contact accordingly
            #       obj.email += '-INVALID'
            #       obj.save()
            #   else:
            #       raise e


class MailChimpUnsubscribeAction(MailChimpAction):
    action_name = 'MailChimp unsubscribe'
    action_parameters = MailChimpAction.action_parameters + [
        ('delete_member', 'Flag to completely delete the member from your list instead of just unsubscribing, default to false (unsubscribed members cannot be re-subscribed).', 'bool'),
        ('send_goodbye', 'Flag to send the goodbye email to the email address, defaults to true.', 'bool'),
    ]

    def run(self, conf, model_identifier=None, pk=None, email=None):
        """
        Unsubscribe from MailChimp list
        """
        if model_identifier and pk:
            try:
                email = self._get_object(model_identifier, pk).email
            except:  # pylint: disable=W0702
                # Couldn't find matching object, try with the email
                email = email if email else ''

            if email:
                list = self._get_list(conf['list_id'])
                list.unsubscribe(email, delete_member=conf['delete_member'], send_goodbye=conf['send_goodbye'], async=False)
                self.get_logger().info("Unsubscribed %s from MailChimp list %s" % (email, list.name))


class MailChimpUpdateAction(MailChimpAction):
    action_name = 'MailChimp update subscription'
    action_parameters = MailChimpAction.action_parameters + [
        ('double_optin', 'Flag to control whether a double opt-in confirmation message is sent, defaults to true. Abusing this may cause our MailChimp account to be suspended.', 'bool'),
        ('send_welcome', 'If double_optin is false and this is true, a welcome email will be sent if this subscribe succeeds. If double_optin is true, this has no effect. defaults to false.', 'bool'),
        ('delete_member', 'Flag to completely delete the member from your list instead of just unsubscribing, default to false.', 'bool'),
        ('send_goodbye', 'Flag to send the goodbye email to the email address, defaults to true.', 'bool'),
    ]

    @classmethod
    def get_arguments(cls, conf, *args, **kwargs):
        if 'instance' in kwargs and 'changes' in kwargs:
            instance = kwargs['instance']
            changes = kwargs['changes']
            model_identifier = smart_unicode(instance._meta)
            pk = smart_unicode(instance._get_pk_val(), strings_only=True)
            return ([], {'model_identifier': model_identifier, 'pk': pk, 'changes': changes})

        return ([], {'model_identifier': None, 'pk': None, 'changes': {}})

    def run(self, conf, model_identifier=None, pk=None, changes=None):
        """
        Email address was updated so change subscriber
        """
        if changes is None:
            changes = {}

        if model_identifier and pk:
            obj = self._get_object(model_identifier, pk)
            list = self._get_list(conf['list_id'])

            # We use get_language instead of language to get the full
            # name for the language. In order to match 'language' in the
            # changes we use a bit of a hack:
            if 'language' in changes:
                changes['get_language'] = changes['language']

            # Email changed
            try:
                (before, after) = changes['email']
            except KeyError:
                (before, after) = '', ''

            before = before.strip()
            after = after.strip()
            if before != after:
                if before == '':
                    # No email before, so wasn't subscribed.
                    merge_fields = list.create_merge_fields(obj)
                    list.subscribe(after, merge_fields=merge_fields, double_optin=conf['double_optin'], send_welcome=conf['send_welcome'], async=False)
                    self.get_logger().info("Subscribed email address '%s' to MailChimp list %s" % (after, list.name))
                else:
                    if after.strip() == '':
                        # Unsubscribe email, since new email is empty
                        list.unsubscribe(before, delete_member=conf['delete_member'], send_goodbye=conf['send_goodbye'], async=False)
                        self.get_logger().info("Unsubscribed email address '%s' from MailChimp list %s" % (before, list.name))
                    else:

                        merge_fields = list.create_merge_fields(obj, changes=changes)
                        list.update_profile(before, after, merge_fields=merge_fields, async=False)
                        self.get_logger().info("Changed email address from '%s' to '%s' on MailChimp list %s" % (before, after, list.name))
            else:
                # Email was not updated - other parts was changed
                merge_fields = list.create_merge_fields(obj, changes=changes)
                list.update_profile(obj.email, obj.email, merge_fields=merge_fields, async=False)
                self.get_logger().info("Updated profile of subscriber with email address '%s' on MailChimp list %s" % (obj.email, list.name))


MailChimpSubscribeAction.register()
MailChimpUnsubscribeAction.register()
MailChimpUpdateAction.register()
#MailChimpSyncAction.register()
