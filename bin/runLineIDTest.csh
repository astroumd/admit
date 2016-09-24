#!/bin/csh -f
# Script to run lineid test
source admit_start.csh
echo python is "("`which python`")"

admit/test/LineIDBaseline.py data/LineTest

