# Bring everything in
from raw.ipo import *
from pyxb.utils import six

# Provide a way to reference the raw bindings that we're going to override
import raw.ipo as raw_ipo

@six.python_2_unicode_compatible
class USAddress (raw_ipo.USAddress):
    def __str__ (self):
        return six.u('''%s
%s
%s %s, %s''') % (self.name(), self.street(), self.city(), self.state(), self.zip())
    pass
raw_ipo.USAddress._SetSupersedingClass(USAddress)
