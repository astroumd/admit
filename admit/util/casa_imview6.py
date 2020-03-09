import os

# called by util/casautil.py:
#     CASA5:  from imview import imview as casa_imview
#     CASA6:  from .casa_imview6 import casa_imview6 as casa_imview

def casa_imview6(**kwargs):
    """
    placeholder for casa6 until we know how that works.....
    """

    print("CASA_IMVIEW6: ")
    if 'raster' in kwargs:
        imagename = kwargs['raster']['file']
        if 'out' in kwargs:
            out = kwargs['out']
            print("PJT",imagename,out)
            shortname = imagename[imagename.rfind('/'):]
            showimage(imagename,'casa6 imview hack %s' % shortname,savefig=out)
            return

# --------------------------------------------------------------------------------------------        
# taken from tips on  https://github.com/radio-astro-tools/casa-notebook-tools

from casatools import image as iatool
from astropy.visualization import simple_norm
import pylab as pl

ia = iatool()


def showimage(imagename, title=None, stretch='asinh', mask=None, savefig=None, **kwargs):
    if isinstance(imagename, str):
        ia.open(imagename)
        data = ia.getchunk().squeeze()
        ia.close()
    else:
        data = imagename

    if 'percentiles' in kwargs:
        min_percent, max_percent = kwargs.pop('percentiles')
        kwargs['min_percent'] = min_percent
        kwargs['max_percent'] = max_percent

    if mask is not None:
        data = data.squeeze().T * mask.T,
    else:
        data = data.squeeze().T

    im = pl.imshow(data, norm=simple_norm(data, stretch=stretch, **kwargs),
                   origin='lower', interpolation='none',)

    if title is not None:
        pl.title(title)
    pl.gca().set_xticklabels([])
    pl.gca().set_yticklabels([])
    pl.colorbar()
    if savefig != None:
        pl.savefig(savefig)

    return im
