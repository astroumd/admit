#  ADMIT = ALMA Data Mining Toolkit 


Documentation:
* our own build: http://admit.astro.umd.edu
* github pages: https://astroumd.github.io/admit (experimental)
* casaguide: https://casaguides.nrao.edu/index.php/ADMIT_Products_and_Usage

## Example Install (CASA 5.x)

Here is an example how to install ADMIT with the old python2 based CASA

      git clone https://github.com/astroumd/admit
      cd admit
      ./configure --with-casa-root=$HOME/CASA/casa-pipeline-release-5.6.2-2.el7/
      source admit_start.sh
      make bench

and this should run a short ~1 minute benchmark, displaying the  measured flux as

      MOM0FLUX: x-cs.CO_115.27120 27292.2 25565.2 35.0141 2790.35 2790.35 58.5574

Detailed installation notes are also in the INSTALL file in this
directory. Developers should also look in INSTALL.dev

Optional components are described in opt/README.



## LATEST News (CASA 6.x)

The *python3* branch can now install ADMIT within the experimental
CASA6. Here's a short installation example, assuming you have installed CASA6
inside of your python3 tree:

      git clone https://github.com/astroumd/admit
      cd admit
      git checkout python3
      pip install -e .

after which your python3 session should work as follows

      ipython --profile casa6
      import admit
      p = admit.Project('test0.fits')
      ...

The official CASA 6.1 will be released soon (Summer 2020), and these instructions here will be updated,
as they will re-instate the casa prompt no doubt.
