#  ADMIT = ALMA Data Mining Toolkit 



Installation notes are in the INSTALL file in this
directory. Developers should also look in INSTALL.dev

Optional components are described in opt/README.



## LATEST News (CASA 6.x)

ADMIT can now installed within CASA6. Here's a short installation
example, assuming you have installed CASA6 inside of your python3
tree:

      git clone https://github.com/astroumd/admit
      cd admit
      pip install -e .

after which your session should work as follows

      ipython --profile casa6
      import admit
      p = admit.Project('test0.fits')
      ...

Modular casa is also known to work now (Jan 2026) - see INSTALL.dev
