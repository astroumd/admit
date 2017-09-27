************************************
Scripts that show real-world flows
************************************

The Python scripts below are detailed, working examples of ADMIT processing as
might be done in the ALMA pipeline or by a scientist with an ALMA FITS cube.

Example 1: Ingest_ through LineID_ and Moment_
==============================================
.. _admit-example1:

This script takes a FITS cube and does the following:

#. Create an ADMIT project directory and import the FITS cube into a CASA image. [Ingest_]

#. Compute `robust statistics`_ on the input data. [CubeStats_]

#. Sum all cube along all channels of the frequency axis to make a integrated map. [CubeSum_]

#. Compute a spectrum through the cube at a specified point (default: the spatial center). [CubeSpectrum_]

#. Create a position-velocity diagram by selecting an optimum slice position angle through examination of the emission properties. [PVSlice_]

#. Compute a position-velocity cross-correlation [PVCorr_]

#. Identify any spectral lines present in the data [LineID_]

#. Create a cutout cube for each spectral lines identified [LineCube_]

#. Compute moment 0,1,2 maps, and spectra for each cutout cube [Moment_, CubeSpectrum_]

#. Write out the ADMIT project results to XML and a summary HTML file.


admit_example1.py_
~~~~~~~~~~~~~~~~~~

.. tabularcolumns:: |p{1cm}|p{16.5cm}|

