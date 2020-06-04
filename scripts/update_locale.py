import os
import csv
import re
from djangoplicity.utils import optionparser
import polib
from django.conf import settings


#  1) Download CSV file from Google Doc
#  2) Run
#     python ../djangoplicity/scripts/update_locale.py -f /Users/lnielsen/Downloads/ESON\ Djangoplicity\ Translations\ Strings\ \(1\).csv -c Portugal -l pt
#  3) Run fab compilemessages
#  4) Commit to mercurial (both po and mo files)
#  5) Deploy


def parse_columns( row ):
    columns = {}
    i = 0
    for c in row:
        if i == 0:
            columns['string'] = i
        else:
            columns[c.strip()] = i
        i += 1

    return columns


def main():
    args = optionparser.get_options( [( 'f', 'filename', 'CSV file', True ),
                                    ( 'c', 'column', 'Column in translation sheet to import', True ),
                                    ( 'l', 'locale', 'Locale to import the strings into', True )] )

    rcsv = csv.reader( open( args['filename'], 'r') )

    #
    # Extract strings
    #
    columns = {}
    strings = {}
    foundstrings = {}
    colname = args['column']
    i = 0

    #  Create regexp to match string formatting, e.g.: %(hours)sh
    regexp = re.compile(r'%[diouxXeEfFgGcrs%]|%\(\S*\)\.?\d?[diouxXeEfFgGcrs%]')

    for r in rcsv:
        if i == 0:
            columns = parse_columns( r )
            if colname not in columns:
                raise Exception("Requested column doesn't exists: %s" % colname)
        else:
            try:
                default = r[columns['string']].strip()
                translation = r[columns[colname]].strip()
                if default and translation:
                    #  Make sure that all string formatting
                    #  are still in the translations:
                    for sub in regexp.findall(default):
                        if sub not in translation:
                            raise Exception("Missing string formatting sequence: '%s' in '%s'" % (sub, translation))
                    strings[default] = unicode(translation, 'utf8' )
                    foundstrings[default] = False
            except IndexError:
                pass
        i += 1

    #
    # Import strings
    #
    pofiles = [os.path.join(settings.PRJBASE, 'src', app.replace('.', '/'), 'locale') for app in settings.FABLICITY_MESSAGE_APPS]
    pofiles.append('%s/src/djangoplicity/locales/locale' % settings.DJANGOPLICITY_ROOT)

    for f in pofiles:
        path = os.path.join( os.path.join( f, args['locale'] ), "LC_MESSAGES/django.po" )

        if not os.path.exists( path ):
            print "%s does not exists - cannot update the file" % path
            continue

        po = polib.pofile( path )
        updated = False

        for i, (s, t) in enumerate(strings.items()):
            entry = po.find( unicode(s, 'utf8') )
            if entry:
                foundstrings[s] = True
                if 'fuzzy' in entry.flags:
                    entry.flags = filter( lambda x: x != 'fuzzy', entry.flags )
                    updated = True
                    print u"Removed fuzzy flag on - %s" % entry.msgstr

                if entry.msgstr != t:
                    entry.msgstr = t
                    updated = True
                    print u"Entry updated - %s" % entry.msgstr
            # Fri May 29 14:08:40 CEST 2015 - Mathias
            # We probably don't want to add the entries in the files if they 
            # don't already exist
            # else:
                # entry = polib.POEntry(
                    # msgid=unicode(s, 'utf-8'),
                    # msgstr=t,
                    # occurences=[('Translation Spreadsheet', i)],
                # )
                # po.append(entry)
                # updated = True
                # print u"New entry added - %s" % entry.msgstr

        if updated:
            po.save()

    if '' in foundstrings.values():
        print ""
        print "Following strings were not found"
        print "================================"
        for s, v in foundstrings.items():
            if not v:
                print s

if __name__ == '__main__':
    main()
