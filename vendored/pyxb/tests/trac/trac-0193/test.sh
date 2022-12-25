test_name=trac/193

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

pyxbgen \
  -m trac193 -u schema.xsd \
|| fail schema generation
python check.py || fail subclass relationship
echo ${test_name} passed
