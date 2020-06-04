# -*- coding: utf-8 -*-
#
# djangoplicity-celery
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

from celery import current_app
import uuid

# Work around fix - see http://stackoverflow.com/questions/1210458/how-can-i-generate-a-unique-id-in-python
uuid._uuid_generate_time = None
uuid._uuid_generate_random = None


def str_keys( d ):
    """
    Return a dict where all keys are 8 bit strings
    """
    return dict( [ ( str( k ), v ) for k, v in d.items() ] )


class SerialSendTaskSet( object ):
    """
    Helper class to create a serial execution of tasks, to be called via ``current_app.send_task()``::

        taskset = SerialSendTaskSet()
        taskset.id # Id is already assigned when you create the class

        taskset.add( "task.name", args=[], kwargs={} ) # Use like you would use current_app.send_task()
        taskset.add( "nexttask.name", args=[], kwargs={} )

        taskset.send_task() # Note, can only be called once.


    Each task in the list must take two keywords arguments ``sendtask_callback`` and ``sendtask_tasksetid``,
    and must also ensure to call the next task::

        def sometask(..., sendtask_callback=None, sendtask_tasksetid=None ):
            # ...
            if sendtask_callback:
                args, kwargs = sendtask_callback
                current_app.send_task( args, kwargs )

    ``sendtask_tasksetid`` is a unique id for the task set which all tasks in the taskset share.
    """
    def __init__( self ):
        self.id = str(uuid.uuid4())
        self.taskset = []
        self.ran = False

    def add( self, *args, **kwargs ):
        self.taskset.append( ( args, kwargs ) )

    def send_task(self):
        if not self.ran:
            if len(self.taskset) > 0:
                next_args, next_kwargs = None, None

                while len(self.taskset) > 0:
                    args, kwargs = self.taskset.pop()
                    if next_args is not None and next_kwargs is not None:
                        if 'kwargs' not in kwargs:
                            kwargs['kwargs'] = {}
                        kwargs['kwargs']['sendtask_callback'] = ( next_args, next_kwargs )
                        kwargs['kwargs']['sendtask_tasksetid'] = self.id
                    next_args, next_kwargs = args, kwargs

                current_app.send_task( *args, **kwargs )
                self.ran = True
        else:
            raise Exception( "SerialSendTaskSet already applied" )
