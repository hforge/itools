PY = $(shell find ./ -name "*.py"|grep -v "^./{arch}")
EN = $(shell find ./ -name "*.x*ml.en")

ES = $(subst .en,.es,$(EN))
MO = locale/en.mo locale/es.mo

# Binary
%.es: %.en
	igettext.py --output=$@ --xhtml $< locale/es.po

%.mo: %.po
	msgfmt $< -o $@

bin: $(ES) $(MO)
	touch bin

# POT/PO
pot: $(PY) $(EN)
	igettext.py --output=locale/locale.pot --pot $(PY) $(EN) 
	touch pot

po: pot
	igettext.py --output=locale/es.po --po locale/locale.pot locale/es.po
	touch po


# Clean
clean:
	rm -f pot po bin
	rm -f $(ES) $(MO)
