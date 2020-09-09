#! /usr/bin/env python
#! /opt/casa/packages/RHEL7/release/current/bin/python
#
#   AAP = Admit After Pipeline
#
#   Example python script (and module) that for a given directory finds all ALMA pbcor.fits files
#   and runs a suite of predefined ADMIT recipes on them, in a local directory named madmit_<YMD_HMS>
#   It normally matches the pb.fits files, so ADMIT can work on noise flat image cubes.
#
#   Notes:
#      1. this is still for old-style admit, not ADMIT3, but should port to python3 when ready
#      2. this does not encode the different tree view that is encoded in the old do_aap5 or runa1
#      3. it handles *.pb.fits as well as *.pb.fits.gz files that should mirror the *.pbcor.fits files
#
#   SCRIPT usage
#      aap.py -d dir1  [-c] [-n] [-r] [-s] [-v]
#          -c     check files to see if there are orphans we may not have encoded for ADMIT processing
#          -n     dry-run, prints out the commands as they would run (old style ADMIT)
#          -r     remove all CASA images/tables after the ADMIT run
#          -s     single mode, only one default run per image/cube
#          -v     verbose
#
#   To use as a script, your shell environment must have 'casa' and  CASA's 'python' in the $PATH,
#   this normally takes two modifications, e.g.
#        export PATH=$CASAROOT/bin:$CASAROOT/lib/casa/bin:$PATH
#
#   MODULE usage
#      import aap
#      madmitname = aap.compute_admit(dirname)
#
#   @todo ...
#

_version = "9-sep-2020 PJT"

import os, sys
import argparse as ap
import glob
import datetime

#   decipher the python environment (yuck)
try:
    import casa
    print("Warning fake: still assuming classic ADMIT")
    is_admit3 = False
except:
    try:
        import casatasks    # pre-release now does this????
        is_admit3 = True
        print("Good fake news: running ADMIT3")
    except:
        print("Bad fake news: your python doesn't know casa or casatasks")


def version():
    """
    identify yourself
    """
    print("AAP Version %s" % _version)


def usage():
    """
    command line helper
    """
    print("Usage: %s -d DIR(s)")
    print("For one or more DIR's find the pbcor.fits files that are needed for 'runa1' and 'runa2' type recipes in ADMIT")
    sys.exit(0)

def splitall(path):
    """
        Taken from https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s16.html
    """
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts

def casa_cleanup(admitname):
    """
    clean an admit directory of all CASA images
    the method here needs to be certified by a CASA expert
    """
    # @todo in Python3:   from pathlib import Path
    # this is only 3 levels deep, works for now
    files =  glob.glob("%s/*/table.info" % admitname) + glob.glob("%s/*/*/table.info" % admitname) + glob.glob("%s/*/*/*/table.info" % admitname)    
    for f in files:
        dat = f.replace("table.info","")
        cmd = "rm -rf %s" % dat
        print("CLEANUP: %s" % cmd)
        os.system(cmd)

def find_pbcor(dirname, mfs=False, cube=False, verbose=False):
    """
    find the ALMA pbcor files in a directory.... since everything starts with a pbcor file.
    We keep the MFS/CONT separate from CUBE, since they require different recipes.
    """
    pbcor = []
    if cube:
        pbcor1a = glob.glob('%s/*.cube.*pbcor*fits' % dirname)
        for p1 in pbcor1a:
            if verbose:
                print(p1)
            pbcor.append(p1)
    if mfs:
        pbcor2a = glob.glob('%s/*.mfs.*pbcor*fits' % dirname)
        pbcor2c = glob.glob('%s/*.cont.*pbcor*fits' % dirname)
        for p2 in pbcor2a+pbcor2c:
            if verbose:
                print(p2)
            pbcor.append(p2)
    return pbcor

def runa1(pbcorname,pbname=None,label=None,apars=[],dryrun=False,cleanup=False):
    """
        the runa1 recipe, with optional extra args
        $ADMIT/admit/test/admit2.py --pb fname.pb.fits.gz --basename x --out fname.<label>.admit --apar fname.<label>.apar   fname.pbcor.fits
    e.g.   runa1(fname, "native.5sigma", ["numsigma=5"])
           runa1(fname, "binned16.3sigma", ["insmooth=-16","numsigma=5"])
    """
    r = '$ADMIT/admit/test/admit1.py'
    r = r + ' --pb %s' % pbname
    r = r + ' --basename x'
    if len(apars) > 0:
        if label == None:
            aparname = pbcorname + '.apar'
        else:
            aparname = pbcorname.replace('.fits','') + '.%s.apar' % label
        if not dryrun:
            fp = open(aparname,"w")
            fp.write("# written by AAP\n")
            for apar in apars:
                fp.write("%s\n" % apar)
            fp.close()
            r = r + ' --apar %s' % aparname
    if label == None:
        outname =  pbcorname.replace('.fits','') + ".admit"
    else:
        outname =  pbcorname.replace('.fits','') + '.%s.admit' % label
    r = r + ' --out %s' % outname
    r = r + ' %s' % pbcorname
    r = r + ' > %s.log 2>&1' % outname
    print(r)
    if not dryrun:
        os.system(r)
        if cleanup:
            casa_cleanup(outname)

