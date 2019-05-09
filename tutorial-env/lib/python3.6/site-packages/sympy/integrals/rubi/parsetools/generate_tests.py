from sympy.integrals.rubi.parsetools.parse import generate_sympy_from_parsed, parse_full_form, rubi_printer
from sympy import sympify
from sympy.integrals.rubi.utility_function import List, If
import os, inspect
def rubi_sstr(a):
    return rubi_printer(a, sympy_integers=True)

def generate_test_file():
    '''
    This function is assuming the name of file containing the fullform is test_1.m.
    It can be changes as per use.
    See `rubi_parsing_guide.md` in `parsetools` for more details.
    '''
    res =[]
    file_name = 'test_1.m'
    with open(file_name, 'r') as myfile:
        fullform =myfile.read().replace('\n', '')
    fullform = fullform.replace('$VersionNumber', 'version_number')
    fullform = fullform.replace('Defer[Int][', 'Integrate[')
    path_header = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
    h = open(os.path.join(path_header, "header.py.txt"), "r").read()
    header = "import sys\nfrom sympy.external import import_module\nmatchpy = import_module({})".format('\"matchpy\"')
    header += "\nif not matchpy:\n    disabled = True\n"
    header += "if sys.version_info[:2] < (3, 6):\n    disabled = True\n"
    header += "\n".join(h.split("\n")[8:-9])
    header += "from sympy.integrals.rubi.rubi import rubi_integrate\n"
    header += "from sympy import Integral as Integrate, exp, log\n"
    header += "\na, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z = symbols('a b c d e f g h i j k l m n o p q r s t u v w x y z')"
    header += "\nA, B, C, F, G, H, J, K, L, M, N, O, P, Q, R, T, U, V, W, X, Y, Z = symbols('A B C F G H J K L M N O P Q R T U V W X Y Z')"
    header += "\n\ndef {}():\n".format(file_name[0:-2])
    s = parse_full_form(fullform)
    tests = []
    for i in s:
        res[:] = []
        if i[0] == 'HoldComplete':
            ss = sympify(generate_sympy_from_parsed(i[1]), locals = { 'version_number' : 11, 'If' : If})
            ss = List(*ss.args)
            tests.append(ss)

    t = ''
    for a in tests:
        if len(a) == 5:
            r = 'rubi_integrate({}, x)'.format(rubi_sstr(a[0]))
            t += '\n    assert rubi_test({}, {}, {}, expand=True, _diff=True, _numerical=True) or rubi_test({}, {}, {}, expand=True, _diff=True, _numerical=True)'.format(r, rubi_sstr(a[1]), rubi_sstr(a[3]), r, rubi_sstr(a[1]),rubi_sstr(a[4]))
        else:
            r = 'rubi_integrate({}, x)'.format(rubi_sstr(a[0]))
            t += '\n    assert rubi_test({}, {}, {}, expand=True, _diff=True, _numerical=True)'.format(r, rubi_sstr(a[1]), rubi_sstr(a[3]))
    t = header+t+'\n'
    test = open('parsed_tests.py', 'w')
    test.write((t))
    test.close()
