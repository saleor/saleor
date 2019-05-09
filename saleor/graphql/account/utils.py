from django.core.exceptions import ValidationError

from ...account import events as customer_events


class UserDeleteMixin:
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        user = info.context.user
        if instance == user:
            raise ValidationError({"id": "You cannot delete your own account."})
        elif instance.is_superuser:
            raise ValidationError({"id": "Cannot delete this account."})


class CustomerDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if instance.is_staff:
            raise ValidationError({"id": "Cannot delete a staff account."})

    @classmethod
    def post_process(cls, info, deleted_count=1):
        customer_events.staff_user_deleted_a_customer_event(
            staff_user=info.context.user, deleted_count=deleted_count
        )


class StaffDeleteMixin(UserDeleteMixin):
    class Meta:
        abstract = True

    @classmethod
    def clean_instance(cls, info, instance):
        super().clean_instance(info, instance)
        if not instance.is_staff:
            raise ValidationError({"id": "Cannot delete a non-staff user."})
