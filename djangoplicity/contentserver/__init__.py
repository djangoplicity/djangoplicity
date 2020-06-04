# -*- coding: utf-8 -*-
#
# djangoplicity
# Copyright (c) 2007-2015, European Southern Observatory (ESO)
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


from djangoplicity.contentserver.base import *

# A Content Server is used to serve files from a different location than
# the default archive.
# This is done by ResourceManager.get_resource_for_instance() which will check
# if a ContentServer is configured for the given resource, and whether it is
# ready (for example in the case where the resources have to be uploaded to a
# CDN a task will be started in the background to upload the files, only when
# the upload is complete will the resource be served through the content server)
#
# The simpliest content server will just set a different domain/url and assume
# that the files are always in sync (e.g.: stored on the same network path),
# these can be configured with ContentServer
#
# More advanced content server must inherit from this basic class and can
# provide more advanced functionalities, such as uploading the files to a CDN,
# etc. For more details see e.g. CDN77ContentServer
#
#  Steps to configure an Archive to use Content server delivery:
#
#  1) Add ContentDeliveryModel to the Archive's inherited classes:
#
#       from djangoplicity.contentserver.models import ContentDeliveryModel
#       class Video(archives.ArchiveModel, TranslationModel, ContentDeliveryModel):
#
# 2) Add ContentDeliveryAdmin tot he Admin class, and the content_server and
#    content_server_ready to the Admin class:
#
#       from djangoplicity.contentserver.admin import ContentDeliveryAdmin
#
#       class VideoAdmin(..., ContentDeliveryAdmin)
#
#       fieldsets = (
#       ...
#           ( _(u'Content Delivery'), {'fields': ( 'content_server', 'content_server_ready'), 'classes': ('collapse',) } ),
#       ...
#       )
#       readonly_fields = ('content_server_ready', )
#       list_filter = ( ..., 'content_server', 'content_server_ready')
#       actions = [ ..., 'action_resync_resources']
#
# 3) Add signals to sync data to the content server if it is changed:
#
#       from django.db.models import signals
#       signals.pre_save.connect(Video.content_server_changed, sender=Video)
#       signals.post_save.connect(Video.sync_archive_to_content_server, sender=Video)
#       archives.post_rename.connect(Video.sync_archive_on_rename, sender=Video)
#
# 4) Configure the content servers in settings.py, each Archive served with the
#    content server is identifyed by it's full path (e.g.: djangoplicity.media.models.images.Image'
#    and lists its own formats), for example for CDN77:
#
#       from djangoplicity.contentserver import ContentServer, CDN77ContentServer
#       MEDIA_CONTENT_SERVERS = {
#           'CDN77': CDN77ContentServer(
#               name='CDN77',
#               formats= {
#                   'djangoplicity.media.models.images.Image': (
#                       'screen',
#                       ...
#                       'zoomable',
#                   ),
#                   'djangoplicity.media.models.videos.Video': (
#                       'dome_2kmaster',
#                       ...
#                       'dome_preview',
#                   ),
#               }
#               url='http://cdn.example.com/',
#               remote_dir='/www/',
#               host='push.example.com',
#               username='username',
#               password='password',
#               api_login='login@example.com',
#               api_password='apipassword',
#               cdn_id='xxxx',
#           )
#       }
#
#       MEDIA_CONTENT_SERVERS_CHOICES = (
#           ('', 'Default'),
#           ('CDN77', 'CDN77'),
#       )
#
#       DEFAULT_MEDIA_CONTENT_SERVER = 'CDN77'
#
# 5) Add Import actions to the archive's Option:
#
#       from djangoplicity.contentserver.import_actions import sync_content_server
#       class VideoOptions(ArchiveOptions):
#       ...
#           class Import(object):
#               ...
#               actions = [
#                   ...
#                   sync_content_server(),
#               ]
