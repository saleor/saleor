TEST_URI=http://www.w3.org/People/mimasa/test/xhtml/media-types/test.xhtml

aout="${0}"

fail () {
  echo 1>&2 "${aout} FAILED: ${@}"
  exit 1
}

if [ ! -f in.xhtml ] ; then
  wget -O in.xhtml ${TEST_URI} || fail Unable to retrieve test document
fi
python rewrite.py || fail Unable to rewrite test document

xmllint --format in.xhtml > inf.xhtml
xmllint --format out.xhtml > outf.xhtml
diff -uw inf.xhtml outf.xhtml > deltas

# Need to manually validate that outf.xhtml and in.xhtml are about the
# same.  The rewrite does not preserve the order of attributes in the
# elements.
echo "See deltas for differences"

# Test most primitive generation of documents
rm -f genout.xhtml
python generate.py \
  && diff expout.xhtml genout.xhtml \
  || fail generate did not match expected

echo "Passed XHTML tests"
