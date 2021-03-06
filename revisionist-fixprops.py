#!/usr/bin/env python
#-*- coding: utf-8 -*-

import sys
import revisionist
from fnmatch import fnmatchcase

def parse_options():
    "Parse command line options. See also print_usage."
    args = sys.argv[1:]
    args.append(None)
    if args[0] in ["-h", "--help", None]:
        print_usage()
        return None, None
    verbose = False
    propsubs = []
    while args[0] in ["--property", "-p", "--verbose", "-v"]:
        if args[0] in ["--property", "-p"]:
            del args[0]
            propname = args[0]; del args[0]
            replacements = []
            while args[0] in ["--replace", "-r",
                              "--normalize-line-breaks", "-n"]:
                if args[0] in ["--replace", "-r"]:
                    del args[0]
                    replacements.append((args[0], args[1]))
                    del args[0]
                    del args[0]
                else:
                    del args[0]
                    replacements.append(('\r', ''))
            propsubs.append((propname, replacements))
        elif args[0] in ["--verbose", "-v"]:
            del args[0]
            verbose = True
    if len(args) != 1 or args[0] != None:
        print_usage()
        return []
    else:
        return propsubs, verbose


def main():
    propsubs, verbose = parse_options()
    if propsubs == None:
        return 1

    def edit(props):
        for propname in props:
            for propmatch, replacements in propsubs:
                if fnmatchcase(propname, propmatch):
                    val = props[propname]
                    for old, new in replacements:
                        val = val.replace(old, new)
                    props[propname] = val

    propnames = [propname for propname, x in propsubs]
    events = revisionist.pull(sys.stdin)
    if verbose:
        events = revisionist.echo_properties(events, propnames)
    events = revisionist.edit_properties(events, edit)
    if verbose:
        events = revisionist.echo_properties(events, propnames)
    revisionist.write_events_to_dumpfile(events, sys.stdout)

def print_usage():
    print >>sys.stderr, \
"""
 %s OPTIONS < dumpfile.in > dumpfile.out

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

 %s --property svn:externals \\
   --replace svn://old.com/repos/ svn://new.com/repos/ -n

 1. Replace every occurance of the string 'svn://old.com/repos/' with
    'svn://new.com/repos' in every svn:externals property in the
    dumpfile.
 2. Normalize the line breaks in every svn:externals property.
""" % (sys.argv[0], sys.argv[0])


if __name__ == "__main__":
    sys.exit(main())
