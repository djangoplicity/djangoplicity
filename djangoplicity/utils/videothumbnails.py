import os
import json
import re

__all__ = ['readexif', 'decode_duration', 'format_duration', 'create_video_thumbnail']


def readexif( f, tags ):
    tags = " ".join(["-%s" % t for t in tags])
    cmd = '/usr/bin/exiftool -j -f %s "%s"' % (tags, f)

    p = os.popen(cmd, "r")
    l = p.readlines()
    exifoutput = "".join(l)

    metadata = json.loads(exifoutput)
    return metadata[0]

durationpattern = re.compile(r"([0-9]+:)*[0-9]+(\.[0-9]+)?")


def decode_duration( s ):
    if s:
        m = durationpattern.search( s )

        if m:
            t = m.group(0).split(".")
            if len(t) > 1:
                frames = int(t[1])
            else:
                frames = 0
            ls = t[0].split(":")
            ls = [int(l) for l in ls]
            ls.reverse()

            secs = 0
            f = 1
            for l in ls:
                secs += l * f
                f = f * 60

            return (secs, int(frames))

    return None


def format_duration( secs ):
    tmp = secs
    secs = tmp % 60
    tmp = (tmp - secs) / 60
    mins = tmp % 60
    hours = (tmp - mins) / 60

    return "%0*d:%0*d:%0*d" % (2, hours, 2, mins, 2, secs)


def create_video_thumbnail( vidfile, duration, output='', name=None ):
    (_root, f) = os.path.split(vidfile)
    (base, _ext) = os.path.splitext(f)

    if name:
        outputfile = os.path.join(output, name + ".png")
    else:
        outputfile = os.path.join(output, base + ".png")
    cmd = 'ffmpeg -i "%s" -r 1 -ss %s -t 00:00:01 -f image2 "%s"' % (vidfile, 1 if duration <= 10 else 10, outputfile )
    p = os.popen(cmd, "r")
    p.readlines()

    return outputfile
