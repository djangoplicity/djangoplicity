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

import hashlib
import logging
import uuid as uuidmod
from datetime import datetime, timedelta
from urllib import urlencode
from requests.exceptions import HTTPError

from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError

from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.validators import validate_email
from django.db import models
from django.db.models.signals import post_save
from django.utils.encoding import smart_unicode

from djangoplicity.actions.models import EventAction  # pylint: disable=no-name-in-module
from djangoplicity.mailinglists.mailman import MailmanList


logger = logging.getLogger(__name__)

# Work around fix - see http://stackoverflow.com/questions/1210458/how-can-i-generate-a-unique-id-in-python
uuidmod._uuid_generate_time = None
uuidmod._uuid_generate_random = None

# Settings
NEWSLETTERS_MAILCHIMP_APIKEY = settings.NEWSLETTERS_MAILCHIMP_APIKEY if hasattr(settings, 'NEWSLETTERS_MAILCHIMP_APIKEY') else ''


def _object_identifier(obj):
    '''
    Return an objects identifier for a model object (e.g. contacts.contact:2579)
    '''
    if isinstance(obj, models.Model):
        return '{}:{}'.format(
            smart_unicode(obj._meta),
            smart_unicode(obj.pk, strings_only=True),
        )
    else:
        return ''


# Models

class BadEmailAddress(models.Model):
    '''
    Bad email addresses which was found to bounce back emails.
    '''
    email = models.EmailField(unique=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.email

    class Meta:
        ordering = ('email', )
        verbose_name_plural = 'bad email addresses'


class Subscriber(models.Model):
    '''
    Subscriber (i.e an email address) to one or more lists.
    '''
    email = models.EmailField(unique=True)

    def __unicode__(self):
        return self.email

    class Meta:
        ordering = ('email', )


class List(models.Model):
    """
    Mailman list
    """
    base_url = models.CharField(max_length=255)
    name = models.SlugField(unique=True)
    password = models.SlugField()
    subscribers = models.ManyToManyField(Subscriber, through='Subscription', blank=True)
    last_sync = models.DateTimeField(blank=True, null=True)

    def _get_mailman(self):
        """
        Get object for manipulating mailman list.
        """
        return MailmanList(name=self.name, password=self.password, main_url=self.base_url)
    mailman = property(_get_mailman)

    def subscribe(self, subscriber=None, email=None, async=True):
        """
        Subscribe a user to this list.
        """
        if not subscriber:
            if email:
                try:
                    BadEmailAddress.objects.get(email=email)
                    raise Exception("%s is a known bad email address" % email)
                except BadEmailAddress.DoesNotExist:
                    pass

                (subscriber, dummy_created) = Subscriber.objects.get_or_create(email=email)
            else:
                raise Exception("Please provide either subscriber or email address")

        sub = Subscription(list=self, subscriber=subscriber)
        sub.save()

        if async:
            from djangoplicity.mailinglists.tasks import mailman_send_subscribe
            mailman_send_subscribe.delay(sub.pk)
        else:
            self._subscribe(subscriber.email)

    def unsubscribe(self, subscriber=None, email=None, async=True):
        """
        Unsubscribe a user to this list.
        """
        try:
            if subscriber:
                sub = Subscription.objects.get(list=self, subscriber=subscriber)
            elif email:
                sub = Subscription.objects.get(list=self, subscriber__email=email)
            else:
                raise Exception("Expected either subscriber or email keyword arguments to be provided.")

            if async:
                from djangoplicity.mailinglists.tasks import mailman_send_unsubscribe
                mailman_send_unsubscribe.delay(sub.pk)
            else:
                email = sub.subscriber.email
                sub.delete()
                self._unsubscribe(email)
        except Subscription.DoesNotExist, e:
            raise e

    def _subscribe(self, email):
        """
        Method that will directly subscribe an email to this list (normally called from
        a background task.)
        """
        try:
            self.mailman.subscribe(email)
        except Exception as e:
            # django-mailman raises a standard exception if the member
            # already exists so we check the exception message:
            if e.message.lower() != 'error subscribing: %s -- already a member' % email.lower():
                raise e

    def _unsubscribe(self, email):
        """
        Method that will directly unsubscribe an email to this list (normally called from
        a background task.
        """
        self.mailman.unsubscribe(email)

    def get_mailman_emails(self):
        """
        Get all current mailman subscribers.
        """
        mailman_members = self.mailman.get_members()

        if mailman_members:
            mailman_emails, _mailman_names = zip(*mailman_members)
            mailman_emails = set(mailman_emails)
        else:
            mailman_emails = set()

        return mailman_emails

    def update_subscribers(self, emails):
        """
        Update the list of subscribers to match a list of emails.
        """
        emails = dict([(x, 1) for x in emails])  # Remove duplicates

        for sub in Subscription.objects.filter(list=self).select_related('subscriber', 'list'):
            if sub.subscriber.email in emails:
                del emails[sub.subscriber.email]
            else:
                # Delete all subscribers not in the list
                sub.delete()

        bad_emails = set(BadEmailAddress.objects.all().values_list('email', flat=True))
        emails = set(emails.keys())  # pylint: disable=redefined-variable-type

        # Subscribe all emails not in subscribers.
        for email in emails - bad_emails:
            (subscriber, dummy_created) = Subscriber.objects.get_or_create(email=email)
            sub = Subscription(list=self, subscriber=subscriber)
            sub.save()

    def push(self, remove_existing=True):
        """
        Push entire list of subscribers to mailman (will overwrite anything in Mailman)
        """
        mailman_emails = self.get_mailman_emails()
        django_emails = set(self.subscribers.all().values_list('email', flat=True))

        subscribe = django_emails - mailman_emails
        unsubscribe = mailman_emails - django_emails

        for e in subscribe:
            self._subscribe(e)

        if remove_existing:
            for e in unsubscribe:
                self._unsubscribe(e)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)


