# Djangoplicity
# Copyright 2007-2010 ESA/Hubble
#
# Authors:
#   Lars Holm Nielsen <lnielsen@eso.org>
#   Luis Clara Gomes <lcgomes@eso.org>
#
""" 
move_resources.py [-i newid] id src dst 

Copies (or moves) all resources under folder src matching id id to target folder dst.
optionally you can specify a new id with -i, --newid

"""
import os, sys,inspect, getopt,glob,fnmatch,shutil

DEBUG_SEARCH = False
DEBUG_COPY = False
DEBUG_VALS = ['original/eso0908a.tif', 'large/eso0908a.jpg', 'screen/eso0908a.jpg', 'wallpaper1/eso0908a.jpg', 'wallpaper2/eso0908a.jpg', 'wallpaper3/eso0908a.jpg', 'news/eso0908a.jpg', 'newsmini/eso0908a.jpg', 'hofthumbs/eso0908a.jpg', 'medium/eso0908a.jpg', 'mini/eso0908a.jpg', 'wallpaperthumbs/eso0908a.jpg', 'thumbs/eso0908a.jpg', 'newsfeature/eso0908a.jpg']


def check_dir(dir,id,rec=False,do_copy=True):
    """
    1-level recursive function that checks for 'id' named files in given directory.
    Will 
    """
    
    dirs = []
    files = []
    d_pattern = '%s*' % id
    pattern = '%s.*' % id
    
        
    current = os.listdir(dir)
 
    if rec:
        for f in current:
            if os.path.isdir(f):
                a,b = check_dir(f,id)
                dirs.extend(a)
                files.extend(b)
    
    
    if not rec:
        ds = fnmatch.filter (current,d_pattern)
        for d in ds:
            if  '.' not in d and os.path.isdir(os.path.join(dir,d)):
                print "[Found Dir]\t\t%s" % os.path.join(dir,d)
                dirs.extend( [os.path.join(dir,d)] )
                
   
        flist = [os.path.join(dir,f) for f in fnmatch.filter (current, pattern)]
        if len(flist):
            for f in flist:
                print "[Found File]\t\t%s" % f
        
            files.extend( flist )
            
    return dirs,files  
       


def main():
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hi:mf", ["help","newid=","move","force"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
        
    if len(args) != 3:
        print __doc__
        sys.exit(0)
    
    id = args[0]
    src = args[1]
    dst = args[2]
    
    target_id = id
    do_copy = True
    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
        if o in ("-i", "--newid"):
            target_id = a
        if o in ("-m", "--move"):
            do_copy = False
         
    # debug
    if DEBUG_COPY or DEBUG_SEARCH:
        print id,src,dst,do_copy,target_id,do_copy
    
    

    cwd = os.getcwd()
    
    
    if not os.path.isdir(src):
         print "Error: src must be a valid directory."
         print __doc__
         sys.exit(0)
         
    os.chdir(src)


    
    filepaths = []
    dirpaths = []
    walknum = 0
    
    print "Searching..."
    if not DEBUG_SEARCH:
        dirpaths,filepaths = check_dir ('.',id,rec=True)
    
    #print dirpaths
    #print filepaths

    
    
#   for dirpath, dirnames, filenames in os.walk ('.'):
#       print "Checking '%s'..." % dirpath
#       
#       
#       #print dirpath,dirnames,filenames
#       filepaths.extend (
#                         #os.path.join 
#                             (dirpath, f) for f in fnmatch.filter (filenames, pattern)
#                               ) 
#       #print filepaths
#       walknum += 1
#       #if walknum > 5:
#       #   break
        
    os.chdir(cwd)
    
    if DEBUG_SEARCH:
        filepaths = DEBUG_VALS
    
    
    
    if do_copy:
        print "Copying..."
    else:
        print "Moving..."
    
    
    for dirpath in dirpaths:
        try:
            os.makedirs(dst)
        except OSError: 
            pass
        
        if os.path.exists(os.path.join(dst,dirpath)):
            print "[ERROR] %s already exists" % os.path.join(dst,dirpath)
            continue

        if not DEBUG_COPY:
            shutil.copytree(os.path.join(src,dirpath),os.path.join(dst,dirpath))
            
        if not do_copy:     
            if not DEBUG_COPY:
                shutil.rmtree(os.path.join(src,dirpath))
            print "[Move Dir Tree]\t%s\tto\t%s\t[OK]" % (os.path.join(src,dirpath),os.path.join(dst,dirpath))
        else:       
            print "[Copy Dir Tree]\t%s\tto\t%s\t[OK]" % (os.path.join(src,dirpath),os.path.join(dst,dirpath))
        
        
        
    
    for filepath in filepaths:
        d,f = os.path.split(filepath)
        try:
            os.makedirs(os.path.join(dst,d))
        except OSError: 
            pass
        
        f,ext = os.path.splitext(filepath)
        
        sfn = os.path.join(src,filepath)
        
        dstfn = os.path.join(dst,d)
        dstfn = os.path.join(dstfn,target_id+ext)
        
        if do_copy:
            if not DEBUG_COPY:
                shutil.copy(sfn,dstfn)
            print "[Copy File]\t%s\tto\t%s\t[OK]" % (sfn,dstfn)
        else:
            if not DEBUG_COPY:
                shutil.move(sfn,dstfn)          
            print "[Move File]\t%s\tto\t%s\t[OK]" % (sfn,dstfn)
        
    

if __name__ == "__main__":
    main()
