
test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

pyxbgen \
    -u http://www.aixm.aero/gallery/content/public/schema/5.0/ISO_19136_Schemas/ \
    -u b.xsd -m b \
    > test.err 2>&1 \
 && fail 'Successfully translated'

( tail -1 test.err | grep SchemaValidationError >/dev/null ) || fail 'Did not produce validation error'
echo 'Received expected validation error, passed'
