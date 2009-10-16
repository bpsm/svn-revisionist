<!-- mode: markdown ; coding: utf-8 -->

# Subversion Dump file Revisionist

Revisionist is a library to read and write Subversion dump files.
Versions 2 and 3 of the dump file format are supported.

Revisionist is designed with correctness in mind.  It is designed to
fail promptly and loudly when reality doesn't match its
expectations. It asserts profusely in the parser and the writer.

Originally, I wrote Revisionist to help me migrate Subversion
repositories from one server to another.  These repositories had used
`svn:externals` to refer to themselves and to each other.  These had to
be rewritten to refer to repositories at their new location on the new
server. Also, some EOL-style bungles had snuck in through Subclipse on
Windows.

The script, revisionist-fixprops, can perform simple string
substitutions and EOL-style normalization on property values.

## Installation

Install revisionist using the usual procedure:

    python setup.py install

This will install the revisionist package among your `site-packages`
and deposit revisionist-fixprops.py in the corresponding `bin`
directory.

## Using revisionist-fixprops

The script `revisionist-fixprops.py` performs string replacements and
newline normalization on arbitrary properties in a dump file.

    revisionist-fixprops.py OPTIONS < dumpfile.in > dumpfile.out

Legal option combinations are described by this BNF:

    OPTIONS         = HelpOpt | PropertyClause* 
    HelpOpt         = -h | --help
    PropertyClause  = PropertyOpt PropertyName EditClause*
    PropertyOpt     = -p | --property
    PropertyName    = text (unix-style glob syntax accepted)
    EditClause      = NormalizeOpt | ReplaceClause
    NormalizeOpt    = -n | --normalize-line-breaks
    ReplaceClause   = ReplaceOpt OldText NewText
    ReplaceOpt      = -r | --replace
    OldText         = text
    NewText         = text

e.g.

    revisionist-fixprops.py --property svn:externals \
         --replace svn://old.com/repos/ svn://new.com/repos/ -n

1. Replace every occurance of the string `svn://old.com/repos/` with
   `svn://new.com/repos` in every svn:externals property in the
   dump file.

2. Normalize the line breaks in every svn:externals property.


## Using the revisionist package

Once it has been installed, you should be able to import revisionist
like this:

    import revisionist

### Parsing

`revisionist.pull()` is a generator consuming an Subversion dump file and
delivering a sequence of parse events as objects. These objects are of
the following classes: `BeginDumpfile`, `EndDumpfile`,
`BeginRevision`, `EndRevisionHeader`, `EndRevisionNodes`, `BeginNode`,
`EndNode`, `UserProperties`, `TextContent`, `BlankLine`. See the
doc-string for `pull` for more information.

### Editing

`revisionist.edit_properties(events, edit)`: Modifies parse events.
Consumes a stream of parse events, invoking the function `edit` on
`BeginRevsion`, `BeginNode` and `UserProperties` events before
yielding the events to its caller.

Changes to `UserProperties` will automatically cause re-computation
of `Content-length` and `Prop-content-length` of the owning Node or
Revision.

### Writing

`revisionist.write_events_to_dumpfile(events, dstFile)` consumes a
sequence of parse events while writing them to `dstFile` (a file-like
object that's opened for writing) in Subversion's dump file format.
