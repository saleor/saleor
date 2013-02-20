#! /usr/bin/env python
"""
Lint all local apps of the project.

Requires pylint and django-lint. You can get them with pip:
    pip install pylint -e git+git@github.com:lamby/django-lint.git@55290dfefc87baa02222db6d9582f2df8437a464#egg=django_lint-dev
"""
import warnings
import os

from pylint import checkers, lint

from DjangoLint import AstCheckers

DISABLED_WARNINGS = [
    # 'C0102',  # Black listed name "%s" Used when the name is listed in the black list (unauthorized names).
    'C0103',  # Invalid name "%s" (should match %s) Used when the name doesn't match the regular expression associated to its type (constant, variable, class...).
    'C0111',  # Missing docstring Used when a module, function, class or method has no docstring. Some special methods like __init__ doesn't necessary require a docstring.
    # 'C0112',  # Empty docstring Used when a module, function, class or method has an empty docstring (it would be too easy ;).
    # 'C0121',  # Missing required attribute "%s" Used when an attribute required for modules is missing.
    # 'C0202',  # Class method should have "cls" as first argument Used when a class method has an attribute different than "cls" as first argument, to easily differentiate them from regular instance methods.
    # 'C0203',  # Metaclass method should have "mcs" as first argument Used when a metaclass method has an attribute different the "mcs" as first argument.
    # 'C0301',  # Line too long (%s/%s) Used when a line is longer than a given number of characters.
    # 'C0302',  # Too many lines in module (%s) Used when a module has too much lines, reducing its readability.
    # 'C0321',  # More than one statement on a single line Used when more than on statement are found on the same line.
    # 'C0322',  # Operator not preceded by a space Used when one of the following operator (!= | <= | == | >= | < | > | = | += | -= | *= | /= | %) is not preceded by a space.
    # 'C0323',  # Operator not followed by a space Used when one of the following operator (!= | <= | == | >= | < | > | = | += | -= | *= | /= | %) is not followed by a space.
    # 'C0324',  # Comma not followed by a space Used when a comma (",") is not followed by a space.
    # 'E0100',  # __init__ method is a generator Used when the special class method __init__ is turned into a generator by a yield in its body.
    # 'E0101',  # Explicit return in __init__ Used when the special class method __init__ has an explicit return value.
    # 'E0102',  # %s already defined line %s Used when a function / class / method is redefined.
    # 'E0103',  # %r not properly in loop Used when break or continue keywords are used outside a loop.
    # 'E0104',  # Return outside function Used when a "return" statement is found outside a function or method.
    # 'E0105',  # Yield outside function Used when a "yield" statement is found outside a function or method.
    # 'E0106',  # Return with argument inside generator Used when a "return" statement with an argument is found outside in a generator function or method (e.g. with some "yield" statements).
    # 'E0107',  # Use of the non-existent %s operator Used when you attempt to use the C-style pre-increment orpre-decrement operator -- and ++, which doesn't exist in Python.
    # 'E0202',  # An attribute inherited from %s hide this method Used when a class defines a method which is hidden by an instance attribute from an ancestor class.
    # 'E0203',  # Access to member %r before its definition line %s Used when an instance member is accessed before it's actually assigned.
    # 'E0211',  # Method has no argument Used when a method which should have the bound instance as first argument has no argument defined.
    # 'E0213',  # Method should have "self" as first argument Used when a method has an attribute different the "self" as first argument. This is considered as an error since this is a so common convention that you shouldn't break it!
    # 'E0221',  # Interface resolved to %s is not a class Used when a class claims to implement an interface which is not a class.
    # 'E0222',  # Missing method %r from %s interface Used when a method declared in an interface is missing from a class implementing this interface
    # 'E0601',  # Using variable %r before assignment Used when a local variable is accessed before it's assignment.
    # 'E0602',  # Undefined variable %r Used when an undefined variable is accessed.
    # 'E0611',  # No name %r in module %r Used when a name cannot be found in a module.
    # 'E0701',  # Bad except clauses order (%s) Used when except clauses are not in the correct order (from the more specific to the more generic). If you don't fix the order, some exceptions may not be catched by the most specific handler.
    # 'E0702',  # Raising %s while only classes, instances or string are allowed Used when something which is neither a class, an instance or a string is raised (i.e. a TypeError will be raised).
    # 'E0710',  # Raising a new style class which doesn't inherit from BaseException Used when a new style class which doesn't inherit from BaseException raised since it's not possible with python < 2.5.
    # 'E0711',  # NotImplemented raised - should raise NotImplementedError Used when NotImplemented is raised instead of NotImplementedError
    # 'E1001',  # Use __slots__ on an old style class Used when an old style class use the __slots__ attribute.
    # 'E1002',  # Use super on an old style class Used when an old style class use the super builtin.
    # 'E1003',  # Bad first argument %r given to super class Used when another argument than the current class is given as first argument of the super builtin.
    'E1101',  # %s %r has no %r member Used when a variable is accessed for an unexistent member.
    # 'E1102',  # %s is not callable Used when an object being called has been inferred to a non callable object
    # 'E1103',  # %s %r has no %r member (but some types could not be inferred) Used when a variable is accessed for an unexistent member, but astng was not able to interpret all possible types of this variable.
    # 'E1111',  # Assigning to function call which doesn't return Used when an assignment is done on a function call but the inferred function doesn't return anything.
    # 'E1120',  # No value passed for parameter %s in function call Used when a function call passes too few arguments.
    # 'E1121',  # Too many positional arguments for function call Used when a function call passes too many positional arguments.
    # 'E1122',  # Duplicate keyword argument %r in function call Used when a function call passes the same keyword argument multiple times.
    # 'E1123',  # Passing unexpected keyword argument %r in function call Used when a function call passes a keyword argument that doesn't correspond to one of the function's parameter names.
    # 'E1124',  # Multiple values passed for parameter %r in function call Used when a function call would result in assigning multiple values to a function parameter, one value from a positional argument and one from a keyword argument.
    # 'F0202',  # Unable to check methods signature (%s / %s) Used when PyLint has been unable to check methods signature compatibility for an unexpected reason. Please report this kind if you don't make sense of it.
    # 'F0220',  # failed to resolve interfaces implemented by %s (%s) Used when a PyLint as failed to find interfaces implemented by a class
    # 'F0401',  # Unable to import %r Used when pylint has been unable to import a module.
    'R0201',  # Method could be a function Used when a method doesn't use its bound instance, and so could be written as a function.
    # 'R0401',  # Cyclic import (%s) Used when a cyclic import between two or more modules is detected.
    # 'R0801',  # Similar lines in %s files Indicates that a set of similar lines has been detected among multiple file. This usually means that the code should be refactored to avoid this duplication.
    # 'R0901',  # Too many ancestors (%s/%s) Used when class has too many parent classes, try to reduce this to get a more simple (and so easier to use) class.
    # 'R0902',  # Too many instance attributes (%s/%s) Used when class has too many instance attributes, try to reduce this to get a more simple (and so easier to use) class.
    'R0903',  # Too few public methods (%s/%s) Used when class has too few public methods, so be sure it's really worth it.
    'R0904',  # Too many public methods (%s/%s) Used when class has too many public methods, try to reduce this to get a more simple (and so easier to use) class.
    # 'R0911',  # Too many return statements (%s/%s) Used when a function or method has too many return statement, making it hard to follow.
    # 'R0912',  # Too many branches (%s/%s) Used when a function or method has too many branches, making it hard to follow.
    # 'R0913',  # Too many arguments (%s/%s) Used when a function or method takes too many arguments.
    # 'R0914',  # Too many local variables (%s/%s) Used when a function or method has too many local variables.
    # 'R0915',  # Too many statements (%s/%s) Used when a function or method has too many statements. You should then split it in smaller functions / methods.
    # 'R0921',  # Abstract class not referenced Used when an abstract class is not used as ancestor anywhere.
    # 'R0922',  # Abstract class is only referenced %s times Used when an abstract class is used less than X times as ancestor.
    # 'R0923',  # Interface not implemented Used when an interface class is not implemented anywhere.
    # 'W0101',  # Unreachable code Used when there is some code behind a "return " or "raise" statement, which will never be accessed.
    # 'W0102',  # Dangerous default value %s as argument Used when a mutable value as list or dictionary is detected in a default value for an argument.
    # 'W0104',  # Statement seems to have no effect Used when a statement doesn' t have (or at least seems to) any effect.
    # 'W0105',  # String statement has no effect Used when a string is used as a statement (which of course has no effect). This is a particular case of W0104 with its own message so you can easily disable it if you're using those strings as documentation, instead of comments.
    # 'W0107',  # Unnecessary pass statement Used when a "pass" statement that can be avoided is encountered.)
    # 'W0108',  # Lambda may not be necessary Used when the body of a lambda expression is a function call on the same argument list as the lambda itself; such lambda expressions are in all but a few cases replaceable with the function being called in the body of the lambda.
    # 'W0109',  # Duplicate key %r in dictionary Used when a dictionary expression binds the same key multiple times.
    # 'W0122',  # Use of the exec statement Used when you use the "exec" statement, to discourage its usage. That doesn't mean you can not use it !
    # 'W0141',  # Used builtin function %r Used when a black listed builtin function is used (see the bad-function option). Usual black listed functions are the ones like map, or filter , where Python offers now some cleaner alternative like list comprehension.
    # 'W0142',  # Used * or * magic* Used when a function or method is called using *args or **kwargs to dispatch arguments. This doesn't improve readability and should be used with care.
    # 'W0150',  # %s statement in finally block may swallow exception Used when a break or a return statement is found inside the finally clause of a try ...finally block: the exceptions raised in the try clause will be silently swallowed instead of being re-raised.
    # 'W0199',  # Assert called on a 2-uple. Did you mean 'assert x,y'? A call of assert on a tuple will always evaluate to true if the tuple is not empty, and will always evaluate to false if it is.
    # 'W0201',  # Attribute %r defined outside __init__ Used when an instance attribute is defined outside the __init__ method.
    # 'W0211',  # Static method with %r as first argument Used when a static method has "self" or "cls" as first argument.
    # 'W0212',  # Access to a protected member %s of a client class Used when a protected member (i.e. class member with a name beginning with an underscore) is access outside the class or a descendant of the class where it's defined.
    # 'W0221',  # Arguments number differs from %s method Used when a method has a different number of arguments than in the implemented interface or in an overridden method.
    # 'W0222',  # Signature differs from %s method Used when a method signature is different than in the implemented interface or in an overridden method.
    # 'W0223',  # Method %r is abstract in class %r but is not overridden Used when an abstract method (i.e. raise NotImplementedError) is not overridden in concrete class.
    # 'W0231',  # __init__ method from base class %r is not called Used when an ancestor class method has an __init__ method which is not called by a derived class.
    # 'W0232',  # Class has no __init__ method Used when a class has no __init__ method, neither its parent classes.
    # 'W0233',  # __init__ method from a non direct base class %r is called Used when an __init__ method is called on a class which is not in the direct ancestors for the analysed class.
    # 'W0301',  # Unnecessary semicolon Used when a statement is ended by a semi -colon (";"), which isn't necessary (that's python, not C ;).
    # 'W0311',  # Bad indentation. Found %s %s, expected %s Used when an unexpected number of indentation's tabulations or spaces has been found.
    # 'W0312',  # Found indentation with %ss instead of %ss Used when there are some mixed tabs and spaces in a module.
    # 'W0331',  # Use of the <> operator Used when the deprecated "<>" operator is used instead of "!=".
    # 'W0332',  # Use l as long integer identifier Used when a lower case "l" is used to mark a long integer. You should use a upper case "L" since the letter "l" looks too much like the digit "1"
    # 'W0333',  # Use of the `` operator Used when the deprecated "``" (backtick ) operator is used instead of the str() function.
    # 'W0401',  # Wildcard import %s Used when from module import * is detected.
    # 'W0402',  # Uses of a deprecated module %r Used a module marked as deprecated is imported.
    # 'W0403',  # Relative import %r, should be %r Used when an import relative to the package directory is detected.
    # 'W0404',  # Reimport %r (imported line %s) Used when a module is reimported multiple times.
    # 'W0406',  # Module import itself Used when a module is importing itself.
    # 'W0410',  # __future__ import is not the first non docstring statement Python 2.5 and greater require __future__ import to be the first non docstring statement in the module.
    # 'W0511',  # Used when a warning note as F_IXME or X_XX is detected.
    # 'W0601',  # Global variable %r undefined at the module level Used when a variable is defined through the "global" statement but the variable is not defined in the module scope.
    # 'W0602',  # Using global for %r but no assignment is done Used when a variable is defined through the "global" statement but no assignment to this variable is done.
    # 'W0603',  # Using the global statement Used when you use the "global" statement to update a global variable. PyLint just try to discourage this usage. That doesn't mean you can not use it !
    # 'W0604',  # Using the global statement at the module level Used when you use the "global" statement at the module level since it has no effect
    # 'W0611',  # Unused import %s Used when an imported module or variable is not used.
    # 'W0612',  # Unused variable %r Used when a variable is defined but not used.
    # 'W0613',  # Unused argument %r Used when a function or method argument is not used.
    # 'W0614',  # Unused import %s from wildcard import Used when an imported module or variable is not used from a 'from X import *' style import.
    # 'W0621',  # Redefining name %r from outer scope (line %s) Used when a variable's name hide a name defined in the outer scope.
    # 'W0622',  # Redefining built-in %r Used when a variable or function override a built-in.
    # 'W0631',  # Using possibly undefined loop variable %r Used when an loop variable (i.e. defined by a for loop or a list comprehension or a generator expression) is used outside the loop.
    # 'W0701',  # Raising a string exception Used when a string exception is raised.
    # 'W0702',  # No exception type(s) specified Used when an except clause doesn't specify exceptions type to catch.
    # 'W0703',  # Catch "Exception" Used when an except catches Exception instances.
    # 'W0704',  # Except doesn't do anything Used when an except clause does nothing but "pass" and there is no "else" clause.
    # 'W0710',  # Exception doesn't inherit from standard "Exception" class Used when a custom exception class is raised but doesn't inherit from the builtin "Exception" class.
    # 'W1001',  # Use of "property" on an old style class Used when PyLint detect the use of the builtin "property" on an old style class while this is relying on new style classes features
    # 'W1111',  # Assigning to function call which only returns None Used when an assignment is done on a function call but the inferred function returns nothing but None.
    # DjangoLint:
    'W6001',  # Naive tree structure implementation using ForeignKey('self')
]


def run(show_reports=False):
    targets = [x for x in os.listdir('.') if (os.path.isdir(x)
                                              and not x.startswith('.')
                                              and not x.endswith('.egg-info'))]

    linter = lint.PyLinter()

    checkers.initialize(linter)

    AstCheckers.register(linter)

    for warning in DISABLED_WARNINGS:
        linter.disable(warning)

    linter.set_option('ignore', ['local_settings.py', 'migrations'])

    if not show_reports:
        linter.set_option('reports', False)

    # django lint uses deprecated style of pylint warning and we are not
    # interested in seeing warnings about this
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        linter.check(targets)

if __name__ == "__main__":
    run()
