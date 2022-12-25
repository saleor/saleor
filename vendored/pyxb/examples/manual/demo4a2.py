from __future__ import print_function
import address

addr = address.USAddress()
addr.street = '8 Oak Avenue'
addr.state = 'AK'
addr.city = 'Anytown'
addr.zip = 12341
addr.name = 'Robert Smith'

print(addr.toxml("utf-8", element_name='USAddress'))
