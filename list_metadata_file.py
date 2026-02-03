
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from saleor.product.models import Category, ProductType
from saleor.warehouse.models import Warehouse
from saleor.channel.models import Channel

def list_data():
    with open("metadata_output.txt", "w") as f:
        f.write("CATEGORIES:\n")
        for c in Category.objects.all():
            f.write(f"  {c.name} ({c.slug}) - ID: {c.id}\n")
        
        f.write("\nPRODUCT TYPES:\n")
        for pt in ProductType.objects.all():
            f.write(f"  {pt.name} ({pt.slug}) - ID: {pt.id}\n")
            
        f.write("\nWAREHOUSES:\n")
        for w in Warehouse.objects.all():
            f.write(f"  {w.name} - ID: {w.id}\n")
            
        f.write("\nCHANNELS:\n")
        for ch in Channel.objects.all():
            f.write(f"  {ch.name} ({ch.slug}) - ID: {ch.id}\n")

if __name__ == "__main__":
    list_data()
