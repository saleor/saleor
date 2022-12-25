test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

pyxbgen -u sample.xsd -m sample || fail unable to generate bindings
python check.py || fail check failed
echo ${test_name} passed
