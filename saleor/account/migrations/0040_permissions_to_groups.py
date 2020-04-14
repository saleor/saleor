from collections import namedtuple

from django.db import migrations


def add_users_to_groups_based_on_users_permissions(apps, schema_editor):
    """Add every user to group with "user_permissions" if exists, else create new one.

    For every user, iff group with exact scope of permissions exists, add user to it,
    else create new group with this scope of permissions and add user to it.
    """
    User = apps.get_model("account", "User")
    Group = apps.get_model("auth", "Group")

    groups = Group.objects.all().prefetch_related("permissions")
    GroupData = namedtuple("GroupData", ["users", "group_name"])

    mapping = create_permissions_mapping(User, GroupData)
    for perms, group_data in mapping.items():
        group = get_group_with_given_permissions(perms, groups)
        users = group_data.users
        if group:
            group.user_set.add(*users)
            continue
        group = create_group_with_given_permissions(perms, group_data.group_name, Group)
        group.user_set.add(*users)


def create_permissions_mapping(User, GroupData):
    """Create mapping permissions to users and potential new group name."""
    mapping = {}
    users = User.objects.filter(user_permissions__isnull=False).prefetch_related(
        "user_permissions"
    )
    for user in users:
        permissions = user.user_permissions.all()
        perm_pks = tuple(permissions.values_list("pk", flat=True))
        if perm_pks not in mapping:
            group_name = create_group_name(permissions)
            mapping[perm_pks] = GroupData({user.pk}, group_name)
        else:
            mapping[perm_pks].users.add(user.pk)
        user.user_permissions.clear()
    return mapping


def create_group_name(permissions):
    """Create group name based on permissions."""
    perm_names = permissions.values_list("name", flat=True)
    formatted_names = [name.rstrip(".").lower() for name in perm_names]
    group_name = ", ".join(formatted_names).capitalize()
    return group_name


def get_group_with_given_permissions(permissions, groups):
    """Get group with given set of permissions."""
    for group in groups:
        group_perm_pks = {perm.pk for perm in group.permissions.all()}
        if group_perm_pks == set(permissions):
            return group


def create_group_with_given_permissions(perm_pks, group_name, Group):
    """Create new group with given set of permissions."""
    group = Group.objects.create(name=group_name)
    group.permissions.add(*perm_pks)
    return group


class Migration(migrations.Migration):

    dependencies = [
        ("account", "0039_auto_20200221_0257"),
    ]
    operations = [
        migrations.RunPython(
            add_users_to_groups_based_on_users_permissions, migrations.RunPython.noop
        ),
    ]
