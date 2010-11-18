PY = $(shell find ./ -name "*.py")
EN = $(shell find ./ -name "*.xhtml.en")

ES = $(subst .en,.es,$(EN))
FR = $(subst .en,.fr,$(EN))
MO = locale/en.mo locale/es.mo locale/fr.mo

IEXTRACT = igettext-extract.py
IBUILD = igettext-build.py


%.es: %.en
	$(IBUILD) $< locale/es.po > $@

%.fr: %.en
	$(IBUILD) $< locale/fr.po > $@

%.mo: %.po
	msgfmt $< -o $@


extract: $(PY) $(EN)
	$(IEXTRACT) $(PY) $(EN) > locale/locale.pot
	msgmerge -U -s locale/en.po locale/locale.pot
	msgmerge -U -s locale/es.po locale/locale.pot
	msgmerge -U -s locale/fr.po locale/locale.pot


build: $(ES) $(FR) $(MO)


clean:
	-rm -f $(ES) $(FR) $(MO) locale/*~
