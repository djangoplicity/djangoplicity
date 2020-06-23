# -*- coding: utf-8 -*-
#
# djangoplicity-newsletters
# Copyright (c) 2007-2011, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#
#   * Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#   * Neither the name of the European Southern Observatory nor the names
#     of its contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
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

from django.test import TestCase, RequestFactory


class ListTest( TestCase ):
    """
    Note, this test requires a working mailman installation..
    """
    LIST_NAME = 'esoepo-monitoring'
    LIST_PASSWORD = 'ohsiechu'
    LIST_BASEURL = 'http://www.eso.org/lists'

    def test_init(self):
        """
        Test creating a list and syncing it with
        """
        from djangoplicity.mailinglists.models import List, Subscriber

        List.objects.all().delete()
        list = List( name=self.LIST_NAME, password=self.LIST_PASSWORD, base_url=self.LIST_BASEURL )
        list.save()

        # Make sure we don't have any subscribers
        Subscriber.objects.all().delete()

        subscribers = list.get_mailman_emails()

        self.assertIn( "lnielsen@eso.org", subscribers )

#   def test_subscribe_unsubscribe( self ):
#       """
#       Test subscribe/unsubscribe to mailman list.
#
#       Note, this list is not connected to any mailchimp lists, so
#       it will only propagate to mailman.
#       """
#       from djangoplicity.mailinglists.models import List, Subscriber
#
#       List.objects.all().delete()
#       Subscriber.objects.all().delete()
#
#       email = "lnielsen@spacetelescope.org"
#
#       list = List( name=self.LIST_NAME, password=self.LIST_PASSWORD, base_url=self.LIST_BASEURL )
#       list.save()
#
#       s = Subscriber( email=email )
#       s.save()
#
#       subscribers, unsubscribers, current_subscribers, mailman_unsubscribe_emails = list.incoming_changes()
#       self.assertNotIn( s.email, subscribers )
#       self.assertNotIn( s.email, [x.email for x in current_subscribers] )
#
#       # Subscribe
#       list.subscribe( s )
#       subscribers, unsubscribers, current_subscribers, mailman_unsubscribe_emails = list.incoming_changes()
#       self.assertIn( s.email, [x.email for x in current_subscribers] )
#       self.assertNotIn( s.email, unsubscribers )
#       self.assertNotIn( s.email, subscribers )
#
#       # Unsubscribe
#       list.unsubscribe( s )
#       subscribers, unsubscribers, current_subscribers, mailman_unsubscribe_emails= list.incoming_changes()
#       self.assertNotIn( s.email, [x.email for x in current_subscribers] )
#       self.assertNotIn( s.email, unsubscribers )
#       self.assertNotIn( s.email, subscribers )
#
#
#   def test_synchronize_mailman( self ):
#       """
#       Test the mailman synchronization
#       """
#       from djangoplicity.mailinglists.models import List, Subscriber, MailChimpList, Subscription
#       from djangoplicity.mailinglists.tasks import synchronize_mailman
#
#       MailChimpList.objects.all().delete()
#       List.objects.all().delete()
#
#       list = List( name=self.LIST_NAME, password=self.LIST_PASSWORD, base_url=self.LIST_BASEURL )
#       list.save()
#
#       # Is called by post_save signal on list.save
#       #synchronize_mailman.delay( list.name )
#
#       list_len = len( list.subscribers.all() )
#       self.assertGreater( list_len, 0 )
#
#       # Fake an unsubscription
#       s = Subscriber( email="lnielsen@spacetelescope.org" )
#       s.save()
#       sub = Subscription( list=list, subscriber=s )
#       sub.save()
#       self.assertEqual( list_len + 1, len( list.subscribers.all() ) )
#
#       # Should be unsubscribed now
#       synchronize_mailman.delay( list.name )
#
#       self.assertEqual( list_len, len( list.subscribers.all() ) )
#       self.assertNotIn( "lnielsen@spacetelescope.org", [s.email for s in list.subscribers.all()] )




