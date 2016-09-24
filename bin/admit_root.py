#! /usr/bin/env casarun
#
#   $ADMIT/bin/admit_root.py:
#
#   this provides $ADMIT for scripts where one might not be present.
#
#   note this routine will be noisy, it is usually called by a shell
#   script 'admit_root' which filters out this noise and just returns
#   the ADMIT root tree (a.k.a. $ADMIT in the developer version)
#
#   In a developer version of ADMIT, this script is not needed, since
#   $ADMIT exists.


import admit.util.utils as utils

admit_root = utils.admit_root()

print admit_root
