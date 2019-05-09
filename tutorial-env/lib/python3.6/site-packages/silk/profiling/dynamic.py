from functools import partial
import inspect
import logging
import sys
import re

from django.utils import six

from silk.profiling.profiler import silk_profile

Logger = logging.getLogger('silk.profiling.dynamic')


def _get_module(module_name):
    """
    Given a module name in form 'path.to.module' return module object for 'module'.
    """
    if '.' in module_name:
        splt = module_name.split('.')
        imp = '.'.join(splt[:-1])
        frm = splt[-1]
        module = __import__(imp, globals(), locals(), [frm], 0)
        module = getattr(module, frm)
    else:
        module = __import__(module_name, globals(), locals(), [], 0)
    return module


def _get_func(module, func_name):
    """
    Given a module and a function name, return the function.

    func_name can be of the forms:
        - 'foo': return a function
        - 'Class.foo': return a method
    """
    cls_name = None
    cls = None
    if '.' in func_name:
        cls_name, func_name = func_name.split('.')
    if cls_name:
        cls = getattr(module, cls_name)
        func = getattr(cls, func_name)
    else:
        func = getattr(module, func_name)
    return cls, func


def profile_function_or_method(module, func, name=None):
    """
    Programmatically apply a decorator to a function in a given module [+ class]

    @param module: module object or module name in form 'path.to.module'
    @param func: function object or function name in form 'foo' or 'Class.method'
    """
    if isinstance(module, six.string_types) or isinstance(module, six.text_type):
        module = _get_module(module)
    decorator = silk_profile(name, _dynamic=True)
    func_name = func
    cls, func = _get_func(module, func_name)
    wrapped_target = decorator(func)
    if cls:
        setattr(cls, func_name.split('.')[-1], wrapped_target)
    else:
        setattr(module, func_name, wrapped_target)


def _get_parent_module(module):
    parent = sys.modules
    splt = module.__name__.split('.')
    if len(splt) > 1:
        for module_name in splt[:-1]:
            try:
                parent = getattr(parent, module_name)
            except AttributeError:
                parent = parent[module_name]
    return parent


def _get_context_manager_source(end_line, file_path, name, start_line):
    inject_code = "with silk_profile('%s', _dynamic=True):\n" % name
    code = 'from silk.profiling.profiler import silk_profile\n'
    with open(file_path, 'r') as f:
        ws = ''
        for i, line in enumerate(f):
            if i == start_line:
                # Use the same amount of whitespace as the line currently occupying
                x = re.search(r"^(\s+).*$", line)
                try:
                    ws = x.groups()[0]
                except IndexError:
                    ws = ''
                code += ws + inject_code
                code += ws + '    ' + line
            elif start_line < i <= end_line:
                code += ws + '    ' + line
            else:
                code += line
    return code


def _get_ws(txt):
    """
    Return whitespace at the beginning of a string
    """
    m = re.search(r"^(\s+).*$", txt)
    try:
        fws = m.groups()[0]
    except AttributeError:
        fws = ''
    return fws


def _get_source_lines(func):
    source = inspect.getsourcelines(func)[0]
    fws = _get_ws(source[0])
    for i in range(0, len(source)):
        source[i] = source[i].replace(fws, '', 1)
    return source


def _new_func_from_source(source, func):
    """
    Create new function defined in source but maintain context from func

    @param func: The function whose global + local context we will use
    @param source: Python source code containing def statement
    """
    src_str = ''.join(source)
    frames = inspect.getouterframes(inspect.currentframe())
    calling_frame = frames[2][0]

    context = {}
    # My initial instict was: exec src_str in func.func_globals.items(), calling_frame.f_locals
    # however this seems to break the function closure so caveat here is that we create a new
    # function with the locals merged into the globals.
    #
    # Possible consequences I can think of:
    #   - If a global exists that already has the same name as the local, it will be overwritten in
    #     in the context of this function. This shouldnt matter though as the global should have already
    #     been hidden by the new name?
    #
    # This functionality should be considered experimental as no idea what other consequences there
    # could be.
    #
    # relevant: http://stackoverflow.com/questions/2749655/why-are-closures-broken-within-exec
    globals = six.get_function_globals(func)
    locals = calling_frame.f_locals
    combined = globals.copy()
    combined.update(locals)
    Logger.debug('New src_str:\n %s' % src_str)
    six.exec_(src_str, combined, context)
    return context[func.__name__]


def _inject_context_manager_func(func, start_line, end_line, name):
    """
    injects a context manager into the given function

    e.g given:

        x = 5
        def foo():
            print x
            print '1'
            print '2'
            print '3'
        inject_context_manager_func(foo, 0, 2, 'cm')

    foo will now have the definition:

        def foo():
            with silk_profile('cm'):
                print x
                print '1'
                print '2'
            print '3'

    closures, globals & locals are honoured

    @param func: object of type<function> or type<instancemethod>
    @param start_line: line at which to inject 'with' statement. line num. is relative to the func, not the module.
    @param end_line: line at which to exit the context
    @param name: name of the profiler
    """
    source = _get_source_lines(func)
    start_line += 1
    end_line += 1
    ws = _get_ws(source[start_line])
    for i in range(start_line, end_line):
        try:
            source[i] = '  ' + source[i]
        except IndexError:
            raise IndexError('Function %s does not have line %d' % (func.__name__, i))

    source.insert(start_line, ws + "from silk.profiling.profiler import silk_profile\n")
    source.insert(start_line + 1, ws + "with silk_profile('%s', _dynamic=True):\n" % name)
    return _new_func_from_source(source, func)


def is_str_typ(o):
    return any(map(partial(isinstance, o), six.string_types)) \
        or isinstance(o, six.text_type)


def inject_context_manager_func(module, func, start_line, end_line, name):
    if is_str_typ(module):
        module = _get_module(module)
    cls = None
    if is_str_typ(func):
        func_name = func
        cls, func = _get_func(module, func_name)
    else:
        func_name = func.__name__
    new_func = _inject_context_manager_func(func, start_line, end_line, name)
    if cls:
        setattr(cls, func_name, new_func)
    else:
        setattr(module, func_name, new_func)
