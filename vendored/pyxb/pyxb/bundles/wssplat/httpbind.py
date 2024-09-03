from pyxb.bundles.wssplat.raw.httpbind import *
import pyxb.bundles.wssplat.raw.httpbind as raw_httpbind
from pyxb.bundles.wssplat.wsdl11 import _WSDL_binding_mixin, _WSDL_port_mixin, _WSDL_operation_mixin

class bindingType (raw_httpbind.bindingType, _WSDL_binding_mixin):
    pass
raw_httpbind.bindingType._SetSupersedingClass(bindingType)

class addressType (raw_httpbind.addressType, _WSDL_port_mixin):
    pass
raw_httpbind.addressType._SetSupersedingClass(addressType)

class operationType (raw_httpbind.operationType, _WSDL_operation_mixin):
    def locationInformation (self):
        return self.location()
raw_httpbind.operationType._SetSupersedingClass(operationType)
