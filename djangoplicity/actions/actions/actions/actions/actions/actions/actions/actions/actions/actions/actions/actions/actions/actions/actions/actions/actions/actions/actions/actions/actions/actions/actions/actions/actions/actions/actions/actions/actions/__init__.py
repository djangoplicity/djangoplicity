# -*- coding: utf-8 -*-
#
# djangoplicity-actions
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
Djangoplicity Actions is an application for user defined actions. An action is essentially
a celery task (hence it will be run asynchronously), which as input is sent user editable
configuration as well as other parameters.

The actions is meant to be integrated with other applications which can launch the actions
however they like (e.g. via signals, or direct user input). For instance djangoplicity-contacts
allow a user to define an action to be run when a contact is added/removed from a group (e.g subscribe
the user to mailman list).

Executions of actions are logged in an action log, so they can be inspected.

Installation
------------
Put ``djangoplicity.actions'' in ``INSTALLED_APPS'' in your projects settings.py.

Make sure you register the administration interface with your admin site if you
are not using the default admin site::

    from djangplicity.actions.admin import register_with_admin
    register_with_admin( admin_site )

If you have South installed then run::

    python manage.py migrate actions

otherwise::

    python manage.py syncdb


Defining actions
----------------

An action should like normal celery task be located in app/tasks.py (see [1] and [2]). Below is
an example of a action::


    from djangoplicity.actions.plugins import ActionPlugin

    class SomeAction( ActionPlugin ):
        # User readable version of the action name
        action_name = 'User readable name'

        # List of user definable parameters for this action - will be
        # passed to the run method in the ``conf'' variable.
        action_parameters = [
            ( '<param name>', '<param help text>', '<value type:str|int|bool|date>' ),
            ( 'password', 'Admin password for list', 'str' ),
            ( 'somenum', 'Some num', 'int' ),
        ]

        @classmethod
        def get_arguments( cls, conf, *args, **kwargs ):
            # Custom processing of input arguments - this will run synchronously (i.e
            # before the task is sent to the message queue). Hence, only very simple
            # processing should be done here - e.g ensure input parameters are given
            # in a specific way etc.
            #
            # You can prevent execution of the task by raising an exception here.
            return (args,kwargs)

        def run( self, conf, ... )
            # conf looks like { '<param_name>' : <user defined value>, 'password' : <user defined value>,
            # 'somenum' : <user defined value> }
            #
            # run will be invoked like this ``run( conf, *args, **kwargs)'' where ``args'' and ``kwargs''
            # are the once that are returned from ``get_arguments''.

            # do something here ...

    # Register the plugin so it's available in the admin.
    SomeAction.register()


Executing actions
-----------------
An action is executed a bit differently than a normal celery task::

    from djangoplicity.actions.models import Action

    a = Action.objects.get( ... )
    a.dispatch( ... ) # what ever you provide as args, kwargs it is sent to get_arguments.

Once dispatch is called, get_arguments will be called immediately but the rest of the method will be
sent to a worker node to be done.

Note, it is up to the third-party app developer to figure out how and where to plugin the executing of tasks.

Special notes
-------------
ActionPlugin is a subclass of celery.task.Task with some special methods implemented. Hence, you should
take care not to overwrite these methods:

  * on_failure
  * on_success
  * dispatch
  * get_class_path
  * reigster

Also, in case you plan to subclass you own action then please do yourself the favor and read about abstract
celery Tasks. Basically, if you don't want your base class to be callable as a celery task, then make
sure you put ``abstract = True'' in the class definition::

    class SomeAction( ActionPlugin ):
        # ...
        abstract = True

[1] http://ask.github.com/django-celery/getting-started/first-steps-with-django.html#defining-and-executing-tasks
[2] http://ask.github.com/celery/configuration.html?highlight=celery_imports#celery-imports
"""
