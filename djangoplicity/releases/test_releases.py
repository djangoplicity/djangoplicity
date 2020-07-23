# -*- coding: utf-8 -*-
#
# djangoplicity-releases
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
from djangoplicity.media.models.comparisons import ImageComparison

# Tests of release date propagation
#
# While in-fact these tests are testing code located in djangoplicity.archives,
# the tests are here, since the primary use case for the code is the propagation
# of releases dates from releases to images/videos.

from django.test import TestCase

from djangoplicity.media.models import Image, PictureOfTheWeek
from djangoplicity.releases.models import Release, ReleaseType, ReleaseImage,\
    ReleaseImageComparison
from datetime import datetime

class ReleaseDatePropagation( TestCase ):

    def clear( self ):
        Release.objects.all().delete()
        Image.objects.all().delete()
        ReleaseImage.objects.all().delete()
        ReleaseType.objects.all().delete()

        self.now = datetime( 2007, 11, 30, 12, 00, 00)
        self.now2 = datetime( 2008, 11, 30, 12, 00, 00)
        self.new_now = datetime( 2009, 11, 30, 12, 00, 00)
        self.new_now2 = datetime( 2010, 11, 30, 12, 00, 00)
        self.now3 = datetime( 2011, 11, 30, 12, 00, 00)
        self.new_now3 = datetime( 2012, 11, 30, 12, 00, 00)
        self.now4 = datetime( 2013, 11, 30, 12, 00, 00)
        self.new_now4 = datetime( 2014, 11, 30, 12, 00, 00)

        rt = ReleaseType( name='Test Release Type' )
        rt.save()
        self.rid = "eso0945"
        self.r = Release( id=self.rid, release_type=rt, title='ESO0945', release_date=self.now )
        self.r.save()
        self.r2id = "eso0946"
        self.r2 = Release( id=self.r2id, release_type=rt, title='ESO0946', release_date=self.now2)
        self.r2.save()
        self.r3id = "eso0947"
        self.r3 = Release( id=self.r3id, release_type=rt, title='ESO0947', release_date=self.now3)
        self.r3.save()
        self.ima = Image( id="eso0945a", priority="50", title='ESO0945a')
        self.ima.save()
        self.ima_da = Image( id="eso0945a-da", priority="50", title='ESO0945a-da', lang='da', source=self.ima )
        self.ima_da.save()
        self.imb = Image( id="eso0945b", priority="50", title='ESO0945b')
        self.imb.save()
        self.imb_da = Image( id="eso0945b-da", priority="50", title='ESO0945b-da', lang='da', source=self.imb )
        self.imb_da.save()

        self.potw = PictureOfTheWeek( id='potw1201', release_date=self.now3, source=None )
        self.potw.save()
        self.potw2 = PictureOfTheWeek( id='eso0945', release_date=self.now4, source=None )
        self.potw2.save()

    def _get_objects( self ):
        r = Release.objects.get( pk="eso0945" )
        r2 = Release.objects.get( pk="eso0946" )
        r3 = Release.objects.get( pk="eso0947" )
        ima = Image.objects.get( pk="eso0945a" )
        imb = Image.objects.get( pk="eso0945b" )
        ima_da = Image.objects.language('da').get( pk="eso0945a" )
        imb_da = Image.objects.language('da').get( pk="eso0945b" )

        return ( r, r2, r3, ima, imb, ima_da, imb_da )

    def _assert_datetimes( self, r_date, ima_date, ima_owner, imb_date, imb_owner ):
        """
        Assert that release date of PR associated images A and B (and their release date owners)
        """
        ( r, _r2, _r3, ima, imb, ima_da, imb_da ) = self._get_objects()

        self.assertEqual( r.release_date, r_date )
        self.assertEqual( ima.release_date, ima_date )
        self.assertEqual( ima.release_date_owner, ima_owner )
        self.assertEqual( ima_da.release_date, ima_date )
        self.assertEqual( ima_da.release_date_owner, ima_owner )
        self.assertEqual( imb.release_date, imb_date )
        self.assertEqual( imb.release_date_owner, imb_owner )
        self.assertEqual( imb_da.release_date, imb_date )
        self.assertEqual( imb_da.release_date_owner, imb_owner )

    def test_rel_creation_simple( self ):
        """
        Test create new relation between source and dest
        """
        self.clear()

        ri1 = ReleaseImage( release=self.r, archive_item=self.ima )
        ri1.save()

        ri2 = ReleaseImage( release=self.r, archive_item=self.imb )
        ri2.save()

        self._assert_datetimes( self.now, self.now, self.r.get_object_identifier(), self.now, self.r.get_object_identifier() )

    def test_rel_deletion_simple(self):
        """
        Test remove relation between source and destionation
        """
        self.test_rel_creation_simple()

        ri1 = ReleaseImage.objects.get( release=self.r, archive_item=self.ima )
        ri2 = ReleaseImage.objects.get( release=self.r, archive_item=self.imb )

        ri1.delete()
        self._assert_datetimes( self.now, self.now, '', self.now, self.r.get_object_identifier() )

        ri2.delete()
        self._assert_datetimes( self.now, self.now, '', self.now, '' )

    def test_release_update_simple(self):
        """ Test that release date is updated in archive items, when release is updated """
        self.test_rel_creation_simple()

        self.r.release_date = self.new_now
        self.r.save()

        self._assert_datetimes( self.new_now, self.new_now, self.rid, self.new_now, self.r.get_object_identifier() )

    def test_multiple_releases_creation(self):
        """
        Test that release date in archive items is not overwritten when
        an image is added to a new release but already have an release date.
        """
        self.clear()

        ri1 = ReleaseImage( release=self.r, archive_item=self.ima )
        ri1.save()

        ( r, r2, _r3, ima, imb, ima_da, imb_da ) = self._get_objects()
        self.assertEqual( r.release_date, self.now )
        self.assertEqual( r2.release_date, self.now2 )
        self.assertEqual( ima.release_date, self.now )
        self.assertEqual( ima.release_date_owner, r.get_object_identifier() )
        self.assertEqual( ima_da.release_date, self.now )
        self.assertEqual( ima_da.release_date_owner, r.get_object_identifier() )
        #self.assertEqual( imb.release_date, None )
        self.assertEqual( imb.release_date_owner, None )
        self.assertEqual( imb_da.release_date_owner, None )
        # Todo: ought to be blank and not None
        #self.assertEqual( imb.release_date_owner, '' )
        #self.assertEqual( imb_da.release_date_owner, '' )

        #
        # Set add img a and b to rel 2, where img a is
        # already owned by rel 1
        #
        ri1_new = ReleaseImage( release=self.r2, archive_item=self.ima )
        ri1_new.save()

        ri2 = ReleaseImage( release=self.r2, archive_item=self.imb )
        ri2.save()

        ( r, r2, _r3, ima, imb, ima_da, imb_da ) = self._get_objects()
        self.assertEqual( r.release_date, self.now )
        self.assertEqual( r2.release_date, self.now2 )
        self.assertEqual( ima.release_date, self.now )
        self.assertEqual( ima.release_date_owner, r.get_object_identifier() )
        self.assertEqual( ima_da.release_date, self.now )
        self.assertEqual( ima_da.release_date_owner, r.get_object_identifier() )
        self.assertEqual( imb.release_date, self.now2 )
        self.assertEqual( imb.release_date_owner, r2.get_object_identifier() )
        self.assertEqual( imb_da.release_date, self.now2 )
        self.assertEqual( imb_da.release_date_owner, r2.get_object_identifier() )

    def test_multiple_releases_deletion_owner(self):
        """
        When an image has more than one related release, and you delete the owner of
        the release, you must ensure that the release date is updated to the other one.
        """
        self.clear()

        ri1 = ReleaseImage( release=self.r, archive_item=self.ima )
        ri1.save()

        ri2 = ReleaseImage( release=self.r2, archive_item=self.ima )
        ri2.save()

        ri3 = ReleaseImage( release=self.r3, archive_item=self.ima )
        ri3.save()

        ( r, r2, _r3, ima, _imb, ima_da, _imb_da ) = self._get_objects()
        self.assertEqual( r.release_date, self.now )
        self.assertEqual( r2.release_date, self.now2 )
        self.assertEqual( ima.release_date, self.now )
        self.assertEqual( ima.release_date_owner, r.get_object_identifier() )
        self.assertEqual( ima_da.release_date, self.now )
        self.assertEqual( ima_da.release_date_owner, r.get_object_identifier() )

        ri1.delete()

        ( r, r2, _r3, ima, _imb, ima_da, _imb_da ) = self._get_objects()
        self.assertEqual( r.release_date, self.now )
        self.assertEqual( r2.release_date, self.now2 )
        self.assertEqual( ima.release_date, self.now2 )
        self.assertEqual( ima.release_date_owner, r2.get_object_identifier() )
        self.assertEqual( ima_da.release_date, self.now2 )
        self.assertEqual( ima_da.release_date_owner, r2.get_object_identifier() )

    def test_multiple_releases_deletion_notowner(self):
        """
        When an image has more than one related release, and you do not delete the owner but one
        of the others, the the release date should stay the same.
        """
        self.clear()

        ri1 = ReleaseImage( release=self.r, archive_item=self.ima )
        ri1.save()

        ri2 = ReleaseImage( release=self.r2, archive_item=self.ima )
        ri2.save()

        ( r, r2, _r3, ima, _imb, ima_da, _imb_da ) = self._get_objects()
        self.assertEqual( r.release_date, self.now )
        self.assertEqual( r2.release_date, self.now2 )
        self.assertEqual( ima.release_date, self.now )
        self.assertEqual( ima.release_date_owner, r.get_object_identifier() )
        self.assertEqual( ima_da.release_date, self.now )
        self.assertEqual( ima_da.release_date_owner, r.get_object_identifier() )

        ri2.delete()

        ( r, r2, _r3, ima, _imb, ima_da, _imb_da ) = self._get_objects()
        self.assertEqual( r.release_date, self.now )
        self.assertEqual( r2.release_date, self.now2 )
        self.assertEqual( ima.release_date, self.now )
        self.assertEqual( ima.release_date_owner, r.get_object_identifier() )
        self.assertEqual( ima_da.release_date, self.now )
        self.assertEqual( ima_da.release_date_owner, r.get_object_identifier() )

    def test_delete_release(self):
        self.clear()

        ri1 = ReleaseImage( release=self.r, archive_item=self.ima )
        ri1.save()

        ima = Image.objects.get( pk="eso0945a" )
        self.assertEqual( ima.release_date, self.now )
        self.assertEqual( ima.release_date_owner, self.r.get_object_identifier() )
        ima_da = Image.objects.language('da').get( pk="eso0945a" )
        self.assertEqual( ima_da.release_date, self.now )
        self.assertEqual( ima_da.release_date_owner, self.r.get_object_identifier() )

        ima_release_date_old = ima.release_date

        self.r.delete()

        ima = Image.objects.get( pk="eso0945a" )
        self.assertEqual( ima.release_date, ima_release_date_old )
        self.assertEqual( ima.release_date_owner, '' )
        ima_da = Image.objects.language('da').get( pk="eso0945a" )
        self.assertEqual( ima_da.release_date, ima_release_date_old )
        self.assertEqual( ima_da.release_date_owner, '' )

    def test_delete_release_multiple(self):
        self.clear()

        ri1 = ReleaseImage( release=self.r, archive_item=self.ima )
        ri1.save()

        ri2 = ReleaseImage( release=self.r2, archive_item=self.ima )
        ri2.save()

        ima = Image.objects.get( pk="eso0945a" )
        self.assertEqual( ima.release_date, self.now )
        self.assertEqual( ima.release_date_owner, self.r.get_object_identifier() )
        ima_da = Image.objects.language('da').get( pk="eso0945a" )
        self.assertEqual( ima_da.release_date, self.now )
        self.assertEqual( ima_da.release_date_owner, self.r.get_object_identifier() )

        self.r.delete()

        ima = Image.objects.get( pk="eso0945a" )
        self.assertEqual( ima.release_date, self.now2 )
        self.assertEqual( ima.release_date_owner, self.r2.get_object_identifier() )
        ima_da = Image.objects.language('da').get( pk="eso0945a" )
        self.assertEqual( ima_da.release_date, self.now2 )
        self.assertEqual( ima_da.release_date_owner, self.r2.get_object_identifier() )

    def _assert_image( self, im_pk, lang, rel_date, owner ):
        if lang:
            im = Image.objects.language( lang ).get( pk=im_pk )
        else:
            im = Image.objects.get( pk=im_pk )

        self.assertEqual( im.release_date_owner, owner )
        if rel_date:
            self.assertEqual( im.release_date, rel_date )

    def test_potw_creation( self ):
        self.clear()

        self._assert_image( self.ima.id, None, None, None )

        self.potw.image = self.ima
        self.potw.save()

        self._assert_image( self.ima.id, None, self.potw.release_date, self.potw.get_object_identifier() )
        self._assert_image( self.ima_da.id, 'da', self.potw.release_date, self.potw.get_object_identifier() )

    def test_potw_deletion( self ):
        self.test_potw_creation()

        self.potw.delete()

        self._assert_image( self.ima.id, None, self.potw.release_date, '' )
        self._assert_image( self.ima_da.id, 'da', self.potw.release_date, '' )

    def test_potw_set_null( self ):
        self.test_potw_creation()

        self.potw.image = None
        self.potw.save()

        self._assert_image( self.ima.id, None, self.potw.release_date, '' )
        self._assert_image( self.ima_da.id, 'da', self.potw.release_date, '' )

    def test_potw_update( self ):
        self.test_potw_creation()

        self.potw.release_date = self.now
        self.potw.save()

        self._assert_image( self.ima.id, None, self.now, self.potw.get_object_identifier() )
        self._assert_image( self.ima_da.id, 'da', self.now, self.potw.get_object_identifier() )

    def test_potw_update_multiple( self ):
        self.test_potw_creation()

        self.potw2.image = self.ima
        self.potw2.save()

        self._assert_image( self.ima.id, None, self.potw.release_date, self.potw.get_object_identifier() )
        self._assert_image( self.ima_da.id, 'da', self.potw.release_date, self.potw.get_object_identifier() )

        self.potw.release_date = self.now2
        self.potw.save()
        self.potw2.release_date = self.now3
        self.potw2.save()

        self._assert_image( self.ima.id, None, self.potw.release_date, self.potw.get_object_identifier() )
        self._assert_image( self.ima_da.id, 'da', self.potw.release_date, self.potw.get_object_identifier() )

    def test_potw_update_multiple_delete( self ):
        self.test_potw_update_multiple()

        self.potw.delete()

        self._assert_image( self.ima.id, None, self.potw2.release_date, self.potw2.get_object_identifier() )
        self._assert_image( self.ima_da.id, 'da', self.potw2.release_date, self.potw2.get_object_identifier() )

    def test_potw_reverse_creation( self ):
        self.clear()

        self._assert_image( self.ima.id, None, None, None )

        self.ima.pictureoftheweek_set.add( self.potw )

        # self._assert_image( self.ima.id, None, self.potw.release_date, self.potw.get_object_identifier() )
        # self._assert_image( self.ima_da.id, 'da', self.potw.release_date, self.potw.get_object_identifier() )

        self.ima.pictureoftheweek_set.add( self.potw2 )

        # self._assert_image( self.ima.id, None, self.potw.release_date, self.potw.get_object_identifier() )
        # self._assert_image( self.ima_da.id, 'da', self.potw.release_date, self.potw.get_object_identifier() )

    def test_potw_reverse_deletion( self ):
        self.test_potw_reverse_creation()

        # self._assert_image( self.ima.id, None, self.potw.release_date, self.potw.get_object_identifier() )
        # self._assert_image( self.ima_da.id, 'da', self.potw.release_date, self.potw.get_object_identifier() )

        self.assertEqual( [u'eso0945', u'potw1201', ], list(self.ima.pictureoftheweek_set.all().order_by( 'id' ).values_list( 'id', flat=True ) ) )

        self.ima.pictureoftheweek_set.remove( self.potw )

        self.assertEqual( [u'eso0945'], list(self.ima.pictureoftheweek_set.all().order_by( 'id' ).values_list( 'id', flat=True ) ))
        # self._assert_image( self.ima.id, None, self.potw2.release_date, self.potw2.get_object_identifier() )

        # self._assert_image( self.ima_da.id, 'da', self.potw2.release_date, self.potw2.get_object_identifier() )

        self.ima.pictureoftheweek_set.remove( self.potw2 )

        # self._assert_image( self.ima.id, None, self.potw2.release_date, '' )
        # self._assert_image( self.ima_da.id, 'da', self.potw2.release_date, '' )

    def test_image_comparison( self ):
        self.clear()

        ( r, _r2, _r3, ima, imb, _ima_da, _imb_da ) = self._get_objects()
        imcom = ImageComparison( id='eso1208da', priority=0, title='ESO1208DA', image_before=ima, image_after=imb, release_date=self.now4 )
        imcom.save()

        self._assert_image( ima.id, None, imcom.release_date, imcom.get_object_identifier() )
        self.assertEqual( r.release_date, self.now )

        ric1 = ReleaseImageComparison( release=r, archive_item=imcom )
        ric1.save()

        # Test
        imcom = ImageComparison.objects.get( id='eso1208da' )
        ( r, _r2, _r3, ima, imb, _ima_da, _imb_da ) = self._get_objects()

        self._assert_image( ima.id, None, r.release_date, r.get_object_identifier() )
        self.assertEqual( r.release_date, self.now )

        # Change release_date
        r.release_date = self.now3
        r.save()

        # Test
        imcom = ImageComparison.objects.get( id='eso1208da' )
        ( r, _r2, _r3, ima, imb, _ima_da, _imb_da ) = self._get_objects()

        self.assertEqual( r.release_date, self.now3 )
        self._assert_image( ima.id, None, r.release_date, r.get_object_identifier() )



        #self.assertEqual( imcom.release_date_owner, r.get_object_identifier() )
        #self.assertEqual( imcom.release_date, r.release_date )
        #self._assert_image( ima.id, None, r.release_date, r.get_object_identifier() )


#
#       imcom = ImageComparison.objects.get( id='eso1208da' )
#       ( r, r2, r3, ima, imb, ima_da, imb_da ) = self._get_objects()
#
#       self.assertEqual( imcom.release_date_owner, r.get_object_identifier() )
#       self.assertEqual( imcom.release_date, self.now3 )
#       self._assert_image( ima.id, None, self.now3, r.get_object_identifier() )
