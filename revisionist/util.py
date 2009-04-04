
"""
revisionist.util: utils for subversion revisionist tools
(c) 2007 Ben Smith-Mannschott <benpsm@gmail.com> 

License
  GNU Lesser General Public License.
  http://www.gnu.org/licenses/lgpl.html
"""

import re

pat_blank = re.compile(r'^\s*$')
pat_lead_space = re.compile(r'^(\s*)(.*)$')

def crop_text_block(text):
    """
    Strip the leading whitespace form the lines of the string text.
    The first line with leading white space determines the maximal
    amount of whitespace stripped from each line.
    """
    lines = text.splitlines()

    # get the index of the first non-blank line
    i = 0
    while i < len(lines) and pat_blank.match(lines[i]): i += 1
    first = i

    if first == len(lines):
        # it's all blank. just return the empty string
        return ""

    # get the index of the last non-blank 
    i = len(lines) - 1
    while i >= 0 and pat_blank.match(lines[i]): i -= 1
    last = i

    assert first <= last

    # cut out leading trailing blank lines
    lines = lines[first:last+1]

    # split each line into its leading whitespace portion
    # and its rest
    split_lines = [ pat_lead_space.match(x).groups()
                    for x in lines ]

    # find the amount of common leading whitespace, which is the
    # length of the shortest leading whitespace segment, ignoring
    # those with length 0.

    cut_length = 0
    for space, rest in split_lines:
        n = len(space)
        if 0 < n < cut_length or cut_length == 0:
            cut_length = n

    # remove cut_length characters from the leading whitespace of each
    # line. Lines with no leading whitespaces are effectively left
    # unaltered by this.

    lines = [ space[cut_length:] + rest
              for space, rest in split_lines ]

    # the result is the incoming lines joined by \n.  We'll want to
    # if the original text had a terminating \n, we'll want to make
    # sure that comes along by stuffing an empty string at the end
    # lines before doing the join.

    if text[-1] == '\n':
        lines.append('')
    
    result = "\n".join(lines)

    return result


def test_strip_leading_space():
    sls = strip_leading_space
    assert sls("") == ""
    assert sls("  ") == ""
    assert sls("first\n  second\n  third") == "first\nsecond\nthird"


def curry(function, *curry_args, **curry_kwargs):
    def _curried(*call_args, **call_kwargs):
        args = curry_args + call_args
        kwargs = curry_kwargs.copy()
        kwargs.update(call_kwargs)
        return function(*args, **kwargs)
    return _curried


class odict(dict):
    """
    An extension of dict which remembers the insertion order of its
    keys.  
    """
    def __init__(self, *args, **kwargs):
        """
        An odict may be initialized with content from the following
        sources:

        1. a single odict
        2. a single dict (key order undefined)
        3. a single list of (key, value) tuples
        4. an arbitrary number of (key, value) tuples
        5. an arbitrary number of keyword arguments (key order
           undefined)
        """
        dict.__init__(self)
        self.ordered_keys = []
        if len(args) == 1 and 'keys' in dir(args[0]):
            contents = args[0]
            for k in contents.keys():
               self[k] = contents[k]
        elif len(args) == 1 and 'append' in dir(args[0]):
            for k, v in args[0]:
                self[k] = v
        elif len(args) > 0:
            for k, v in args:
                self[k] = v
        for k in kwargs:
            self[k] = kwargs[k]
        
    def __setitem__(self, key, value):
        if key not in self:
            self.ordered_keys.append(key)
        dict.__setitem__(self, key, value)
        
    def __getitem__(self, key):
        return dict.__getitem__(self, key)
    
    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.ordered_keys.remove(key)
        
    def keys(self):
        return list(self.ordered_keys)
    
    def copy(self):
        cp = odict(self)
        return cp

    def iteritems(self):
        for k in self.ordered_keys:
            yield k, self[k]

    def __iter__(self):
        return iter(self.ordered_keys)

    def iterkeys(self):
        return iter(self.ordered_keys)

    def itervalues(self):
        for k in self.ordered_keys:
            yield self[k]

    def __str__(self):
        out = ["{"]
        for k in self.ordered_keys:
            if len(out) > 1:
                out.append(', ')
            out.append('%s: %s' % (k, self[k]))
        out.append("}")
        return "".join(out)

    def __repr__(self):
        return "odict(%r)" % ( [item for item in self.iteritems()],)

                   
def test_odict():
    o = odict()
    assert len(o) == 0
    o = odict([ (5,1), (4,2), (3,3), (2,4), (1,5) ])
    assert o.keys() == [5, 4, 3, 2, 1]
    o = odict((5,1),(4,2),(3,3),(2,4),(1,5))
    assert o.keys() == [5, 4, 3, 2, 1]
    d = dict([(5,1),(4,2),(3,3),(2,4),(1,5)])
    assert d.keys() != [5, 4, 3, 2, 1]
    o2 = odict(o)
    assert o.keys() == o2.keys()
    assert [x for x in o.iteritems()] == [(5,1),(4,2),(3,3),(2,4),(1,5)]
    assert [x for x in o.iterkeys()] == [5, 4, 3, 2, 1]
    assert [x for x in o.itervalues()] == [1, 2, 3, 4, 5]
    
            
    
    