def runa2(pbcorname,pbname=None,label=None,apars=[],dryrun=False,cleanup=False):
    """
        the runa2 recipe, with optional extra args
        $ADMIT/admit/test/admit2.py --pb fname.pb.fits.gz --basename x --out fname.<label>.admit --apar fname.<label>.apar   fname.pbcor.fits
    e.g.   runa1(fname, "native.5sigma", ["numsigma=5"])
           runa1(fname, "binned16.3sigma", ["insmooth=-16","numsigma=5"])

           pbcorname = basename.pbcor.fits
           outname   = basename.pbcor.admit      or basename.pbcor.<label>.admit
           aparname  = basename.pbcor.fits.apar  or basename.pbcor.<label>.apar
    """
    r = '$ADMIT/admit/test/admit2.py'
    r = r + ' --pb %s' % pbname
    r = r + ' --basename x'
    if len(apars) > 0:
        if label == None:
            aparname = pbcorname + '.apar'
        else:
            aparname = pbcorname.replace('.fits','') + '.%s.apar' % label
        if not dryrun:
            fp = open(aparname,"w")
            fp.write("# written by AAP\n")
            for apar in apars:
                fp.write("%s\n" % apar)
            fp.close()
            r = r + ' --apar %s' % aparname
    if label == None:
        outname =  pbcorname.replace('.fits','') + ".admit"
    else:
        outname =  pbcorname.replace('.fits','') + '.%s.admit' % label
    r = r + ' --out %s' % outname
    r = r + ' %s' % pbcorname
    r = r + ' > %s.log 2>&1' % outname
    print(r)
    if not dryrun:
        os.system(r)
        if cleanup:
            casa_cleanup(outname)        

def run_admit(recipe, pbcor, madmitname, dryrun=False, verbose=False, single=False, cleanup=False):
    """
         based on a full pbcor file run an ADMIT recipe 
    """ 
    idx = pbcor.find('.pbcor.fits')
    pb = glob.glob(pbcor[:idx] + '.pb.fits*')
    if len(pb) == 0:
        print("Warning: no matching pb found for %s" % pbcor)
        return
    pb = pb[0]
    if verbose:
        print(pbcor)
        print(pb)
    #  pbcor and pb are filenames relative to the dirname
    #  e.g. PID/S/G/M/product/member.uid___A001_X133f_X1a2.Tile_004_SMC_SWBar_sci.spw22.cube.I.pbcor.fits
    #                 product/member.uid___A001_X133f_X1a2.Tile_004_SMC_SWBar_sci.spw22.cube.I.pbcor.fits
    pbname = splitall(pb)[-1]
    d = splitall(pbcor)
    pbcorname = d[-1]
    pbcorpath = os.path.abspath(pbcor)
    pbpath = os.path.abspath(pb)
    pdir = '/'.join(d[:-1])
    adir = '/'.join(d[:-2]) + '/admit'
    adir = madmitname
    if verbose:
        print(adir)
    #    now some horrid file operations which can possible be done more efficiently if I had a better toolkit
    cmd = 'mkdir -p %s' % adir
    if not dryrun:
        os.system(cmd)
        cwd = os.getcwd()
        os.chdir(adir)
        os.system('ln -sf %s' % (pbcorpath))
        os.system('ln -sf %s' % (pbpath))

    if recipe == 'runa2':
        os.system('listfitsa %s' % pbcorname)
        if single:
            runa2(pbcorname,pbname,dryrun=dryrun,cleanup=cleanup)
        else:
            # @todo   add some smoothing?   go from 5ppx to 10ppx ?
            # @todo   LGM's default is numsigma=6
            runa2(pbcorname,pbname,"5sigma",["numsigma=5"],dryrun=dryrun,cleanup=cleanup)
            runa2(pbcorname,pbname,"3sigma",["numsigma=3"],dryrun=dryrun,cleanup=cleanup)
    elif recipe == 'runa1':
        os.system('listfitsa %s' % pbcorname)
        if single:
            runa1(pbcorname,pbname,dryrun=dryrun,cleanup=cleanup)
        else:
            #  @todo   LineID's default is numsigma=5
            #runa1(pbcorname,pbname,"native.5sigma",["numsigma=5"],dryrun=dryrun,cleanup=cleanup)
            #runa1(pbcorname,pbname,"binned4.3sigma",["insmooth=[-4]","numsigma=3"],dryrun=dryrun,cleanup=cleanup)
            runa1(pbcorname,pbname,"native.3sigma",["numsigma=3"],dryrun=dryrun,cleanup=cleanup)
            runa1(pbcorname,pbname,"binned16.3sigma",["insmooth=[-16]","numsigma=3"],dryrun=dryrun,cleanup=cleanup)
            
    if not dryrun:
        os.chdir(cwd)

