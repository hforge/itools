doc:
	pydoc -w .


clean:
	rm -f *~ *.pyc
	rm -rf dist
	rm MANIFEST


test:
	python test.py


binary: doc
	python setup.py sdist
