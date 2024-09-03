Standard customization consists of using _SetSupersedingClass on a subclass
so that when the content model requires an instance object the customized
class is used.

In some cases, it is desirable to perform the same customization on multiple
types or elements, either repetitively or because the customization applied
to an intermediate (often abstract) type but is expected to be visible on
the subclasses of that type.

The "normal.py" solution demonstrates standard direct customization, that
the binding classes are not affected by customization of superclasses, and
that multiple inheritance can be used to force this at the cost of
explicitly creating custom bindings for every subclass.

The "introspect.py" solution demonstrates a more advanced technique which
scans the contents of the binding module for classes of interest and
dynamically performs the necessary customization.
