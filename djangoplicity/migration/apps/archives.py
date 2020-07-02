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

from djangoplicity.migration import MigrationTask, MigrationConfAdapter
import csv


class DataMapping( MigrationConfAdapter ):
    """
    """
    def __init__(self, entry):
        self.dataentry = entry

    def run(self):
        pass


class DataSourceIterator( object ):
    """
    Dummy data source iterator, that just stops immediately.
    """
    def __iter__(self):
        return self

    def next(self):
        raise StopIteration


class DataSource( MigrationConfAdapter ):
    """
    Abstract class defining the minimum interface that must
    be implemented.
    """
    def initialize(self):
        pass

    def __iter__(self):
        return DataSourceIterator()


class CSVIterator( object ):
    """
    Special CSV iterator which can returns a dictionary object
    mapping CSV fields to values instead of a list of values.
    """

    def __init__( self, reader, fieldnames ):
        self.reader = reader
        self.fieldnames = fieldnames

    def __iter__(self):
        return self

    def _to_dict( self, entry ):
        i = 0
        data = {}

        for f in self.fieldnames:
            try:
                data[f] = entry[i]
                i += 1
            except IndexError:
                data[f] = None

        return data

    def next(self):
        return self._to_dict( next(self.reader) )


class CSVDataSource( DataSource ):
    """
    CSV-file data source provider for an archive migration
    task.

    By default the first line in the CSV file is assumed to be
    the header, unless they are provided on object initialization.

    Only the fields defined in the header will be returned.
    """
    def __init__( self, filename, dialect=None, fieldnames=None ):
        self.csvfilename = filename
        self.dialect = dialect
        self.reader = None
        self.fieldnames = fieldnames

    def __iter__(self):
        """
        Returns special iterator for CSV files that returns
        dictionary objects instead of lists. If dialect have been
        specified the CSV file will be opened using that dialect.
        """
        if self.dialect:
            self.reader = csv.reader( open( self.csvfilename, "r"), dialect=self.dialect )
        else:
            self.reader = csv.reader( open( self.csvfilename, "r") )

        if not self.fieldnames:
            self.fieldnames = next(self.reader)

        return CSVIterator( self.reader, self.fieldnames )


class ArchiveInitializationTask( MigrationTask ):
    """
    Initialization of environment before starting a migration.
    The task clears any page objects and redirects from the
    database.
    """
    def __init__( self, archiveclass ):
        self.archiveclass = archiveclass

    def run(self):
        self.archiveclass.objects.all().delete()


class ArchiveMigrationTask( MigrationTask ):
    """
    Migration of a single document on the file path
    """
    conf_injection = ['datasource']

    def __init__( self, datasource, datamapping ):
        self.datasource = datasource
        self.datamapping = datamapping
        super( ArchiveMigrationTask, self ).__init__()

    def run(self):
        """
        Migrate document
        """
        self.logger.debug("Initializing data source...")
        self.datasource.initialize()

        #
        # Creating archive entries
        #
        i = 1
        for entry in self.datasource:
            self.logger.debug("Mapping data entry to archive item %s..." % i)

            mapping = self.datamapping( entry )

            self.inject_conf( mapping )

            mapping.run()

            i += 1


        #
        # Create redirects
        #

        #TOOD
        #self.logger.debug("Creating redirects...")

        #
        # Update global state
        #


        # save p id, extracted links.
