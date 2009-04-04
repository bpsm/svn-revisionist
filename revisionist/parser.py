
"""
revisionist.parser: a parser for Subversion dumpfiles (vers 2 & 3).
(c) 2007 Ben Smith-Mannschott <benpsm@gmail.com> 

License
  GNU Lesser General Public License.
  http://www.gnu.org/licenses/lgpl.html
"""

import re
import sys
from md5 import md5
from util import crop_text_block as msg
from util import curry, odict

# ------------------------------------------------------------------------
# This module's primary entry point(s)
# ------------------------------------------------------------------------

def pull(fileLike):
    """
    Parse the SVN Dumpfile in the open file fileLike.

    This is a generator. It yields a series of parse events described
    by the following BNF-like notation::

      BeginDumpfile
      BlankLine* 
        (
        BeginRevision
        BlankLine?
        UserProperties?
        BlankLine*
        EndRevisionHeader
          (
          BeginNode
          BlankLine?
          UserProperties?
            (
            TextContent
            BlankLine
            )?
          BlankLine*
          )*
        EndRevisionNodes
        BlankLine*
        )*
      EndDumpFile
    """
    return Parser().parse(fileLike)

# ------------------------------------------------------------------------
# Parse Events
# ------------------------------------------------------------------------

class BeginDumpfile( object ):
    """
    Parse Event. Signalling the start of a Dumpfile.

    version
        Version of the dumpfile. This parse is written for dumpfile
        formats 2 and 3, though the parser doesn't check for this.

    uuid
        The UUID of the repository.  This can be None.
    """
    def __init__(self, version, uuid=None):
        self.version = version
        self.uuid = uuid
    def __str__(self):
        out = ["SVN-fs-dump-format-version: %d\n\n" % (self.version,)]
        if (self.uuid):
            out.append("UUID: %s\n" % (self.uuid,))
        return "".join(out)
    def __repr__(self):
        return "BeginDumpfile(%r, %r)" % (self.version, self.uuid)

        
class EndDumpfile( object ):
    """
    Parse Event. Signals the end of the Dumpfile.  No further events
    will follow.
    """
    def __str__(self):
        return ""
    def __repr__(self):
        return "EndDumpfile()"


class BeginRevision( odict ):
    """
    Parse Event. Signals the start of a Revision.

    This is a dictionary. It's items are the dumpfile properties of
    the the revision, for example Revision-number.

    keys() preserves the order present in the original dump file.
    """
    def __str__(self):
        """
        Returns the contained dumpfile properties exactly as they
        should be written to the dumpfile.
        """
        return "".join(["%s: %s\n" % (k, self[k]) for k in self.keys()])
    def __repr__(self):
        return "BeginRevision(%s)" % odict.__repr__(self)


class EndRevisionHeader(object):
    """
    Parse Event. Signals that the Revision's header has been parsed.
    """
    def __str__(self):
        return ""
    def __repr__(self):
        return "EndRevisionHeader()"


class EndRevisionNodes(object):
    """
    Parse Event. Signals the end of the Revision.  Only EndDumpfile or
    BeginRevision may follow.
    """
    def __str__(self):
        return ""
    def __repr__(self):
        return "EndRevisionNodes()"


class BeginNode( odict ):
    """
    Parse Event. Signals the start of a Node.

    This is a dictionary. It's items are the dumpfile properties of
    the node, for ecample: Node-path.

    keys() preserves the order of declaration.
    """
    def __str__(self):
        """
        Returns the contained dumpfile properties exactly as they
        should be written to the dumpfile.
        """
        return "".join(["%s: %s\n" % (k, self[k]) for k in self.keys()])
    def __repr__(self):
        return "BeginNode(%s)" % odict.__repr__(self)


class EndNode( object ):
    """
    Parse Event. Signals the end of a Node.
    """
    def __str__(self):
        return ""
    def __repr__(self):
        return "EndNode()"


class UserProperties( odict ):
    """
    Parse Event. Signals user properties, i.e. Node or Revision
    properties in the SVN sense.

    This is a dictionary.  It's items are the user parsed user
    properties, e.g. 'svn:externals', 'svn:log', etc.

    keys() preserves declaration order.

    This may occur between BeginNode and EndNode or between
    BeginRevision and EndRevisionHeader.
    """
    def __str__(self):
        out = []
        for k in self.keys():
            v = self[k]
            if v != None:
                out.append("K %d\n%s\nV %d\n%s\n" % (len(k), k, len(v), v))
            else:
                out.append("D %d\n%s\n" % (len(k), k))
        else:
            out.append("PROPS-END\n")
        return "".join(out)
    def __repr__(self):
        return "UserProperties(%s)" % odict.__repr__(self)


