***********************
Usage of python in CASA
***********************

In this chapter we review some issues with programming in python in the CASA
environment

CASA vs numpy
=============

Python indices are 0 based, like in C/C++. CASA arays are also indexed 0-based,
but for those familiar with python's numpy and masking arrays, this is where
all similarity ends. Image data in CASA are columnn major, as in Fortran,
where in numpy there are row major, as in C. Masking arrays in casa and numpy's masking
have a reversed logic (mask=True means a bad data point in numpy, but a good one in
CASA)

Our standard example below is an array with 2 planes, 3 rows and 4 columns. The values
in the array will be **i + 10*j + 100*k**, where **i** counts the columns,
**j** the rows, and **k** the planes, all 0-based indexed. This the first value
in the array is 0 (000), the last one 123.  You can also find a file **cube432.fits**
in the ADMIT data distribution.


.. code:: python

   import numpy    as np
   import numpy.ma as ma

   a = np.arange(24).reshape(2,3,4)
   print a.shape, a[1,2,3], a[1][2][3]              # should print: (2, 3, 4) 23 23

   # re-assign values based on their (i,j,k) index
   for k in range(a.shape[0]):
       for j in range(a.shape[1]):
           for j in range(a.shape[2]):
	       a[k,j,i] = i+10*j+100*k

   # mask every third number bad
   b = ma.masked_where(a%3==0,a)
   print a.size, b.count()                          # should print:  24 16
  

We will now see how masking in python and CASA is different.

CODING style
============

When reading the help files within CASA, there are a few bad habits you can pick up,
which may seem convenient, but should not be used if you want your code to be more
portable outside of CASA:


In random order

* **True** and **False** are the python literals for the two boolean values, but you will see
  both **true** and **t** being used in CASA examples. They are defined for convenience within CASA, but if you
  ever want to use your code outside of CASA, this will obviously cause problems. There is no reason
  to not use the official names (if not just for your colorizing editor to recognize them and
  color them appropriately), so use the original python literals.

* more to come

    

  

CASA and ADMIT
==============

For an ADMIT developer environment (the case where your shell has an $ADMIT environment variable and you
would have loaded this by sourcing the appropriate *admit_start.[c]sh* script), your CASA environment has
also been modified to include not only $CASA_ROOT/bin in your $PATH, but also $CASA_ROOT/lib/casa/bin.

If you want to build documentation, you will also have had to install *pip* and *sphinx*.  The **make pip**
target in the $ADMIT directory should do this for most installations.


.. os.getenv("CASAPATH").split()[0]
