from __future__ import print_function, division

class PlotObject(object):
    """
    Base class for objects which can be displayed in
    a Plot.
    """
    visible = True

    def _draw(self):
        if self.visible:
            self.draw()

    def draw(self):
        """
        OpenGL rendering code for the plot object.
        Override in base class.
        """
        pass
