doc:
	pydoc -w .


clean:
	find ./ -name "*~" -exec rm {} \;
	find ./ -name "*.pyc" -exec rm {} \;
	rm -rf dist
	rm -rf build
	rm -f MANIFEST


test:
	python test.py


binary: doc
	python setup.py sdist
