# Demonstrate alternatives for bindings customization
# Traditional customization
from raw.custom import *
import raw.custom as raw_custom

class ta0 (raw_custom.ta0):
    def xa0 (self):
        return 'extend ta0'
raw_custom.ta0._SetSupersedingClass(ta0)

class tc01 (raw_custom.tc01):
    def xc01 (self):
        return 'extend tc01'
raw_custom.tc01._SetSupersedingClass(tc01)

class tc02 (raw_custom.tc02, ta0):
    def xc02 (self):
        return 'extend tc02'
raw_custom.tc02._SetSupersedingClass(tc02)

# class tc03 left as original
