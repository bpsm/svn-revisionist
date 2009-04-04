"""
revisionist.editors: edit subversion dumpfiles emitted by parser
(c) 2007 Ben Smith-Mannschott <benpsm@gmail.com> 

License
  GNU Lesser General Public License.
  http://www.gnu.org/licenses/lgpl.html
"""

import sys
from util import crop_text_block as msg
from parser import BeginDumpfile, EndDumpfile, \
     BeginRevision, EndRevisionHeader, EndRevisionNodes, \
     BeginNode, EndNode, UserProperties, TextContent, BlankLine


def edit_properties(events, edit):
    """
    Modifies parse events.  Consumes a stream of parse events,
    invoking the function 'edit' on BeginRevsion, BeginNode and
    UserProperties events before yielding the events to its caller.

    The events passed to edit are all dictionaries. Edit may modify
    their content as it sees fit.

    Changes to UserProperties will automatically cause recomputation
    of Content-length of Prop-content-length of the owning Node or
    Revision.
    """
    evt = events.next()
    while type(evt) != EndDumpfile:
        if type(evt) in (BeginRevision, BeginNode) :
            edit(evt) # Edit dump properties of Node or Revision
            
            # we'll need to postpone emitting this event and any that
            # follow until the end of the node or end of the revision
            # header so that we can recompute Prop and Content lengths
            # if UserProperties have been changed.

            evt_hold = [evt]
            prop_evt = None
            evt = events.next()
            while type(evt) not in (EndRevisionHeader, EndNode):
                if type(evt) == UserProperties:
                    assert prop_evt == None
                    prop_evt = evt
                evt_hold.append(evt)
                evt = events.next()

            assert type(evt) in (EndRevisionHeader, EndNode)
            if prop_evt:
                assert type(evt_hold[0]) in (BeginRevision, BeginNode)
                # edit user properties of node or Revision
                edit(prop_evt)
                # recompute Prop-content-length and Content-length
                dump_props = evt_hold[0]
                prop_len = len(str(prop_evt))
                dump_props["Prop-content-length"] = prop_len
                text_len = int(dump_props.get("Text-content-length", 0))
                dump_props["Content-length"] = prop_len + text_len
            for held_evt in evt_hold:
                yield held_evt
            yield evt
        else:
            yield evt
        evt = events.next()
    assert type(evt) == EndDumpfile
    yield evt

def echo_properties(events, property_names):
    """
    Print selected properties to stderr as they pass through.
    
    Passes parse events through unchanged.  Any property, be it a user
    property or a dump property with a name in the list events will be
    printed.
    """
    for evt in events:
        if type(evt) in [ UserProperties, BeginNode, BeginRevision ]:
            for name in property_names:
                if name in evt.keys():
                    print >>sys.stderr, name, evt[name]
        yield evt

def consume_events(events):
    """
    The universal sink. Think of it as /dev/null for parse events.
    """
    for x in events:
        pass
    
def show_progress(events):
    """
    Print out some nead lines of periods to stderr while events pass
    through.
    """
    period = 1000
    line_width = 78
    
    next_nl = period*line_width
    next_dot = period
    n = 0
    for evt in events:
        yield evt
        n += 1
        if n == next_dot:
            sys.stderr.write(".")
            next_dot += period
            if n > next_nl:
                sys.stderr.write("\n")
                next_nl += period*line_width
    else:
        sys.stderr.write("\n")


