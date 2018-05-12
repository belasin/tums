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

from pycha.chart import Chart, uniqueIndices
from pycha.color import hex2rgb, clamp

class BarChart(Chart):

    def __init__(self, surface=None, options={}):
        super(BarChart, self).__init__(surface, options)
        self.bars = []
        self.minxdelta = 0.0
        self.barWidthForSet = 0.0
        self.barMargin = 0.0

    def _updateChart(self):
        """Evaluates measures for vertical bars"""
        stores = self._getDatasetsValues()
        uniqx = uniqueIndices(stores)

        barWidth = 0
        if len(uniqx) == 1:
            xdelta = 1.0
            self.xscale = 1.0
            self.minxval = uniqx[0]
            barWidth = 1.0 * self.options.barWidthFillFraction
            self.barWidthForSet = barWidth / len(stores)
            self.barMargin = (1.0 - self.options.barWidthFillFraction) / 2
        else:
            xdelta = min([abs(uniqx[j] - uniqx[j-1])
                          for j in range(1, len(uniqx))])
            self.xscale = 1.0 / (self.xrange + 1)
            barWidth = xdelta * self.xscale * self.options.barWidthFillFraction
            self.barWidthForSet = barWidth / len(stores)
            self.barMargin = (xdelta * self.xscale
                              * (1.0 - self.options.barWidthFillFraction) / 2)
        
        self.minxdelta = xdelta
        self.bars = []

    def _renderChart(self, cx):
        """Renders a horizontal/vertical bar chart"""

        def drawBar(bar):
            cx.set_line_width(self.options.stroke.width)
            
            # gather bar proportions
            x = self.area.w * bar.x + self.area.x
            y = self.area.h * bar.y + self.area.y
            w = self.area.w * bar.w
            h = self.area.h * bar.h
            
            if w < 1 or h < 1:
                return # don't draw when the bar is too small
            
            if self.options.stroke.shadow:
                cx.set_source_rgba(0, 0, 0, 0.15)
                rectangle = self._getShadowRectangle(x, y, w, h)
                cx.rectangle(*rectangle)
                cx.fill()
            
            if self.options.shouldFill:
                cx.rectangle(x, y, w, h)
                cx.set_source_rgb(*self.options.colorScheme[bar.name])
                cx.fill_preserve()
            
            if not self.options.stroke.hide:
                cx.set_source_rgb(*hex2rgb(self.options.stroke.color))
                cx.stroke()
        
        cx.save()
        for bar in self.bars:
            drawBar(bar)
        cx.restore()

class VerticalBarChart(BarChart):

    def _updateChart(self):
        """Evaluates measures for vertical bars"""
        super(VerticalBarChart, self)._updateChart()

        for i, (name, store) in enumerate(self.datasets):
            for item in store:
                xval, yval = item
                x = (((xval - self.minxval) * self.xscale)
                    + (i * self.barWidthForSet) + self.barMargin)
                w = self.barWidthForSet
                h = (yval - self.minyval) * self.yscale
                y = 1.0 - h
                rect = Rect(x, y, w, h, xval, yval, name)
                
                if (0.0 <= rect.x <= 1.0) and (0.0 <= rect.y <= 1.0):
                    self.bars.append(rect)

    def _updateTicks(self):
        """Evaluates bar ticks"""
        super(BarChart, self)._updateTicks()
        offset = (self.minxdelta * self.xscale) / 2
        self.xticks = [(tick[0] + offset, tick[1]) for tick in self.xticks]

    def _getShadowRectangle(self, x, y, w, h):
        return (x-2, y-2, w+4, h+2)


class HorizontalBarChart(BarChart):

    def _updateChart(self):
        """Evaluates measures for horizontal bars"""
        super(HorizontalBarChart, self)._updateChart()

        for i, (name, store) in enumerate(self.datasets):
            for item in store:
                xval, yval = item
                y = (((xval - self.minxval) * self.xscale)
                     + (i * self.barWidthForSet) + self.barMargin)
                x = 0.0
                h = self.barWidthForSet
                w = (yval - self.minyval) * self.yscale
                rect = Rect(x, y, w, h, xval, yval, name)
                
                if (0.0 <= rect.x <= 1.0) and (0.0 <= rect.y <= 1.0):
                    self.bars.append(rect)

    def _updateTicks(self):
        """Evaluates bar ticks"""
        super(BarChart, self)._updateTicks()
        offset = (self.minxdelta * self.xscale) / 2
        tmp = self.xticks
        self.xticks = [(1.0 - tick[0], tick[1]) for tick in self.yticks ]
        self.yticks = [(tick[0] + offset, tick[1]) for tick in tmp]

    def _renderLines(self, cx):
        """Aux function for _renderBackground"""
        ticks = self.xticks
        for tick in ticks:
            self._renderLine(cx, tick, True)

    def _getShadowRectangle(self, x, y, w, h):
        return (x, y-2, w+2, h+4)


class Rect(object):
    def __init__(self, x, y, w, h, xval, yval, name):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.xval, self.yval = xval, yval
        self.name = name
