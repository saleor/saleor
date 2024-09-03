from __future__ import print_function
import xml.dom.minidom
import DWML
import datetime
import pyxb.binding.datatypes as xsd
from pyxb.utils.six.moves.urllib.request import urlopen
import time
import collections
import sys

# Get the next seven days forecast for two locations
zip = [ 85711, 55108 ]
if 1 < len(sys.argv):
    zip = sys.argv[1:]
begin = xsd.dateTime.today()
end = xsd.dateTime(begin + datetime.timedelta(7))

# Create the REST URI for this query
uri = 'http://www.weather.gov/forecasts/xml/sample_products/browser_interface/ndfdXMLclient.php?zipCodeList=%s&product=time-series&begin=%s&end=%s&maxt=maxt&mint=mint' % ("+".join([ str(_zc) for _zc in zip ]), begin.xsdLiteral(), end.xsdLiteral())
print(uri)

# Retrieve the data
xmld = urlopen(uri).read()
open('forecast.xml', 'wb').write(xmld)
#print xmld

# Convert it to  DWML object
r = DWML.CreateFromDocument(xmld)

product = r.head.product
print('%s %s' % (product.title, product.category))
source = r.head.source
print(", ".join(source.production_center.content()))
data = r.data
if isinstance(data, collections.MutableSequence):
    data = data.pop(0)
print(data)

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
            print('%s (%s): %s' % (t.name[0], t.units, " ".join([ str(_v) for _v in t.content() ])))
        # Sometimes the service doesn't provide the same number of
        # data points for min and max
        mint_time_layout = maxt_time_layout = None
        for tl in data.time_layout:
            if tl.layout_key == mint.time_layout:
                mint_time_layout = tl
            if tl.layout_key == maxt.time_layout:
                maxt_time_layout = tl
        for ti in range(min(len(mint_time_layout.start_valid_time), len(maxt_time_layout.start_valid_time))):
            start = mint_time_layout.start_valid_time[ti].value()
            end = mint_time_layout.end_valid_time[ti]
            print('%s: min %s, max %s' % (time.strftime('%A, %B %d %Y', start.timetuple()),
                                          mint.value_[ti].value(), maxt.value_[ti].value()))
