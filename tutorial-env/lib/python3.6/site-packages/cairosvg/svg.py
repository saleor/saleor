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
Root tag drawer.

"""

from .helpers import node_format, preserve_ratio


def svg(surface, node):
    """Draw a svg ``node``."""
    width, height, viewbox = node_format(surface, node)
    if viewbox:
        rect_x, rect_y = viewbox[0:2]
        node.image_width = viewbox[2]
        node.image_height = viewbox[3]
    else:
        rect_x, rect_y = 0, 0
        node.image_width = width
        node.image_height = height

    if node.parent is None:
        return

    scale_x, scale_y, translate_x, translate_y = preserve_ratio(surface, node)
    rect_x, rect_y = rect_x * scale_x, rect_y * scale_y
    rect_width, rect_height = width, height
    surface.context.translate(*surface.context.get_current_point())
    surface.context.translate(-rect_x, -rect_y)
    if node.get('overflow', 'hidden') != 'visible':
        surface.context.rectangle(rect_x, rect_y, rect_width, rect_height)
        surface.context.clip()
    surface.context.scale(scale_x, scale_y)
    surface.context.translate(translate_x, translate_y)
    surface.context_width, surface.context_height = rect_width, rect_height
