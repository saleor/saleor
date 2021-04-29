from collections import defaultdict
from datetime import date

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....attribute import AttributeType
from ....social import models
from ...attribute.utils import AttributeAssignmentMixin
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.types.common import SocialError
from ...core.utils import clean_seo_fields, validate_slug_and_generate_if_needed
from ...core.types import SeoInput, Upload
from ...utils.validators import check_for_duplicates
from ....core.permissions import SocialPermissions
from ....core.exceptions import PermissionDenied
from ..types import Social
from ....social.error_codes import SocialErrorCode
from ....product import ProductMediaTypes
from ...channel import ChannelContext
from ....product.thumbnails import (
    create_store_background_image_thumbnails,
)
from ...core.utils import (
    clean_seo_fields,
    from_global_id_strict_type,
    get_duplicated_values,
    validate_image_file,
)

class SocialInput(graphene.InputObjectType):
    follow = graphene.Boolean(description="follow/unfollow action.")

class SocialCreate(ModelMutation):
    class Arguments:
        input = SocialInput(
            required=True, description="Fields required to follow/unfollow."
        )

    class Meta:
        description = "Follow/unfollow a store."
        model = models.Social
        permissions = (SocialPermissions.MANAGE_SOCIALS,)
        error_type_class = SocialError
        error_type_field = "social_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info, **data):
        return super().perform_mutation(root, info, **data)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

