#! /usr/bin/env python
#
#   Example python script that for a given directory and finds all ALMA {cube,mfs} pbcor.fits files,
#   and runs a suite of predefined ADMIT recipes on them, in a local directory named madmit-<YMD-HMS>
#
#   Notes:
#      1. this is still for old-style admit, not ADMIT3
#      2. this does not encode the different tree view that is encoded in the old do_aap5
#      3. it handles *.pb.fits as well as *.pb.fits.gz files that should mirror the *.pbcor.fits files
#
#   Script usage
#      aap.py dir1 [dir2 ...]
#
#   Module usage
#      import aap
#      aap.compute_admit(directoryname)
#
import os, sys
import glob
import datetime

try:
    import casa
    print("Warning: still assuming classic ADMIT")
    is_admit3 = False
except:
    try:
        import casatasks    # pre-release now does this????
        is_admit3 = True
        print("Good news: running ADMIT3")
    except:
        print("Bad news: your python doesn't know casa or casatasks")

    
def usage():
    print("Usage: %s PID(s)")
    print("For one or more PID's find the pbcor.fits files that are needed for 'runa1' and 'runa2' in ADMIT")
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

def find_pbcor(dirname, mfs=False, cube=False, verbose=False):
    """
    find the ALMA pbcor files in a directory.
    Currently limited to "mfs" and/or "cube"
    """
    pbcor = []
    if cube:
        pbcor1 = glob.glob('%s/*_sci*.cube.I.pbcor.fits' % dirname)
        for p1 in pbcor1:
            if verbose:
                print(p1)
            pbcor.append(p1)
    if mfs:
        pbcor2 = glob.glob('%s/*_sci*.mfs.I.pbcor.fits' % dirname)
        for p2 in pbcor2:
            if verbose:
                print(p2)
            pbcor.append(p2)
    return pbcor

def runa1(pbcorname,pbname=None,label=None,apars=[],dryrun=False):
    """ the runa1 recipe, with optional extra args
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

def runa2(pbcorname,pbname=None,label=None,apars=[],dryrun=False):
    """ the runa1 recipe, with optional extra args
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


def run_admit(recipe, pbcor, madmitname, dryrun=False, verbose=False):
    """ based on a full pbcor file run a recipe in a directory parallel to product
            [dir/]product/basename.mfs.I.pbcor.fits       runa1
            [dir/]product/basename.cube.I.pbcor.fits      runa2
        A directory name before 'product' is optional, but recommended
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
        print("PJT",pbcor)
        os.system('ln -sf %s' % (pbcorpath))
        os.system('ln -sf %s' % (pbpath))

    if recipe == 'runa2':
        runa2(pbcorname,pbname,dryrun=dryrun)
        runa2(pbcorname,pbname,"native.5sigma",["numsigma=3"],dryrun=dryrun)
    elif recipe == 'runa1':
        runa1(pbcorname,pbname,"native.5sigma",["numsigma=5"],dryrun=dryrun)
        runa1(pbcorname,pbname,"binned4.3sigma",["insmooth=-4","numsigma=3"],dryrun=dryrun)

    if not dryrun:
        os.chdir(cwd)

def compute_admit(dirname, madmitname=None, verbose=False, dryrun=False):
    """
    do it all
    """
    if madmitname == None:
        # try some unique name that filecompletes but is parses fast by the human eye
        # strftime('%Y-%m-%dT%H:%M:%S.%f')   ->  does not work deep inside casa (lattice expr?)
        madmitname = os.path.abspath('./madmit_'+datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S.%f'))
    print("MADMIT: ",madmitname)
    
    p1 = find_pbcor(dirname,cube=True, verbose=verbose)
    print("Found %d cube pbcor fits files for ADMIT to process" % len(p1))
    p2 = find_pbcor(dirname,mfs=True, verbose=verbose)
    print("Found %d msf pbcor fits files for ADMIT to process" % len(p2))
    if len(p1) + len(p2) == 0:
        return None

    if True:
        # quick single test
        # madmitname = './madmit'
        run_admit('runa2', p2[0], madmitname, verbose=verbose, dryrun=False)
        run_admit('runa1', p1[0], madmitname, verbose=verbose, dryrun=False)
        return madmitname
    
    # the cheap continuum maps
    for p in p2:
        run_admit('runa2', p, madmitname, verbose=verbose, dryrun=dryrun)

    # the expensive cubes
    for p in p1:
        run_admit('runa1', p, madmitname, verbose=verbose, dryrun=dryrun)

    return madmitname


if __name__ == "__main__":

    if len(sys.argv) == 1:
        usage()

    # Project ID, below which there is (at least one) Sous/Gous/Mous
    dirname = sys.argv[1]
    verbose = False
    dryrun = True

    madmitname = compute_admit(dirname,verbose=verbose,dryrun=dryrun)

# - end
    