+------------+------------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                    |
+============+==========================================================================================+
| 1          | casarun is ADMIT's wrapper for running Python scripts with 'casapy  --quiet --nogui -c'  |
+------------+------------------------------------------------------------------------------------------+
| 21         | You need only to 'import admit' to get all ADMIT functionality.                          |
+------------+------------------------------------------------------------------------------------------+
| 27-45      | Initial parameters to for script options.                                                |
+------------+------------------------------------------------------------------------------------------+
| 48-54      | ALMA does not yet pass VLSR to its output cubes, so we have to kludge it here.           |
+------------+------------------------------------------------------------------------------------------+
| 56-70      | Method to create string name of output directory based on input cube name.  E.g., for    |
|            | input cube 'mycube.fits', output directory will be 'mycube.admit'                        |
+------------+------------------------------------------------------------------------------------------+
| 73-80      | Parse command line arguments                                                             |
+------------+------------------------------------------------------------------------------------------+
| 89-91      | Potentially clean up an old run                                                          |
+------------+------------------------------------------------------------------------------------------+
| 98         | Create an ADMIT project or open existing one (if it wasn't cleaned up)                   |
+------------+------------------------------------------------------------------------------------------+
| 100-108    | If a new ADMIT project, copy the FITS file into it, otherwise print some info and exit   |
+------------+------------------------------------------------------------------------------------------+
| 111        | Set default plotting parameters.                                                         |
+------------+------------------------------------------------------------------------------------------+
| 114-116    | Create the first task, Ingest_, which reads in the FITS cube, and add the task to the    |
|            | project flow_. Optionally mask data that are zero (useMask=True).                        |
+------------+------------------------------------------------------------------------------------------+
| 119-123    | Create the second task, CubeStats_AT which calculates data statistics, and add the task  |
|            | to the project flow_. Set the method of robust statistics to be used (robust) and        |
|            | optionally create the peak-point plot (usePPP=True).                                     |
+------------+------------------------------------------------------------------------------------------+
| 125-129    | Create the third task, CubeSum_AT which calculates a map over all channels, and add it to|
|            | the flow_.                                                                               |
+------------+------------------------------------------------------------------------------------------+
| 131-137    | Create the fourth task, CubeSpectrum_AT calculates a spectrum through the cube and add it|
|            | to the flow_.                                                                            |
+------------+------------------------------------------------------------------------------------------+
| 141-146    | Choose one of the hardcoded ways of specifying a slice or slit for a position-velocity   |
|            | diagram.   See `PVSlice`_ for the difference between slices and slits.                   |
+------------+------------------------------------------------------------------------------------------+
| 147-151    | Alternatively, let PVSlice_AT determine the best slice location.                         |
+------------+------------------------------------------------------------------------------------------+
| 152-153    | Now create the 5th task, PVSlice_, and add it to the flow_.                              |
+------------+------------------------------------------------------------------------------------------+
| 155-156    | Create the 6th task, PVCorr_, and add it to the flow_.                                   |
+------------+------------------------------------------------------------------------------------------+
| 159-166    | This is a workaround for the fact that ALMA data cubes do not currently include the      |
|            | source LSR velocity in the image header.  So we look in our own internal list to see if  |
|            | there is an entry for the source.  Future releases should not need this workaround.      |
+------------+------------------------------------------------------------------------------------------+
| 168-170    | Create the 6th task, LineID_, and add it to the flow_.                                   |
+------------+------------------------------------------------------------------------------------------+
| 168-170    | Create the 7th task, LineCube_, and add it to the flow_. Set the growth option to        |
|            | include 10 channels around the channel range found by LineID_.                           |
+------------+------------------------------------------------------------------------------------------+
| 172-174    | Now we must run the tasks created so far, so that the subsequent tasks, which depend     |
|            | the number of lines found, can run.                                                      |
+------------+------------------------------------------------------------------------------------------+
| 179-180    | Now we must run the tasks created so far, so that the subsequent tasks, which depend     |
|            | the number of lines found, can run.   Write the results to disk.                         |
+------------+------------------------------------------------------------------------------------------+
| 183-184    | Informational, print the number of lines found, equal the the length of the linecube     |
|            | output BDP vector.                                                                       |
+------------+------------------------------------------------------------------------------------------+
| 193-195    | For each spectral line found, there will be a linecube image, accessed by                |
|            | ImageBDP.getimagefile_.                                                                  |
+------------+------------------------------------------------------------------------------------------+
| 197        | Make the tuple needed for the subsequent addTask                                         |
+------------+------------------------------------------------------------------------------------------+
| 198        | Create and add a Moment_ task for the i-th spectral line.                                | 
+------------+------------------------------------------------------------------------------------------+
| 200-202    | Set the parameters for the moment tasks                                                  |
+------------+------------------------------------------------------------------------------------------+
| 203-214    | Make a choice as to how to compute the CubeSpectrum_ for each output of LineCube_. Use   |
|            | the peak the moment map (usePeak=True), the positions listed in maxpos, or the location  |
|            | of the original input FITS cube emission maximum.                                        | 
+------------+------------------------------------------------------------------------------------------+
| 216-221    | If no spectral lines were found, create moments of the whole input cube instead.         |
+------------+------------------------------------------------------------------------------------------+
| 224-229    | Finally, run all the un-run tasks, write the output to disk, and create a summary HTML   |
|            | file index.html in the output admit directory.                                           | 
+------------+------------------------------------------------------------------------------------------+


.. literalinclude:: ../examples/admit-example1.py
   :linenos:
   :language: python

Example 2: Adding optional continuum map input, Smooth_, and OverlapIntegral_
=============================================================================

This script is identical to Example1_ , with the addition of optional
clipping and smoothing of the input FITS file when ingested, finding
sources in a related continuum map using SFind2D_, and creating an OverlapIntegral image
of the first three spectral lines identified.  The notes below highlight the differences
between Example1_ and Example2_.

.. _admit-example2:

admit_example2.py_
~~~~~~~~~~~~~~~~~~

.. tabularcolumns:: |p{1cm}|p{16.5cm}|

+------------+------------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                    |
+============+==========================================================================================+
| 7          | The name of the continuum image can be passed in on the command line                     |
+------------+------------------------------------------------------------------------------------------+
| 40-44      | Options to smooth the cube when ingesting (insmooth), or trim the size of the input cube |
|            | (inbox or inedge).  See Ingest_ documentation for details of these keywords. Note this   |
|            | is an in-place smoothing, the output will be the smoothed cube.                          |
+------------+------------------------------------------------------------------------------------------+
| 45         | Optionally, one can smooth the output of Ingest_, rather than doing it in place.         |
+------------+------------------------------------------------------------------------------------------+
| 129-133    | Smooth and trim options passed to Ingest_.                                               |
+------------+------------------------------------------------------------------------------------------+
| 136-152    | Add a task to smooth the output of Ingest_ with Smooth_ and use the smoothed output from |
|            | here on (bandcube1 = bandcube2).                                                         |
+------------+------------------------------------------------------------------------------------------+
| 157-165    | If a continuum image was give, set up processing of it with Ingest_, CubeStats_, and     |
|            | SFind2D_.                                                                                |
+------------+------------------------------------------------------------------------------------------+
| 273-281    | If more than 3 spectral lines were identified by LineID_, create an OverlapIntegral_     | 
|            | task and add it to the flow.                                                             |
+------------+------------------------------------------------------------------------------------------+
| 284-289    | Run the flow, write the output to disk, and create a summary HTML                        |
|            | file index.html in the output admit directory.                                           | 
+------------+------------------------------------------------------------------------------------------+

.. literalinclude:: ../examples/admit-example2.py
   :linenos:
   :language: python

Example 3: Multiflow
====================

This is an example of a simple multiflow_ that takes the output of several Moment_ tasks
to use as input to PrincipalComponent_ analysis.   The initial setup is similar to Example1_
and Example2_.

.. _admit-example3:

admit_example3.py_
~~~~~~~~~~~~~~~~~~

.. tabularcolumns:: |p{1cm}|p{16.5cm}|

+------------+------------------------------------------------------------------------------------------+
| Line #     | Notes                                                                                    |
+============+==========================================================================================+
| 45         | At least two projects must be provided on the command line (or you can't do PCA!)        |
+------------+------------------------------------------------------------------------------------------+
| 83         | In order to create a multiflow, one uses the ProjectManager_.                            |
+------------+------------------------------------------------------------------------------------------+
| 85-94      | For each input project, find output of Moment_ tasks to use as input to                  |
|            | PrincipalComponent_.                                                                     |
+------------+------------------------------------------------------------------------------------------+
| 89         | findTask_ will locate tasks of a specific type, in this case Moment_AT.                  |
+------------+------------------------------------------------------------------------------------------+
| 92         | Add each Moment_ task that is found to the current project, in case the tasks are stale  |
|            | and need to be re-run.                                                                   | 
+------------+------------------------------------------------------------------------------------------+
| 93         | Keep track of the zeroth moment output BDPs of each Moment_ task                         |
+------------+------------------------------------------------------------------------------------------+
| 100        | Create the PrincipalComponent_ task and add it to the flow.  Its input BDPs are the      |
|            | zeroth moment outputs of the Moment_ tasks.                                              |
+------------+------------------------------------------------------------------------------------------+
| 102-105    | Run the flow, including possible re-run of the Moment_ tasks, write the output to disk,  |
|            | and create a summary HTML file index.html in the output admit directory.                 |
+------------+------------------------------------------------------------------------------------------+

.. literalinclude:: ../examples/admit-example3.py
   :linenos:
   :language: python

.. _Example1:        admit-example1_
.. _Example2:        admit-example2_
.. _Example3:        admit-example3_
.. _flow:            module/admit/FlowManager.html
.. _multiflow:       module/multiflows.html
.. _ProjectManager:  module/admit/ProjectManager.html
.. _findTask:        module/admit/ProjectManager.html#admit.ProjectManager.ProjectManager.findTask
.. _Ingest:          module/admit.at/Ingest_AT.html
.. _CubeSum:         module/admit.at/CubeSum_AT.html
.. _CubeSum:         module/admit.at/CubeSum_AT.html
.. _CubeStats:       module/admit.at/CubeStats_AT.html
.. _CubeSpectrum:    module/admit.at/CubeSpectrum_AT.html
.. _PVSlice:         module/admit.at/PVSlice_AT.html
.. _PVCorr:          module/admit.at/PVCorr_AT.html
.. _LineID:          module/admit.at/LineID_AT.html
.. _LineCube:        module/admit.at/LineCube_AT.html
.. _Moment:          module/admit.at/Moment_AT.html
.. _Smooth:          module/admit.at/Smooth_AT.html
.. _SFind2D:         module/admit.at/SFind2D_AT.html
.. _OverlapIntegral: module/admit.at/OverlapIntegral_AT.html
.. _PrincipalComponent: module/admit.at/PrincipalComponent_AT.html
.. _robust statistics: https://en.wikipedia.org/wiki/Robust_statistics
.. _ImageBDP.getimagefile: module/admit.bdp/Image_BDP.html#admit.bdp.Image_BDP.Image_BDP.getimagefile
.. _admit_example1.py: admit-example1.py
.. _admit_example2.py: admit-example2.py
.. _admit_example3.py: admit-example3.py
