from __future__ import print_function
import sys
import time
from pyxb.utils.six.moves.urllib import request as urllib_request
import pyxb.bundles.wssplat.soap11 as soapenv
import weather

zip = 55113
if 1 < len(sys.argv):
    zip = int(sys.argv[1])

# Create an envelope, and give it a body that is the request for the
# service we want.
env = soapenv.Envelope(soapenv.Body(weather.GetCityForecastByZIP(ZIP=str(zip))))
open('request.xml', 'w').write(env.toxml("utf-8"))

# Invoke the service
uri = urllib_request.Request('http://wsf.cdyne.com/WeatherWS/Weather.asmx',
                             env.toxml("utf-8"),
                             { 'SOAPAction' : "http://ws.cdyne.com/WeatherWS/GetCityForecastByZIP", 'Content-Type': 'text/xml' } )
rxml = urllib_request.urlopen(uri).read()
open('response.xml', 'w').write(rxml)

# Convert the response to a SOAP envelope, then extract the actual
# response from the wildcard elements of the body.  Note that because
# the weather namespace was registered, PyXB already created the
# binding for the response.
soap_resp = soapenv.CreateFromDocument(rxml)
resp = soap_resp.Body.wildcardElements()[0]

fc_return = resp.GetCityForecastByZIPResult
if fc_return.Success:
    print('Got response for %s, %s:' % (fc_return.City, fc_return.State))
    for fc in fc_return.ForecastResult.Forecast:
        when = time.strftime('%A, %B %d %Y', fc.Date.timetuple())
        outlook = fc.Desciption # typos in WSDL left unchanged
        low = fc.Temperatures.MorningLow
        high = fc.Temperatures.DaytimeHigh
        print('  %s: %s, from %s to %s' % (when, outlook, low, high))
