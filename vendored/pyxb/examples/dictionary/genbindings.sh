URI='http://services.aonaware.com/DictService/DictService.asmx?WSDL'
PREFIX='dict'
WSDL="${PREFIX}.wsdl"
if [ ! -f ${WSDL} ] ; then
  wget -O ${WSDL} "${URI}"
fi

rm -rf raw
mkdir -p raw
touch raw/__init__.py
pyxbgen \
   --wsdl-location="${WSDL}" \
   --module="${PREFIX}" \
   --write-for-customization
if [ ! -f ${PREFIX}.py ] ; then
  echo "from raw.${PREFIX} import *" > ${PREFIX}.py
fi
