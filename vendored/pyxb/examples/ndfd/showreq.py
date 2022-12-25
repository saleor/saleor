from __future__ import print_function
import xml.dom
import xml.dom.minidom
import pyxb.utils.domutils
from pyxb.utils import six
import pyxb.namespace

# Structure
#import DWML
#print 'Validating DWML'
#DWML.Namespace.validateSchema()
#print 'Validated DWML: types %s' % ("\n".join(six.iterkeys(DWML.Namespace.typeDefinitions()),)

dom = xml.dom.minidom.parse(open('NDFDgen.xml', 'rb'))
body_dom = dom.documentElement.firstChild.nextSibling.firstChild.nextSibling
print(body_dom)

# Service interface types
import ndfd

# WSDL
import pyxb.bundles.wssplat.wsdl11 as wsdl

uri_src = open('ndfdXML.wsdl')
doc = xml.dom.minidom.parse(uri_src)
spec = wsdl.definitions.createFromDOM(doc.documentElement, process_schema=True)

binding = spec.binding[0]
print(binding.name)
port_type = spec.portType[0]
print(port_type.name)
bop = binding.operationMap()[body_dom.localName]
print(bop.toxml("utf-8"))
pop = port_type.operationMap()[body_dom.localName]
print(pop.toxml("utf-8"))
input = pop.input
print(input.toxml("utf-8"))
print(type(input))
print(input.message)
im_en = input.message
print(im_en)
msg = im_en.message()
print(msg)
for p in msg.part:
    print(p.toxml("utf-8"))
msg_ns = pyxb.namespace.NamespaceForURI(body_dom.namespaceURI)
print('%s %s' % (body_dom.namespaceURI, msg_ns))

parts = msg.part
nodes = body_dom.childNodes

while parts and nodes:
    p = parts.pop(0)
    while nodes and (not (xml.dom.Node.ELEMENT_NODE == nodes[0].nodeType)):
        nodes.pop(0)
    assert nodes
    n = nodes.pop(0)
    if p.name != n.localName:
        print('Desynchronized: part %s expected node %s' % (p.name, n.localName))
        nodes.insert(0, n)
        continue
    print('%s %s' % (p.name, n.localName))

#print '%s yielded %s' msg_ns

#msg = spec.messageMap()
#print msg

#print req
#dom_support =  req.toDOM(pyxb.utils.domutils.BindingDOMSupport())
#dom_support.finalize()
#print dom_support.document().toxml("utf-8")
