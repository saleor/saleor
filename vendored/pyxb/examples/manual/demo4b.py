# examples/manual/demo4b.py
from __future__ import print_function

import address

addr = address.USAddress('Robert Smith', '8 Oak Avenue', 'Anytown', 'AK', 12341)

print(addr.toxml("utf-8", element_name='USAddress'))
