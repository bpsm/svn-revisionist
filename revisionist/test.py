#!/usr/bin/env python

"""
Test script for revisionist module.
(c) 2007 Ben Smith-Mannschott <benpsm@gmail.com> 

License
  GNU Lesser General Public License.
  http://www.gnu.org/licenses/lgpl.html
"""

from util import crop_text_block as msg
import parser
import writer
import editors
import os

dumpfiles = ["short.dump2",  "short.dump3"]

def round_trip_test(dumpFilePath):
    inFilePath = dumpFilePath
    outFilePath = dumpFilePath + ".out"
    inFile = file(inFilePath, "rb")
    outFile = file(outFilePath, "wb")
    events = parser.pull(inFile)
    writer.write_events_to_dumpfile(events, outFile)
    inFile.close()
    outFile.close()

    original = file(inFilePath, "rb")
    copy = file(outFilePath, "rb")

    original_bytes = original.read()
    copy_bytes = copy.read()

    original.close()
    copy.close()

    assert original_bytes == copy_bytes

    os.unlink(outFilePath)

def run_tests():
    for filePath in dumpfiles:
        round_trip_test(filePath)
    print "ok"

def main():
    run_tests()

if __name__ == "__main__":
    main()

    

