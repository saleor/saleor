test_name=trac/186

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

pyxbgen \
  --schema-location=8_3_2_resource.xsd --module=resources \
|| fail s1 generation
python check.py || fail validation
echo ${test_name} passed
