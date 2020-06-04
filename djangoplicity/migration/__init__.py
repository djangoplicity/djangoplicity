# -*- coding: utf-8 -*-
#
# djangoplicity-migration
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
The ``djangoplicity.migration`` package contains a general framework for
migrating content from legacy systems into djangoplicity.

It works by specifying the migration in a script as a number of *tasks* to be carried out.
Each task has the job of reading content from the legacy system and mapping it into djangoplicity
models and possibly setting up redirects or other extra tasks. The framework provides features for
easy logging and error handling in each task, as well as maintaining a global state which can be
manipulated by each task.

An example migration script looks like this::

    # Define logger to use
    logger = define_logger( "migration_logger", level=logging.DEBUG, file_logging=False )

    # Define configuration options
    conf = {
        # ... more conf options ...
        'logger' : 'migration_logger',
    }

    # Define migration tasks
    tasks = [
        SomeMigrationTask( ... ),
        SomeMigrationTask( ... ),
        SomeOtherMigrationTask( ... ),
        SomeMigrationTask( ... ),
    ]

    if __name__ == "__main__":
        # Run migration
        run_migration( conf, tasks )

In ``djangoplicity.migration.apps`` there is already a lot of migration tasks that can be used as
a starting point for migrating content.
"""

from djangoplicity.migration.migration import *
