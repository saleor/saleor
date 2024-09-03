#!/bin/sh

test_name=trac/183

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -f root.py branch1.py branch2.py

pyxbgen \
    -u root.xsd -m root \
    -u branch1.xsd -m branch1 \
    -u branch2.xsd -m branch2 \
|| fail translation failed

python check.py || fail binding validation failed

echo 1>&2 "${test_name} passed"
