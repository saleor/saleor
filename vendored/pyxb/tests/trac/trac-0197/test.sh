test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -f *.wxs X.py s.py

pyxbgen --archive-to-file X.wxs -m X -u X.xsd || fail unable to generate included schema
pyxbgen --archive-path .:+ -m s -u s.xsd || fail unable to generate including schema
python s.py || fail unable to load generated binding
echo ${test_name} passed
