def test_discarded_filter_result():
    """Missing `qs =` => should flag it."""
    qs = Product.objects.all()

    # ruleid: django-queryset-filter-without-assignment
    qs.filter(pk=1)


def test_assigned_filter_result():
    """Properly assign `qs = ...` shouldn't be flagged."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    qs = qs.filter(pk=1)


def test_filter_result_passed_to_function():
    """When queryset is passed to a function, it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    my_function(qs.filter(pk=1))


def test_filter_result_returned():
    """When returning the new queryset it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    return qs.filter(pk=1)


def test_filter_result_deleted():
    """When deleting a queryset it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    qs.filter(pk=1).delete()


def test_filter_result_updated():
    """When updating a queryset it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    qs.filter(pk=1).update(name="Updated product")


def test_filter_result_checked_for_existence():
    """When checking for existance it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    qs.filter(pk=1).exists()


def test_filter_result_first():
    """When retrieving the 1st row of a queryset it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    qs.filter(pk=1).first()


def test_filter_result_iterated():
    """When iterating a queryset it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    for product in qs.filter(pk=1):
        product.save()


def test_filter_result_iterated_through_iterator():
    """When using iterator() it shouldn't match in a loop."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    for product in qs.filter(pk=1).iterator():
        product.save()


def test_filter_result_used_as_condition():
    """When filtering in an `if` condition, it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    if qs.filter(pk=1):
        return


def test_filter_result_used_in_boolean_condition():
    """When filtering in AND/OR clauses, it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    if flag and qs.filter(pk=1):
        return

    # ok: django-queryset-filter-without-assignment
    if qs.filter(pk=1) and flag:
        return

    # ok: django-queryset-filter-without-assignment
    if flag or qs.filter(pk=1):
        return

    # ok: django-queryset-filter-without-assignment
    if qs.filter(pk=1) or flag:
        return


def test_filter_result_used_in_while_condition():
    """When filtering in a `while` condition, it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    while qs.filter(pk=1):
        break

    # ok: django-queryset-filter-without-assignment
    while not qs.filter(pk=1):
        break


def test_filter_result_asserted():
    """When asserting the queryset's truthiness, it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    assert qs.filter(pk=1)


def test_filter_result_used_in_augmented_assignment():
    """When updating a queryset using `ior` assignment it shouldn't match."""
    qs = Product.objects.all()
    query_objects = Q()

    # ok: django-queryset-filter-without-assignment
    query_objects |= qs.filter(pk=1)


def test_filter_result_indexed():
    """When retrieving a specific item it shouldn't match."""
    qs = Product.objects.all()

    # ok: django-queryset-filter-without-assignment
    qs.filter(pk=1)[0]
