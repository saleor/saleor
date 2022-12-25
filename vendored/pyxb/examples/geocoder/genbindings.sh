GEO_WSDL_URI='http://geocoder.us/dist/eg/clients/GeoCoder.wsdl'
GEO_PREFIX=GeoCoder
GEO_WSDL="${GEO_PREFIX}.wsdl"

if [ ! -f ${GEO_WSDL} ] ; then
  wget -O ${GEO_WSDL} "${GEO_WSDL_URI}"
  patch -p0 < ${GEO_WSDL}-patch
fi

rm -rf raw

pyxbgen \
  --wsdl-location=${GEO_WSDL} \
  --module=${GEO_PREFIX} \
  --write-for-customization \
  --archive-path=${PYXB_ROOT}/pyxb/bundles/wssplat//:+
