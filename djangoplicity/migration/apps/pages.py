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

from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import str
from bs4 import BeautifulSoup
from djangoplicity.pages.models import Page
from django.contrib.redirects.models import Redirect
from djangoplicity.migration import MigrationTask, MigrationError, MigrationConfAdapter
from djangoplicity.migration.utils import links
import os
from urllib.request import url2pathname
from urllib.parse import urlsplit, urlunsplit
from django.utils.encoding import python_2_unicode_compatible


def nl2space( text ):
    if text:
        text = text.split('\n')
        text = [x.strip() for x in text]
        text = " ".join(text)
    return text


@python_2_unicode_compatible
class PageDocument( MigrationConfAdapter ):
    """
    Base class for migration of any document into a djangoplicity.pages.models.Page
    object.

    Assumptions::
      * Pages are static files located in a directory structure.
      * The directory structure is used to determine the page URL.
        For instance /somedir/somepage.html becomes /somedir/somepage/
        while e.g. /somedir/index.html becomes /somedir/.
    """
    default_pages = ['index.html', 'index.htm']

    def __init__(self, filename, new_url=None ):
        self._filename = filename
        self._parsed = False
        self._title = None
        self._new_url = new_url

    def filepath( self, root ):
        """
        Get absolute path to file for document
        """
        return os.path.join( root, self._filename )

    def new_url(self):
        """
        Generate new URL for page.
        """
        if self._new_url:
            return self._new_url

        elements = list(os.path.split( self._filename ))
        filename = elements[-1]

        if elements[0] == '':
            del elements[0]

        if filename in self.default_pages:
            return '/%s/' % "/".join( elements[:-1] )
        else:
            base, _ext = os.path.splitext( filename )
            elements[-1] = base
            return '/%s/' % "/".join( elements )

    def old_urls(self):
        """
        Determine URLs of old document
        """
        elements = os.path.split( self._filename )
        if elements[-1] in self.default_pages:
            return ["/%s" % self._filename, '/%s/' % "/".join( elements[:-1] ) ]
        else:
            return ["/%s" % self._filename]

    def __str__( self ):
        return self.title()

    #
    # All methods below you most likely will
    # want to override in a subclass
    #
    def parse( self ):
        """
        Parse document to be able to extract relevant information. By default,
        the method just reads a text file and maps it to Page.content.

        You most likely want to overwrite this method in a subclass.
        """
        f = open( self.filepath( self.conf['pages']['root'] ) )
        self._file_contents = f.read()
        f.close()
        self._parsed = True

    def title(self):
        return None

    def content(self):
        return self._file_contents if self._parsed else None

    def description(self):
        return None

    def keywords(self):
        return None

    def section(self):
        return None


class HTMLPageDocument( PageDocument ):
    """
    Migration of a HTML page

    Experiment
    """
    def __init__( self, *args, **kwargs ):
        super( HTMLPageDocument, self ).__init__( *args, **kwargs )
        self._title = None
        self.encoding = None
        self.soup = None

    def soup2str( self, s ):
        """
        Get the contents of a soup element as a string.
        """
        return "".join([str(x) for x in s.contents])

    def convert_entities(self, s):
        from djangoplicity.utils.html_cleanup import convert_html_entities
        return self.soup2str(convert_html_entities(s))

    #
    # Parser
    #
    def parse(self):
        """
        Parse spacetelescope.org HTML page.
        """
        super( HTMLPageDocument, self ).parse()
        self.soup = BeautifulSoup( self._file_contents, 'lxml')
        self._parsed = True

    def title(self):
        elem = self.soup.find( 'title' )
        return "".join( elem.contents ).strip()

    def content(self):
        elem = self.soup.find( 'body' )
        if elem:
            return "".join([str(x) for x in elem.contents]).strip()
        else:
            return None


