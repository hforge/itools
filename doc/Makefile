SOURCES = itools.tex itools.sty intro.tex uri.tex resources.tex \
	handlers.tex xml.tex stl.tex chandlers.tex i18n.tex addendum.tex \
	arch.tex

FIGURES = handlers.eps l10n.eps


%.eps: %.dot
	dot -Tps $< -o $@


%.eps: %.dia
	dia --export=$@ $<


dvi: $(FIGURES) $(SOURCES)
	latex itools.tex
	latex itools.tex
	touch dvi

ps: dvi
	dvips itools.dvi -o itools.ps
	touch ps

pdf: ps
	ps2pdf itools.ps
	touch pdf

html: $(SOURCES)
	latex2html itools.tex
	touch html


clean:
	rm -f itools.toc itools.lot itools.log itools.aux
	rm -f itools.dvi itools.ps itools.pdf
	rm -f missfont.log 
	rm -f *~
	rm -f dvi ps pdf html
	rm -rf itools
