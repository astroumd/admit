#  ADMIT = ALMA Data Mining Toolkit 



Installation notes are in the INSTALL file in this
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
