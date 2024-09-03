from __future__ import print_function
import pyxb
import po1

xml = open('badcontent.xml').read()
try:
    order = po1.CreateFromDocument(xml, location_base='badcontent.xml')
except pyxb.ValidationError as e:
    print(e.details())