class Subscription(models.Model):
    """
    Relation between subscribers and lists.
    """
    subscriber = models.ForeignKey(Subscriber)
    list = models.ForeignKey(List)

    def __unicode__(self):
        return "%s subscribed to %s" % (self.subscriber, self.list)

    class Meta:
        unique_together = ('subscriber', 'list')
        ordering = ('subscriber__email',)


class MailChimpList(models.Model):
    '''
    A list already defined in MailChimp.

    Most information will be fetched directly from MailChimp.
    '''
    # Model properties defined in djangoplicity
    api_key = models.CharField(max_length=255, verbose_name="API key",
        default=NEWSLETTERS_MAILCHIMP_APIKEY)
    list_id = models.CharField(unique=True, max_length=50)

    synchronize = models.BooleanField(default=False)
    # Enable list to be sync'ed with mailchimp.

    # Model properties replicated from MailChimp
    name = models.CharField(max_length=255, blank=True)
    web_id = models.CharField(blank=True, max_length=255)
    email_type_option = models.CharField(max_length=50, blank=True)
    default_from_name = models.CharField(max_length=255, blank=True)
    default_from_email = models.CharField(max_length=255, blank=True)
    default_subject = models.CharField(max_length=255, blank=True)
    default_language = models.CharField(max_length=10, blank=True)
    list_rating = models.IntegerField(blank=True, null=True)
    member_count = models.IntegerField(blank=True, null=True)
    unsubscribe_count = models.IntegerField(blank=True, null=True)
    cleaned_count = models.IntegerField(blank=True, null=True)
    member_count_since_send = models.IntegerField(blank=True, null=True)
    unsubscribe_count_since_send = models.IntegerField(blank=True, null=True)
    cleaned_count_since_send = models.IntegerField(blank=True, null=True)
    avg_sub_rate = models.IntegerField(blank=True, null=True, help_text="per month")
    avg_unsub_rate = models.IntegerField(blank=True, null=True, help_text="per month")
    target_sub_rate = models.IntegerField(blank=True, null=True, help_text="per month")
    open_rate = models.IntegerField(blank=True, null=True, help_text="per campaign")
    click_rate = models.IntegerField(blank=True, null=True, help_text="per campaign")

    # Status properties
    connected = models.BooleanField(default=False)
    # Designates if the list is being successfully sync'ed with MailChimp.

    last_sync = models.DateTimeField(blank=True, null=True)
    # Designates last time a sync was done for this list.

    # Model link
    content_type = models.ForeignKey(ContentType, null=True, blank=True,
        help_text='Select the content type of objects that subscribers on '
        'this list can be linked with.')
    primary_key_field = models.ForeignKey('MailChimpMergeVar', models.SET_NULL,
            blank=True, null=True)

    def mailchimp_dc(self):
        '''
        Get the MailChimp data center for an instance's API key.
        '''
        if self.api_key:
            dc = 'us1'
            if '-' in self.api_key:
                dc = self.api_key.split('-')[1]
            return dc
        return None

    def get_admin_url(self):
        '''
        Get URL to MailChimp's admin interface for list.
        '''
        dc = self.mailchimp_dc()
        if dc and self.web_id:
            return 'https://%s.admin.mailchimp.com/lists/dashboard/overview?id=%s' % \
                (dc, self.web_id)
        else:
            return None

    def connection(self, path, *args, **kwargs):
        '''
        Randomly the API Throws an HTTPError: 500 Server Error
        Mailchimp support can't seem to help and I suspect it's related
        to the firewall which randomly messes up SSL packets
        So we wrap the connection and catch these error and retry
        Usage:
        Instead of:
            ml.connection.campaigns.update(campaign_id, data)
        Use:
            ml.connection(
                'campaigns.update',
                campaign_id,
                data,
            )
        '''
        method = MailChimp(mc_api=self.api_key, mc_user='USER')

        # Extract the final method from the path
        for name in path.split('.'):
            method = getattr(method, name)

        for i in range(1, 21):
            # Try the API call up to 20 times
            try:
                return method(*args, **kwargs)
            except HTTPError as e:
                if e.response.status_code != 500:
                    logger.warning('%s: %s', path, e.response.text)
                    raise e

                logger.debug('Oops! Caught error 500 (%d), retrying: %s', i,
                    path)

                if i == 20:
                    # Log the error
                    logger.error('%s: %s', path, e.response.text)
                    raise e

    def get_merge_fields(self):
        '''
        Get all defined MERGE FIELDS for this list.
        '''
        return MailChimpMergeVar.objects.filter(list=self).order_by('order')

    def parse_merge_fields(self, params):
        """
        Given MERGE FIELDS parameters, map it to field values.
        """
        mapping = {}

        if self.primary_key_field and self.content_type:
            for m in MergeVarMapping.objects.filter(list=self):
                mapping.update(dict(m.parse_merge_field(params)))

            if 'GROUPINGS' in params:
                for g in GroupMapping.objects.filter(list=self):
                    key, value = g.parse_interests(params['GROUPINGS'])
                    if key:
                        mapping[key] = value

        return mapping

    def create_merge_fields(self, obj, changes=None):
        '''
        Create a MERGE FIELDS dictionary from a model object. The model object
        must have the same content type as defined in content_type field. Hence
        both content_type and primiary_key_field must be specified for the list.

        The mapping from model object field to MERGE FIELD is defined by MergeVarMapping model.

        If the MERGE FIELD dictionary should only contain updates, you need to pass a ``changes''
        dictionary with model field names as keys and 2-tuples as values. The 2-tuples should contain
        the before and after value::

            changes = {
                'email': ('email+old@eso.org', 'email+new@eso.org'),
                # ...
            }

        The changes dictionary can easily be created with django-dirtyfields app.
        See http://pypi.python.org/pypi/django-dirtyfields
        '''
        merge_fields = {}
        if self.content_type and self.primary_key_field and isinstance(obj, self.content_type.model_class()):
            if changes is None:
                merge_fields[self.primary_key_field.tag] = "%s:%s" % (smart_unicode(obj._meta), smart_unicode(obj.pk, strings_only=True))

            for m in MergeVarMapping.objects.filter(list=self).select_related(
                'list', 'merge_var'):
                (tag, val) = m.create_merge_field(obj, changes=changes)
                if val and tag != self.primary_key_field.tag:
                    merge_fields[tag] = val

            interests = {}
            for g in GroupMapping.objects.filter(list=self).select_related(
                'list', 'group'):
                interest = g.create_interests(obj, changes=changes)
                if interest:
                    interests.update(interest)

            if interests:
                merge_fields['INTERESTS'] = interests

        return merge_fields

    def get_modelpk_from_identifier(self, object_identifier):
        model_identifier, pk = object_identifier.split(":")
        app_label, model_name = model_identifier.split(".")

        if app_label == self.content_type.app_label and model_name == self.content_type.model:
            return (app_label, model_name, pk)
        return None

    def get_object_from_identifier(self, object_identifier):
        val = self.get_modelpk_from_identifier(object_identifier)
        if val:
            app_label, model_name, pk = val  # pylint: disable=W0633
            Model = apps.get_model(app_label, model_name)
            return Model.objects.get(pk=pk)
        return None

    def get_object_from_mergefields(self, params):
        '''
        If list is linked with a django model (i.e content_type and
        primary_key_field is set), then this method will retrieve the model
        object
        '''
        # get object_identifier from params, and extract dictionary mapping
        if self.primary_key_field and self.content_type:
            pk_tag = self.primary_key_field.tag

            if pk_tag in params and params[pk_tag]:
                # Ensure pk_tag is in merge fields and it's non-empty.
                return self.get_object_from_identifier(params[pk_tag])
        return None

    def subscribe(self, email, merge_fields=None, email_type='html',
        double_optin=True, send_welcome=False, async=True):
        '''
        Subscribe the provided email address
        '''
        if merge_fields is None:
            merge_fields = {}

        # validate email address
        validate_email(email)

        try:
            BadEmailAddress.objects.get(email=email)
            raise Exception('%s is a known bad email address' % email)
        except BadEmailAddress.DoesNotExist:
            pass

        # validate email_type
        if email_type not in ['html', 'text', 'mobile']:
            raise Exception('Invalid email type %s - options are html, text, '
                'or mobile.' % email_type)

        # Check merge fields.
        allowed_fields = ['INTERESTS']
        allowed_fields.extend(self.get_merge_fields().values_list('tag', flat=True))

        for k in merge_fields.keys():
            if k not in allowed_fields:
                raise Exception('Invalid merge field %s - allowed variables '
                'are %s' % (k, ', '.join(allowed_fields)))

        # Extract interests from merge_fields if any
        if 'INTERESTS' in merge_fields:
            interests = merge_fields.pop('INTERESTS')
        else:
            interests = {}

        # Check if the email is already subscribed:
        email_hash = hashlib.md5(email).hexdigest()
        logger.debug('Will run lists.members.get for email "%s"', email)
        try:
            self.connection(
                'lists.members.get',
                self.list_id,
                email_hash,
            )
            # If we get a response then subscriber already exists
            return True
        except MailChimpError as e:
            if e.args[0]['status'] != 404:
                raise e
            # We got a 404 indicating that the address is not already a
            # member, all good

        logger.debug('Will run lists.members.create for email "%s"', email)
        self.connection(
            'lists.members.create',
            self.list_id, {
                'email_address': email,
                'email_type': email_type,
                'status': 'pending' if double_optin else 'subscribed',
                'merge_fields': merge_fields,
                'interests': interests,
            },
        )

        return True

    def unsubscribe(self, email, delete_member=False, send_goodbye=True,
        send_notify=True, async=True):
        '''
        Unsubscribe email from MailChimp (sets its status to "unsubscribed")
        '''
        # validate email address
        validate_email(email)

        # Make sure that the email is actually already subscribed
        email_hash = hashlib.md5(email).hexdigest()
        logger.debug('Will run lists.members.get for email "%s"', email)
        try:
            self.connection(
                'lists.members.get',
                self.list_id,
                email_hash,
            )
            # If we get a response then subscriber does exists
        except MailChimpError as e:
            if e.args[0]['status'] != 404:
                raise e

            # We got a 404, so the subscribers doesn't exist
            return True

        # Mark the member as unsubscribed
        logger.debug('Will run lists.members.update for email "%s"', email)
        self.connection(
            'lists.members.update',
            self.list_id,
            email_hash, {
                'status': 'unsubscribed',
            },
        )

        return True

    def update_profile(self, email, new_email, merge_fields=None,
        email_type=None, replace_interests=True, async=True):
        '''
        Update the profile of an existing member
        '''
        if merge_fields is None:
            merge_fields = {}

        if email == '' or new_email == '':
            # Contact has no email and won't be in Mailchimp
            return True

        # validate email address
        validate_email(email)
        validate_email(new_email)

        try:
            BadEmailAddress.objects.get(email=new_email)
            raise Exception('%s is a known bad email address' % new_email)
        except BadEmailAddress.DoesNotExist:
            pass

        # Validate email_type
        if email_type not in ['html', 'text', 'mobile', None]:
            raise Exception('Invalid email type %s - options are html, text, '
                'mobile or <blank>.' % email_type)

        # Check merge fields.
        allowed_fields = list(
            self.get_merge_fields().values_list('tag', flat=True)
        ) + ['EMAIL', 'NEW_EMAIL', 'OPTIN_IP', 'OPTIN_TIME', 'MC_LOCATION',
            'INTERESTS']

        for k in merge_fields.keys():
            if k not in allowed_fields:
                raise Exception('Invalid merge field %s - allowed variables '
                    'are %s' % (k, ', '.join(allowed_fields)))

        # Extract interests from merge_fields if any
        if 'INTERESTS' in merge_fields:
            interests = merge_fields.pop('INTERESTS')
        else:
            interests = {}

        # Set the new email address
        merge_fields['EMAIL'] = new_email
        if 'NEW_EMAIL' in merge_fields:
            del merge_fields['NEW_EMAIL']

        # Make sure that the email is actually already subscribed
        email_hash = hashlib.md5(email).hexdigest()
        logger.debug('Will run lists.members.get for email "%s"', email)
        try:
            self.connection(
                'lists.members.get',
                self.list_id,
                email_hash,
            )
            # If we get a response then subscriber does exists
        except MailChimpError as e:
            if e.args[0]['status'] != 404:
                raise e
            return False  # TODO: Should we send an action back?

        # Send update_member
        logger.debug('Will run lists.members.update for email "%s"', email)
        self.connection(
            'lists.members.update',
            self.list_id,
            email_hash, {
                'merge_fields': merge_fields,
                'interests': interests,
            },
        )

        return True

    def save(self, *args, **kwargs):
        '''
        Save instance (and sync info from MailChimp if it hasn't been done before).
        '''
        super(MailChimpList, self).save(*args, **kwargs)
        if self.list_id and self.api_key and not self.web_id:
            self.fetch_info()
            self.save()

    def fetch_info(self):
        '''
        Synchronize information from MailChimp list to Djangoplicity
        '''
        logger.debug('Will run lists.get for list "%s"', self.list_id)
        response = self.connection('lists.get', self.list_id)

        self.name = response['name']
        self.web_id = response['web_id']
        self.email_type_option = response['email_type_option']
        self.default_from_name = response['campaign_defaults']['from_name']
        self.default_from_email = response['campaign_defaults']['from_email']
        self.default_subject = response['campaign_defaults']['subject']
        self.default_language = response['campaign_defaults']['language']
        self.list_rating = response['list_rating']
        self.member_count = response['stats']['member_count']
        self.unsubscribe_count = response['stats']['unsubscribe_count']
        self.cleaned_count = response['stats']['cleaned_count']
        self.member_count_since_send = response['stats']['member_count_since_send']
        self.unsubscribe_count_since_send = response['stats']['unsubscribe_count_since_send']
        self.cleaned_count_since_send = response['stats']['cleaned_count_since_send']
        self.avg_sub_rate = response['stats']['avg_sub_rate']
        self.avg_unsub_rate = response['stats']['avg_unsub_rate']
        self.target_sub_rate = response['stats']['target_sub_rate']
        self.open_rate = response['stats']['open_rate']
        self.click_rate = response['stats']['click_rate']

        self.last_sync = datetime.now()
        self.connected = True

        # Try to get Merge fields
        logger.debug('Will run lists.merge_fields.all for list "%s"', self.list_id)
        response = self.connection('lists.merge_fields.all', self.list_id,
            get_all=True)

        pks = []
        for field in response['merge_fields']:
            size = field['options']['size'] \
                if 'size' in field['options'] else ''
            choices = ','.join(field['options']['choices']) \
                if 'choices' in field['options'] else ''

            merge_field, _created = MailChimpMergeVar.objects.get_or_create(
                list=self,
                name=field['name'],
                required=field['required'],
                field_type=field['type'],
                public=field['public'],
                show=True,  # No longer available in API 3.0
                order=field['display_order'],
                default=field['default_value'],
                size=size,
                tag=field['tag'],
                choices=choices,
            )
            pks.append(merge_field.pk)

        # Delete all merge fields which were are no longer defined
        MailChimpMergeVar.objects.filter(list=self).exclude(pk__in=pks).delete()

        # Try to get Interest categories (previously known as Groups)
        logger.debug('Will run lists.interest_categories.all for list "%s"', self.list_id)
        response = self.connection('lists.interest_categories.all',
            self.list_id, get_all=True)

        categories_pk = []
        interests_pk = []

        for category in response['categories']:
            group, _created = MailChimpGroup.objects.get_or_create(
                list=self,
                name=category['title'],
                group_id=category['id'],
            )
            categories_pk.append(group.pk)

            # Try to get Interests (previously known as Groupings)
            logger.debug('Will run lists.interest_categories.interests.all'
                'for list "%s", category "%s"', self.list_id, category['id'])
            response = self.connection(
                'lists.interest_categories.interests.all',
                self.list_id,
                category['id'],
                get_all=True,
            )

            for interest in response['interests']:
                grouping, _created = MailChimpGrouping.objects.get_or_create(
                    list=self,
                    interest_id=interest['id'],
                    group_id=category['id'],
                    option=interest['name'],
                    name=category['title'],
                )
                interests_pk.append(grouping.pk)

        # Delete all categories and interests which are no longer defined
        MailChimpGroup.objects.filter(list=self).exclude(pk__in=categories_pk).delete()
        MailChimpGrouping.objects.filter(list=self).exclude(pk__in=interests_pk).delete()

    def get_member_info(self, email=None):
        '''
        Retrieve info of the member with the given email address
        '''
        if not email:
            return {}

        email_hash = hashlib.md5(email).hexdigest()
        logger.debug('Will run lists.members.get for email "%s"', email)
        try:
            response = self.connection('lists.members.get', self.list_id,
                email_hash)
        except HTTPError as e:
            if e.response.status_code != 404:
                # Address is not subscribed
                return {}
            raise e

        return response

    @classmethod
    def post_save_handler(cls, sender=None, instance=None, created=False,
            raw=False, **kwargs):
        '''
        Start task to setup list in MailChimp (e.g. add webhooks).
        '''
        from djangoplicity.mailinglists.tasks import webhooks

        if created and not raw:
            webhooks.delay(list_id=instance.list_id)

    def __unicode__(self):
        return self.name if self.name else self.list_id

    class Meta:
        ordering = ('name', )


