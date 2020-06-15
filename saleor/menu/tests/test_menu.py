from ..models import MenuItem


def test_menu_item_status(menu, category, collection, page):
    item = MenuItem.objects.create(name="Name", menu=menu)
    assert item.is_public()

    item = MenuItem.objects.create(name="Name", menu=menu, collection=collection)
    assert item.is_public()
    collection.is_published = False
    collection.save()
    item.refresh_from_db()
    assert not item.is_public()

    item = MenuItem.objects.create(name="Name", menu=menu, category=category)
    assert item.is_public()

    item = MenuItem.objects.create(name="Name", menu=menu, page=page)
    assert item.is_public()
    page.is_published = False
    page.save()
    item.refresh_from_db()
    assert not item.is_public()
