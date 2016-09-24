#!/usr/bin/env casarun
#
import admit

for d in range(5):
  pdir = 'pca-test%d' % (1+d)
  p = admit.Project(pdir + '.admit', commit=False)
  img = []
  tid = []
  src = []
  for i in range(5):
    img.append(admit.Ingest_AT(file='%s/mol%d.fits' % (pdir, i+1)))
    tid.append(p.addtask(img[i]))
    src.append(tid[i])

  pca = admit.PrincipalComponent_AT(alias='pca', clipvals=[0.,0.,0.,0.,0.])
  pid = p.addtask(pca, src)

  p.run()
