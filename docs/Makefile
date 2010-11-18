SRC_NAMES=$(wildcard figures-src/*)
SRC_BASE_NAMES=$(basename $(SRC_NAMES))
TARGET_BASE_NAMES=$(patsubst  figures-src/%, figures/%, $(SRC_BASE_NAMES))

PDF_NAMES=$(addsuffix .pdf, $(TARGET_BASE_NAMES))
PNG_NAMES=$(addsuffix .png, $(TARGET_BASE_NAMES))

.PHONY: pdf png clean

pdf: figures $(PDF_NAMES)

png: figures $(PNG_NAMES)

clean:
	rm -rf figures

figures:
	mkdir -p figures

# To PDF rules

figures/%.eps: figures-src/%.png
	convert $< -compress jpeg eps2:$@

figures/%.eps: figures-src/%.jpg
	convert -units PixelsPerInch -density 72 $< eps2:$@

figures/%.eps: figures-src/%.svg
	inkscape -z $< -E $@

figures/%.eps: figures-src/%.fig
	fig2dev -L eps $< $@

figures/%.eps: figures-src/%.dot
	dot -Tps $< -o $@

%.pdf: %.eps
	epstopdf $<

# To PNG rules

figures/%.png: figures-src/%.png
	cp $< $@

figures/%.png: figures-src/%.jpg
	convert  $< $@

figures/%.png: figures-src/%.svg
	inkscape -z $< -e $@

figures/%.png: figures-src/%.dot
	dot -Tpng $< -o $@
