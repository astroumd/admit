"""
**LinePlot** --- Interactive/non-interactive line plotting utility.
-----------------------------------------------------------------------

This module defines the LinePlot class.
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import PlotControl
import APlot

class LinePlot(object):
  """
  Interactive and non-interactive line plot generator.

  This class takes a LineID BDP as produced by the LineID task and creates 
  standardized line plots for each of the inputs.

  Parameters
  ----------
  pmode : int, optional
    Plotting mode (admit.util.PlotControl plot mode; e.g., PlotControl.BATCH).

  ptype : int, optional
    Plotting format (admit.util.PlotControl plot type; e.g., PlotControl.PNG).
    Ignored for interactive plots.

  figno : int, optional
    Starting figure number.

  abspath : str
    Fully-qualified path where images will be written. An empty string
    implies relative to the current working directory.

  Attributes
  ----------
  _plot : APlot
    ADMIT plotter.
  """
  
  def __init__(self, pmode=PlotControl.INTERACTIVE,
                     ptype=PlotControl.SVG, figno=None, abspath=""):
    self._plot = APlot.APlot(pmode, ptype, figno, abspath)


  def plot(self, llbdp, names=None, showlines=True, numsigma=4.0, 
           vlsr=None, refs={}):
    """
    Generates line plots.

    Generates a complete set of LineID-style line plots for the spectra present
    in a LineList (e.g., as output by LineID), or only a selected set if
    `names` is specified. A summary plot combining all spectra is **not** produced.

    In interactive mode, plots are presented individually to the user and need
    to be dismissed to proceed to the next.

    Parameters
    ----------
    llbdp : LineList_BDP
      Input spectra.

    names : list of str, optional
      Spectrum names to plot; if ``None``, all spectra in the BDP will be
      plotted. Call `llbdp.getSpectraNames()` to see the complete list.

    showlines : bool, optional
      Whether to include line segments and identifications on each plot.
      (Note this includes **all** lines present in the BDP, not just those 
      derived from the plotted spectrum in particular.)
      
    numsigma : float, optional
      Noise multiplier for cut-off.

    vlsr : float, optional
      Object line-of-sight velocity (km/s); labeled 'unknown' if not specified.

    refs : dict, optional
      A dictionary of frequencies and reference line names to be included in
      the plots. Allows plotting specific lines whether or not they are present
      in the spectra.

    Returns
    -------
    None
    """
    # Separate lines by blend or force trait.
    lines = []
    force = []
    blend = []
    if showlines:
      for line in llbdp.getall():
        if line.blend:
          blend.append(line)
        elif line.force:
          force.append(line)
        else:
          lines.append(line)

    if not names: names = llbdp.getSpectraNames()
    for name in names:
      print name, "spectrum..."
      ftype = "Sky" if llbdp.veltype == 'vlsr' else "Rest"
      label = "Peak/Noise"    if name == 'CubeStats_0' else \
              "Minimum/Noise" if name == 'CubeStats_1' else \
              "Correlation"   if name == 'PVCorr' else \
              "Intensity"
      mult  = -1 if name == "CubeStats_1" else 1
      spec  = llbdp.getSpectrum(name)
      vstr  = " (vlsr=%.2f)" % vlsr if vlsr is not None else " (vlsr unknown)"
      self._plot.makespec(
                    x = spec.freq(),
                    y = mult*spec.spec(csub=False),
                    chan = spec.chans(),
                    continuum = mult*spec.contin(),
                    cutoff = spec.contin() + mult*spec.noise()*numsigma,
                    figname = name,
                    title = name+vstr,
                    xlabel = ftype + " Frequency (GHz)",
                    ylabel = label,
                    blends = blend,
                    force = force,
                    lines = lines,
                    references=refs,
                    thumbnail = True)
