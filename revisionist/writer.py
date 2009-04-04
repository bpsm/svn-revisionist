
"""
revisionist.write: write Subversion dumpfiles (vers 2 & 3)
(c) 2007 Ben Smith-Mannschott <benpsm@gmail.com> 

License
  GNU Lesser General Public License.
  http://www.gnu.org/licenses/lgpl.html
"""

import sys
from md5 import md5
from util import crop_text_block as msg
from parser import BeginDumpfile, EndDumpfile, \
     BeginRevision, EndRevisionHeader, EndRevisionNodes, \
     BeginNode, EndNode, UserProperties, TextContent, BlankLine


def write_events_to_dumpfile(events, dstFile):
    """
    Consume a series of parse events while writing them dstFile as a
    SVN Dumpfile.

    All events will return exactly the bytes that need to be written
    to the dumpfile when they are asked for their string
    representation.
    """
    version = None
    text_content_md5 = None
    text_content_length = None

    try:
        for evt in events:
            
            # This is all sanity checking, to make sure we don't
            # silently produce an invalid dump file.
            
            if type(evt) == BeginDumpfile:
                # remember the version of the dump file
                version = evt.version
                assert 2 <= version <= 3, msg(
                    """Only dumpfile format versions 2 and 3 are supported.""")

            if version == 2:
                # Version 2 doesn't support Text and Property deltas,
                # so make sure we're not using any of those.
                if type(evt) == UserProperties:
                    assert None not in evt.values(), msg(
                        """Property deleting requires Prop-deltas: true
                           and dump file format version 3 or higher.""")
                if type(evt) in (BeginRevision, BeginNode):
                    assert evt.get("Prop-delta") != "true", msg(
                        """Dump file format must be at least version 3 to
                        support Prop-deltas.""")
                if type(evt) == BeginNode:
                    assert evt.get("Text-delta") != "true", msg(
                        """Text deltas should not occur in this dumpfile.
                           Its format is too old to support them.
                           version = %s""" % (version,))

            if type(evt) == BeginNode:
                # remember checksum and lengths
                if evt.get("Text-delta") == "true":
                    # don't bother to remember the checksum.  we don't
                    # know how to interpret text deltas.
                    text_content_md5 = None
                else:
                    text_content_md5 = evt.get("Text-content-md5")
                text_content_length = int(evt.get("Text-content-length", 0))
                prop_content_length = int(evt.get("Prop-content-length", 0))
                
            elif type(evt) == EndNode:
                # forget checksum and size
                text_content_md5 = None
                text_content_length = None
                prop_content_length = None

            elif type(evt) == BeginRevision:
                prop_content_length = int(evt.get("Prop-content-length", 0))

            elif type(evt) == EndRevisionHeader:
                prop_content_length = None
                
            elif type(evt) == TextContent:
                # validate against text_content_length
                assert text_content_length == len(evt), msg(
                    """Text length mismatched.
                       Text-content-length: %d
                       Actual length:       %d"""
                    % ( text_content_length, len(evt) ))
                # validate the text content against the checksum, if
                # present.
                if text_content_md5:
                    h = md5(evt).hexdigest()
                    assert h == text_content_md5, msg(
                           """MD5 mismatch. The Text-content-md5 claimed by
                              the parent node does not match the computed md5.
                              expected: %s
                              computed: %s"""
                           % (text_content_md5, h))

            elif type(evt) == UserProperties:
                assert prop_content_length == len(str(evt)), msg(
                    """Property length mismatched.
                       Prop-content-length: %d
                       Actual length:       %d"""
                    % (prop_content_length, len(str(evt))))
                    
            # this is the actual write to the file. compact, isn't it?
                    
            dstFile.write(str(evt))
            
    finally:
        dstFile.close()
