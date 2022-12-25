test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

URI='http://www.accellera.org/XMLSchema/SPIRIT/1685-2009/index.xsd'
if [ -d uriArchive ] ; then
  echo "${test_name}: building from local cache"
  pyxbgen \
   -u index.xsd \
   --schema-root=uriArchive \
   -m spirit \
  || fail unable to generate bindings from local cache
else
  echo "${test_name}: retrieving schema"
  pyxbgen \
   -u "${URI}" \
   -m spirit \
   --uri-content-archive-directory=uriArchive \
  || fail unable to generate bindings through download
fi

python check.py || fail check failed

echo ${test_name} passed
