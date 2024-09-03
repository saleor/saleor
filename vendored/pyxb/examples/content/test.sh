rm -f content.py
pyxbgen \
   -u content.xsd -m content \
 && python showcontent.py > showcontent.out \
 && cat showcontent.out
