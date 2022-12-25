test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -f poc.py*
pyxbgen -u poc.xsd -m poc || fail unable to generate binding
python pocSample.py || fail could not process sample
echo trac/133 passed
