#! /usr/bin/env casarun
#
# Simple ADMIT script processing a FITS cube into sub-cubes and moment maps
# for individual spectral lines.
#
# Usage: admit-example0.py input.fits
#
# =============================================================================

# Used Python and ADMIT functionality.
import os
import admit

# Retrieve FITS file name, respecting CASA options.
ifile = admit.utils.casa_argv(sys.argv)[1]

# Create (or re-open) the ADMIT project.
# Our project directory is the input path with extension set to admit.
proj = admit.Project(os.path.splitext(ifile)[0] + '.admit', commit=False)

# Ingest the FITS cube.
proj.addtask(admit.Ingest_AT(file=ifile, alias='cube'))

# Cube manipulation template.
tmpl = proj.addtask(admit.Template_AT(imgslice=550,specpos=(183,151)), ['cube'])

# Calculate some statistics on the FITS cube (including peak point plot).
cstats = proj.addtask(admit.CubeStats_AT(ppp=True), ['cube'])

# Calculate the moment-0 (integrated intensity) map for the entire cube.
csum = proj.addtask(admit.CubeSum_AT(numsigma=4., sigma=99.), ['cube', cstats])

# Calculate the source spectrum at (by default) the peak position in the cube.
cspect = proj.addtask(admit.CubeSpectrum_AT(), ['cube', csum])

# Identify lines in the cube.
lines = proj.addtask(admit.LineID_AT(numsigma=4.0,minchan=3), [cspect, cstats])

# Cut input cube into line-specific sub-cubes (padding lines by 10 channels).
lcubes = proj.addtask(admit.LineCube_AT(pad=10), ['cube', lines])

# Finally, compute moment-0,1,2 maps and peak position spectrum for each line.
# Since lcubes is variadic, the following tasks will be replicated as needed.
mom = proj.addtask(admit.Moment_AT(moments=[0,1,2], mom0clip=2.0),
                   [lcubes, cstats])
csp = proj.addtask(admit.CubeSpectrum_AT(alias='lcs'), [lcubes, mom])

# Run project and save to disk. (Open project index.html to view summary.)
proj.run()
