
EN = $(shell find cms/ui -name "*.x*ml.en" | grep -v web_site_templates | grep -v "Root_license.xml")

ES = $(subst .en,.es,$(EN))

EU = $(subst .en,.eu,$(EN))

FR = $(subst .en,.fr,$(EN))

ZH = $(subst .en,.zh,$(EN))

IT = $(subst .en,.it,$(EN))

MO = locale/en.mo locale/es.mo locale/fr.mo locale/zh.mo locale/it.mo



# Binary
%.es: %.en
	igettext-build --output=$@ $< locale/es.po

%.eu: %.en
	igettext-build --output=$@ $< locale/eu.po

%.fr: %.en
	igettext-build --output=$@ $< locale/fr.po

%.zh: %.en
	igettext-build --output=$@ $< locale/zh.po

%.it: %.en
	igettext-build --output=$@ $< locale/it.po

%.mo: %.po
	msgfmt $< -o $@

bin: $(ES) $(FR) $(ZH) $(IT) $(MO)
	touch bin


clean:
	rm -f pot po bin
	rm -f $(ES) $(EU) $(FR) $(ZH) $(IT) $(MO)
	find ./ -name "*.pyc" -exec rm -f {} \;
	find ./ -name "*~" -exec rm -f {} \;
##	find ./ -type d -name dot -exec rm -fr {} \;
##	find ./ -name ".#*" -exec rm -f {} \;
##	find ./ -name ".log" -exec rm -f {} \;
