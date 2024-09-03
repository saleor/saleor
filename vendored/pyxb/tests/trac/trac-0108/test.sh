rm -f TestPatternRestriction.py
pyxbgen -u TestPatternRestriction.xsd -m TestPatternRestriction \
 && python check.py \
 && echo "trac108 passed" \
|| ( echo "trac108 FAILED" ; exit 1)