def alma_names(dirname):
    """
    debugging: search and destroy what we know
    """
    cwd = os.getcwd()
    os.chdir(dirname)
    files = glob.glob('*fits*')
    pbcors = glob.glob('*.pbcor.fits')
    pbcors.sort()
    nfiles = len(files)
    npbcors = len(pbcors)
    print("Found %d pbcor in %d fits files" % (npbcors,nfiles))
    for pbcor in pbcors:
        pb = pbcor.replace('.pbcor.fits','.pb.fits.gz')
        try:
            i1=files.index(pb)
            files.remove(pbcor)
            files.remove(pb)
        except:
            print("missing %s" % pb)
        mask = pb.replace('.pb.','.mask.')
        try:
            i1=files.index(mask)
            files.remove(mask)
        except:
            print("missing %s" % mask)
    for f in files:
        print("orphan  %s" % f)
    if len(files)==0:
        print("Hurray, no orphan files")
    os.chdir(cwd)

def compute_admit(dirname, madmitname=None, verbose=False, dryrun=False, single=False, cleanup=False):
    """
    do it all
    """
    # @todo    if dirname contains the whole P/S/G/M name, store that too
    if madmitname == None:
        prefix=dirname.split('/')
        # try some unique name that name-completes but also parses fast by the human eye and filebrowsers
        madmitname = os.path.abspath('./madmit_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S.%f'))
        madmitname = os.path.abspath(prefix[-1]+"_"+prefix[-2]+"_"+datetime.datetime.now().strftime('%Y%m%d_%H%M%S.%f'))
    print("MADMIT: %s" % madmitname)

    # @todo   only mfs and cube?  what about cont ?  or _ph and _pb
    p1 = find_pbcor(dirname,cube=True, verbose=verbose)
    print("Found %d cube pbcor fits files for ADMIT to process" % len(p1))
    p2 = find_pbcor(dirname,mfs=True, verbose=verbose)
    print("Found %d msf pbcor fits files for ADMIT to process" % len(p2))
    if len(p1) + len(p2) == 0:
        return None

    # the cheap continuum maps
    for p in p2:
        run_admit('runa2', p, madmitname, verbose=verbose, dryrun=dryrun, single=single, cleanup=cleanup)

    # the expensive cubes
    for p in p1:
        run_admit('runa1', p, madmitname, verbose=verbose, dryrun=dryrun, single=single, cleanup=cleanup)

    return madmitname


if __name__ == "__main__":

    
    parser = ap.ArgumentParser(description='AAP (ADMIT After Pipeline) processing - %s' % _version)
    
    parser.add_argument('-d', '--dirname', nargs = 1, type = str, default = ['.'],
                        help = 'Name of the directory containing data')

    parser.add_argument('-c', '--checknames', action="store_true", default = False,
                        help = 'Name Check on all fits files, report orphans')

    parser.add_argument('-n', '--dryrun', action = "store_true", default = False,
                        help = 'Dryrun mode')
    
    parser.add_argument('-r', '--cleanup', action = "store_true", default = False,
                        help = 'Cleanup CASA images after run')

    parser.add_argument('-s', '--single', action = "store_true", default = False,
                        help = 'Single ADMIT mode')

    parser.add_argument('-v', '--verbose', action = "store_true", default = False,
                        help = 'Verbose mode.')

    args = vars(parser.parse_args())

    if len(sys.argv) == 1:
        usage()

    version()

    # Project ID, below which there is (at least one) Sous/Gous/Mous
    dirname = args['dirname'][0]
    do_names = args['checknames']
    verbose = args['verbose']
    dryrun = args['dryrun']
    single = args['single']
    cleanup = args['cleanup']
    print(single)

    if do_names:
        alma_names(dirname)
    else:
        madmitname = compute_admit(dirname,verbose=verbose,dryrun=dryrun,single=single,cleanup=cleanup)

# - end
    
