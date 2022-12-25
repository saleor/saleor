find pyxb/bundles -name __init__.py \
 | sed -e 's@^@"@' -e 's@/[^/]*$@",@' -e 's@/@.@g' \
 | fmt


find pyxb/bundles -name '*.wxs' \
 > /tmp/x$$
cat /tmp/x$$ \
 | sed -e 's@/[^/]*$@@' \
 | sort \
 | uniq \
 > /tmp/y$$

for f in `cat /tmp/y$$` ; do
  echo -n `echo "'${f}'" | sed -e 's@/@.@g'`
  echo ' : ['
  grep "^${f}" /tmp/x$$ \
    | sed -e 's@^.*/\([^/]*\)$@\1@' \
    | sed -e 's@^@"@' -e 's@$@",@' \
    | fmt
  echo '],'
done
rm -f /tmp/x$$ /tmp/y$$
