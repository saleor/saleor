test_name=${0}

fail () {
  echo 1>&2 "${test_name} FAILED: ${@}"
  exit 1
}

expand () {
  v=$1 ; shift
  if [ "${v}" = "q" ] ; then
    echo "qualified"
  elif [ "${v}" = "u" ] ; then
    echo "unqualified"
  else
    exit 1
  fi
}

rm -f *.wxs *.pyc
for ea in qq qu uq uu ; do
  eax="${ea}0196"
  e=$(echo ${ea} | cut -c1)
  a=$(echo ${ea} | cut -c2)
  E=$(expand "$e")
  A=$(expand "$a")
  cat template.xsd \
    | sed \
        -e "s/@ea@/${ea}/g" \
        -e "s/@a@/${a}/g" -e "s/@A@/${A}/g" \
        -e "s/@e@/${e}/g" -e "s/@E@/${E}/g" \
    > ${eax}.xsd
  rm -f ${eax}.py
  pyxbgen --archive-to-file=${eax}.wxs -m ${eax} -u ${eax}.xsd || fail generating ${ea}
done
pyxbgen --archive-path .:+ -m mix -u mix.xsd || fail generating mix

python check.py || fail validating forms
echo ${test_name} passed