# Connect signal handlers
post_save.connect(MailChimpList.post_save_handler, sender=MailChimpList)

MERGEFIELD_DATATYPES = [
    ('email', 'email'),
    ('text', 'text'),
    ('number', 'number'),
    ('radio', 'radio'),
    ('dropdown', 'dropdown'),
    ('date', 'date'),
    ('address', 'address'),
    ('phone', 'phone'),
    ('url', 'url'),
    ('imageurl', 'imageurl'),
]


class MailChimpMergeVar(models.Model):
    '''
    Store information about mailchimp mergefields for each list.
    Merge vars are now named Merge fields, but the class name was kept
    '''
    list = models.ForeignKey(MailChimpList)
    name = models.CharField(max_length=255)
    required = models.BooleanField(default=False)
    field_type = models.CharField(max_length=20, choices=MERGEFIELD_DATATYPES,
        blank=True)
    public = models.BooleanField(default=False)
    show = models.BooleanField(default=False)
    order = models.CharField(max_length=255, blank=True)
    default = models.CharField(max_length=255, blank=True)
    size = models.CharField(max_length=255, blank=True)
    tag = models.CharField(max_length=255, blank=True)
    choices = models.TextField(blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.list,
            self.name if self.field_type != 'address' else
                '%s (addr1,addr2,city,state,zip,country)' % self.name)

    class Meta:
        ordering = ['list', 'name']
        verbose_name = 'mailchimp merge field'