class PageInitializationTask( MigrationTask ):
    """
    Initialization of environment before starting a migration.
    The task clears any page objects and redirects from the
    database.
    """
    def run(self):
        Page.objects.all().delete()
        Redirect.objects.all().delete()


class PageMigrationTask( MigrationTask ):
    """
    Migration of a single document on the file path
    """
    conf_injection = ['document']

    def __init__( self, document ):
        self.document = document
        super( PageMigrationTask, self ).__init__()

    def _setup_redirects( self, page ):
        """
        Setup redirects for new URLs
        """
        for url in self.document.old_urls():
            if url != page.url:
                r = Redirect( site=self.conf['pages']['site'], old_path=url, new_path=page.url )
                r.save()

    def _create_page(self ):
        """
        Create a new page object from a PageDocument.
        """
        try:
            p = Page(
                    title=self.document.title(),
                    url=self.document.new_url(),
                    content=self.document.content(),
                    section=self.document.section() or self.conf['pages']['section'],
                )
            p.save()
            return p
        except Exception as e:
            import pprint
            pprint.pprint(e)
            raise MigrationError( "Could not save the parse page." )

    def run(self):
        """
        Migrate document
        """
        self.document.parse()

        #
        # Create page object
        #
        self.logger.debug("Creating Page object...")
        page = self._create_page()

        #
        # Create redirects
        #
        self.logger.debug("Creating redirects...")
        self._setup_redirects( page )

        #
        # Update global state
        #


        # save p id, extracted links.

class PageLinksCleanupTask( MigrationTask ):
    """
    Updating of links in all migrated pages.
    """
    conf_injection = []

    def __init__( self, bases=None, patterns=[], link_replacements={} ):
        super( PageLinksCleanupTask, self ).__init__()
        self.redirects = {}
        self.bases = bases
        self.patterns = patterns
        self.link_replacements = link_replacements
        self.not_updated = []
        self.not_considered = []
        self.externallinks = []

        for b in self.bases:
            if b[-1] == '/':
                b = b[:-1]

    def _pagebase(self, page):
        """
        Determine the page base for the old page, so we know from where
        relative links should be interpreted from.
        """
        try:
            pagebase = Redirect.objects.get( new_path=page.url ).old_path
        except:
            pagebase = page.url

        return pagebase

    def url_update( self, link ):
        # First try redirect
        try:
            parts = urlsplit( link )
            tmp = urlunsplit( ( parts[0], parts[1], parts[2], parts[3], '' ) )
            new_link = self.redirects[tmp]
            new_parts = urlsplit( new_link )
            return ( urlunsplit( ( new_parts[0], new_parts[1], new_parts[2], new_parts[3], parts[4] ) ), True )
        except KeyError:
            pass

        # Next try manually specified replacements
        try:
            return (self.link_replacements[link], True)
        except KeyError:
            pass

        # Next try patterns
        for p in self.patterns:
            if p[0].match( link ):
                return (p[0].sub( p[1], link ), True)

        self.not_updated.append( (None, link) )
        return (link, False)

    def _is_page_link(self, link):
        return links.is_ext( link, ['.html', '.htm', '/'] )

    def update_page_links( self, page ):
        """
        Update links in a page according to the list of redirects.
        """
        pagelinks = links.extract_links( page.content )
        pagelinks = list(zip( pagelinks, [links.normalize_link( x, self.bases ) for x in pagelinks] ))

        #  Internal/external links
        internallinks = [x for x in pagelinks if links.is_internal_link( x[1], self.bases )]
        self.externallinks += [x for x in pagelinks if not links.is_internal_link( x[1], self.bases )]

        # Normalize to absolute path
        internallinks = [( x[0], links.to_absolute_link( x[1], self._pagebase( page ) ) ) for x in internallinks]

        # Determine if link should be updated
        self.not_considered += [x for x in internallinks if not self._is_page_link( x[1] )]
        internallinks = [x for x in internallinks if self._is_page_link( x[1] )]

        # Update links
        replacements = [( x[0], self.url_update( x[1] ) ) for x in internallinks]

        # Update links in content
        content = links.replace_links( page.content, replacements, self.logger )

        if page.content != content:
            page.content = content
            page.save()

    def _print_links(self, msg, links, logmethod=None ):
        """
        Print a list of links
        """
        if not logmethod:
            logmethod = self.logger.debug

        # Make dict.
        tmp = {}

        for l in links:
            if l[1] in tmp:
                tmp[l[1]].append(l[0])
            else:
                tmp[l[1]] = [l[0]]

        # Sort keys
        keys = list(tmp.keys())
        keys.sort()

        for k in keys:
            logmethod("%s %s..." % (msg, k ) )
            #self.logger.debug("%s %s (original(s) %s)..." % (msg, k, tmp[k] ) )

    def run(self):
        """
        Fix links in migrated pages.
        """
        # First get list of redirects
        self.logger.debug("Generating list of redirects...")
        self.redirects = links.redirect_list()

        # Then check every page
        pages = Page.objects.all()
        for p in pages:
            self.logger.info( "Updating page %s..." % p.url )
            self.update_page_links( p )

        self._print_links( "Link not updated", self.not_updated )
        self._print_links( "Link not considered", self.not_considered )
        self._print_links( "External link", self.externallinks )


