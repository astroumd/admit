#! /bin/csh -f 
#
#   run the "M3 buildbot", previously buried in
#   redo_from_scratch_chara, now allowing you
#   to run this assuming ADMIT exists.
#
# at UMD:   /n/chara/admit/testdata
# else:     see $ADMIT/etc/data/test.sum

echo run_M3-bb.csh:


#  usually a symlink to a safe read-only location
set testdata = $ADMIT/testdata

#  list of "test$n.fits" files to be tested from $testdata
set data1 = (0 1 3 13 14 21 22 23 201 202 253_spw0 253_spw1 253_spw2 253_spw3 91 6503)
set data2 = (34 )   # 253_cont

set rerun = 0


# -- no need to change anything below --

if (! -e $testdata) then
  echo 'No $ADMIT/testdata/'
  echo Symlink this to your testdata repo, it can be read-only
  exit 1
endif

# set up
cp $ADMIT/etc/data/test*.apar .
set log = ()


# process line cubes
foreach i ($data1)
  set f = test${i}.fits
  set a = ${f:r}.admit

  echo $f
  
  ln -s $testdata/$f
  $ADMIT/admit/test/admit1.py --basename x $f   >& $f.log
  if ($rerun) $a/admit0.py                     >>& $f.log
  if ($rerun) $a/admit0.py                     >>& $f.log

  set log = ($log $f.log)
end
# regressions
grep MOM0FLUX: $log > fluxes.tab
grep LINEID:   $log > lines.tab

# process continuuum maps
foreach i ($data2)
  set f = test${i}.fits
  set a = ${f:r}.admit

  echo $f
    
  ln -s $testdata/$f
  $ADMIT/admit/test/admit2.py --basename x $f   >& $f.log
  if ($rerun) $a/admit0.py                     >>& $f.log
  if ($rerun) $a/admit0.py                     >>& $f.log

  set log = ($log $f.log)
end

# process special ones
if (1) then
  $ADMIT/admit/test/admit3.py test253_all test253_spw[0,2-3].admit >& test253_all.log
  if ($rerun) test253_all/admit0_all.admit/admit0.py              >>& test253_all.log
  if ($rerun) test253_all/admit0_all.admit/admit0.py              >>& test253_all.log

  set log=($log test253_all.log) 
endif

if (1) then
  $ADMIT/admit/test/admit253.py                                    >& test253_0123.fits.log
  if ($rerun) test253_all/admit0_all.admit/admit0.py              >>& test253_0123.fits.log
  if ($rerun) test253_all/admit0_all.admit/admit0.py              >>& test253_0123.fits.log
  # sanity check if both methods give the same
  grep MOM0FLUX test253_spw?.fits.log | awk -F: '{print $4}' | cut -c4- | sort  > test253-sflow.tab
  grep MOM0FLUX test253_0123.fits.log | awk -F: '{print $3}' | sed s/-@1// | sed s/-@2// | sed s/-@3// | cut -c7- | sort > test253-mflow.tab
  echo test253: comparing sflow and mflow
  diff test253-sflow.tab test253-mflow.tab
  set log=($log test253_all.log) 
endif

if (0) then
  $ADMIT/admit/test/admit5.py  >& testSD_all.log
  set log=($log testSD_all.log) 
endif


grep REGRESSION $log > regres.log
