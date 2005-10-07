SOURCES = itools.tex itools.sty intro.tex uri.tex types.tex resources.tex \
	files.tex files2.tex folders.tex xml.tex stl.tex i18n.tex web.tex \
	style.tex arch.tex

FIGURES = packages.eps state.eps handlers.eps l10n.eps web_tree.eps stl.eps


%.eps: %.dot
	dot -Tps $< -o $@


%.eps: %.dia
	dia --export=$@ $<


%.eps: %.fig
	fig2dev -L eps $< $@

dvi: $(FIGURES) $(SOURCES)
	latex itools.tex
	makeindex itools.idx
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
	rm -f itools.idx itools.ilg itools.ind
	rm -f itools.dvi itools.ps itools.pdf
	rm -f missfont.log 
	rm -f *~
	rm -f $(FIGURES)
	rm -f dvi ps pdf html
	rm -rf itools