class PageFilesCopyTask( PageLinksCleanupTask ):
    def _is_static_file( self, link ):
        return True

    def _setup_redirect(self, old, new ):
        if old != new:
            try:
                r = Redirect( site=self.conf['pages']['site'], old_path=old, new_path=new )
                r.save()
            except:
                self.logger.warn( "Could not setup redirect %s to %s " % (old, new) )

    def url_update( self, link ):
        ret = super( PageFilesCopyTask, self ).url_update( link )

        if ret[1]:  # Link has been updated
            old_path = os.path.join( self.conf['pages']['root'], url2pathname(link[1:]) )  # Kill first back-slash in link
            new_path = os.path.join( self.conf['media_root'], url2pathname( ret[0][1:] ) )

            if not os.path.isfile( old_path ):
                self.nonexistingfiles.append( (None, link) )
            else:
                if not os.path.exists( new_path ):
                    self.logger.debug( "Copying file %s to %s " % (old_path, new_path) )
                    (head, _tail) = os.path.split( new_path )

                    # Create intermediate directories
                    try:
                        os.makedirs( head )
                    except OSError as e:
                        if e.errno != 17:
                            raise e

                    # Copy file
                    #shutil.copyfile( old_path, new_path )
                    os.symlink( old_path, new_path )
                else:
                    self.logger.debug( "Files not copied (already exists): %s..." % new_path )

                # Setup a redirect
                self._setup_redirect( link, ret[0] )

        return ret

    def update_page_links( self, page ):
        """
        Update links in a page according to the list of redirects.
        """
        pagelinks = links.extract_links( page.content )
        pagelinks = list(zip( pagelinks, [links.normalize_link( x, self.bases ) for x in pagelinks] ))

        internallinks = [x for x in pagelinks if links.is_internal_link( x[1], self.bases )]
        filelinks = [( x[0], links.to_absolute_link( x[1], self._pagebase( page ) ) ) for x in internallinks]
        filelinks = [x for x in filelinks if self._is_static_file( x[1] )]

        # Update links
        _replacements = [( x[0], self.url_update( x[1] ) ) for x in filelinks]

    def run(self):
        """
        Fix links in migrated pages.
        """
        # First get list of redirects
        #self.logger.debug("Generating list of redirects...")
        #elf.redirects = links.redirect_list()
        self.nonexistingfiles = []

        # Then check every page
        pages = Page.objects.all()
        for p in pages:
            self.logger.info( "Copying files linked in page %s..." % p.url )
            self.update_page_links( p )

        self._print_links( "Non existing file", self.nonexistingfiles, logmethod=self.logger.warn )