class MailChimpListTest( TestCase ):
    """
    To ensure that this test runs, you must first manually create
    a mailchimp list, via the web interface.

    When creating the list, please ensure that
      * list name
      * default from name
      * default from email
    fields have a non-blank value (currently they are all required fields)
    """

    TEST_API_KEY = "5b9aa23a4e53e80db2de92975de8dd5b-us2"
    TEST_LIST_ID = "326ca61f64"

    #
    # Helper methods
    #
    def _valid_list( self ):
        from djangoplicity.mailinglists.models import MailChimpList
        return MailChimpList( api_key=self.TEST_API_KEY, list_id=self.TEST_LIST_ID )


    def _invalid_list( self ):
        from djangoplicity.mailinglists.models import MailChimpList
        return MailChimpList( api_key="not_valid", list_id="not_valid" )

    def _fixture_delete( self, objects ):
        for o in objects:
            try:
                o.delete()
            except Exception:
                pass

    def _reset(self):
        from djangoplicity.mailinglists.models import List, Subscriber, Subscription, MailChimpList, MailChimpListToken, MailChimpSourceList, MailChimpSubscriberExclude

        Subscription.objects.all().delete()
        MailChimpListToken.objects.all().delete()
        MailChimpSourceList.objects.all().delete()
        MailChimpSubscriberExclude.objects.all().delete()
        List.objects.all().delete()
        Subscriber.objects.all().delete()
        MailChimpList.objects.all().delete()


    #
    # Tests
    #
    def test_init( self ):
        # Valid api key + list
        list = self._valid_list()
        list.save()

        self.assertEqual( list.connected, True )
        self.assertNotEqual( list.web_id, "" )
        self.assertIsNotNone( list.web_id )
        self.assertNotEqual( list.name, "" )
        self.assertIsNotNone( list.name )
        self.assertNotEqual( list.default_from_name, "" )
        self.assertIsNotNone( list.default_from_name )
        self.assertNotEqual( list.default_from_email, "" )
        self.assertIsNotNone( list.default_from_email )

        list.delete()

        # Non valid api key + list
        list = self._invalid_list()
        list.save()

        self.assertEqual( list.connected, False )
        list.delete()


    def test_mailchimp_dc( self ):
        from djangoplicity.mailinglists.models import MailChimpList

        list = MailChimpList( api_key="5b9aa23a4e53e80db2de92975de8dd5b-us2", list_id="not_valid" )
        self.assertEqual( list.mailchimp_dc(), "us2" )

        list = MailChimpList( api_key="5b9aa23a4e53e80db2de92975de8dd5b-us1", list_id="not_valid" )
        self.assertEqual( list.mailchimp_dc(), "us1" )

        list = MailChimpList( api_key="5b9aa23a4e53e80db2de92975de8dd5b", list_id="not_valid" )
        self.assertEqual( list.mailchimp_dc(), "us1" )


    def test_connection( self ):
        from djangoplicity.mailinglists.models import MailChimpList

        # Valid api key + list
        list = self._valid_list()
        self.assertEqual( list.connection.ping(), "Everything's Chimpy!" )


