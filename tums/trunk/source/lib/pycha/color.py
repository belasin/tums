# Copyright (c) 2007-2008 by Lorenzo Gil Sanchez <lorenzo.gil.sanchez@gmail.com>
#
# This file is part of PyCha.
#
# PyCha is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyCha is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with PyCha.  If not, see <http://www.gnu.org/licenses/>.

DEFAULT_COLOR = '#3c581a'

def clamp(minValue, maxValue, value):
    """Make sure value is between minValue and maxValue"""
    if value < minValue:
        return minValue
    if value > maxValue:
        return maxValue
    return value
    
def hex2rgb(hexstring, digits=2):
    """Converts a hexstring color to a rgb tuple.

    Example: #ff0000 -> (1.0, 0.0, 0.0)

    digits is an integer number telling how many characters should be
    interpreted for each component in the hexstring.
    """
    if isinstance(hexstring, (tuple, list)):
        return hexstring

    top = float(int(digits * 'f', 16))
    r = int(hexstring[1:digits+1], 16)
    g = int(hexstring[digits+1:digits*2+1], 16)
    b = int(hexstring[digits*2+1:digits*3+1], 16)
    return r / top, g / top, b / top

def lighten(r, g, b, amount):
    """Return a lighter version of the color (r, g, b)"""
    return (clamp(0.0, 1.0, r + amount),
            clamp(0.0, 1.0, g + amount),
            clamp(0.0, 1.0, b + amount))
    
def generateColorscheme(masterColor, keys):
    """Generates a dictionary where the keys match the keys argument and
    the values are colors derivated from the masterColor.

    Each color is a lighter version of masterColor. This difference is
    computed based on the number of keys.

    The masterColor is given in a hex string format.
    """
    r, g, b = hex2rgb(masterColor)
    light = 1.0 / (len(keys)*2)
    return dict([(key, lighten(r, g, b, light * i))
                 for i, key in enumerate(keys)])

def defaultColorscheme(keys):
    """Return the default color scheme (derived from a dark green)"""
    return generateColorscheme(DEFAULT_COLOR, keys)

def getColorscheme(color, keys):
    """Get a color scheme from the six predefined ones or makes another
    one if the color is not found
    """
    return generateColorscheme(colorSchemes.get(color, color), keys)

# default colors for color schemes
colorSchemes = dict(
    red='#6d1d1d',
    green=DEFAULT_COLOR,
    blue='#224565',
    grey='#444444',
    black='#000000',
    darkcyan='#305755'
    )
