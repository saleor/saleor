#  PYTHONPATH=../..:. PYXB_ARCHIVE_PATH=opengis/iso19139:+ ../../scripts/pyxbgen -u gmlapp.xsd -m gmlapp

from __future__ import print_function
import pyxb.bundles.opengis.gml_3_2 as gml
import gmlapp
import pyxb.utils.domutils

limits = gml.GridLimitsType(gml.GridEnvelopeType([0, 0], [4, 4]))
origin = gml.PointPropertyType(gml.Point(gml.pos([-93.25, 43.5]), id='_origin'))
offset_vector = gml.VectorType([0, 0])
grid = gml.RectifiedGrid(limits, 'latitude longitude', origin, offset_vector, dimension=2)
grid.id = '_%x' % id(grid)
domain = gml.domainSet(grid)

val_template = gmlapp.Temperature(nilReason='template', _nil=True, uom='urn:x-si:v1999:uom:degreesC')
cv = gml.CompositeValue(gml.valueComponents(AbstractValue=[val_template]))
cv.id = '_%s' % (id(cv),)
data = gml.tupleList('34.2 35.4')
range = gml.rangeSet(DataBlock=gml.DataBlockType(gml.rangeParameters(cv), data))

rgc = gml.RectifiedGridCoverage(domain, range)
rgc.id = '_%x' % (id(rgc),)

bds = pyxb.utils.domutils.BindingDOMSupport(namespace_prefix_map={ gml.Namespace : 'gml' , gmlapp.Namespace : 'app' })

xml = rgc.toxml("utf-8", bds=bds)
instance = gml.CreateFromDocument(xml)
bds.reset()
xml2 = instance.toxml("utf-8", bds=bds)

assert xml == xml2
print(xml2)
