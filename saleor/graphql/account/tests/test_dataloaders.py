from ....account.models import Group
from ...context import SaleorContext
from ..dataloaders import AddressesByUserIdLoader, PermissionGroupsByUserIdLoader


def test_addresses_by_user_id_loader_batches_users(
    customer_user,
    customer_user2,
    address,
    django_assert_num_queries,
):
    # given
    second_address = address.get_copy()
    customer_user.addresses.add(address)
    customer_user2.addresses.add(second_address)
    customer_user.default_shipping_address = address
    customer_user.save(update_fields=["default_shipping_address"])
    customer_user2.default_billing_address = second_address
    customer_user2.save(update_fields=["default_billing_address"])
    expected_address_ids = [
        list(customer_user.addresses.order_by("pk").values_list("pk", flat=True)),
        list(customer_user2.addresses.order_by("pk").values_list("pk", flat=True)),
    ]
    keys = [
        (
            customer_user.id,
            customer_user.default_shipping_address_id,
            customer_user.default_billing_address_id,
        ),
        (
            customer_user2.id,
            customer_user2.default_shipping_address_id,
            customer_user2.default_billing_address_id,
        ),
    ]
    loader = AddressesByUserIdLoader(SaleorContext())

    # when
    with django_assert_num_queries(2):
        result = loader.batch_load(keys)

    # then
    assert [
        [item.id for item in addresses] for addresses in result
    ] == expected_address_ids
    first_default = next(item for item in result[0] if item.id == address.id)
    second_default = next(item for item in result[1] if item.id == second_address.id)
    assert first_default.user_default_shipping_address_pk == address.id
    assert (
        first_default.user_default_billing_address_pk
        == customer_user.default_billing_address_id
    )
    assert (
        second_default.user_default_shipping_address_pk
        == customer_user2.default_shipping_address_id
    )
    assert second_default.user_default_billing_address_pk == second_address.id


def test_permission_groups_by_user_id_loader_batches_users(
    customer_user,
    customer_user2,
    django_assert_num_queries,
):
    # given
    first_group = Group.objects.create(name="First group")
    second_group = Group.objects.create(name="Second group")
    customer_user.groups.add(first_group)
    customer_user2.groups.add(first_group, second_group)
    loader = PermissionGroupsByUserIdLoader(SaleorContext())

    # when
    with django_assert_num_queries(2):
        result = loader.batch_load([customer_user.id, customer_user2.id])

    # then
    assert [[group.id for group in groups] for groups in result] == [
        [first_group.id],
        [first_group.id, second_group.id],
    ]
