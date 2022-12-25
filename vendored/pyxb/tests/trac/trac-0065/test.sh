#!/bin/bash
#
# Test assorted issues related to module prefix with raw and binding root options

test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

rm -rf Schemata RawSchemata TestPrefix RawTestPrefix
pyxbgen -m TestSchema -u TestSchema.xsd --module-prefix=TestPrefix || fail "No raw, no custom: generation error"
grep -q 'Alma/APDMTest/ObsProject' TestPrefix/TestSchema.py || fail "No raw, no custom: content error"
test -f TestPrefix/__init__.py || fail "No raw, no custom: missing init"
echo "No raw, no custom passed"

pyxbgen -m TestSchema -u TestSchema.xsd --module-prefix=RawTestPrefix --write-for-customization || fail "No raw, with custom: generation error"
test -f RawTestPrefix/__init__.py || fail "No raw, with custom: missing init"
test -f RawTestPrefix/raw/__init__.py || fail "No raw, with custom: missing init"
grep -q 'Alma/APDMTest/ObsProject' RawTestPrefix/raw/TestSchema.py || fail "No raw, with custom: content error"
grep 'from RawTestPrefix.raw.TestSchema import' RawTestPrefix/TestSchema.py || fail "No raw, with custom: wrapper content error"
echo "No raw, with custom passed"

pyxbgen -m TestSchema -u TestSchema.xsd --module-prefix=TestPrefix --binding-root=Schemata || fail "Raw, no custom: generation error"
test -f Schemata/__init__.py && fail "Raw, no custom: unexpected init at binding root"
test -f Schemata/TestPrefix/__init__.py || fail "Raw, no custom: missing init"
grep -q 'Alma/APDMTest/ObsProject' Schemata/TestPrefix/TestSchema.py || fail "No raw, no custom: content error"
echo "Raw, no custom passed"

pyxbgen -m TestSchema -u TestSchema.xsd --module-prefix=TestPrefix --binding-root=RawSchemata --write-for-customization || fail "Raw, with custom: generation error"
test -f RawSchemata/__init__.py && fail "Raw, with custom: unexpected init at binding root"
test -f RawSchemata/TestPrefix/__init__.py || fail "Raw, with custom: missing custom init"
test -f RawSchemata/TestPrefix/raw/__init__.py || fail "Raw, with custom: missing raw init"
grep -q 'Alma/APDMTest/ObsProject' RawSchemata/TestPrefix/raw/TestSchema.py || fail "No raw, with custom: content error"
grep 'from TestPrefix.raw.TestSchema import' RawSchemata/TestPrefix/TestSchema.py || fail "No raw, with custom: wrapper content error"
echo "Raw, with custom passed"
