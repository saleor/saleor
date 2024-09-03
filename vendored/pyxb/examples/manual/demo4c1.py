from __future__ import print_function
import pyxb
import po4
import address
import pyxb.binding.datatypes as xs

po = po4.purchaseOrder(orderDate=xs.date(1999, 10, 20))
po.shipTo = address.USAddress('Alice Smith', '123 Maple Street', 'Anytown', 'AK', 12341)
po.billTo = address.USAddress('Robert Smith', '8 Oak Avenue', 'Anytown', 'AK', 12341)
po.items = pyxb.BIND(pyxb.BIND('Lapis necklace', 1, 99.95, partNum='833-AA'),
                     pyxb.BIND('Plastic necklace', 4, 3.95, partNum='833-AB'))

print(po.toxml("utf-8"))
