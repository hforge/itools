#!../../../../python
from itools.pdf import rml2topdf
import sys

if __name__ == "__main__" :
    argv = sys.argv

    output = "/tmp/rml2.pdf"
    if len(argv) == 3:
        output = argv[2]
    if len(argv) >= 2 :
        filename = sys.argv[1]
        data = rml2topdf(filename)
        len(data)
        o = open(output, 'w')
        o.write(data)
        o.close()
    else :
        print "not enough arguments"
