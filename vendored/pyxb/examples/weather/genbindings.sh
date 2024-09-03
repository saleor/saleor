WSDL_URI='http://ws.cdyne.com/WeatherWS/Weather.asmx?wsdl'
WSDL_URI='http://wsf.cdyne.com/WeatherWS/Weather.asmx?WSDL'
wget -O weather.wsdl "${WSDL_URI}"
pyxbgen \
   --wsdl-location="${WSDL_URI}" --module=weather \
   --write-for-customization \
 || ( echo "Failed to generate bindings" ; exit 1 )
