#
AD = AdmitDesign
AP = AdmitProgramming
CT = CodeTesting
IC = Image_class
M1 = milestone1
SPHINXIM = sphinx/images
BDP = $(wildcard BDP/*.tex) $(wildcard AT/*.tex)
EXAMPLES = ../admit/test/milestone1.py $(wildcard examples/*.xml) $(wildcard examples/*.png)

FAA = AdmitArchitecture.png connection.png
FIL = Box.png Gauss.png Hanning.png Raw_Spec.png Savgol.png Triangle.png Welch.png \
      Box2D.png Gauss2D.png Hanning2D.png Raw_Map2D.png Savgol2D.png Triangle2D.png Welch2D.png \
      peakfind.png peakfind2.png pattern.png pattern_cut.png
FM  = flow6-FM.png fm-gui1.png fm-gui2.png fm-gui3.png fm-gui4.png fm-gui5.png \
      fm-gui6.png fm-gui7.png

FLOW = flow1.png flow2.png flow4.png flow5.png flow1bad.png flow2b.png \
       flow6-AT.png flow6-FM.png BDPorder.png

PDF = $(AP).pdf $(CT).pdf $(IC).pdf
PNG = $(FLOW) $(FAA) $(FM) $(FIL) databrowser.png

ALL = $(PNG) $(PDF)

.SUFFIXES: .dot .fig .pdf .png .tex

#.dia.png:
#	dia -t png-libart -e $*.png $*.dia

.dot.png:
	dot -Tpng $*.dot -o $*.png

# Will this work on Mac OS?
.fig.png:
	/usr/bin/fig2dev -L png $*.fig $*.png || /usr/bin/convert  $*.fig $*.png

# Do it twice to get cross-references right.
.tex.pdf:
	pdflatex $*.tex
	pdflatex $*.tex

all:	$(ALL)
	mkdir -p $(SPHINXIM)
	for img in $(PNG); do cp $$img $(SPHINXIM)/$$img; done

$(AD).pdf:  $(AD).tex $(PNG) $(BDP) $(EXAMPLES)
$(M1).pdf:  $(M1).tex $(AD).tex $(EXAMPLES)

ADMIT.pdf: all
	$(MAKE) -C sphinx latex 2>&1 | \
	  grep -vF "WARNING: toctree references unknown document" | \
	  grep -vF "WARNING: toctree contains ref to nonexisting"
	TEXINPUTS=$(TEXINPUTS) $(MAKE) -C sphinx/_build/latex all 2>&1 | \
	  grep -vF Overfull | grep -vF Underfull | grep -vF "[]"
	cp sphinx/_build/latex/ADMIT.pdf .
	@echo A copy of the sphinx manual is in:
	@echo " $(ADMIT)/doc/ADMIT.pdf"

clean:
	rm -rf $(FLOW) $(PDF) $(SPHINXIM) sphinx/_build *.aux *.log CodeTesting.out
