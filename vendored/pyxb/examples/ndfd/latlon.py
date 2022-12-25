from __future__ import print_function
import time
import sys
import DWML
import datetime
import pyxb
from pyxb.utils import domutils, six
from pyxb.utils.six.moves.urllib import request as urllib_request
import pyxb.binding.datatypes as xsd
import pyxb.bundles.wssplat.soap11 as soapenv

today = xsd.dateTime.today()
later = today + datetime.timedelta(days=7)

# Set a standard position for which we want the weather
lat = 38.898748
lon = -77.037684

# Override the position from the command line
if 2 < len(sys.argv):
    lat = float(sys.argv[1])
    lon = float(sys.argv[2])

# Import the schema bindings that were extracted from the WSDL in a
# separate, previous step.
import ndfd

# Read in the WSDL spec for the service.  Note that we have to process
# the schema again here, because we were unable to save the component
# model for it before, and we need the definition maps in order to
# resolve part type references in the WSDL messages.
import pyxb.bundles.wssplat.wsdl11 as wsdl
uri_src = open('ndfdXML.wsdl')
doc = domutils.StringToDOM(uri_src.read())
spec = wsdl.definitions.createFromDOM(doc.documentElement, process_schema=True)

# Create a helper that will generate XML in the WSDL's namespace,
# qualifying every element with xsi:type just like the service
# expects.
bds = domutils.BindingDOMSupport(default_namespace=spec.targetNamespace(), require_xsi_type=True)

# Set the parameters that you want enabled.  See
# http://www.nws.noaa.gov/xml/docs/elementInputNames.php
weather_params = ndfd.weatherParametersType(maxt=True, mint=True, temp=True, sky=True, pop12=True, rh=True, wx=True, appt=True)

# The schema didn't say the other parameters are optional (even though
# they are), so set them to false if not already initialized.
for eu in six.itervalues(weather_params._ElementMap):
    if eu.value(weather_params) is None:
        eu.set(weather_params, False)

# There is no schema element or type corresponding to the request
# message; it's only in a WSDL message definition.  We need to build
# it manually.

# Create a root element corresponding to the operation's input message
root = bds.createChildElement('NDFDgen')

# Create a map from the message part name to the value to use for that
# part.
request_values = { 'latitude' : lat
                 , 'longitude' : lon
                 , 'startTime' : today
                 , 'endTime' : later
                 , 'product' : ndfd.productType.time_series
                 , 'Unit' : ndfd.unitType.e
                 , 'weatherParameters' : weather_params }

# Get the WSDL message description, and for each part for which we
# have a value, add an element to the message document.
req_msg = spec.messageMap()['NDFDgenRequest']
for p in req_msg.part:
    fv = request_values.get(p.name)
    if fv is None:
        # Fatal error if a field required by the message is not available
        raise Exception('%s: %s has no value' % (p.name, p.typeReference.expandedName()))
    else:
        print('%s: %s' % (p.name, p.typeReference.expandedName()))
        # Make sure the value is of the expected type
        type_binding = p.typeReference.expandedName().typeBinding()
        if not isinstance(fv, type_binding):
            fv = type_binding.Factory(fv)
        fv.toDOM(bds, root, element_name=p.name)

# Finish the request message and get it as a DOM document.
dom = bds.finalize()

# We don't have a facility to add DOM values (as opposed to binding
# instances) to a soap binding instance, so just directly generate the
# message by wedging the request into a generic SOAP envelope body.
soap_message = '''<?xml version="1.0" encoding="ISO-8859-1"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
  <SOAP-ENV:Body>''' + dom.documentElement.toxml("utf-8") + '''</SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''

#soap_message = open('NDFDgen.xml').read()
#soap_message = open('test.xml').read()
# Save the request message so it can be examined later
open('req.xml', 'w').write(soap_message)

# Pull the SOAPAction and endpoint out of the WSDL spec.  This is gross.
spec_ns = spec.namespaceContext().targetNamespace()
binding = spec_ns.createExpandedName('ndfdXMLBinding').binding()
operation = binding.operationMap()['NDFDgen']
soap_op = operation.wildcardElements()[0]
soap_action = soap_op.soapAction

service = spec_ns.createExpandedName('ndfdXML').service()
soap_addr = service.port[0].wildcardElements()[0]
endpoint = soap_addr.location

# Execute the request
uri = urllib_request.Request(endpoint,
                      soap_message,
                      { 'SOAPAction' : soap_action, 'Content-Type': 'text/xml' } )
rxml = urllib_request.urlopen(uri).read()
#rxml = open('rawresp.xml').read()

# Save the raw SOAP-wrapped response
open('rawresp.xml', 'w').write(rxml)

# The NDFD interface is "interesting" in that the response message for
# the SOAP interface is encoded as a text string, rather than being
# provided as XML directly.  The noise below extracts it.
rdom = domutils.StringToDOM(rxml)
resp = soapenv.CreateFromDOM(rdom)
v = resp.Body.wildcardElements()[0]
rxml = v.childNodes[0].childNodes[0].value
# Save the extracted response
open('resp.xml', 'w').write(rxml)
#rxml = open('resp.xml').read()

# Create the binding instance from the response.  If there's a
# problem, diagnose the issue, then try again with validation
# disabled.
r = None
try:
    r = DWML.CreateFromDocument(rxml)
except pyxb.UnrecognizedContentError as e:
    print('*** ERROR validating response:')
    print(e.details())
if r is None:
    pyxb.RequireValidWhenParsing(False)
    r = DWML.CreateFromDocument(rxml)

# Start spitting out the processed data.
product = r.head.product
print('%s %s' % (product.title, product.category))
source = r.head.source
print(", ".join(source.production_center.content()))
data = r.data[0]

for i in range(len(data.location)):
    loc = data.location[i]
    print('%s [%s %s]' % (loc.location_key, loc.point.latitude, loc.point.longitude))
    for p in data.parameters:
        if p.applicable_location != loc.location_key:
            continue
        mint = maxt = None
        for t in p.temperature:
            if 'maximum' == t.type:
                maxt = t
            elif 'minimum' == t.type:
                mint = t
            print('%s (%s): %s' % (t.name, t.units, " ".join([ str(_v.value()) for _v in t.value_ ])))
        time_layout = None
        for tl in data.time_layout:
            if tl.layout_key == mint.time_layout:
                time_layout = tl
                break
        for ti in range(len(time_layout.start_valid_time)):
            start = time_layout.start_valid_time[ti].value()
            end = time_layout.end_valid_time[ti]
            print('%s: min %s, max %s' % (time.strftime('%A, %B %d %Y', start.timetuple()),
                                          mint.value_[ti].value(), maxt.value_[ti].value()))
