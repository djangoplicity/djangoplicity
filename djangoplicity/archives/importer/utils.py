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

import os
import re
from datetime import datetime

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.template.defaultfilters import date as date_filter

from djangoplicity.archives.importer.forms import GenericImportForm
from djangoplicity.celery.serialtaskset import SerialSendTaskSet


def _get_files( path ):
    """
    Get files in a specified directory (creating the directory if it does not exists).
    """
    if not os.path.exists( path ):
        os.makedirs( path )
    return os.listdir( path )


def run_import_actions( root, model, options, obj, data={}, form_values={}, extra_conf={} ):
    """
    Build a SerialSendTaskSet from a list of defined actions and send it for background
    processing.
    """
    taskset = SerialSendTaskSet()

    conf = {
        'import_root': root,
        'archive_root': os.path.join( settings.MEDIA_ROOT, model.Archive.Meta.root ),
        'archive_path': model.Archive.Meta.root,
    }

    conf.update( extra_conf )

    for action in options.Import.actions:
        taskset, conf = action( taskset, model, options, obj, data, form_values, conf=conf, )

    taskset.send_task()


def rerun_import_actions( model, options, obj, extra_conf={} ):
    """
    """
    taskset = SerialSendTaskSet()

    conf = {
        'archive_root': os.path.join( settings.MEDIA_ROOT, model.Archive.Meta.root ),
        'archive_path': model.Archive.Meta.root,
    }
    conf.update( extra_conf )

    for action in options.Import.actions:
        taskset, conf = action( taskset, model, options, obj, {}, {}, conf=conf, reimport=True )

    taskset.send_task()


def find_importables( archive_import_root, archive_model, archive_options, exclude_id=None ):
    """
    Finds files suitable for import.

    Will look for files matching <archive_root>/<format>/<id>.<ext>. The <archive_root> is defined in settings.py,
    <format> in the variable scan_directories in the import form (see archive_options.Import.form).

    If the archive options has its own find_importables method, this method will not be called.
    Returns a dict of importable files and a list of invalid files
    """
    files = {}
    invalid = []

    # Find files for all formats
    for fmt, allowed_exts in archive_options.Import.scan_directories:
        # Ignore directories which does not match a resource on the archive.
        if not hasattr( archive_model.Archive, fmt ):
            continue

        fmt_directory = os.path.join( archive_import_root, fmt )

        disallowed_characters_regex = r"[^\w-]"
        # Get files in directory or creates the directory if it doesn't exists.
        for f in _get_files( fmt_directory ):
            ( obj_id, ext ) = os.path.splitext( f )
            cleanid = re.sub(disallowed_characters_regex, "", obj_id)
            fpath = os.path.join(fmt_directory, f)

            # Skip file if: excluded file, unallowed extension, dot file,
            # disallowed characters or whitespace in file
            if cleanid == exclude_id or ext.lower() not in allowed_exts or \
                re.search(disallowed_characters_regex, obj_id) or ' ' in obj_id:
                invalid.append(fpath)
                continue

            # Skip file is name is longer than the id's max_length
            try:
                max_length = archive_model._meta.get_field('id').max_length
            except FieldDoesNotExist:
                max_length = 0
            if max_length and len(obj_id) > max_length:
                continue

            if cleanid not in files:
                files[cleanid] = {
                    'id': cleanid,
                    'formats': [fmt],
                    'files': [fpath],
                }
            else:
                files[cleanid]['formats'].append( fmt )

                files[cleanid]['files'].append( fpath )

    #
    # Find existing objects and metadata for files.
    #

    # Dict mapping object ids to objcets
    objects = dict( [( x.pk, x ) for x in archive_model.objects.filter( pk__in=files.keys() )] )
    # Flag indicating if model options has special method to extract metadata from file.
    # Import form
    blank_form = getattr( archive_options.Import, 'form', GenericImportForm )()

    for obj_id in files:
        file_data = {
            'is_new': True,
            'obj': None,
        }

        # Get existing object
        if obj_id in objects:
            file_data["is_new"] = False
            file_data["obj"] = objects[obj_id]
            obj = file_data["obj"]

            # Copy values from model object to initial form value (e.g. title, priority)
            # Only fields defined on the form are copied.
            for field in blank_form:
                if field.name in obj.__dict__ and field.name not in ['is_new', 'obj']:
                    file_data[field.name] = getattr( obj, field.name )

        # Get metadata
        data = {}
        if hasattr( archive_options.Import, 'metadata' ) and archive_options.Import.metadata in files[obj_id]['formats']:
            if 'handle_metadata' in dir( archive_options ) and callable( archive_options.handle_metadata ):
                data = archive_options.handle_metadata( files[obj_id]['files'][files[obj_id]['formats'].index( archive_options.Import.metadata )], locked=file_data.keys() + files[obj_id].keys() )
            else:
                data = handle_metadata( files[obj_id]['files'][files[obj_id]['formats'].index( archive_options.Import.metadata )], locked=file_data.keys() + files[obj_id].keys() )
        data.update( file_data )  # Overwrite any conflicting data which has been extracted from the file metadata

        # Check priority, published, title, date_modifiwed
        if 'priority' not in data and 'priority' in blank_form.fields:
            data['priority'] = "0"
        if 'published' not in data and 'published' in blank_form.fields:
            data['published'] = False
        if 'title' not in data and 'title' in blank_form.fields:
            data['title'] = obj_id
        if 'date_modified' not in data and 'date_modified' in blank_form.fields:
            data['date_modified'] = date_filter( datetime.fromtimestamp( os.path.getmtime( files[obj_id]['files'][0] ) ), arg='r' )

        data.update( files[obj_id] )
        data['formats'] = "; ".join( data['formats'] )

        files[obj_id] = data

    return (files, invalid)


DJANGOPLICITY2AVM = {
    'title': 'Title',
    'description': 'Description',
    'credit': 'Credit',
}


def handle_metadata( filename, locked=[] ):
    """
    Read basic metadata from image file
    """
    try:
        from libavm.utils import avm_from_file
        dict = avm_from_file( filename )

        out_dict = {}

        for dj, av in DJANGOPLICITY2AVM.iteritems():
            if dj not in locked:
                if dict.get( av, False ):
                    out_dict[dj] = dict[av]
        return out_dict
    except ( ImportError, Exception ):
        return {}


def handle_import( obj, id=None, data={}, form_values={}, save=True ):
    """
    Must save object.
    """
    if data['is_new']:
        obj.pk = id

    hidden_keys = ['files', 'formats', 'obj', 'date_modified', 'is_new', 'import', 'id', ]
    form_keys = ['title', 'priority', 'published']
    metadata_keys = set( data.keys() ) - set( hidden_keys + form_keys )

    # Copy form values to object
    for k in form_keys:
        try:
            setattr( obj, k, form_values[k] )
        except KeyError:
            pass

    # Copy metadata only for new objects
    if data['is_new']:
        for k in metadata_keys:
            try:
                setattr( obj, k, data[k] )
            except Exception:
                pass
    if save:
        obj.save()
    return obj