#   def test_default_lists( self ):
#       lists, mailman_lists = self._fixture_create()
#
#       list, list2 = lists
#       mailman_list1, mailman_list2, mailman_list3 = mailman_lists
#
#       self.assertEqual( mailman_list1.name, list.default_lists()[0].name )
#       self.assertNotEqual( mailman_list2.name, list.default_lists()[0].name )
#       self.assertEqual( mailman_list2.name, list2.default_lists()[0].name )
#       self.assertNotEqual( mailman_list3.name, list2.default_lists()[0].name )
#       self.assertEqual( len( list.default_lists() ), 1 )
#       self.assertEqual( len( list2.default_lists() ), 1 )
#
#       self._fixture_delete( lists + mailman_lists)
#
#
#   def test_subscribers_subscriptions( self ):
#       from djangoplicity.mailinglists.models import MailChimpSubscriberExclude
#
#       lists, mailman_lists = self._fixture_create()
#
#       list, list2 = lists
#       mailman_list1, mailman_list2, mailman_list3 = mailman_lists
#
#       subscribers = self._subscribers( 10 )
#       self._subscribe( mailman_list1, subscribers[0:1] + subscribers[1:3] )
#       self._subscribe( mailman_list2, subscribers[0:1] + subscribers[3:5] )
#       self._subscribe( mailman_list3, subscribers[0:1] + subscribers[5:7] )
#
#       MailChimpSubscriberExclude( mailchimplist=list, subscriber=subscribers[3] ).save()
#
#       list_subs = ["testemail%s@eso.org" % x for x in 0, 1, 2, 4]
#       list2_subs = ["testemail%s@eso.org" % x for x in 0, 3, 4, 5, 6]
#
#       self.assertEqual( len( list.get_subscribers() ), 4 )
#       self.assertEqual( len( list2.get_subscribers() ), 5 )
#       self.assertEqual( len( list.get_subscriptions() ), 5 )
#       self.assertEqual( len( list2.get_subscriptions() ), 6 )
#
#       self.assertNotIn( "testemail3@eso.org", [x.email for x in list.get_subscribers() ] )
#       self.assertIn( "testemail3@eso.org", [x.email for x in list2.get_subscribers() ] )
#       self.assertNotIn( "testemail3@eso.org", [x.subscriber.email for x in list.get_subscriptions() ] )
#       self.assertIn( "testemail3@eso.org", [x.subscriber.email for x in list2.get_subscriptions() ] )
#
#       self._fixture_delete( lists + mailman_lists )
#

#   def test_webhooks_setup( self ):
#       """
#       Note, can only be run in production, since it mailchimp requires a valid URL.
#       """
#       from djangoplicity.mailinglists.tasks import webhooks
#
#       list = self._valid_list()
#       list.save()
#       self.assertEqual( list.connected, True )
#
#       hooks = list.connection.listWebhooks( id=list.list_id )
#       if len(hooks) > 0:
#           for h in hooks:
#               list.connection.listWebhookDel( id=list.list_id, url=h['url'] )
#
#       hooks = list.connection.listWebhooks( id=list.list_id )
#       self.assertEqual( len( hooks ), 0 )
#
#       webhooks.delay( list_id=list.list_id )
#
#       hooks = list.connection.listWebhooks( id=list.list_id )
#       self.assertEqual( len( hooks ), 1 )
#
#       list.connection.listWebhookDel( id=list.list_id, url=hooks[0]['url'] )
#
#       hooks = list.connection.listWebhooks( id=list.list_id )
#       self.assertEqual( len( hooks ), 0 )


class MailChimpListTokenTest( TestCase ):
    def test_get_token( self ):
        from djangoplicity.mailinglists.models import MailChimpList, MailChimpListToken
        from datetime import datetime, timedelta

        list = MailChimpList( api_key="not_valid", list_id="not_valid", connected=True )
        list.save()

        t = MailChimpListToken.create( list )

        # Valid unexpired token
        t2 = MailChimpListToken.get_token( t.token )
        self.assertNotEqual( t2, None )
        self.assertEqual( t.token, t2.token )
        self.assertEqual( t.uuid, t2.uuid )
        self.assertEqual( t.list, t2.list )
        assert( t.validate_token( list ) )
        assert( t2.validate_token( list ) )

        # Expire token, but still valid 10 min after expire date.
        t.expired = datetime.now() - timedelta( minutes=9 )
        t.save()

        t2 = MailChimpListToken.get_token( t.token )
        self.assertNotEqual( t2, None )
        self.assertEqual( t.token, t2.token )
        self.assertEqual( t.uuid, t2.uuid )
        self.assertEqual( t.list, t2.list )
        assert( t.validate_token( list ) )
        assert( t2.validate_token( list ) )

        # Expire token but now not valid any more.
        t.expired = datetime.now() - timedelta( minutes=11 )
        t.save()

        t2 = MailChimpListToken.get_token( t.token )
        self.assertEqual( t2, None )



