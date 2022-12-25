rm -f noi.py nois.py *.pyc

pyxbgen -u namespace_other_issue.xsd -m noi

# We don't use this namespace within pyxb
# pyxbgen -u namespace_other_issue_support.xsd -m nois

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

python check.py || fail trac0114
echo 'trac0114 passed'
