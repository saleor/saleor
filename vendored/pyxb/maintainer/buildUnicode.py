# Copyright 2009-2013, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Utility to generate the code point sets defined by the Unicode standard.

You'll need these files, corresponding to the U{Unicode Database for XML
Schema Part 2: Datatypes<http://www.w3.org/TR/xmlschema-2/#UnicodeDB>},
which is:

 - U{http://www.unicode.org/Public/3.1-Update/UnicodeData-3.1.0.txt}
 - U{http://www.unicode.org/Public/3.1-Update/Blocks-4.txt}

Invoke this script, redirecting the output to
C{pyxb/utils/unicode_data.py}.

"""

from __future__ import print_function
import textwrap
import re
from pyxb.utils import six
from pyxb.utils.six.moves import xrange

def countCodepoints (codepoints):
    count = 0
    for v in codepoints:
        if isinstance(v, tuple):
            count = count + v[1] - v[0] + 1
        else:
            count = count + 1
    return count

def condenseCodepoints (codepoints):
    ranges = []
    codepoints = list(codepoints)
    codepoints.sort()
    range_min = None
    for ri in xrange(len(codepoints)):
        codepoint = codepoints[ri]
        if not isinstance(codepoint, tuple):
            if range_min is None:
                range_last = range_min = codepoint
                range_next = range_last + 1
                continue
            if codepoint == range_next:
                range_last = codepoint
                range_next += 1
                continue
        if range_min is not None:
            ranges.append( (range_min, range_last) )
        if isinstance(codepoint, tuple):
            range_min = None
            ranges.append(codepoint)
        else:
            range_last = range_min = codepoints[ri]
            range_next = range_last + 1
    if range_min is not None:
        ranges.append( (range_min, range_last) )
    return ranges

def rangesToPython (ranges, indent=11, width=67):
    ranges.sort()
    text = ', '.join( [ '(0x%06x, 0x%06x)' % _r for _r in ranges ] )
    text += ','
    wrapped = textwrap.wrap(text, 67)
    return ("\n%s" % (' ' * indent,)).join(wrapped)

def emitCategoryMap (data_file):
    category_map = {}
    unicode_data = open(data_file)
    range_first = None
    last_codepoint = -1
    while True:
        line = unicode_data.readline()
        fields = line.split(';')
        if 1 >= len(fields):
            break
        codepoint = int(fields[0], 16)
        char_name = fields[1]
        category = fields[2]

        # If code points are are not listed in the file, they are in the Cn category.
        if range_first is None and last_codepoint + 1 != codepoint:
            category_map.setdefault('Cn', []).append((last_codepoint + 1, codepoint))
            category_map.setdefault('C', []).append((last_codepoint + 1, codepoint))
        last_codepoint = codepoint

        if char_name.endswith(', First>'):
            assert range_first is None
            range_first = codepoint
            continue
        if range_first is not None:
            assert char_name.endswith(', Last>')
            codepoint = ( range_first, codepoint )
            range_first = None
        category_map.setdefault(category, []).append(codepoint)
        category_map.setdefault(category[0], []).append(codepoint)

    # Code points at the end of the Unicode range that are are not listed in
    # the file are in the Cn category.
    category_map.setdefault('Cn', []).append((last_codepoint + 1, 0x10FFFF))
    category_map.setdefault('C', []).append((last_codepoint + 1, 0x10FFFF))

    for k, v in six.iteritems(category_map):
        category_map[k] = condenseCodepoints(v)

    print('# Unicode general category properties: %d properties' % (len(category_map),))
    print('PropertyMap = {')
    for (k, v) in sorted(six.iteritems(category_map)):
        print('  # %s: %d codepoint groups (%d codepoints)' % (k, len(v), countCodepoints(v)))
        print("  %-4s : CodePointSet([" % ("'%s'" % k,))
        print("           %s" % (rangesToPython(v, indent=11, width=67),))
        print("         ]),")
    print('  }')

def emitBlockMap (data_file):
    block_map = { }
    block_re = re.compile('(?P<min>[0-9A-F]+)(?P<spans>\.\.|; )(?P<max>[0-9A-F]+);\s(?P<block>.*)$')
    block_data = open(data_file)
    while True:
        line = block_data.readline()
        if 0 == len(line):
            break
        mo = block_re.match(line)
        if mo is None:
            continue
        rmin = int(mo.group('min'), 16)
        rmax = int(mo.group('max'), 16)
        block = mo.group('block').replace(' ', '')
        block_map.setdefault(block, []).append( (rmin, rmax) )

    print('# Unicode code blocks: %d blocks' % (len(block_map),))
    print('BlockMap = {')
    for k in sorted(six.iterkeys(block_map)):
        v = block_map.get(k)
        print('  %s : CodePointSet(' % (repr(k),))
        print('     %s' % (rangesToPython(v, indent=6, width=67),))
        print('  ),')
    print('  }')

print('''# -*- coding: utf-8 -*-
# Unicode property and category maps.

from pyxb.utils.unicode import CodePointSet
''')

emitBlockMap('Blocks-4.txt')
emitCategoryMap('UnicodeData-3.1.0.txt')
