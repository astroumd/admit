#! /bin/csh -f
#
#
#   this will clone all CLI based casa tasks to a shadow tree
#   so sphinx can try and build. It was fun while it worked,
#   but they certainly don't look at clean as they should, and
#   CASA also maintains their own formatted version.
#   As an example how to automate this though, we'll leave the
#   script here.
#
#   
#   A better reference for a casa tasks "ABC" would be
#        https://casa.nrao.edu/docs/TaskRef/ABC-task.html


#   pick the x.py (cli=0) or x_cli.py (cli=1)
set cli = 0


if ($?CASA_ROOT == 0) exit 1
if ($?ADMIT     == 0) exit 2


set shcasa = $ADMIT/admit/shcasa
set docsph = $ADMIT/doc/sphinx/module/admit.shcasa

if (-e $CASA_ROOT/lib/python) then
    cd $CASA_ROOT/lib/python
else
    cd $CASA_ROOT/lib/python2.7
endif
mkdir -p $shcasa

set clis = (echo *_cli.py)

echo There are $#clis _cli.py tasks

set ipy = $shcasa/__init__.py

echo '"""admit.shcasa'  > $ipy
echo '   ------------' >> $ipy
echo ' '               >> $ipy
echo '   This package is a shadow package of CASA, purely to generate documentation from sphinx.'  >> $ipy
echo '"""'             >> $ipy

foreach p ($clis)
   set f = `echo $p | sed s/_cli.py//`
   if ($cli) then
      set fpy = $p
   else
      set fpy = $f.py
   endif
   set url = `printf https://casa.nrao.edu/docs/TaskRef/%s-task.html $f`
   if (-e $fpy) then
      echo '""" '$f              > $shcasa/$fpy
      echo '    ----'           >> $shcasa/$fpy
      echo '    See also ' $url >> $shcasa/$fpy
      echo '"""'                >> $shcasa/$fpy
      cat $fpy                  >> $shcasa/$fpy
      echo ".. automodule:: admit.shcasa.$f" > $docsph/$f.rst
   else
      echo MISSING $fpy
   endif
end

echo Copied to $shcasa for html production
