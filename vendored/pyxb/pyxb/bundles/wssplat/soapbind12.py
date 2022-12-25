from pyxb.bundles.wssplat.raw.soapbind12 import *
import pyxb.bundles.wssplat.raw.soapbind12 as raw_soapbind12
from pyxb.bundles.wssplat.wsdl11 import _WSDL_binding_mixin, _WSDL_port_mixin, _WSDL_operation_mixin

class tBinding (raw_soapbind12.tBinding, _WSDL_binding_mixin):
    pass
raw_soapbind12.tBinding._SetSupersedingClass(tBinding)

class tAddress (raw_soapbind12.tAddress, _WSDL_port_mixin):
    pass
raw_soapbind12.tAddress._SetSupersedingClass(tAddress)

class tOperation (raw_soapbind12.tOperation, _WSDL_operation_mixin):
    def __getLocationInformation (self):
        rvl = []
        if self.soapAction is not None:
            rvl.append('action=%s' % (self.soapAction,))
        if self.style is not None:
            rvl.append('style=%s' % (self.style,))
        if self.soapActionRequired:
            rvl.append('REQUIRED')
        return ','.join(rvl)
    locationInformation = property(__getLocationInformation)

raw_soapbind12.tOperation._SetSupersedingClass(tOperation)
