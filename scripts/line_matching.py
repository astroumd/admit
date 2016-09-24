#! /usr/bin/env python
#
#  line_match toy program
#  - read in a line list  (restfreq,name)
#  - read in a spectrum   (freq,amp)
#  - specify a restfreq
#  - use VLSR (or Z) to shift spectrum
#  - use something to cut down the lines vertically
#
#  Example run:
#    line_matching.py test3.csp.tab test3.tier?.tab
#  where any of the test3.???.tab can be tested

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons, CheckButtons
try:
    from matplotlib.widgets import AxesWidget
    has_aw = True
except:
    has_aw = False

import sys



if has_aw:
    class VertSlider(AxesWidget):
        """
        A slider representing a floating point range

        The following attributes are defined
          *ax*        : the slider :class:`matplotlib.axes.Axes` instance

          *val*       : the current slider value

          *vline*     : a :class:`matplotlib.lines.Line2D` instance
                         representing the initial value of the slider

          *poly*      : A :class:`matplotlib.patches.Polygon` instance
                         which is the slider knob

          *valfmt*    : the format string for formatting the slider text

          *label*     : a :class:`matplotlib.text.Text` instance
                         for the slider label
          *closedmin* : whether the slider is closed on the minimum

          *closedmax* : whether the slider is closed on the maximum

          *slidermin* : another slider - if not *None*, this slider must be
                         greater than *slidermin*

          *slidermax* : another slider - if not *None*, this slider must be
                         less than *slidermax*

          *dragging*  : allow for mouse dragging on slider

        Call :meth:`on_changed` to connect to the slider event
        """
        def __init__(self, ax, label, valmin, valmax, valinit=0.5, valfmt='%1.2f',
                     closedmin=True, closedmax=True, slidermin=None,
                     slidermax=None, dragging=True, **kwargs):
            """
            Create a slider from *valmin* to *valmax* in axes *ax*

            *valinit*
                The slider initial position

            *label*
                The slider label

            *valfmt*
                Used to format the slider value

            *closedmin* and *closedmax*
                Indicate whether the slider interval is closed

            *slidermin* and *slidermax*
                Used to constrain the value of this slider to the values
                of other sliders.

            additional kwargs are passed on to ``self.poly`` which is the
            :class:`matplotlib.patches.Rectangle` which draws the slider
            knob.  See the :class:`matplotlib.patches.Rectangle` documentation
            valid property names (e.g., *facecolor*, *edgecolor*, *alpha*, ...)
            """
            AxesWidget.__init__(self, ax)

            self.valmin = valmin
            self.valmax = valmax
            self.val = valinit
            self.valinit = valinit
            self.poly = ax.axhspan(valmin, valinit, 0, 1, **kwargs)

            self.vline = ax.axhline(valinit, 0, 1, color='r', lw=1)

            self.valfmt = valfmt
            ax.set_xticks([])
            ax.set_ylim((valmin, valmax))
            ax.set_yticks([])
            ax.set_navigate(False)

            self.connect_event('button_press_event', self._update)
            self.connect_event('button_release_event', self._update)
            if dragging:
                self.connect_event('motion_notify_event', self._update)
            self.label = ax.text(0.5, 1.03, label, transform=ax.transAxes,
                                 verticalalignment='center',
                                 horizontalalignment='center')

            self.valtext = ax.text(0.5, -0.03, valfmt % valinit,
                                   transform=ax.transAxes,
                                   verticalalignment='center',
                                   horizontalalignment='center')

            self.cnt = 0
            self.observers = {}

            self.closedmin = closedmin
            self.closedmax = closedmax
            self.slidermin = slidermin
            self.slidermax = slidermax
            self.drag_active = False

        def _update(self, event):
            """update the slider position"""
            if self.ignore(event):
                return

            if event.button != 1:
                return

            if event.name == 'button_press_event' and event.inaxes == self.ax:
                self.drag_active = True
                event.canvas.grab_mouse(self.ax)

            if not self.drag_active:
                return

            elif ((event.name == 'button_release_event') or
                  (event.name == 'button_press_event' and
                   event.inaxes != self.ax)):
                self.drag_active = False
                event.canvas.release_mouse(self.ax)
                return

            val = event.ydata
            if val <= self.valmin:
                if not self.closedmin:
                    return
                val = self.valmin
            elif val >= self.valmax:
                if not self.closedmax:
                    return
                val = self.valmax

            if self.slidermin is not None and val <= self.slidermin.val:
                if not self.closedmin:
                    return
                val = self.slidermin.val

            if self.slidermax is not None and val >= self.slidermax.val:
                if not self.closedmax:
                    return
                val = self.slidermax.val

            self.set_val(val)

        def set_val(self, val):
            xy = self.poly.xy
            xy[1] = 0, val
            xy[2] = 1, val
            self.poly.xy = xy
            self.valtext.set_text(self.valfmt % val)
            if self.drawon:
                self.ax.figure.canvas.draw()
            self.val = val
            if not self.eventson:
                return
            for cid, func in self.observers.iteritems():
                func(val)

        def on_changed(self, func):
            """
            When the slider value is changed, call *func* with the new
            slider position

            A connection id is returned which can be used to disconnect
            """
            cid = self.cnt
            self.observers[cid] = func
            self.cnt += 1
            return cid

        def disconnect(self, cid):
            """remove the observer with connection id *cid*"""
            try:
                del self.observers[cid]
            except KeyError:
                pass

        def reset(self):
            """reset the slider to the initial value if needed"""
            if (self.val != self.valinit):
                self.set_val(self.valinit)