class MailChimpGroup(models.Model):
    '''
    Represent a Mailchimp Interest Category (formerly known as Group)
    '''
    list = models.ForeignKey(MailChimpList)
    group_id = models.CharField(db_index=True, max_length=50)
    name = models.CharField(max_length=255)

    def __unicode__(self):
        return '%s: %s' % (self.list, self.name)


class MailChimpGrouping(models.Model):
    '''
    Represent a Mailchimp Interest (formerly known as Grouping)
    '''
    list = models.ForeignKey(MailChimpList)
    group_id = models.CharField(db_index=True, max_length=50)
    interest_id = models.CharField(db_index=True, max_length=50)
    name = models.CharField(max_length=255)
    option = models.TextField(blank=True)

    def __unicode__(self):
        return '%s: %s' % (self.name, self.option)

    class Meta:
        ordering = ['name', 'option']


class GroupMapping(models.Model):
    '''
    Mapping between a Mailchimp Group and a field.
    '''
    list = models.ForeignKey(MailChimpList)
    group = models.ForeignKey(MailChimpGroup)
    field = models.CharField(max_length=255)

    def parse_interests(self, interests):
        for interest in interests:
            if interest['unique_id'] != self.group.group_id:
                continue
            return (self.field, interest['groups'])
        return [None, None]

    def create_interests(self, obj, changes=None):
        '''
        Return a dict of form {'grouping_id': True_false, ...} for each ID
        in the group
        '''
        val = None

        try:
            if changes is None or (changes is not None and self.field in changes):
                field = getattr(obj, self.field)
                if hasattr(field, '__call__'):
                    val = field()
                else:
                    val = field
        except AttributeError:
            pass

        interests = {}
        for interest in MailChimpGrouping.objects.filter(
                group_id=self.group.group_id):
            interests[interest.interest_id] = interest.option == val

        return interests

    def __unicode__(self):
        return "%s -> %s" % (self.group, self.field)


