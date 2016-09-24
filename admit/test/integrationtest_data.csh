#! /bin/csh -f 
#
# at UMD:   /n/chara/admit/testdata

echo integrationtest_data.csh:


#  usually a symlink to a read-only location
set testdata = $ADMIT/testdata

#  list of files to be tested in $testdata
set data = (test21.fits)


# -- no need to change anything below --

if ($#argv > 0) then
  set data = ($*)
endif
echo Testing $data

if (! -e $testdata) then
  echo 'No $ADMIT/testdata/'
  echo Symlink this to your testdata repo, it can be read-only
  exit 1
endif


if (! -e $ADMIT/data) mkdir $ADMIT/data
cd $ADMIT/data


set nfail = 0

foreach ff ($data)
  if (! -e $ff) then
    if (-e $testdata/$ff) then
       ln -s $testdata/$ff
    else
       echo $ff not in $testdata for a symlink
       @ nfail++
       continue
    endif
  endif

  set adir = ${ff:r}.admit

  $ADMIT/admit/test/admit1.py $ff --basename x
  @ nfail += $status

  $ADMIT/admit/test/admit1.py $adir
  @ nfail += $status

end

# needed for grepping in bin/runIntegrationTests.csh
if ($nfail > 0 ) echo "FAILED $0" >> $ADMIT/INTEGTESTRESULT

exit $nfail
