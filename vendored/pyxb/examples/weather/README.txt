A free weather service at http://ws.cdyne.com/WeatherWS/Weather.asmx

Use genbindings.sh to retrieve the wsdl and generate the bindings for the
schema used in it.

Use client.py to retrieve the forecast for a given zip code.

Note the various misspellings in the schema (e.g., "Desciption").  The
weather information in this service does not get updated often, and for some
locations has bogus dates.
