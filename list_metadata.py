
from saleor.product.models import Category, ProductType, Product, ProductVariant
from saleor.warehouse.models import Warehouse
from saleor.channel.models import Channel

def list_data():
    print("CATEGORIES:")
    for c in Category.objects.all():
        print(f"  {c.name} ({c.slug}) - ID: {c.id}")
    
    print("\nPRODUCT TYPES:")
    for pt in ProductType.objects.all():
        print(f"  {pt.name} ({pt.slug}) - ID: {pt.id}")
        
    print("\nWAREHOUSES:")
    for w in Warehouse.objects.all():
        print(f"  {w.name} - ID: {w.id}")
        
    print("\nCHANNELS:")
    for ch in Channel.objects.all():
        print(f"  {ch.name} ({ch.slug}) - ID: {ch.id}")

if __name__ == "__main__":
    list_data()
