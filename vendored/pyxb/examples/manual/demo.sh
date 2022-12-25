rm -f *.wxs po?.py *.pyc
sh demo1.sh \
 && python demo1.py > demo1.out \
 && cat demo1.out
sh demo2.sh \
 && python demo2.py
sh demo3a.sh \
 && python demo3.py
sh demo3b.sh \
 && python demo3.py
sh demo3c.sh \
 && sh demo3d.sh \
 && python demo3.py
sh demo4.sh
python demo4a.py > demo4a.out
python demo4a1.py > demo4a1.out 2>&1
python demo4a2.py > demo4a2.out
python demo4c.py | xmllint --format - > demo4c.out
python demo4c1.py | xmllint --format - > demo4c1.out
python demo4c2.py | xmllint --format - > demo4c2.out
python demo4c3.py | xmllint --format - > demo4c3.out
python badcontent.py > badcontent.out
