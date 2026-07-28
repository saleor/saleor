# ruff: noqa: T201
"""Idempotent menu items seeder for the AURELLE Cosmetics storefront.

Connects the navbar and footer menus in the local database directly to the seeded
product categories.

Usage:
    python scripts/seed_menus.py
"""

import os
import sys
from pathlib import Path

import django

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

from saleor.menu.models import Menu, MenuItem
from saleor.product.models import Category

AURELLE_CATEGORIES = ["Skincare", "Makeup", "Fragrance", "Hair", "Bath and Body", "Beauty Tools", "Gifts"]

def seed():
    navbar = Menu.objects.filter(slug="navbar").first()
    if not navbar:
        navbar = Menu.objects.create(name="navbar", slug="navbar")
        print("Created navbar menu")

    footer = Menu.objects.filter(slug="footer").first()
    if not footer:
        footer = Menu.objects.create(name="footer", slug="footer")
        print("Created footer menu")

    # Clear existing items
    navbar.items.all().delete()
    footer.items.all().delete()
    print("Cleared existing menu items")

    # Categories to add
    categories = list(Category.objects.filter(name__in=AURELLE_CATEGORIES).order_by("name"))
    print(f"Loaded {len(categories)} AURELLE categories: {[c.name for c in categories]}")

    # Add items to navbar
    for category in categories:
        MenuItem.objects.create(
            menu=navbar,
            name=category.name,
            category=category,
        )
        print(f"Added {category.name} to navbar")

    # Add items to footer
    # 1. Shop column
    shop_root = MenuItem.objects.create(
        menu=footer,
        name="Shop",
    )
    for category in categories:
        MenuItem.objects.create(
            menu=footer,
            parent=shop_root,
            name=category.name,
            category=category,
        )
    print("Added Shop categories to footer column")

    # 2. Company column
    company_root = MenuItem.objects.create(
        menu=footer,
        name="Aurelle",
    )
    MenuItem.objects.create(
        menu=footer,
        parent=company_root,
        name="Our Story",
        url="/pages/about",
    )
    MenuItem.objects.create(
        menu=footer,
        parent=company_root,
        name="Locations",
        url="/pages/store-locator",
    )
    print("Added Company column to footer")

    # 3. Help column
    help_root = MenuItem.objects.create(
        menu=footer,
        name="Support",
    )
    MenuItem.objects.create(
        menu=footer,
        parent=help_root,
        name="Contact Us",
        url="/pages/contact",
    )
    MenuItem.objects.create(
        menu=footer,
        parent=help_root,
        name="Shipping & Returns",
        url="/pages/shipping-returns",
    )
    print("Added Help column to footer")

    print("Menu Seeding complete.")

if __name__ == "__main__":
    seed()
