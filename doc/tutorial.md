# ADMIT installation + tutorial

For this tutorial we'll be using the standard ADMIT version that
expects ALMA-like data (cube with frequency as the spectral
axis). BYOD or you can use our ADMIT test data.

ADMIT tutorial: https://github.com/astroumd/admit/blob/master/doc/tutorial.md (this page)

ADMIT documentation: http://admit.astro.umd.edu/admit/

## Preparations

Minus some startup time, a typical cube takes about 1" CPU per Mpixel
to process, so if you bring a Gpixel cube, expect to be waiting 20
mins or so.

You can speed up your installation by:

1) Installing CASA on your system, e.g. via https://casa.nrao.edu/casa_obtaining.shtml

    5.1.1 is the preferred latest version, but anything from 4.7.2 and up should be ok.
 
2) Grab the ADMIT source code:

   git clone https://github.com/astroumd/admit.git

   (the $ADMIT/INSTALL file should get you the basic steps, see below)

3) Grab some sample data using wget or curl:

     wget ftp://ftp.astro.umd.edu/pub/admit/testdata/test0.fits

     wget ftp://ftp.astro.umd.edu/pub/admit/testdata/test253_spw3.fits

     wget ftp://ftp.astro.umd.edu/pub/admit/testdata/test253_cont.fits

   these files need to be placed in $ADMIT/testdata (at least if you follow the tutorial guidelines below)


## CASA sanity check

Open a terminal, and the command

     which casa

should give you some hint where the CASA_ROOT directory is. Example problem case is NRAO, where
the return value is **/opt/local/bin/casa**. You would like to see something like **/astromake/opt/casa/511/bin/casa**
in which case the CASA_ROOT is **/astromake/opt/casa/511** where it expects CASA's directories (bin, data, share, xml, etc.).
At NRAO the true CASA_ROOT is hidden from the user, but after some inspection you can find them in
/home/casa/packages/RHEL6/release/casa-release-5.1.1-5 and the usual variations on that theme (RHEL6, RHEL7 etc.).

## Prepare ADMIT to see the correct CASA

Again in the terminal, issue the following commands in the admit directory, e.g.

    git clone https://github.com/astroumd/admit.git
    cd admit
    autoconf

if that command fails (most developers would have this command), use our backup:

    cp scripts/configure  .

and then proceed configuring ADMIT to use the CASA that you have.

On **Linux** you will probably need something like

    ./configure --with-casa-root=/astromake/opt/casa/511

On **MAC**, if you have installed CASA via the DMG file, it should already detect the location, but here is the full command:

    ./configure --with-casa-root=/Applications/CASA.app/Contents

Now add ADMIT to your shell (.sh or .csh)

    source admit_start.sh

To test if everything looks good, use the **admit** command

	admit

   	ADMIT        = /data2/teuben/ADMIT/tutorial/admit
   	    version  = 1.0.7
	CASAPATH     = /astromake/opt/casa/511 linux admit nemo2
	CASA_ROOT    = /astromake/opt/casa/511
	    prefix   = /data2/teuben/ADMIT/casa/casa-release-5.1.1-5.el7
	    version  = 5.1.1-rel-5
	    revision = 1

and thus we are ready to run ADMIT scripts. On MAC systems you might see a warning about casa.init.py, please follow the instructions
on what to put in your **~/.init/casa.py** file.

## Preparing testdata

If you had downloaded the 3 testdata FITS files, you can install them manually, e.g.

       mkdir testdata
       mv ../*.fits testdata

otherwise, the following command will do the same thing, albeit a bit slower

       make testdata


## Running admit: batch-mode


There are two ways to run admit.

1) The **runa1** style scripts, which were used to process pipeline data at NRAO. This has some
black belt options.

2) the more modern **admit_recipe** method. Easier to understand when you are new to ADMIT.

### Method 1: runa1

The command **runa1** is somewhat intelligent on various flavors of CASA pipeline data naming conventions, but
the simplest is a single fits file (no pb,pbcor,flux,image,....):

    runa1 test0.fits
    
    ### (1/1) : processing test0.fits
    test0.fits [128, 128, 50, 1] NGC3256 156.965 -43.905 113.813299345 0.003
    /data2/teuben/ADMIT/tutorial/admit/admit/test/admit1.py --basename x test0.fits
    77.700u 7.120s 2:58.46 47.5%	0+0k 417656+50928io 998pf+0w
    Logfile: test0.fits.log

after which you can browse the ADMIT data in a variety of ways:

      aopen test0.admit/index.html 
      xdg-open test0.admit/index.html

The (successful) flow is ALWAYS recorded in a script **admit0.py**, which can optionally be used for re-execution.

### Method 2: admit_recipe

Recipes are in $ADMIT/admit/recipes, the command **admit_recipe** will remind you which ones exist:

	Available recipes: (see also /data2/teuben/ADMIT/tutorial/admit/admit/recipes)
	------------------
	Archive_Pipeline
	Archive_SpecLine
	Line_Moment
	Source_Find
	Source_Spectra

For example

	admit_recipe Line_Moment test0.fits

would run 
	

### Running via the browser:

Here we can re-run admit via the browser, use the line editor, etc.. But you need to start up CASA first:

     casa
     import admit
     a = admit.Project('test0.admit',dataserver=True)


## Advanced usage

Install ADMIT in the CASA distribution

	cd $ADMIT
	casa-config --exec python setup.py

this should allow usage of ADMIT without any $ADMIT environment.
