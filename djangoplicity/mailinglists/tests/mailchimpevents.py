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

from djangoplicity.mailinglists.models import MailChimpList, MailChimpEventAction, MailChimpMergeVar, MailChimpGrouping, MergeVarMapping, BadEmailAddress
from djangoplicity.mailinglists.tasks import mailchimp_unsubscribe, mailchimp_cleaned, mailchimp_profile
from djangoplicity.contacts.tasks import *
from djangoplicity.contacts.models import Contact, ContactGroup, Country

class MailChimpEvents( TestCase ):
    """
    Note, this test requires a working mailman installation..
    """

    def _create_list( self ):
        from django.contrib.contenttypes.models import ContentType
        
        ct = ContentType.objects.get( app_label="contacts", model="contact" )
        
        # MailChimpList (fake)
        MergeVarMapping.objects.all().delete()
        MailChimpGrouping.objects.all().delete()
        MailChimpMergeVar.objects.all().delete()
        MailChimpList.objects.all().delete()
        l,created = MailChimpList.objects.get_or_create( api_key='INVALID', list_id='INVALID', web_id='INVALID', content_type=ct, connected=True )
        l.save()
        
        (tag_email,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='EMAIL', name='Email Address', required=True, field_type='email', public=True, show=True )
        (tag_fname,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='FNAME', name='First Name', required=False, field_type='text', public=True, show=True )
        (tag_lname,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='LNAME', name='Last Name', required=False, field_type='text', public=True, show=True )
        (tag_org,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='ORGNAME', name='Organisation', required=False, field_type='text', public=True, show=True )
        (tag_position,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='POS', name='Position', required=False, field_type='text', public=True, show=True )
        (tag_phone,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='PHONE', name='Telephone', required=False, field_type='phone', public=True, show=True )
        (tag_url,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='WEBSITE', name='Website Organisation/Personal', required=False, field_type='website', public=True, show=True )
        (tag_social,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='SOCIAL', name='Social Media', required=False, field_type='text', public=True, show=True )
        (tag_address,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='ADDRESS', name='Address', required=False, field_type='address', public=True, show=True )
        (tag_objid,created) = MailChimpMergeVar.objects.get_or_create( list=l, tag='OBJID', name='Object ID', required=False, field_type='text', public=False, show=True )
        

        grping_id, grping_name, grp_opt0, grp_opt1 = '1','Interests','Amateur','Science Communicator'
        MailChimpGrouping.objects.get_or_create( list=l, group_id=grping_id, name=grping_name, option=grp_opt0 )
        MailChimpGrouping.objects.get_or_create( list=l, group_id=grping_id, name=grping_name, option=grp_opt1 )
        
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_fname, field='first_name')
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_lname, field='last_name')
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_org, field='organisation')
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_position, field='position')
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_phone, field='phone')
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_url, field='website')
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_social, field='social')
        MergeVarMapping.objects.get_or_create( list=l, merge_var=tag_address, field='street_1,street_2,city,state,zip,country' )
        
        l.primary_key_field = tag_objid
        l.save()
        
        return ( l, grping_id, grping_name, grp_opt0, grp_opt1 )

    
    def _create_contact(self, emailaddr, grp_name):
        
        
        # Country
        germany,created = Country.objects.get_or_create( name='Germany', iso_code='DE', dialing_code='+49', zip_after_city=False )
        
        ContactGroup.objects.all().delete()
        Contact.objects.all().delete()
        # Contact
        
        c = Contact( 
            first_name='Lars Holm',
            last_name='Nielsen',
            title='Mr.',
            position='Web & Advanced Projects Coordinator',
            organisation='European Southern Observatory',
            department='education & Public Outreach Department',
            street_1='Karl-Schwarzschild-Str. 2',
            street_2='',
            city='85748 München',
            country=germany,
            phone='+49 89 3200 6615',
            website='http://www.eso.org',
            social='',
            email=emailaddr,
        )
        c.save()
        
        # Group
        
        grp,created = ContactGroup.objects.get_or_create( name=grp_name )       
        c.groups.add( grp )

        return c
        
    def test_unsubscribe(self):
        """
        Test creating a list and syncing it with 
        """
        
        
        
        grp_name = 'test_epodpress_e'
        emailaddr = 'lars@hankat.dk'
        
        l, grping_id, grping_name, grp_opt0, grp_opt1 = self._create_list()
        c = self._create_contact( emailaddr, grp_name )
        
        # Action setup
        from djangoplicity.actions.models import Action, ActionParameter
        MailChimpEventAction.objects.all().delete()
        Action.objects.all().delete()
        
        a = Action( plugin='djangoplicity.contacts.tasks.UnsetContactGroupAction', name='Test Action' )
        a.save()
        
        p,created = ActionParameter.objects.get_or_create( action=a, name='group' )
        p.value = grp_name
        p.save()
        
        MailChimpEventAction( action=a, on_event='on_unsubscribe', model_object=l ).save()
        
        #
        # Test
        #
        
        # Incoming data
        data = {
            'action' : 'unsub',
            'email' : emailaddr,
            'email_type' : 'html',
            'id' : 'b743dfb3db',
            'ip_opt' : '134.171.34.28',
            'ip_signup' : '134.171.34.28',
            'web_id' : '280123277',
            'reason' : 'manual',
            'merges' : {
                'FNAME' : 'Lars Holm',
                'LNAME' : 'Nielsen',
                'ADDRESS' : {
                    'addr1' : 'Karl-Schwarzschild-Str 2',
                    'addr2' : '',
                    'city' : 'Garching bei Muenchen',
                    'state' : '',
                    'zip' : '85748',
                    'country' : 'DE',
                },
                'OBJID' : 'contacts.contact:%s' % c.pk,
                'EMAIL' : emailaddr,
                'GROUPINGS' : [
                    { 'name' : '%s' % grping_name, 'id' : '%s' % grping_id, 'groups' : ", ".join( [grp_opt0, grp_opt1] ) },
                ],
            },
        }
        
        self.assertEqual( c.groups.all().count(), 1 )
        mailchimp_unsubscribe( list=l.pk, fired_at='2011-10-13 11:26:31', params=data, ip='N/A', user_agent='N/A' )
        self.assertEqual( c.groups.all().count(), 0 )
        
    def test_cleaned(self):
        grp_name = 'test_epodpress_e'
        emailaddr = 'lars@hankat.dk'
        
        l, grping_id, grping_name, grp_opt0, grp_opt1 = self._create_list()
        c = self._create_contact( emailaddr, grp_name )
        
        # Action setup
        from djangoplicity.actions.models import Action, ActionParameter
        
        BadEmailAddress.objects.all().delete()
        MailChimpEventAction.objects.all().delete()
        Action.objects.all().delete()
        a = Action( plugin='djangoplicity.contacts.tasks.RemoveEmailAction', name='Test Action 2' )
        a.save()
        
        p,created = ActionParameter.objects.get_or_create( action=a, name='clear' )
        p.value = 'True'
        p.save()
        p,created = ActionParameter.objects.get_or_create( action=a, name='append' )
        p.value = ''
        p.save()
        
        MailChimpEventAction( action=a, on_event='on_cleaned', model_object=l ).save()
        
        # Incoming data
        data = {
            'email' : emailaddr,
            'reason' : 'hard',
            'campaign_id' : '4fjk2ma9xd',
        }
        
        self.assertNotIn( emailaddr, BadEmailAddress.objects.all().values_list( 'email', flat = True ) )
        self.assertEqual( Contact.objects.get(pk=c.pk).email, emailaddr )
        mailchimp_cleaned( list=l.pk, fired_at='2011-10-13 11:26:31', params=data, ip='N/A', user_agent='N/A' )
        self.assertIn( emailaddr, BadEmailAddress.objects.all().values_list( 'email', flat = True ) )
        self.assertEqual( Contact.objects.get(pk=c.pk).email, '' )
        
        c.email = emailaddr
        c.save()
        append_text = '-INVALID'
        
        p,created = ActionParameter.objects.get_or_create( action=a, name='clear' )
        p.value = 'False'
        p.save()
        p,created = ActionParameter.objects.get_or_create( action=a, name='append' )
        p.value = append_text
        p.save()
        
        self.assertEqual( Contact.objects.get(pk=c.pk).email, emailaddr )
        mailchimp_cleaned( list=l.pk, fired_at='2011-10-13 11:26:31', params=data, ip='N/A', user_agent='N/A' )
        self.assertEqual( Contact.objects.get(pk=c.pk).email, emailaddr+append_text )
        
    def test_profile_update(self):
        """
        """
        grp_name = 'test_epodpress_e'
        emailaddr = 'lars@hankat.dk'
        new_email = 'lnielsen@spacetelescope.org'
        
        l, grping_id, grping_name, grp_opt0, grp_opt1 = self._create_list()
        c = self._create_contact( emailaddr, grp_name )
        
        # Action setup
        from djangoplicity.actions.models import Action, ActionParameter
        MailChimpEventAction.objects.all().delete()
        Action.objects.all().delete()
        
        a = Action( plugin='djangoplicity.contacts.tasks.UpdateContactAction', name='Test Action' )
        a.save()
        
        MailChimpEventAction( action=a, on_event='on_profile', model_object=l ).save()
        
        # Incoming data
        data = {
            'email' : emailaddr,
            'email_type' : 'html',
            'id' : 'b743dfb3db',
            'ip_opt' : '134.171.34.28',
            'ip_signup' : '134.171.34.28',
            'web_id' : '280123277',
            'merges' : {
                'FNAME' : 'FNAME',
                'LNAME' : 'LNAME',
                'ORGNAME' : 'ORGNAME',
                'POS' : 'POS',
                'WEBSITE' : 'WEBSITE',
                'PHONE' : 'PHONE',
                'SOCIAL' : 'SOCIAL',
                'ADDRESS' : {
                    'addr1' : 'ADDR1',
                    'addr2' : 'ADDR2',
                    'city' : 'CITY',
                    'state' : 'STATE',
                    'zip' : 'ZIP',
                    'country' : 'DE',
                },
                'OBJID' : 'contacts.contact:%s' % c.pk,
                'EMAIL' : emailaddr,
                'GROUPINGS' : [
                    { 'name' : '%s' % grping_name, 'id' : '%s' % grping_id, 'groups' : ", ".join( [grp_opt0, grp_opt1] ) },
                ],
            },
        }
        
        self.assertNotEqual( c.first_name, data['merges']['FNAME'] )
        self.assertNotEqual( c.last_name, data['merges']['LNAME'] )
        self.assertNotEqual( c.position, data['merges']['POS'] )
        self.assertNotEqual( c.organisation, data['merges']['ORGNAME'] )
        self.assertNotEqual( c.website, data['merges']['WEBSITE'] )
        self.assertNotEqual( c.phone, data['merges']['PHONE'] )
        self.assertNotEqual( c.social, data['merges']['SOCIAL'] )
        self.assertNotEqual( c.street_1, data['merges']['ADDRESS']['addr1'] )
        self.assertNotEqual( c.street_2, data['merges']['ADDRESS']['addr2'] )
        mailchimp_profile( list=l.pk, fired_at='2011-10-13 11:26:31', params=data, ip='N/A', user_agent='N/A' )
        c = Contact.objects.get( pk=c.pk )
        self.assertEqual( c.first_name, data['merges']['FNAME'] )
        self.assertEqual( c.last_name, data['merges']['LNAME'] )
        self.assertEqual( c.position, data['merges']['POS'] )
        self.assertEqual( c.organisation, data['merges']['ORGNAME'] )
        self.assertEqual( c.website, data['merges']['WEBSITE'] )
        self.assertEqual( c.phone, data['merges']['PHONE'] )
        self.assertEqual( c.social, data['merges']['SOCIAL'] )
        self.assertEqual( c.street_1, data['merges']['ADDRESS']['addr1'] )
        self.assertEqual( c.street_2, data['merges']['ADDRESS']['addr2'] )
        self.assertEqual( c.city, "%s  %s  %s" % ( data['merges']['ADDRESS']['zip'], data['merges']['ADDRESS']['city'], data['merges']['ADDRESS']['state'] ) )
        self.assertEqual( c.country.iso_code.upper(), data['merges']['ADDRESS']['country'].upper() )

        