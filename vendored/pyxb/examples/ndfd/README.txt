Interact with the National Digital Forecast Database (http://www.nws.noaa.gov/xml)

Use the genbindings.sh script to retrieve the schema for Digital Weather
Markup Language and generate the bindings.  (Note that the schema has two
levels of include directives, which PyXB follows.)

Use forecast.py to get the forecast temperature data for two locations, and
print it in several ways.  The sole inconvenience with the Python data
structures is the need to dereference the element content when comparing
complex elements with simple types with strings.  (This example uses the
REST interface rather than the SOAP one, just b'cuz.)

The showreq.py script is an in-progress playground for parsing the example
query, mostly showing how to pair messages with DOM elements.
