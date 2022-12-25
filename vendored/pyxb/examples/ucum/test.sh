pyxbgen \
  -u ucum-essence.xsd \
  -m ucum
if [ ! -f ucum-essence.xml ] ; then
    wget http://unitsofmeasure.org/ucum-essence.xml
fi

# This allows this script to run under the autotest environment, where
# output is sent to a file.
export PYTHONIOENCODING='utf-8'

python showunits.py
