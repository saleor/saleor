# This file is part of CairoSVG
# Copyright © 2010-2018 Kozea
#
# This library is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with CairoSVG.  If not, see <http://www.gnu.org/licenses/>.

"""
Command-line interface to CairoSVG.

"""

import argparse
import os
import sys

from . import SURFACES, VERSION


def main(argv=None, stdout=None, stdin=None):
    """Entry-point of the executable."""
    # Get command-line options
    parser = argparse.ArgumentParser(
        description='Convert SVG files to other formats')
    parser.add_argument('input', default='-', help='input filename or URL')
    parser.add_argument(
        '-v', '--version', action='version', version=VERSION)
    parser.add_argument(
        '-f', '--format', help='output format',
        choices=sorted([surface.lower() for surface in SURFACES]))
    parser.add_argument(
        '-d', '--dpi', default=96, type=float,
        help='ratio between 1 inch and 1 pixel')
    parser.add_argument(
        '-W', '--width', default=None, type=float,
        help='width of the parent container in pixels')
    parser.add_argument(
        '-H', '--height', default=None, type=float,
        help='height of the parent container in pixels')
    parser.add_argument(
        '-s', '--scale', default=1, type=float, help='output scaling factor')
    parser.add_argument(
        '-u', '--unsafe', action='store_true',
        help='resolve XML entities and allow very large files '
             '(WARNING: vulnerable to XXE attacks and various DoS)')
    parser.add_argument(
        '--output-width', default=None, type=float,
        help='desired output width in pixels')
    parser.add_argument(
        '--output-height', default=None, type=float,
        help='desired output height in pixels')

    parser.add_argument('-o', '--output', default='-', help='output filename')

    options = parser.parse_args(argv)
    kwargs = {
        'parent_width': options.width, 'parent_height': options.height,
        'dpi': options.dpi, 'scale': options.scale, 'unsafe': options.unsafe,
        'output_width': options.output_width,
        'output_height': options.output_height}
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    kwargs['write_to'] = (
        stdout.buffer if options.output == '-' else options.output)
    if options.input == '-':
        kwargs['file_obj'] = stdin.buffer
    else:
        kwargs['url'] = options.input
    output_format = (
        options.format or
        os.path.splitext(options.output)[1].lstrip('.') or
        'pdf').upper()

    SURFACES[output_format.upper()].convert(**kwargs)


if __name__ == '__main__':  # pragma: no cover
    main()
