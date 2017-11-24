# ADMIT installation + tutorial

For this tutorial we'll be using the standard ADMIT version that
expects ALMA-like data (cube with frequency as the spectral
axis). BYOD or you can use my ADMIT test data.

See also: https://github.com/astroumd/admit/blob/master/doc/tutorial.md

Minus some startup time, a typical cube takes about 1" CPU per Mpixel
to process, so if you bring a Gpixel cube, expect to be waiting 20
mins or so.

You can speed things up by:

1) Installing CASA on your system, e.g. https://casa.nrao.edu/casa_obtaining.shtml

    5.1.1 is the preferred latest version, but anything from 4.7.2 and up should be ok.
 
2) Grab the ADMIT source code:

   git clone https://github.com/astroumd/admit.git

3) Grab some sample data using wget or curl:

     wget ftp://ftp.astro.umd.edu/pub/admit/testdata/test0.fits

     wget ftp://ftp.astro.umd.edu/pub/admit/testdata/test253_spw3.fits

     wget ftp://ftp.astro.umd.edu/pub/admit/testdata/test253_cont.fits


## CASA sanity check

Open a terminal, and the command

     which casa

should give you some hint where the CASA_ROOT directory is. Example problem case is NRAO, where
the return value is **/opt/local/bin/casa**. You would like to see something like **/astromake/opt/casa/511/bin/casa**
in which case the CASA_ROOT is **/astromake/opt/casa/511**

## Prepare ADMIT to see the correct CASA

Again in the terminal, issue the following commands in the admit directory, e.g.

    git clone https://github.com/astroumd/admit.git
    cd admit
    autoconf

if that command fails (most developers would have this command), use our backup:

    cp scripts/configure  .

and then proceed configuring ADMIT to use the CASA that you have.   On **Linux** you will probably need something like

    ./configure --with-casa-root=/astromake/opt/casa/511/bin/casa

On **MAC**, if you have installed CASA via the DMG file, it should already detect the location, but here is the full command:

    ./configure --with-casa-root=/Applications/CASA.app/Contents

Now add ADMIT to your shell

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

and thus we are ready to run ADMIT

## Preparing testdata

If you had downloaded the 3 testdata FITS files, you can install them manually, e.g.

       mkdir testdata
       mv ../*.fits testdata

otherwise this will do the same thing, albeit a bit slower

       make testdata


## Running admit: batch-mode


There are two ways to run admit. The **runa1** style scripts, which were used to 