class MergeVarMapping(models.Model):
    '''
    Mapping between a Mailchimp Merge Field (formally Merge Var) and a django
    field
    '''
    list = models.ForeignKey(MailChimpList)
    merge_var = models.ForeignKey(MailChimpMergeVar)
    field = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'mailchimp merge field mapping'

    def _field_list(self):
        fields = [x.strip() for x in self.field.split(",")]

        if len(fields) == 6:
            return zip(['addr1', 'addr2', 'city', 'state', 'zip', 'country'], fields)
        else:
            raise Exception("Address type merge fields must specify 5 elements.")

    def parse_merge_field(self, params, addr_oneline=False):
        """
        """
        tag = self.merge_var.tag

        if tag not in params:
            return []

        val = params[tag]

        if self.merge_var.field_type == 'address' and val:
            try:
                res = {}
                fields = self._field_list()

                for mc_f, dj_f in fields:
                    res[dj_f] = val[mc_f] if dj_f not in res else (res[dj_f] + "  " + val[mc_f] if val[mc_f] else res[dj_f])
                return res.items()
            except KeyError:
                return []
        else:
            return [(self.field, val)]

    def create_merge_field(self, obj, changes=None):
        val = None
        field_type = self.merge_var.field_type

        if field_type == 'address':
            fields = self._field_list()

            changed = True
            if changes is not None:
                changed = False
                for f in fields:
                    if f in changes:
                        changed = True

            if changed:
                val = {}
                fields_done = []
                for mc_f, dj_f in fields:
                    if dj_f not in fields_done:
                        try:
                            val[mc_f] = getattr(obj, dj_f)
                            fields_done.append(dj_f)
                        except AttributeError:
                            pass
                    else:
                        val[mc_f] = ''

                # Country
                if isinstance(val['country'], models.Model):
                    try:
                        val['country'] = val['country'].iso_code
                    except AttributeError:
                        pass
        else:
            try:
                if changes is None or (changes is not None and self.field in changes):
                    val = getattr(obj, self.field)
            except AttributeError:
                pass

        return (self.merge_var.tag, val)

    def __unicode__(self):
        return '%s -> %s' % (self.merge_var, self.field)


