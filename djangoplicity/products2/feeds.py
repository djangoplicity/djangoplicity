# -*- coding: utf-8 -*-
#
# djangoplicity-products
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


#from djangoplicity.archives.feeds import DjangoplicityArchiveFeed
#from models import *
#from options import *
#
#class AnnouncementFeed ( DjangoplicityArchiveFeed ):
#   title = 'Hubble Announcements'
#   link = '/announcements/'
#   description = ''
#
#   description_template = 'feeds/announcement_description.html'
#
#   class Meta(DjangoplicityArchiveFeed.Meta):
#       model = Announcement
#       options = AnnouncementOptions
#       latest_fieldname = Announcement.Archive.Meta.release_date_fieldname
#       enclosure_resources = { ''   : 'resource_screen' }
#       default_query = AnnouncementOptions.Queries.default
#       category_query = None
#       items_to_display = 10
#       archive_query = "default"
#       external_feed_url = "http://feeds.feedburner.com/hubble_announcements/"
#
#
#   def item_enclosure_mime_type( self, item ):
#       return 'image/jpeg'
