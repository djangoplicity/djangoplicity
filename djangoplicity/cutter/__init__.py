# -*- coding: utf-8 -*-
#
# djangoplicity-cutter
# Copyright (c) 2007-2016, European Southern Observatory (ESO)
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


# Djangoplicity-cutter process all the images derivatives of a given archive
#
# To determine which formats to process it looks at all the resources of type
# ImageResourceManager defined in Archive for the given archive.
# Using the dimensions, compression etc. defined in the resource type all
# the derivatives images are then created.
#
# To enable it simply add djangoplicity.cutter to settings.py
#
# The tasks are called automatically by process_images_derivatives if it is
# configured in the Archive's Import actions
#
# Steps to enable the Crop interface:
#
# 1) Add CropModel and crop_display_format to the Archive's inherited classes:
#    crop_display_format is the format used in the admin interface, it should
#    be non-cropped format.
#       from djangoplicity.cutter.models import CropModel
#       class Image(archives.ArchiveModel, TranslationModel, CropModel):
#           class Archive:
#               class Meta:
#                   crop_display_format = 'thumb300y'
# 2) Add CropAdmin to the ModelAdmin:
#    from djangoplicity.cutter.admin import CropAdmin
#    class ImageAdmin(dpadmin.DjangoplicityModelAdmin, RenameAdmin, CropAdmin):
#
# 3) Add a link to crop/ to the Archive's detailed admin template
#    <li><a href="crop/" class="historylink">{% trans "Crop" %}</a></li>
