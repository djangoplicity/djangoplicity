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


from builtins import str
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.admin.utils import quote
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.urls import reverse, NoReverseMatch
from django.forms.formsets import formset_factory
from django.http import Http404
from django.shortcuts import render
from django.utils.safestring import mark_safe

from djangoplicity.archives.importer.forms import GenericImportForm, \
    GenericImportFormSet, UploadFileForm
from djangoplicity.archives.importer.utils import find_importables, \
    handle_import, run_import_actions

TITLE = "%s file import"


def _check_perms(request, model):
    """
    Check user permissions
    """
    # Check user for change permission on model (i.e. "<app>.<model>_change" permissions)
    perm = '%s.change_%s' % (model._meta.app_label, model._meta.model_name)
    if not request.user.has_perm(perm):
        raise PermissionDenied


@staff_member_required
def upload_file(request, archive_model, archive_options):
    """
    Files upload view for archives

    Note: Files upload requires change permission on the archive model
    """
    _check_perms(request, archive_model)

    if not archive_options.Import.uploadable or not archive_options.Import.scan_directories:
        raise Http404

    # Get paths and settings
    archive_import_root = os.path.join(settings.ARCHIVE_IMPORT_ROOT,
        archive_options.urlname_prefix)

    # Process form
    if request.method == 'POST':
        file_upload_form = UploadFileForm(request.POST, request.FILES,
            directories=archive_options.Import.scan_directories, model=archive_model)

        if file_upload_form.is_valid():
            file_upload_form.handle_files(request,
                os.path.join(archive_import_root, file_upload_form.cleaned_data['format']))

            files = ', '.join([f.name for f in request.FILES.getlist('files')])
            n = len(request.FILES.getlist('files'))
            messages.add_message(request, messages.SUCCESS,
                u'%d file(s) were successfully uploaded: %s' % (n, files))
            messages.add_message(request, messages.INFO,
                mark_safe(u"If you're not automatically returned to the previous form in 5 seconds, please click <a href='../'>here</a>."))
            redirect = mark_safe(u'<META HTTP-EQUIV="refresh" CONTENT="5;URL=../" />')

            return render(request, 'admin/archives/upload_success.html', {
                'app_label': archive_model._meta.app_label,
                'opts': archive_model._meta,
                'title': "Video file import: Upload",
                'redirect': redirect,
                'file_upload_form': file_upload_form,
            })
        else:
            return render(request, 'admin/archives/upload_success.html', {
                'app_label': archive_model._meta.app_label,
                'opts': archive_model._meta,
                'file_upload_form': file_upload_form,
                'title': "Video file import: Upload",
            })
    else:
        raise Http404


@staff_member_required
def manage_archive_imports(request, archive_model, archive_options):
    """
    Files import view for archives

    Note: Files import requires change permission on the archive model
    """
    _check_perms(request, archive_model)

    # Get paths and settings
    archive_import_root = os.path.join(settings.ARCHIVE_IMPORT_ROOT,
        archive_options.urlname_prefix)

    # Setup forms (import and file upload)
    FormSet = formset_factory(getattr(archive_options.Import, 'form', GenericImportForm),
        extra=0, formset=GenericImportFormSet)

    if archive_options.Import.uploadable:
        file_upload_form = UploadFileForm(initial={'format': 'original'},
            directories=archive_options.Import.scan_directories,
            model=archive_model)
    else:
        file_upload_form = None

    # Retrieve available files for import
    if 'find_importables' in dir(archive_options) and \
        callable(archive_options.find_importables):
        files, invalid = archive_options.find_importables(archive_import_root,
            archive_model, archive_options)
    else:
        files, invalid = find_importables(archive_import_root, archive_model,
                    archive_options)

    # Process form
    if request.method == 'POST':
        formset = FormSet(request.POST, request.FILES)
        if not formset.is_valid():
            return render(request, 'admin/archives/importer.html', {
                'import_root': archive_import_root,
                'formset': formset,
                'upload_form': file_upload_form,
                'title': TITLE % archive_model._meta.verbose_name.title(),
                'object_name': archive_model._meta.verbose_name,
                'app_label': archive_model._meta.app_label,
                'opts': archive_model._meta,
                'invalid': invalid,
            })
        else:
            for frm in formset.cleaned_data:
                # Check "import" field if id is selected for import
                if not frm['import']:
                    continue

                # Find or create model object and associated file data
                obj_id = frm['id']
                data = files[obj_id]
                obj = data["obj"] if data["obj"] else archive_model()

                # Update model object with new values
                if 'handle_import' in dir(archive_options) and \
                    callable(archive_options.handle_import):
                    archive_options.handle_import(obj, id=obj_id, data=data,
                        form_values=frm)
                else:
                    handle_import(obj, id=obj_id, data=data, form_values=frm)

                extra_conf = {'user_id': request.user.pk}

                # Run import actions in background (i.e import files, generate derivatives etc.)
                run_import_actions(archive_import_root, archive_model,
                    archive_options, obj, data=data, form_values=frm,
                    extra_conf=extra_conf)

                # Add entry to object's admin history
                try:
                    change_message = 'Imported files: %s' % frm['formats']
                except KeyError:
                    # This shouldn't happen, but better safe than sorry
                    change_message = 'Imported files: no file formats found'

                LogEntry.objects.log_action(
                    user_id=request.user.pk,
                    content_type_id=ContentType.objects.get_for_model(obj).pk,
                    object_id=obj_id,
                    object_repr=str(obj),
                    action_flag=CHANGE,
                    change_message=change_message
                )

                # Remove just imported id from list of files
                try:
                    del files[obj_id]
                except KeyError:
                    pass

                # Prepare message for user
                try:
                    messages.add_message(request, messages.SUCCESS,
                        mark_safe(
                            u'File was successfully imported as <a href="%s">%s</a> <a href="%s">(Edit)</a>. Processing file in background job.' % (
                                obj.get_absolute_url(),
                                obj.pk,
                                reverse('admin:%s_%s_change' %
                                    (obj._meta.app_label, obj._meta.model_name),
                                    args=[quote(obj.pk)],
                                ),
                            )
                        )
                    )
                except (AttributeError, NoReverseMatch):
                    messages.add_message(request, messages.SUCCESS,
                        mark_safe(u"File was successfully imported and is being processed in a background job."))

    # Note any id that has been imported, will have been removed from here.
    initial = list(files.values())
    initial.sort(key=lambda x: x['id'])

    formset = FormSet(initial=initial)

    return render(request, 'admin/archives/importer.html', {
        'import_root': archive_import_root,
        'formset': formset,
        'upload_form': file_upload_form,
        'title': TITLE % archive_model._meta.verbose_name.title(),
        'object_name': archive_model._meta.verbose_name,
        'app_label': archive_model._meta.app_label,
        'opts': archive_model._meta,
        'invalid': invalid,
    })
