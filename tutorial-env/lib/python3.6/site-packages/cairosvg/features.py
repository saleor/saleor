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
Helpers related to SVG conditional processing.

"""

import locale

ROOT = 'http://www.w3.org/TR/SVG11/feature'
LOCALE = locale.getdefaultlocale()[0] or ''
SUPPORTED_FEATURES = frozenset((
    ROOT + '#' + feature for feature in (
        'SVG',
        'SVG-static',
        'CoreAttribute',
        'Structure',
        'BasicStructure',
        'ConditionalProcessing',
        'Image',
        'Style',
        'ViewportAttribute',
        'Shape',
        'BasicText',
        'BasicPaintAttribute',
        'OpacityAttribute',
        'BasicGraphicsAttribute',
        'Marker',
        'Gradient',
        'Pattern',
        'Clip',
        'BasicClip',
        'Mask'
    )))


def has_features(features):
    """Check whether ``features`` are supported by CairoSVG."""
    return SUPPORTED_FEATURES >= set(features.strip().split(" "))


def support_languages(languages):
    """Check whether one of ``languages`` is part of the user locales."""
    for language in languages.split(','):
        language = language.strip()
        if language and LOCALE.startswith(language):
            return True
    return False


def match_features(node):
    """Check the node match the conditional processing attributes."""
    features = node.attrib.get('requiredFeatures')
    languages = node.attrib.get('systemLanguage')
    if 'requiredExtensions' in node.attrib:
        return False
    if features is not None and not has_features(features):
        return False
    if languages is not None and not support_languages(languages):
        return False
    return True