# this subclass is an attempt to link the two horizontal sliders together through a new set_val method
# the original set_val method seems to trap the code in an endless loop...
class mySlider(Slider):
    def __init__(self, *args, **kwargs):
        super(mySlider, self).__init__(*args, **kwargs)

    if False:
        def set_val(self, val):
            discrete_val = val
            # We can't just call Slider.set_val(self, discrete_val), because this 
            # will prevent the slider from updating properly (it will get stuck at
            # the first step and not "slide"). Instead, we'll keep track of the
            # the continuous value as self.val and pass in the discrete value to
            # everything else.
            xy = self.poly.xy
            xy[2] = discrete_val, 1
            xy[3] = discrete_val, 0
            self.poly.xy = xy
            self.valtext.set_text(self.valfmt % discrete_val)
            if self.drawon: 
                self.ax.figure.canvas.draw()
            self.val = val
            if not self.eventson: 
                return
            for cid, func in self.observers.iteritems():
                func(discrete_val)

    if False:
        def set_val(self, value):
            """Set value of slider."""
            # Override matplotlib.widgets.Slider.set_val
            self.value = value

            if self.drawon:
                self.ax.figure.canvas.draw()
            if not self.eventson:
                return

            for cid, func in self.observers.iteritems():
                func(value)

"""---------------------------------------------------------------------------------------------"""



def gauss(freq,freq0,sig0,amp0):
        """ return a gauss"""
        x = (freq-freq0)/sig0
        y = amp0*np.exp(-0.5*x*x)
        return y

def toy1():
    """ return a spectrum to play with """
    x = np.arange(110.0,116.0,0.01)
    y = np.random.normal(0.0,0.4,len(x))
    y = y + gauss(x,111,0.1,1.0)
    y = y + gauss(x,112,0.2,2.0)
    y = y + gauss(x,113,0.3,3.0)
    y = y + gauss(x,114,0.1,2.0)
    y = y + gauss(x,115,0.05,6.0)
    y = y + gauss(x,111.8,0.1,4.0)
    return (x,y)


def toy2(choice):
    """ return three fake line lists to play with"""
    lines1 = {"lee":115.27, "doug":115.0, "marc":112.0}
    lines2 = {"leslie":111.00, "mark":110.0, "peter":113.0}
    lines3 = {"lisa":114.0,   "robert":112.1,  "kevin":112.2}
    if choice == 1:
        return lines1
    elif choice == 2:
        return lines2
    else:
        return lines3


def makespectfile(afile):
    """ reads in a file and returns np.arrays containing values for frequency and amplitude """
    if True:
        x = []
        y = []
        with open(afile) as f:
            for line in f:
                if line.startswith('#'): continue
                (freq,flux) = line.split()
                x.append(float(freq))
                y.append(float(flux))
        return (np.asarray(x),np.asarray(y))
    

def makelinedict(afile):
    """ read in lines from a file to create a line dictionary """
    tier = {}
    with open(afile) as f:
        for line in f:
            if line.startswith('#'): continue
            (key,val) = line.split()
            tier[val] = key
    print "Found %d lines in %s" % (len(tier),afile)
    return tier


def plotsetlines(tier,lines,toggle,lmin,lmax):
    """ plot vertical, labeled lines """
    #if len(lines) == 0: return
    x = []
    a = []
    maxl = lmax
    if tier == 1:
        minl = lmin
        lw = 2
        
    elif tier == 2:
        minl = lmin * 1.05
        lw = 1.5
        
    else:
        minl = lmin* 1.1
        lw = 1
        
    for name in lines:
        x.append(lines[name])
        a.append(plt.annotate(s=name, xy=(lines[name], maxl), xytext=(lines[name], maxl+lmax*0.2), rotation=90,size='large', visible=toggle))
    return plt.vlines(x, minl, maxl, lw=lw,visible=toggle), a




def plotspec(delt=0.0):
    """ draw the spectrum and the shadow """
    t = freq*(1+delt)
    s = amp
    k, = plt.plot(t,s, lw=0.5, color='#501919')
    l, = plt.plot(t,s, lw=2, color='red',visible=True)
    
    plt.axis([frmin, frmax, amin, amax])
    
    return l,k

