pyxbgen -u example.xsd -m example

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

python tryit.py || fail 'Unable to read generated code'
echo 'Successfully read code, passed'
