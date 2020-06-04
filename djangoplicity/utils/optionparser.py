from optparse import OptionParser
import sys


def get_options( argoptions ):
    parser = OptionParser()
    for o in argoptions:
        try:
            extras = o[4]
        except IndexError:
            extras = {}

        parser.add_option( "-%s" % o[0], "--%s" % o[1], dest=o[1], help=o[2], **extras )

    (options, args) = parser.parse_args()

    args = {}

    for o in argoptions:
        attr = getattr( options, o[1], None )

        if attr is None and o[3]:
            print "Error: Option -%s must be specified." % o[0]
            print ""
            args = ['-h']
            (options, args) = parser.parse_args(args)
            sys.exit(1)

        args[o[1]] = attr

    return args
