#! /usr/bin/env python
#
# Testing Flow Manager
#

import sys, os
from  optparse import OptionParser

import admit
import admit.at.File_AT   as A
import admit.bdp.File_BDP as B

#=======================================
def addNode(fm, id, nOut = 0, stuples = [], dtuples = []):
    """Creates and registers new File_AT/File_BDP node.

       Creates a new task with the requested number of output BDPs
       and adds the task to the existing flow.

       fm:
       Flow manager instance.

       id:
       New task ID.

       nOut:
       Number of BDP outputs.

       Returns:
       New task ID.
    """
    a = A.File_AT()
    a._taskid = id
    for i in range(nOut): a.addoutputbdp(B.File_BDP())
    fm.add(a, stuples, dtuples)
    return id


def flow4(fm):
    """ test flow4 """

    ## flow4 (left to right)
    #
    #      /--a1--\
    #    a0        a3
    #      \--a2--/
    #
    # fm.connmap = [(0, 0, 1, 0), (0, 0, 2, 0), (1, 0, 3, 0), (2, 0, 3, 1)]

    i0 = addNode(fm, 0, 1)
    i1 = addNode(fm, 1, 1, [(i0, 0)])
    i2 = addNode(fm, 2, 1, [(i0, 0)])
    i3 = addNode(fm, 3, 0, [(i1, 0), (i2, 0)])


def flow6(fm):
    """ test flow6 """

    # flow6
    #        a1                a1
    #       /|\               /|\
    #      / | \             / | \
    #     a2 |  |           a2 |  |
    #     /\ |  |    ==>    /\ |  |    (substitute a5 for a4)
    #    a3 a4  |          a3 a5  |
    #        \ /               \ /
    #         a6                a6

    # Intial flow.
    i1 = addNode(fm, 1, 1)
    i2 = addNode(fm, 2, 2, [(i1, 0)])
    i3 = addNode(fm, 3, 0, [(i2, 0)])
    i4 = addNode(fm, 4, 1, [(i2, 1), (i1, 0)])
    i6 = addNode(fm, 6, 0, [(i4, 0), (i1, 0)])

    # Now replace a4 with a5 by inserting a5, then removing a4.
    a5 = A.File_AT()
    a5._taskid = 5
    a5.enabled(False)  # Exercise flag.
    a5.addoutputbdp(B.File_BDP())
    fm.replace(i4, a5)

    # Here we clone the flow starting from a2 (not shown in diagram).
    i2c = fm.clone(i2)


def flowN(fm, n):
    # A flow with N tasks (except flow4/flow6)
    # a0->a1-> ... ->an

    # leaf is the task ID of current leaf node.
    leaf = addNode(fm, 0, 1)
    for i in range(1, n+1): leaf = addNode(fm, i, 1, [(leaf, 0)])


# ==================================================

if __name__ == "__main__":

    parser = OptionParser(usage=__doc__)

    # Pick a test flow.
    parser.add_option('-f', "--flow", help="type of flow (1 to n)", default=None)

    # Test flow with dryrun?
    parser.add_option('-D', "--dryrun", action="store_true", help="dry run a flow", default=False)

    (opts, args) = parser.parse_args()

    # Options check.
    if not opts.flow:
        print "Please use '-f <number>' option to pick a flow."
        print "For options help: 'python test_FM.py -h'"
        print "Usage example: 'python test_FM.py -f 4'"
        exit(1)

    # Flow option.
    n  = int(opts.flow)
    fm = admit.Flow()

    # Flow select.
    if   n == 4: flow4(fm)
    elif n == 6: flow6(fm)
    else:        flowN(fm, n)

    if opts.dryrun: fm.dryrun()

    # Display and verify FM state.
    fm.show()
    fm.verify()
