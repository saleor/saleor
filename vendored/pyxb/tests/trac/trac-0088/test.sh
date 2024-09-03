fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -f example.py
pyxbgen -u example.xsd -m example || fail 'Unable to generate'
echo 'Successfully generated, passed'
