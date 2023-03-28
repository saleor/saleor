from django.db.models import Q, Exists, OuterRef

from ....celeryconf import app
from ...models import User, Group

# The batch of size 5000 took about 0.5 s to assign users to groups
BATCH_SIZE = 5000


@app.task
def create_full_channel_access_group_task(group_name):
    full_channel_access_group, _ = Group.objects.get_or_create(
        name=group_name, defaults={"restricted_access_to_channels": False}
    )
    GroupUser = User.groups.through
    group_users = GroupUser.objects.filter(group_id=full_channel_access_group.id)
    users = User.objects.filter(
        Q(is_staff=True) & ~Exists(group_users.filter(user_id=OuterRef("id")))
    ).order_by("-pk")
    user_ids = users.values_list("pk", flat=True)[:BATCH_SIZE]
    if user_ids:
        full_channel_access_group.user_set.add(*user_ids)
        create_full_channel_access_group_task.delay(group_name)
