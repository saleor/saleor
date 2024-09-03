URI='http://docs.tms.tribune.com/tech/xml/schemas/tmsxtvd.xsd'
PREFIX='tmstvd'

rm -rf raw
mkdir -p raw
touch raw/__init__.py
pyxbgen \
   -m "${PREFIX}" \
   -u "${URI}" \
   -r
if [ ! -f ${PREFIX}.py ] ; then
  echo "from raw.${PREFIX} import *" > ${PREFIX}.py
fi

if [ ! -f tmsdatadirect_sample.xml ] ; then
  wget http://tmsdatadirect.com/docs/tv/tmsdatadirect_sample.xml
fi
