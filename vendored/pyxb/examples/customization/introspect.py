# Demonstrate alternatives for bindings customization

# Introspection-based customization.
from raw.custom import *
import raw.custom as raw_custom

class ta04 (raw_custom.ta04):
    def xa04 (self):
        return 'extend ta04'
raw_custom.ta04._SetSupersedingClass(ta04)

import inspect

# Utility function to identify classes of interest
def _isSupersedable (cls):
    return inspect.isclass(cls) and issubclass(cls, pyxb.binding.basis._DynamicCreate_mixin)

def _injectClasses ():
    import sys
    import pyxb.binding.basis

    # All PyXB complex type definitions in the original module
    raw_classes = set([_o for (_, _o) in inspect.getmembers(raw_custom) if _isSupersedable(_o)])
    #print 'Original classes: %s' % (raw_classes,)

    # PyXB complex type definitions in this module that did not come
    # from the original import *.
    this_module = sys.modules[__name__]
    this_classes = set([_o for (_, _o) in inspect.getmembers(this_module) if _isSupersedable(_o) and _o not in raw_classes])
    this_classes_tuple = tuple(this_classes)
    #print 'This classes: %s' % (this_classes,)

    # Raw classes superseded by something in this module
    superseded_classes = set([ _o for _o in raw_classes if _o._SupersedingClass() in this_classes ])
    superseded_classes_tuple = tuple(superseded_classes)
    #print 'Superseded classes: %s' % (superseded_classes,)

    # Raw classes that are subclasses of something superseded by this
    # module, but that are not themselves superseded by this module
    need_supersedure_classes = set([_o for _o in raw_classes if issubclass(_o, superseded_classes_tuple) and _o not in superseded_classes])
    #print 'Need supersedure classes: %s' % (need_supersedure_classes,)

    # Add local definitions to supersede classes all of whose
    # ancestors have been superseded as necessary.
    while need_supersedure_classes:
        did_replacement = False
        new_need_supersedure_classes = set()
        for o in need_supersedure_classes:
            candidate = True
            # Build the new sequence of base classes while we check them.
            new_mro = []
            for super_o in o.__mro__:
                if super_o == o:
                    # Put the superseded class in its original position (probably first)
                    new_mro.append(o)
                    continue
                if super_o in need_supersedure_classes:
                    # Subclass of a class we haven't gotten to yet; put it off
                    candidate = False
                    break
                # Append the replacement or the original, as needed
                if super_o in superseded_classes:
                    new_mro.append(super_o._SupersedingClass())
                else:
                    new_mro.append(super_o)
            if not candidate:
                new_need_supersedure_classes.add(o)
                continue
            # Create a new class that subclasses the replacements
            name = o.__name__
            new_o = type(name, tuple(new_mro), o.__dict__.copy())
            # Install it in the module
            setattr(this_module, name, new_o)
            # Tell PyXB to use it as the superseding class
            o._SetSupersedingClass(new_o)
            # Record it so future passes will find it
            superseded_classes.add(o)
        assert need_supersedure_classes != new_need_supersedure_classes
        need_supersedure_classes = new_need_supersedure_classes

_injectClasses()
