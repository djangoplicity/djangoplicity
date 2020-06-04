# -*- coding: utf-8 -*-
#
# djangoplicity-archives-importer
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
This module relying on heavily on djangoplicity.celery.serialtaskset.SerialSendTaskSet. Be sure to know
how it works before changing anything.
"""

import os


def move_resources( taskset, model, options, obj, data, form_values, conf={}, reimport=False ):
    """
    Action to move resources from import root to archive root
    """
    if not reimport:
        exclude_formats = obj.locked_resources()
        taskset.add( "archives.move_resources", args=[conf['import_root'], conf['archive_root']], kwargs={ 'archive_id': obj.pk, 'exclude': exclude_formats } )
    return taskset, conf


def remove_old_resources( resources_to_del=[] ):
    """
    Action to remove old resources prior to import
    """
    def action( taskset, model, options, obj, data, form_values, conf={}, reimport=False ):
        try:
            if form_values['delete_old_formats'] or reimport:
                taskset.add( 'archives.delete_resources', args=[ obj._meta.app_label, obj._meta.model_name, obj.pk, resources_to_del ], kwargs={ } )
        except KeyError:
            pass
        return taskset, conf
    return action


def rename_resource_ext( fmt, old_ext, new_ext ):
    """
    Generate an action that will rename the extensions of a file.
    """
    def action( taskset, model, options, obj, data, form_values, conf={}, reimport=False ):
        if fmt in data.get('formats', []):  # check if format is being imported.
            fmt_path = os.path.join( conf['archive_root'], fmt )

            src = os.path.join( fmt_path, obj.pk + '.%s' % old_ext )
            dst = os.path.splitext( src )[0] + '.%s' % new_ext

            taskset.add( 'archives.move_file', args=[ src, dst ] )
        return taskset, conf
    return action


def process_image_derivatives():
    '''
    Generate an action to make derivatives from images.
    '''
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):

        # If we are importing new formats we receive a list, otherwise
        # it is empty (e.g. in case of a re-import)
        try:
            imported_formats = data['formats']
            if ';' in imported_formats:
                imported_formats = imported_formats.split(';')
            else:
                imported_formats = [imported_formats]
            imported_formats = [f.strip() for f in imported_formats]
        except KeyError:
            imported_formats = None

        args = [obj._meta.app_label, obj._meta.model_name, conf.get('user_id'),
            [obj.pk], None, imported_formats]

        taskset.add('djangoplicity.cutter.tasks.process_images_derivatives', args=args)

        return taskset, conf
    return action


def process_audio_derivatives():
    '''
    Generate an action to make audio derivatives.
    '''
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):
        args = [obj._meta.app_label, obj._meta.model_name, [obj.pk]]
        taskset.add('djangoplicity.media.tasks.process_audio_derivatives', args=args)
        return taskset, conf
    return action


def process_audio_extras():
    '''
    Generate an action to make audio derivatives.
    '''
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):
        args = [obj._meta.app_label, obj._meta.model_name, [obj.pk]]
        taskset.add('djangoplicity.media.tasks.audio_extras', args=args)
        return taskset, conf
    return action


def compute_archive_checksums():
    '''
    Generate an action to computer the resources checksums
    '''
    def action(taskset, model, options, obj, data, form_values, conf={}, reimport=False):

        args = [obj._meta.app_label, obj._meta.model_name, obj.pk]

        taskset.add('djangoplicity.archives.tasks.compute_checksums', args=args)

        return taskset, conf
    return action
