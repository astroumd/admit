#
#  this is a piece of code MAC users will need to place in ~/.casa/init.py
#
#  MAC users: if you want clicking the CASA desktop icon to work, your .bash_profile
#             file needs to source the correct admit_start.sh file (recommended),
#             or hack the admit_path variable below (not recommended)
#
#  Some discussion on this issue in
#        https://open-jira.nrao.edu/browse/CAS-5295
#        https://open-jira.nrao.edu/browse/CAS-7372
#
#  CAVEAT: this code has no check if the code is appropriate for your CASA version.
#
import os
import sys
from os.path import join

try:
    admit_path = os.environ['ADMIT']
    sys.path.append(admit_path)
    os.environ["PATH"] += os.pathsep + join(admit_path,'bin')
    os.environ["PATH"] += os.pathsep + '/usr/local/bin/'
except KeyError:
    print("ADMIT path not defined. If you wish to use ADMIT, source the admit_start.[c]sh file.")
    print("and place this in your .bash_profile (mac) or .bashrc (linux) file")
