test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -f trac169.* pyxbgen.log
pyxbgen \
   --logging-config-file=logging.cfg \
   -u root.xsd -m trac169
grep -q 'WARNING Skipping apparent redundant inclusion' pyxbgen.log || fail Did not produce warning
python check.py
