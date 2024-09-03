fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

for sample in good*.xml ; do
  xmllint --schema example.xsd ${sample}
  if [ 0 -ne $? ] ; then
    echo 1>&2 "FAIL : ${sample} should have validated"
  fi
done

for sample in bad*.xml ; do
  xmllint --schema example.xsd ${sample}
  if [ 0 -eq $? ] ; then
    echo 1>&2 "FAIL : ${sample} should NOT have validated"
  fi
done

rm -f example.py
pyxbgen -u example.xsd -m example || fail 'Unable to generate'
echo 'Successfully generated, passed'
