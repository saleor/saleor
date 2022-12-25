# -*- coding: utf-8 -*-
# This file contains code adopted from http://code.activestate.com/recipes/.
# Copyright and licensing information is associated with each incorporated
# recipe.  At this time, all code is licensed under PSF.

# http://code.activestate.com/recipes/363841/
# by Lars Tiede, derivative from:
# http://code.activestate.com/recipes/52257/
# by Paul Prescod
# Licensed under PSF
# No changes
def detectXMLEncoding(fp):
    """ Attempts to detect the character encoding of the xml file
    given by a file object fp. fp must not be a codec wrapped file
    object!

    The return value can be:
        - if detection of the BOM succeeds, the codec name of the
        corresponding unicode charset is returned

        - if BOM detection fails, the xml declaration is searched for
        the encoding attribute and its value returned. the "<"
        character has to be the very first in the file then (it's xml
        standard after all).

        - if BOM and xml declaration fail, None is returned. According
        to xml 1.0 it should be utf_8 then, but it wasn't detected by
        the means offered here. at least one can be pretty sure that a
        character coding including most of ASCII is used :-/
    """
    ### detection using BOM

    ## the BOMs we know, by their pattern
    bomDict={ # bytepattern : name
             (0x00, 0x00, 0xFE, 0xFF) : "utf_32_be",
             (0xFF, 0xFE, 0x00, 0x00) : "utf_32_le",
             (0xFE, 0xFF, None, None) : "utf_16_be",
             (0xFF, 0xFE, None, None) : "utf_16_le",
             (0xEF, 0xBB, 0xBF, None) : "utf_8",
            }

    ## go to beginning of file and get the first 4 bytes
    oldFP = fp.tell()
    fp.seek(0)
    (byte1, byte2, byte3, byte4) = tuple(map(ord, fp.read(4)))

    ## try bom detection using 4 bytes, 3 bytes, or 2 bytes
    bomDetection = bomDict.get((byte1, byte2, byte3, byte4))
    if not bomDetection :
        bomDetection = bomDict.get((byte1, byte2, byte3, None))
        if not bomDetection :
            bomDetection = bomDict.get((byte1, byte2, None, None))

    ## if BOM detected, we're done :-)
    if bomDetection :
        fp.seek(oldFP)
        return bomDetection


    ## still here? BOM detection failed.
    ##  now that BOM detection has failed we assume one byte character
    ##  encoding behaving ASCII - of course one could think of nice
    ##  algorithms further investigating on that matter, but I won't for now.


    ### search xml declaration for encoding attribute
    import re

    ## assume xml declaration fits into the first 2 KB (*cough*)
    fp.seek(0)
    buffer = fp.read(2048)

    ## set up regular expression
    xmlDeclPattern = r"""
    ^<\?xml             # w/o BOM, xmldecl starts with <?xml at the first byte
    .+?                 # some chars (version info), matched minimal
    encoding=           # encoding attribute begins
    ["']                # attribute start delimiter
    (?P<encstr>         # what's matched in the brackets will be named encstr
     [^"']+              # every character not delimiter (not overly exact!)
    )                   # closes the brackets pair for the named group
    ["']                # attribute end delimiter
    .*?                 # some chars optionally (standalone decl or whitespace)
    \?>                 # xmldecl end
    """

    xmlDeclRE = re.compile(xmlDeclPattern, re.VERBOSE)

    ## search and extract encoding string
    match = xmlDeclRE.search(buffer)
    fp.seek(oldFP)
    if match :
        return match.group("encstr")
    else :
        return None
