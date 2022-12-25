#!/bin/sh

: ${PYXB_TEST_ROOT:=${PYXB_ROOT}/tests}
. ${PYXB_TEST_ROOT}/support.sh

TEST_URI=https://raw.githubusercontent.com/redsteve/EnterpriseArchitect_ReqIF_AddIn/master/EA_ReqIF_AddIn/example.reqif.xml

if [ ! -f in.xml ]; then
  wget -O in.xml ${TEST_URI} || fail retrieving document
fi

PYXB_ARCHIVE_PATH=${PYXB_ROOT}/pyxb/bundles/reqif//:+
export PYXB_ARCHIVE_PATH

python process.py > test.out || fail running
cmp test.out test.expected || fail output comparison
passed
