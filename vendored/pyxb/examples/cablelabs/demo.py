from __future__ import print_function
import xml.dom.minidom
import pyxb.utils.domutils
from cablelabs import core, offer, title, vod30
import custom

pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(core.Namespace, 'core')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(offer.Namespace, 'offer')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(title.Namespace, 'title')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(vod30.Namespace, 'vod30')
pyxb.utils.domutils.BindingDOMSupport.DeclareNamespace(custom.Namespace, 'custom')

adi3 = vod30.ADI3()

# Create an instance of ContentGroupType (which extends AssetType). It
# is not associated with an element.
cgt = offer.ContentGroupType()

# The thing we want to use as an extension
venue = custom.Venue('some multiplex')

# Give it an extension value. The Ext element in AssetType contains
# only wildcards; you can put whatever you want into it, but at the
# Ext Python attribute level it will have no structure.  You do need
# an instance of ExtType to hold the content.
ext = core.ExtType(venue)

# You can uncomment this to see what happens if you skip the
# core.ExtType wrapper
#ext = venue

# The assignment of a value to the Ext member is validated.
try:
    cgt.Ext = ext
except pyxb.ValidationError as e:
    print(e.details())
    raise

# Unfortunately cgt with just an Ext element does not validate.  Each
# of the following assignments comes in reaction to the nice error
# messages generated when a ValidationError is raised below.  Try
# commenting each out to see what happens.
cgt.uriId = 'urn:one'
cgt.TitleRef = core.AssetRefType(uriId='urn:aMovie')
cgt.PosterRef.append(core.AssetRefType(uriId='urn:aPoster'))

# Now you can add the instance to the description and convert it to an
# XML document.
adi3.ContentGroup.append(cgt)
try:
    xmls = adi3.toDOM().toprettyxml()
except pyxb.ValidationError as e:
    print(e.details())
    raise

# Show off the pretty document
print(xmls)

# Let's convert it back.  This showed a different misunderstanding of
# the schema too complicated to replicate here.
try:
    instance = core.CreateFromDocument(xmls)
except pyxb.ValidationError as e:
    print(e.details())
    raise

ivenue = instance.ContentGroup[0].Ext.wildcardElements()[0]
assert isinstance(ivenue, type(venue))
# NB: Python 2.6.8 and Python 2.7.3 have whitespace differences in
# text emitted by toprettyxml() which results in failure of
# non-stripped comparison in 2.6.8.
assert ivenue.strip() == venue.strip()

# Since the Ext element holds its content as an unbounded number of
# wildcards, you can just add stuff to it.
cgt.Ext.append(custom.Venue('another location'))
cgt.Ext.append(custom.Venue('and yet another'))

xmls = adi3.toDOM().toprettyxml()
print(xmls)
