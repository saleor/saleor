#!/bin/sh

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

xmllint --schema custom.xsd test.xml || fail Test document is not valid

rm -rf raw *.pyc
pyxbgen \
    -m custom \
    -u custom.xsd \
    --write-for-customization
python tst-normal.py || fail Normal customization failed
python tst-introspect.py || fail Introspection customization failed
