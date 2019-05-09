"""Functions that involve magic. """

from __future__ import print_function, division

def pollute(names, objects):
    """Pollute the global namespace with symbols -> objects mapping. """
    from inspect import currentframe
    frame = currentframe().f_back.f_back

    try:
        for name, obj in zip(names, objects):
            frame.f_globals[name] = obj
    finally:
        del frame  # break cyclic dependencies as stated in inspect docs
