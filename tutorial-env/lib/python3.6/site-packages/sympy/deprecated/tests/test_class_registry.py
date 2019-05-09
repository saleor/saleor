from sympy.utilities.pytest import warns_deprecated_sympy

def test_C():
    from sympy.deprecated.class_registry import C
    with warns_deprecated_sympy():
        C.Add
