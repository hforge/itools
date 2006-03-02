
IGETTEXT=$(shell if [ -f igettext.txt ]; then cat igettext.txt; else echo igettext.py; fi)



PY = $(shell find ./ -name "*.py" | grep -v "^./ikaaro/utils.py" | grep -v "^./build" | grep -v "^./dist")

EN = $(shell find cms/ui -name "*.x*ml.en" | grep -v web_site_templates | grep -v "Root_license.xml")

ES = $(subst .en,.es,$(EN))

EU = $(subst .en,.eu,$(EN))

FR = $(subst .en,.fr,$(EN))

ZH = $(subst .en,.zh,$(EN))

IT = $(subst .en,.it,$(EN))

MO = locale/en.mo locale/es.mo locale/fr.mo locale/zh.mo locale/it.mo



# Binary
%.es: %.en
	$(IGETTEXT) --output=$@ --xhtml $< locale/es.po

%.eu: %.en
	$(IGETTEXT) --output=$@ --xhtml $< locale/eu.po

%.fr: %.en
	$(IGETTEXT) --output=$@ --xhtml $< locale/fr.po

%.zh: %.en
	$(IGETTEXT) --output=$@ --xhtml $< locale/zh.po

%.it: %.en
	$(IGETTEXT) --output=$@ --xhtml $< locale/it.po

%.mo: %.po
	msgfmt $< -o $@

bin: $(ES) $(FR) $(ZH) $(IT) $(MO)
	touch bin


# POT/PO
pot: $(PY) $(EN)
	$(IGETTEXT) --output=locale/locale.pot --pot $(PY) $(EN) 
	touch pot


po: pot
	$(IGETTEXT) --output=locale/es.po --po locale/locale.pot locale/es.po
	$(IGETTEXT) --output=locale/fr.po --po locale/locale.pot locale/fr.po
	$(IGETTEXT) --output=locale/zh.po --po locale/locale.pot locale/zh.po
	$(IGETTEXT) --output=locale/it.po --po locale/locale.pot locale/it.po
	touch po


clean:
	rm -f pot po bin
	rm -f $(ES) $(EU) $(FR) $(ZH) $(IT) $(MO)
	find ./ -name "*.pyc" -exec rm -f {} \;
	find ./ -name "*~" -exec rm -f {} \;
##	find ./ -type d -name dot -exec rm -fr {} \;
##	find ./ -name ".#*" -exec rm -f {} \;
##	find ./ -name ".log" -exec rm -f {} \;
