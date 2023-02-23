import re
from collections import defaultdict

from django.db import migrations


def add_users_to_groups_based_on_users_permissions(apps, schema_editor):
    """Add every user to group with "user_permissions" if exists, else create new one.

    For each user, if the group with the exact scope of permissions exists,
    add the user to it, else create a new group with this scope of permissions
    and add the user to it.
    """
    User = apps.get_model("account", "User")
    Group = apps.get_model("auth", "Group")

    groups = Group.objects.all().prefetch_related("permissions")
    counter = get_counter_value(Group)
    mapping = create_permissions_mapping(User)
    for perms, users in mapping.items():
        group = get_group_with_given_permissions(perms, groups)
        if group:
            group.user_set.add(*users)
            continue
        group = create_group_with_given_permissions(perms, counter, Group)
        group.user_set.add(*users)
        counter += 1


def get_counter_value(Group):
    """Get the number of next potential group."""
    pattern = r"^Group (\d+)$"
    group = Group.objects.filter(name__iregex=pattern).order_by("name").last()
    if not group:
        return 1
    return int(re.match(pattern, group.name).group(1)) + 1


def create_permissions_mapping(User):
    """Create mapping permissions to users and potential new group name."""
    mapping = defaultdict(set)
    users = User.objects.filter(user_permissions__isnull=False).distinct().iterator()

    for user in users:
        permissions = user.user_permissions.all().order_by("pk")
        perm_pks = tuple([perm.pk for perm in permissions])
        mapping[perm_pks].add(user.pk)
        user.user_permissions.clear()
    return mapping


def get_group_with_given_permissions(permissions, groups):
    """Get group with given set of permissions."""
    for group in groups:
        group_perm_pks = {perm.pk for perm in group.permissions.all()}
        if group_perm_pks == set(permissions):
            return group


def create_group_with_given_permissions(perm_pks, counter, Group):
    """Create new group with given set of permissions."""
    group_name = f"Group {counter:03d}"
    group = Group.objects.create(name=group_name)
    group.permissions.add(*perm_pks)
    return group


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0040_auto_20200415_0443"),
    ]
    operations = [
        migrations.RunPython(
            add_users_to_groups_based_on_users_permissions, migrations.RunPython.noop
        ),
    ]
