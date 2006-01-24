#
# TransFig makefile
#

all: 

clean:
	find ./ -name "*.pyc" -exec rm -f {} \;
	find ./ -name "out.ps" -exec rm -f {} \;
	find ./ -name "out.dot" -exec rm -f {} \;
	find ./ -name "out.png" -exec rm -f {} \;
	