class MailChimpListToken(models.Model):
    '''
    Tokens used in get parameters to secure webhook requests
    from MailChimp.
    '''
    list = models.ForeignKey(MailChimpList)
    uuid = models.CharField(unique=True, max_length=36, verbose_name='UUID')
    token = models.CharField(unique=True, max_length=56)
    expired = models.DateTimeField(null=True, blank=True)

    def get_absolute_url(self):
        '''
        Get absolute URL to webhook.
        '''
        ten_minutes_ago = datetime.now() - timedelta(minutes=10)

        if self.token and \
            (self.expired is None or self.expired >= ten_minutes_ago):
            baseurl = 'https://{}{}'.format(
                Site.objects.get_current().domain,
                reverse('djangoplicity_mailinglists:mailchimp_webhook'),
            )
            hookurl = '{}?{}'.format(baseurl, urlencode(self.hook_params()))
            return hookurl

        return None
    get_absolute_url.short_description = 'Webhook URL'

    @classmethod
    def create(cls, l):
        '''
        Create a MailChimpListToken for a MailChimpList.
        '''
        if not l.list_id:
            raise Exception('List is empty, cannot create token')

        uuid = str(uuidmod.uuid4())
        token = cls.token_value(l.list_id, uuid)

        obj = cls(list=l, uuid=uuid, token=token)
        obj.save()

        return obj

    @staticmethod
    def token_value(list_id, uuid):
        '''
        Generate token value from list_id and uuid
        '''
        m = hashlib.sha224()
        m.update(settings.SECRET_KEY)
        m.update(list_id)
        m.update(uuid)
        return str(m.hexdigest())

    @classmethod
    def get_token(cls, token):
        '''
        Find a valid token instance matching the token
        '''
        ten_minutes_ago = datetime.now() - timedelta(minutes=10)
        try:
            return cls.objects.filter(token=token).filter(
                models.Q(expired__gte=ten_minutes_ago) |
                models.Q(expired__isnull=True)
            ).get()
        except cls.DoesNotExist:
            return None

    def validate_token(self, l):
        '''
        Validate input parameters
        '''
        return l and self.list.pk == l.pk

    def hook_params(self):
        '''
        Return a dict of query parameters for a MailChimp webhook
        '''
        return {'token': self.token}


#
# More advanced stuff - configurable actions to be execute once
# contacts are added/removed from groups (e.g subscribe to mailman).
#
ACTION_EVENTS = (
    ('on_subscribe', 'On subscribe'),
    ('on_unsubscribe', 'On unsubscribe'),
    ('on_upemail', 'On update email'),
    ('on_profile', 'On profile update'),
    ('on_cleaned', 'On cleaned'),
    ('on_campaign', 'On campaign'),
)


class MailChimpEventAction(EventAction):
    '''
    Define actions to be executed when a event occurs for a list (e.g. sub,
    unsub, clean etc.)
    '''
    def __init__(self, *args, **kwargs):
        super(MailChimpEventAction, self).__init__(*args, **kwargs)
        self._meta.get_field('on_event')._choices = ACTION_EVENTS

    model_object = models.ForeignKey(MailChimpList)

    _key = 'djangoplicity.mailinglists.action_cache'
