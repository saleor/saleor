import re
import os
import inspect
from sympy.integrals.rubi.parsetools.parse import (parse_full_form, downvalues_rules, temporary_variable_replacement,
    permanent_variable_replacement)

def generate_rules_from_downvalues():
    '''
    This function generate rules and saves in file. For more details,
    see `sympy/integrals/rubi/parsetools/rubi_parsing_guide.md` in `parsetools`.
    '''
    cons_dict = {}
    cons_index =0
    index = 0
    cons = ''
    input = ["Integrand_simplification.txt", "Linear_products.txt", "Quadratic_products.txt", "Binomial_products.txt",
        "Trinomial_products.txt", "Miscellaneous_algebra.txt", "Piecewise_linear.txt", "Exponentials.txt", "Logarithms.txt",
        "Sine.txt", "Tangent.txt", "Secant.txt", "Miscellaneous_trig.txt", "Inverse_trig.txt", "Hyperbolic.txt",
        "Inverse_hyperbolic.txt", "Special_functions.txt", "Miscellaneous_integration.txt"]

    output =['integrand_simplification.py', 'linear_products.py', 'quadratic_products.py', 'binomial_products.py', 'trinomial_products.py',
        'miscellaneous_algebraic.py' ,'piecewise_linear.py', 'exponential.py', 'logarithms.py', 'sine.py', 'tangent.py', 'secant.py', 'miscellaneous_trig.py',
        'inverse_trig.py', 'hyperbolic.py', 'inverse_hyperbolic.py', 'special_functions.py', 'miscellaneous_integration.py']

    for k in range(0, 18):
        module_name = output[k][0:-3]
        path_header = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        header = open(os.path.join(path_header, "header.py.txt"), "r").read()
        header = header.format(module_name)
        with open(input[k], 'r') as myfile:
            fullform =myfile.read().replace('\n', '')
        for i in temporary_variable_replacement:
            fullform = fullform.replace(i, temporary_variable_replacement[i])
        # Permanently rename these variables
        for i in permanent_variable_replacement:
            fullform = fullform.replace(i, permanent_variable_replacement[i])

        rules = []
        for i in parse_full_form(fullform): # separate all rules
            if i[0] == 'RuleDelayed':
                rules.append(i)
        parsed = downvalues_rules(rules, header, cons_dict, cons_index, index)
        result = parsed[0].strip() + '\n'
        cons_index = parsed[1]
        cons += parsed[2]
        index = parsed[3]
        # Replace temporary variables by actual values
        for i in temporary_variable_replacement:
            cons = cons.replace(temporary_variable_replacement[i], i)
            result = result.replace(temporary_variable_replacement[i], i)

        file = open(output[k],'w')
        file.write(str(result))
        file.close()

    cons = "\n".join(header.split("\n")[:-2])+ '\n' + cons
    constraints = open('constraints.py', 'w')
    constraints.write(str(cons))
    constraints.close()
