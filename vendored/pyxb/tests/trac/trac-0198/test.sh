test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -f *.wxs wsu.py wsse.py top.py
pyxbgen --archive-to-file wsu.wxs -m wsu -u wsu.xsd || fail unable to build wsu bindings
pyxbgen --archive-path .:+  -m wsse -u wsse.xsd || fail unable to build wsse bindings
python check.py || fail check failed
echo ${test_name} passed