class TextContent( str ):
    """
    Parse Event. Signals text content of a node. (Revisions never have
    text content.)

    It behaves like a string.  It not only signals the content, it
    *is* the content.
    """
    def __repr__(self):
        return "TextContent(%s)" % str.__repr__(self)


class BlankLine(object):
    """
    Parse Event. Signals a blank line between two other Events.
    """
    def __init__(self):
        pass
    def __str__(self):
        return '\n'
    def __repr__(self):
        return "BlankLine()"


# ------------------------------------------------------------------------
# The Pull Parser
# ------------------------------------------------------------------------

pat_dump_property = re.compile(r"^([-A-Za-z0-9_]+):[ ](.*)$")
        
class Parser(object):
    """
    A parser for Subversion dump file format versions 2 and 3.

    This is a *pull* parser, meaning it presents itself as a generator
    offering a series of parse events.

    The parse events and the sequence in which you can expect to
    receive them is not described here. See the function parse() of
    this module.

    This parser is intentionally *very* unforgiving.  It will stop
    noisily with an AssertionError if anything about its input doesn't
    meet with its expectations.

    It's better to fail obviously than to silently corrupt your data,
    after all.  (Incidentally, being so explicit about my assumptions
    and understandings of the dump file format also made it much
    easier to develop a *correct* parser.)
    """
    
    def __init__(self):
        pass
    
    def parse(self, fileLike):
        """
        Generate parse events from the bytes provided by fileLike.
        """
        try:
            self.reader = None
            self.reader = Reader(fileLike)
            self.reader.next()
            for evt in self.parseDumpfile(): yield evt
        except:
            print >>sys.stderr, str(self.reader)
            raise
        assert self.reader.eof, msg("""
            Stopped parsing before end of input
            %s""" % (parser.reader,))

    def parseDumpfile(self):
        """
        A Dumpfile consists of a Version, an (optional?) UUID, and
        zero or more Revisions.  Extra blank lines may occur.  Blank
        lines before and after the version declaration are not
        reported.
        """
        self.version = None
        self.skipBlankLines()
        version = int(self.parseDumpProperty("SVN-fs-dump-format-version"))
        assert 2 <= version <= 3, \
               "Only dump format versions 2 and 3 are supported"
        self.version = version
        self.skipBlankLines()
        if self.matchDumpProperty("UUID"):
            uuid = self.parseDumpProperty("UUID")
        else:
            uuid = None

        yield BeginDumpfile(version, uuid)

        for evt in self.parseBlankLines(): yield evt
            
        while self.matchRevision():
            for evt in self.parseRevision(): yield evt
            for evt in self.parseBlankLines(): yield evt

        yield EndDumpfile()

    def matchDumpProperty(self, name=None):
        if name:
            prefix = name + ": "
            result = self.reader.cur.startswith(prefix)
            return result
        else:
            return pat_dump_property.match(self.reader.cur)
    
    def parseDumpProperty(self, name=None, store=None):
        """
        A dump property consists of a name and a value on a single
        line, separated by a colon.

        name
           If specified: (1) the parsed property must have this
           name. (2) we return the value of the property as a string.

           If None, then we return a tuple (*name*, *value*), both
           strings.

        store
           If specified, it must be a dictionary.  We'll update it as
           store[name] = value before we return.

        returns
          *value* or ( *name*, *value* )
        """
        m = pat_dump_property.match(self.reader.cur)

        assert m, "Expecting a dump property, but found \n%s" % (self.reader,)
        assert name == None or name == m.group(1), msg("""
            Expected property %s, but found %s
            """ % (name, m.group(1)))
        
        value = m.group(2)
        if store != None:
            store[m.group(1)] = value
        self.reader.next()
        if name == None:
            return m.group(1), value
        else:
            return value

    def skipBlankLines(self):
        """
        Skip blank lines in input without reporting them as parse events.
        """
        while self.reader.cur == "\n":
            self.reader.next()

    def matchBlankLine(self):
        return self.reader.cur == "\n"
    
    def parseBlankLine(self):
        """
        Parse blank line in input, reporting it as a BlankLine()
        event.
        """
        assert self.reader.cur == "\n", "Expected blank line"
        self.reader.next()
        return BlankLine()

    def parseBlankLines(self):
        while self.reader.cur == "\n":
            self.reader.next()
            yield BlankLine()


    def getBytes(self, n):
        """
        Returns the next n bytes of input, starting with and including
        the current line.

        We consume one extra byte of input without reporting it. It is
        always a line feed character which terminates the value.
        """
        buf, buflen = [], 0
        while n >= buflen and not self.reader.eof:
            buflen += len(self.reader.cur)
            buf.append(self.reader.cur)
            self.reader.next()
        assert buflen == n+1 and buf[-1][-1] == '\n', \
            "Didn't find expected newline terminator."
        buf[-1] = buf[-1][:-1] # strip newline terminator
        result = "".join(buf)
        assert len(result) == n
        return result

    def matchRevision(self):
        return self.matchDumpProperty("Revision-number")
    
    def parseRevision(self):
        """
        Parse a revision, which may contain UserProperties and will
        not include TextContent::

          Revision = 
            BeginRevision
            BlankLine?
            UserProperties?
            BlankLine*
            EndRevisionHeader
              (
              BeginNode
              BlankLine?
              UserProperties?
                (
                TextContent
                BlankLine
                )?
              BlankLine*
              )*
            EndRevisionNodes
        """
        dump_props = odict()
        rev = int(self.parseDumpProperty("Revision-number", dump_props))
        plen = int(self.parseDumpProperty("Prop-content-length", dump_props))
        clen = int(self.parseDumpProperty("Content-length", dump_props))
        assert clen - plen == 0, "A revision never has text content."

        yield BeginRevision(dump_props)

        if self.matchBlankLine():
            yield self.parseBlankLine()
        if self.matchUserProperties():
            yield self.parseUserProperties(plen)
        for evt in self.parseBlankLines():
            yield evt

        yield EndRevisionHeader()

        while self.matchNode():
            for evt in self.parseNode():
                yield evt

        yield EndRevisionNodes()

    def matchUserProperties(self):
        return (self.matchUserPropertyKey()
                or self.matchUserPropertyDelete())
    
    def parseUserProperties(self, plen, prop_delta=False):
        start = self.reader.start
        properties = UserProperties()
        while not self.matchUserPropertyEnd(): 
            assert not self.reader.eof
            if self.matchUserPropertyKey():
                key = self.parseUserPropertyKey()
                value = self.parseUserPropertyValue()
                properties[key] = value
            elif self.matchUserPropertyDelete():
                assert prop_delta, msg("""
                    Property deletion (operation 'D') is only allowed
                    when the Prop-delta dump property is true for the
                    containing node or revision.
                    """)
                key = self.parseUserPropertyDelete()
                properties[key] = None
        else:
            self.parseUserPropertyEnd()
        stop = self.reader.start
        assert plen == stop - start
        return properties

    def matchUserPropertyEnd(self):
        return self.reader.cur == "PROPS-END\n"

    def parseUserPropertyEnd(self):
        assert self.matchUserPropertyEnd(), msg("""
            Expected PROPS-END, but found\n%s
            """ % (self.reader,))
        self.reader.next()
    
    def matchUserPropertyKey(self):
        return self.reader.cur.startswith("K ")

    def parseUserPropertyKey(self):
        assert self.matchUserPropertyKey()
        key = self.getPropertyEntryContent()
        return key

    def matchUserPropertyValue(self):
        return self.reader.cur.startswith("V ")

    def parseUserPropertyValue(self):
        assert self.matchUserPropertyValue()
        value = self.getPropertyEntryContent()
        return value

    def matchUserPropertyDelete(self):
        return self.reader.cur.startswith("D ")

    def parseUserPropertyDelete(self):
        assert self.matchUserPropertyDelete()
        key = self.getPropertyEntryContent()
        return key

    def getPropertyEntryContent(self):
        """
        Parses property entry of the form:

           chararcter space n:integer newline bytes[n] newline

        and returns the bytes[n].
        """
        assert (len(self.reader.cur) and
                self.reader.cur[0:2] in ['K ', 'V ', 'D ']), msg("""
                Expected a pair of property entry lines, where the
                first has the form (K|V|D) <number>. Found this:
                %s""" % (self.reader,))
        n = int(self.reader.cur[2:])
        self.reader.next()
        result = self.getBytes(n)
        return result

    def matchNode(self):
        return self.matchDumpProperty("Node-path")
                                 
    def parseNode(self):
        """
        Parse a single node, which may contain both UserProperties and
        TextContent.
        
          Node = 
              BeginNode
              BlankLine?
              UserProperties?
                (
                TextContent
                BlankLine
                )?
        """
        chunk_pos = self.reader.start
        dump_props = BeginNode()
        node_path = self.parseDumpProperty("Node-path", dump_props)
        if self.matchDumpProperty("Node-kind"):
            node_kind = self.parseDumpProperty("Node-kind", dump_props)
        else:
            node_kind = None
        node_action = self.parseDumpProperty("Node-action", dump_props)
        
        # A number of optional properties follow. We know what they
        # can be, but their order isn't fixed.
        #
        # Content-length is optional, contrary to the available
        # documentation, which claims that it is always present for
        # compatability with generic rfc822 parsers.
        #
        # e.g. a dir node with action add and no properties has no
        # lengths at all.

        tlen, plen, clen = None, None, None
        while self.matchDumpProperty():
            name, value = self.parseDumpProperty(store=dump_props)
            if name == "Text-content-length":
                tlen = int(value)
            elif name == "Prop-content-length":
                plen = int(value)
            elif name == "Content-length":
                clen = int(value)

        prop_delta = dump_props.get("Prop-delta") == "true"
        if prop_delta:
            assert self.version > 2, msg("""
                Property deltas should not occur in this dumpfile.
                Its format is too old to support them.
                """)

        text_delta = dump_props.get("Text-delta") == "true"
        if text_delta:
            assert self.version > 2, msg("""
                Text deltas should not occur in this dumpfile.
                Its format is too old to support them.
                """)

        if clen == None:
            clen = 0
        if plen == None:
            plen = 0
        if tlen != None:
            assert tlen == clen - plen
        else:
            tlen = clen - plen

        yield dump_props

        if plen > 0 or tlen > 0:
            yield self.parseBlankLine()

        if plen > 0:
            yield self.parseUserProperties(plen, prop_delta)

        if tlen > 0:
            text = self.getBytes(tlen)
            assert len(text) == tlen

            # We can only verify the checksum when text_deltas are not
            # in use.  When text_deltas are being used, the checksum
            # refers to the *result* of applying the deltas and we
            # have no idea how nor desire to do that here.
            if not text_delta:
                expected_chksum = dump_props.get("Text-content-md5")
                if expected_chksum:
                    computed_chksum = md5(text).hexdigest()
                    assert expected_chksum == computed_chksum, msg("""
                           MD5 mismatch.
                           expected: %s,
                           computed: %s.
                           """ % (expected_chksum, computed_chksum))

            yield TextContent(text)
            # TextContent is always terminated by an 'extra' newline,
            # which getBytes consumes for us, but does not return.
            yield BlankLine() 

        for evt in self.parseBlankLines():
            yield evt

        yield EndNode()