def updateh(val):
    global old_v, old_z
    v = svlsr.val/c
    z = sreds.val
    
    if v != old_v:
        delt = v
        sreds.reset()

    if z!=0.0:
        if z != old_z:
            delt = z
            svlsr.reset() #if you start using the other horizontal slider, the one you were using before should reset (alternative to linked sliders)
           

    old_v  = v
    old_z  = z
    print "delt={0}".format(delt)
    fac = 1.0 + delt
    l.set_xdata(freq*fac)
    fig.canvas.draw_idle()

def updatevlsr(val):
    pass

def updatev(val):
    global old_astart
    ldat = l.get_ydata()
    amp = samp.val
    add = amp - old_astart
    l.set_ydata(ldat+add)
    old_astart = amp
    fig.canvas.draw_idle()

def reset(event):
    svlsr.reset()
    sreds.reset()
    if has_aw:
        samp.reset()

def toggletiers(label):
    if label == 'tier 1':
        lns1.set_visible(not lns1.get_visible())
        for i in range(len(ann1)):
            ann1[i].set_visible(not ann1[i].get_visible())
    elif label == 'tier 2':
        lns2.set_visible(not lns2.get_visible())
        for i in range(len(ann2)):
            ann2[i].set_visible(not ann2[i].get_visible())
    elif label == 'tier 3':
        lns3.set_visible(not lns3.get_visible())
        for i in range(len(ann3)):
            ann3[i].set_visible(not ann3[i].get_visible())
    elif label == 'shadow':
        k.set_visible(not k.get_visible())
    fig.canvas.draw_idle()


if __name__ == "__main__":
    if len(sys.argv) == 1 or len(sys.argv) > 6:
        print "Usage: {0} spectrum [tier1 [tier2 [tier3 [restfreq]]]]".format(sys.argv[0])
        sys.exit(0)



    if len(sys.argv) > 1:
        spectrum_file = sys.argv[1]

    freq,amp = makespectfile(spectrum_file)
    
    


    frav  = (freq.min()+freq.max())/2
    frmin = freq.min() - 0.001*frav
    frmax = freq.max() + 0.001*frav

    aav  = (amp.min()+amp.max())/2
    amin = amp.min()  - 0.05*aav
    amax = amp.max()  + 1.8*aav

    fig, ax = plt.subplots()
    plt.subplots_adjust(left=0.25, bottom=0.25) #make room for buttons and such

    
    

    if len(sys.argv) > 2:
        tier1_file    = sys.argv[2]
        tier1 = makelinedict(tier1_file)
        lns1,ann1 = plotsetlines(1,tier1,True,amp.max()+0.1*aav,amp.max()+0.8*aav)
    if len(sys.argv) > 3:
        tier2_file    = sys.argv[3]
        tier2 = makelinedict(tier2_file)
        lns2,ann2 = plotsetlines(2,tier2,False,amp.max()+0.1*aav,amp.max()+0.8*aav)
    if len(sys.argv) > 4:
        tier3_file    = sys.argv[4]
        tier3 = makelinedict(tier3_file)
        lns3,ann3 = plotsetlines(3,tier3,False,amp.max()+0.1*aav,amp.max()+0.8*aav)

    d0 = 0.0                # 236.0 for N253
    if len(sys.argv) == 6:
        d0 = float(sys.argv[5])
    c = 299792.458          # speed of light
    z0 = d0/c               

    l,k = plotspec(z0)

    axcolor = 'lightgoldenrodyellow'

    if has_aw:
        tamp = 0
        count = 0
        for x in amp:
            tamp += x
            count += 1
        astart = tamp/count
        print astart

        axamp  = plt.axes([0.2, 0.25, 0.03, 0.65], axisbg=axcolor)
        samp   = VertSlider(axamp,'amp',amin,amax,valinit=astart)

        
        old_astart = astart

        samp.on_changed(updatev)

    

    vmin = -300.0
    vmax = 3000.0

    zmin = -0.01
    zmax = 2

    axfreq = plt.axes([0.25, 0.1, 0.65, 0.03], axisbg=axcolor)
    axz    = plt.axes([0.25, 0.15, 0.65, 0.03], axisbg=axcolor)

    svlsr   = Slider(axfreq, 'VLSR', vmin, vmax, valinit=d0, valfmt=u'%1.1f')
    sreds   = Slider(axz, 'z', zmin, zmax, valinit=z0, valfmt=u'%1.4f')

    old_v = d0
    old_z = z0

    svlsr.on_changed(updateh)
    
    sreds.on_changed(updateh)

    resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
    button = Button(resetax, 'Reset', color=axcolor, hovercolor='0.975')
    button.on_clicked(reset)


    cax = plt.axes([0.025, 0.5, 0.15, 0.15], axisbg=axcolor)
    if has_aw:
        check = CheckButtons(cax, ('tier 1', 'tier 2', 'tier 3', 'shadow'), (True, False, False,True))
    else:
        check = CheckButtons(cax, ('tier 1', 'tier 2', 'tier 3'), (True, False, False))
    check.on_clicked(toggletiers)

    plt.show()