class WebHooksTest( TestCase ):
    def setUp( self ):
        self.factory = RequestFactory()

        from djangoplicity.mailinglists.models import MailChimpList, MailChimpListToken
        from urllib import urlencode

        list = MailChimpList( api_key="not_valid", list_id="not_valid", connected=True )
        list.save()

        token = MailChimpListToken.create( list )

        self.list = list
        self.token = token
        self.params = urlencode( token.hook_params() )

    def _mailchimp_webhook( self, data ):
        from djangoplicity.mailinglists.views import mailchimp_webhook
        request = self.factory.post( '/webhook/?%s' % self.params, data=data )
        return mailchimp_webhook( request, require_secure=False )

    def test_subscribe( self ):
        data = {
            "type": "subscribe",
            "fired_at": "2009-03-26 21:35:57",
            "data[id]": "8a25ff1d98",
            "data[list_id]": self.list.list_id,
            "data[email]": "api@mailchimp.com",
            "data[email_type]": "html",
            "data[merges][EMAIL]": "api@mailchimp.com",
            "data[merges][FNAME]": "MailChimp",
            "data[merges][LNAME]": "API",
            "data[merges][INTERESTS]": "Group1,Group2",
            "data[ip_opt]": "10.20.10.30",
            "data[ip_signup]": "10.20.10.30",
        }
        response = self._mailchimp_webhook( data )
        self.assertEqual( response.status_code, 200 )


    def test_unsubscribe( self ):
        data = {
            "type": "unsubscribe",
            "fired_at": "2009-03-26 21:40:57",
            "data[id]": "8a25ff1d98",
            "data[list_id]": self.list.list_id,
            "data[email]": "api+unsub@mailchimp.com",
            "data[email_type]": "html",
            "data[merges][EMAIL]": "api+unsub@mailchimp.com",
            "data[merges][FNAME]": "MailChimp",
            "data[merges][LNAME]": "API",
            "data[merges][INTERESTS]": "Group1,Group2",
            "data[ip_opt]": "10.20.10.30",
            "data[campaign_id]": "cb398d21d2",
            "data[reason]": "hard"
        }
        response = self._mailchimp_webhook( data )
        self.assertEqual( response.status_code, 200 )

    def test_cleaned( self ):
        data = {
            "type": "cleaned",
            "fired_at": "2009-03-26 22:01:00",
            "data[list_id]": self.list.list_id,
            "data[campaign_id]": "4fjk2ma9xd",
            "data[reason]": "hard",
            "data[email]": "api+cleaned@mailchimp.com"
        }
        response = self._mailchimp_webhook( data )
        self.assertEqual( response.status_code, 200 )

    def test_upemail( self ):
        data = {
            "type": "upemail",
            "fired_at": "2009-03-26 22:15:09",
            "data[list_id]": self.list.list_id,
            "data[new_id]": "51da8c3259",
            "data[new_email]": "api+new@mailchimp.com",
            "data[old_email]": "api+old@mailchimp.com"
        }
        response = self._mailchimp_webhook( data )
        self.assertEqual( response.status_code, 200 )

    def test_profile( self ):
        data = {
            "type": "profile",
            "fired_at": "2009-03-26 21:31:21",
            "data[id]": "8a25ff1d98",
            "data[list_id]": self.list.list_id,
            "data[email]": "api@mailchimp.com",
            "data[email_type]": "html",
            "data[merges][EMAIL]": "api@mailchimp.com",
            "data[merges][FNAME]": "MailChimp",
            "data[merges][LNAME]": "API",
            "data[merges][INTERESTS]": "Group1,Group2",
            "data[ip_opt]": "10.20.10.30"
        }
        response = self._mailchimp_webhook( data )
        self.assertEqual( response.status_code, 200 )




