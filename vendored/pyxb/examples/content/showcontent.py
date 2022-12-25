from __future__ import print_function
from pyxb import BIND
import content

v = content.numbers(1, BIND(2), attribute=3)
v.complex.style = "decimal"
print(v.toxml("utf-8").decode('utf-8'))
print(3 * v.simple)
print(4 * v.complex.value())
print(5 * v.attribute)