class Reader(object):
    """
    Reads a fileLike object one line at a time, while remembering the
    most recently read line in 'cur'.  This allows us a look-ahead of
    one line, which is all we need.

    It keeps tack of quite a lot of state (linenr, start, stop, ...)
    for ease of debugging.

    fileLike
        The source of text lines

    cur
        The most recently read line

    start
        The byte offset, within fileLike of the first byte of
        cur. (i.e. cur[0])

    stop
        The byte offset, within fileLike, of the the next character
        following the last character of cur.  (This makes start
        .. stop a half-open range.)

    eof
        True fileLike's supply of lines has been exhausted.

    linenr
        The number (1-based) of the line of text in cur.
    """
    def __init__(self, fileLike):
        """
        Initialize a new LineReader.

        - fileLike must be a file open for reading.
        - fileLike will be closed automatically when all lines have
          been consumed.
        """
        self.fileLike = fileLike
        self.cur = None
        self.start = 0
        self.stop = 0
        self.eof = False
        self.linenr = 0

    def next(self):
        """
        Read the next line of input, returning it and storing it in
        cur.  Other properties are updated accordingly.  The first
        call to next(), following the last line will set eof to True.
        """
        try:
            self.cur = self.fileLike.next()
            self.linenr += 1
            self.start, self.stop = self.stop, self.stop+len(self.cur)
        except StopIteration:
            self.cur = ""
            self.eof = True
            self.start, self.stop = self.stop, self.stop
            self.fileLike.close()
        return self.cur

    def close(self):
        """
        Close the underlying fileLike
        """
        self.fileLike.close()

    def __str__(self):
        """
        The str(Reader) is intended for debugging.
        """
        return msg("""
            LineReader
            cur[%3d] = %s
            start    = %d
            stop     = %d
            linenr   = %d
            eof      = %s
            """ % (len(self.cur), self.cur[:72], 
                   self.start, self.stop, self.linenr, self.eof))


