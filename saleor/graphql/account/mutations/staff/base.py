from ....core.mutations import ModelDeleteMutation, ModelWithExtRefMutation
from ..base import UserDeleteMixin


class UserDelete(UserDeleteMixin, ModelDeleteMutation, ModelWithExtRefMutation):
    class Meta:
        abstract = True
