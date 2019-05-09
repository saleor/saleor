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
CairoSVG - A simple SVG converter based on Cairo.

"""

import os
import sys
from pathlib import Path

if hasattr(sys, 'frozen'):
    if hasattr(sys, '_MEIPASS'):
        # Frozen with PyInstaller
        # See https://github.com/Kozea/WeasyPrint/pull/540
        ROOT = Path(sys._MEIPASS)
    else:
        # Frozen with something else (py2exe, etc.)
        # See https://github.com/Kozea/WeasyPrint/pull/269
        ROOT = Path(os.path.dirname(sys.executable))
else:
    ROOT = Path(os.path.dirname(__file__))

VERSION = __version__ = (ROOT / 'VERSION').read_text().strip()


# VERSION is used in the "url" module imported by "surface"
from . import surface  # noqa isort:skip


SURFACES = {
    'PDF': surface.PDFSurface,
    'PNG': surface.PNGSurface,
    'PS': surface.PSSurface,
    'SVG': surface.SVGSurface,
}


def svg2svg(bytestring=None, *, file_obj=None, url=None, dpi=96,
            parent_width=None, parent_height=None, scale=1, unsafe=False,
            write_to=None, output_width=None, output_height=None):
    return surface.SVGSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        unsafe=unsafe, write_to=write_to, output_width=output_width,
        output_height=output_height)


def svg2png(bytestring=None, *, file_obj=None, url=None, dpi=96,
            parent_width=None, parent_height=None, scale=1, unsafe=False,
            write_to=None, output_width=None, output_height=None):
    return surface.PNGSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        unsafe=unsafe, write_to=write_to, output_width=output_width,
        output_height=output_height)


def svg2pdf(bytestring=None, *, file_obj=None, url=None, dpi=96,
            parent_width=None, parent_height=None, scale=1, unsafe=False,
            write_to=None, output_width=None, output_height=None):
    return surface.PDFSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        unsafe=unsafe, write_to=write_to, output_width=output_width,
        output_height=output_height)


def svg2ps(bytestring=None, *, file_obj=None, url=None, dpi=96,
           parent_width=None, parent_height=None, scale=1, unsafe=False,
           write_to=None, output_width=None, output_height=None):
    return surface.PSSurface.convert(
        bytestring=bytestring, file_obj=file_obj, url=url, dpi=dpi,
        parent_width=parent_width, parent_height=parent_height, scale=scale,
        unsafe=unsafe, write_to=write_to, output_width=output_width,
        output_height=output_height)


svg2svg.__doc__ = surface.Surface.convert.__doc__.replace(
    'the format for this class', 'SVG')
svg2png.__doc__ = surface.Surface.convert.__doc__.replace(
    'the format for this class', 'PNG')
svg2pdf.__doc__ = surface.Surface.convert.__doc__.replace(
    'the format for this class', 'PDF')
svg2ps.__doc__ = surface.Surface.convert.__doc__.replace(
    'the format for this class', 'PS')
