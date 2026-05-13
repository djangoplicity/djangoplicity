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

from shutil import rmtree
from tempfile import mkdtemp

from celery import current_app
from celery.task import task
from django.conf import settings

from djangoplicity.celery.serialtaskset import str_keys
from djangoplicity.cutter.imagemagick import process_image_derivatives


@task
def process_images_derivatives(app_label, module_name, user_id, pks,
        formats=None, imported_formats=None, sendtask_callback=None,
        sendtask_tasksetid=None):
    '''
    Generate the given formats (or all applicable) for the given archives
    '''
    for pk in pks:
        # Create temporary directory
        tmp_dir = mkdtemp(dir=settings.TMP_DIR)

        try:
            process_image_derivatives(app_label, module_name, pk,
                formats, imported_formats, tmp_dir, user_id)
        finally:
            # Clean up temporary directory
            rmtree(tmp_dir)

    # send_task callback
    if sendtask_callback:
        args, kwargs = sendtask_callback  # pylint: disable=W0633
        current_app.send_task(*args, **str_keys(kwargs))
