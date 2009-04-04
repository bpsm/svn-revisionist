Subversion Dumpfile Revisionist
===============================

Welcome!

Have you used svn:externals in your repository and now find that this
complicates migrating your repository to a new server? Do you have
problems with svn:externals edited in subclipse under windows having
inconsistent line breaks?  If so, then revisionist-fixprops is for
you.

In fact, if you're a fan of rewriting history (of your subversion
repositories) then the revisionist library may be just what you need.

Revisionist
-----------

Revisionst is a library to read and write Subversion dumpfiles.
Versions 2 and 3 of the dumpfile format are supported.

Revisionist is designed with correctness in mind.  It is designed to
fail promptly and loudly when reality doesn't match its
expectations. It asserts profusely in the parser and the writer.

parser.py
  Provides a pull-parser for Subversion dumpfiles.  The parser is
  implemened as a python generator which consumes a dump file (a
  sequence of lines of text) and yields a series of parse events. 

  The classes representing the parse events are also defined here.

editors.py
  ``edit_properties(events, edit)``: Modifies parse events.  Consumes
  a stream of parse events, invoking the function ``edit`` on
  ``BeginRevsion``, ``BeginNode`` and ``UserProperties`` events before
  yielding the events to its caller.

  Changes to ``UserProperties`` will automatically cause recomputation
  of Content-length of Prop-content-length of the owning Node or
  Revision.

writer.py
  Provides ``write_events_to_dumpfile(events, dstFile)``, which
  consumes a sequence of parse events while writing them to dstFile (a
  file-like object that's opened for writing) in Subversion's dumpfile
  format.

revisionist-fixprops
--------------------

The script revisionist-fixprops.py performs string replacements and
newline normalization on arbitrary properties in a dumpfile.

::

  revisionist-fixprops.py OPTIONS < dumpfile.in > dumpfile.out

Legal option combinations are described by this BNF::

 OPTIONS         = HelpOpt | PropertyClause* 
 HelpOpt         = -h | --help
 PropertyClause  = PropertyOpt EditClause*
 PropertyOpt     = -p | --property
 EditClause      = NormalizeOpt | ReplaceClause
 NormalizeOpt    = -n | --normalize-line-breaks
 ReplaceClause   = ReplaceOpt OldText NewText
 ReplaceOpt      = -r | --replace
 OldText         = text
 NewText         = text
 
e.g. ::

  revisionist-fixprops.py --property svn:externals \
     --replace svn://old.com/repos/ svn://new.com/repos/ -n

1. Replace every occurance of the string 'svn://old.com/repos/' with
   'svn://new.com/repos' in every svn:externals property in the
   dumpfile.

2. Normalize the line breaks in every svn:externals property.








