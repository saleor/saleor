from __future__ import print_function
import address

addr = address.USAddress()
addr.name = 'Robert Smith'
addr.street = '8 Oak Avenue'
addr.city = 'Anytown'
addr.state = 'NY'
addr.zip = 12341

print(addr.toxml("utf-8"))
