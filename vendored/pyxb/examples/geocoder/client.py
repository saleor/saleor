from __future__ import print_function
import sys
from pyxb.utils.six.moves.urllib import request as urllib_request
import GeoCoder
from pyxb import BIND
from pyxb.utils import domutils
import pyxb.bundles.wssplat.soap11 as soapenv
import pyxb.bundles.wssplat.soapenc as soapenc

address = '1600 Pennsylvania Ave., Washington, DC'
if 1 < len(sys.argv):
    address = sys.argv[1]

env = soapenv.Envelope(Body=BIND(GeoCoder.geocode(address)))

uri = urllib_request.Request('http://rpc.geocoder.us/service/soap/',
                      env.toxml("utf-8"),
                      { 'SOAPAction' : "http://rpc.geocoder.us/Geo/Coder/US#geocode", 'Content-Type': 'text/xml' } )

rxml = urllib_request.urlopen(uri).read()
#open('response.xml', 'w').write(rxml)
#rxml = open('response.xml').read()
response = soapenv.CreateFromDocument(rxml)

# OK, here we get into ugliness due to WSDL's concept of schema in the
# SOAP encoding not being consistent with XML Schema, even though it
# uses the same namespace.  See
# http://tech.groups.yahoo.com/group/soapbuilders/message/5879.  In
# short, the WSDL spec shows an example using soapenc:Array where a
# restriction was used to set the value of the wsdl:arrayType
# attribute.  This restriction failed to duplicate the element content
# of the base type, resulting in a content type of empty in the
# restricted type.  Consequently, PyXB can't get the information out
# of the DOM node, and we have to skip over the wildcard items to find
# something we can deal with.

# As further evidence the folks who designed SOAP 1.1 didn't know what
# they were doing, the encodingStyle attribute that's supposed to go
# in the Envelope can't validly be present there, since it's not
# listed and it's not in the namespace admitted by the attribute
# wildcard.  Fortunately, PyXB doesn't currently validate wildcards.

encoding_style = response.wildcardAttributeMap().get(soapenv.Namespace.createExpandedName('encodingStyle'))
items = []
if encoding_style == soapenc.Namespace.uri():
    gcr = response.Body.wildcardElements()[0]
    soap_array = gcr.wildcardElements()[0]
    items = soap_array.wildcardElements()
else:
    pass

for item in items:
    if (item.lat is None) or item.lat._isNil():
        print('Warning: Address did not resolve')
    print('''
%s %s %s %s %s
%s, %s  %s
%s %s''' % (item.number, item.prefix, item.street, item.type, item.suffix,
            item.city, item.state, item.zip,
            item.lat, item.long))
