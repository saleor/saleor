from __future__ import print_function
import po3

order = po3.CreateFromDocument(open('po3.xml').read())

print('%s is sending %s %d thing(s):' % (order.billTo.name, order.shipTo.name, len(order.items.item)))
for item in order.items.item:
    print('  Quantity %d of %s at $%s' % (item.quantity, item.productName, item.USPrice))
